"""
Link validation and health checking.

Validates external links via HTTP, internal file references,
and anchor existence within documents.
"""

import re
import time
import urllib.parse
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from requests.exceptions import RequestException, SSLError, Timeout

from .scanner import ExtractedLink, LinkType


class LinkStatus(Enum):
    """Status of a validated link."""
    OK = "ok"
    BROKEN = "broken"
    WARNING = "warning"
    TIMEOUT = "timeout"
    REDIRECT = "redirect"
    IGNORED = "ignored"
    SKIPPED = "skipped"


@dataclass
class LinkResult:
    """Result of validating a single link."""
    link: ExtractedLink
    status: LinkStatus
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    final_url: Optional[str] = None
    redirect_chain: List[str] = field(default_factory=list)
    available_anchors: List[str] = field(default_factory=list)
    suggestion: Optional[str] = None


class LinkChecker:
    """Validates links for health and accessibility."""
    
    DEFAULT_USER_AGENT = (
        "DocLink-Doctor/1.0 "
        "(+https://github.com/gitgoat2003/DocLink-Doctor)"
    )
    
    # Status codes that indicate a working link
    OK_STATUS_CODES = {200, 201, 202, 203, 204}
    
    # Status codes that should be warnings
    WARNING_STATUS_CODES = {301, 302, 303, 307, 308}
    
    # Status codes to ignore (often false positives)
    IGNORE_STATUS_CODES = {403, 429, 503}
    
    def __init__(
        self,
        timeout_seconds: float = 10.0,
        max_redirects: int = 5,
        user_agent: Optional[str] = None,
        retry_attempts: int = 3,
        retry_delay_ms: int = 1000,
        verify_ssl: bool = True,
        rate_limit_per_domain: int = 10,
        ignore_patterns: Optional[List[str]] = None,
        concurrent_requests: int = 10
    ):
        """
        Initialize the link checker.
        
        Args:
            timeout_seconds: HTTP request timeout
            max_redirects: Maximum redirects to follow
            user_agent: Custom user agent string
            retry_attempts: Number of retry attempts for failed requests
            retry_delay_ms: Delay between retries in milliseconds
            verify_ssl: Whether to verify SSL certificates
            rate_limit_per_domain: Max requests per second per domain
            ignore_patterns: URL patterns to ignore
            concurrent_requests: Number of concurrent HTTP requests
        """
        self.timeout = timeout_seconds
        self.max_redirects = max_redirects
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay_ms / 1000.0
        self.verify_ssl = verify_ssl
        self.rate_limit = rate_limit_per_domain
        self.ignore_patterns = ignore_patterns or []
        self.concurrent_requests = concurrent_requests
        
        # Track requests per domain for rate limiting
        self._domain_requests: Dict[str, float] = {}
        
        # Cache for document anchors
        self._anchor_cache: Dict[str, Set[str]] = {}
        
        # Session for connection pooling
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
    
    def check_links(
        self, 
        links: List[ExtractedLink],
        base_path: Optional[Path] = None,
        progress_callback=None
    ) -> List[LinkResult]:
        """
        Check all links and return results.
        
        Args:
            links: List of extracted links to check
            base_path: Base path for resolving relative links
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of LinkResult objects
        """
        results = []
        total = len(links)
        
        # Group links by type for efficient processing
        external_links = []
        internal_links = []
        anchor_links = []
        
        for link in links:
            if self._should_ignore(link.url):
                results.append(LinkResult(
                    link=link,
                    status=LinkStatus.IGNORED,
                    error_message="Matched ignore pattern"
                ))
                continue
            
            if link.link_type == LinkType.EXTERNAL:
                external_links.append(link)
            elif link.link_type == LinkType.GITHUB:
                external_links.append(link)
            elif link.link_type == LinkType.ANCHOR:
                anchor_links.append(link)
            elif link.link_type == LinkType.INTERNAL:
                internal_links.append(link)
            elif link.link_type == LinkType.MAILTO:
                # Skip mailto validation
                results.append(LinkResult(
                    link=link,
                    status=LinkStatus.SKIPPED,
                    error_message="Mailto links not validated"
                ))
        
        # Check external links concurrently
        if external_links:
            external_results = self._check_external_batch(external_links)
            results.extend(external_results)
        
        # Check internal links
        for link in internal_links:
            result = self._check_internal_link(link, base_path)
            results.append(result)
        
        # Check anchor links
        for link in anchor_links:
            result = self._check_anchor_link(link)
            results.append(result)
        
        if progress_callback:
            progress_callback(total, total)
        
        return results
    
    def _should_ignore(self, url: str) -> bool:
        """Check if URL matches ignore patterns."""
        url_lower = url.lower()
        for pattern in self.ignore_patterns:
            if pattern.lower() in url_lower:
                return True
            # Simple wildcard matching
            if '*' in pattern:
                regex = pattern.replace('*', '.*')
                if re.match(regex, url, re.IGNORECASE):
                    return True
        return False
    
    def _check_external_batch(
        self, 
        links: List[ExtractedLink]
    ) -> List[LinkResult]:
        """Check external links concurrently."""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.concurrent_requests) as executor:
            future_to_link = {
                executor.submit(self._check_external_link, link): link
                for link in links
            }
            
            for future in as_completed(future_to_link):
                link = future_to_link[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(LinkResult(
                        link=link,
                        status=LinkStatus.BROKEN,
                        error_message=str(e)
                    ))
        
        return results
    
    def _check_external_link(self, link: ExtractedLink) -> LinkResult:
        """Check a single external link."""
        url = link.url
        
        # Rate limiting
        domain = urllib.parse.urlparse(url).netloc
        self._rate_limit_domain(domain)
        
        # Retry logic with exponential backoff
        last_error = None
        for attempt in range(self.retry_attempts):
            try:
                start_time = time.time()
                response = self._session.get(
                    url,
                    timeout=self.timeout,
                    allow_redirects=True,
                    verify=self.verify_ssl
                )
                elapsed_ms = (time.time() - start_time) * 1000
                
                # Build redirect chain
                redirect_chain = [r.url for r in response.history]
                
                # Determine status
                if response.status_code in self.OK_STATUS_CODES:
                    status = LinkStatus.OK
                    if elapsed_ms > 3000:
                        status = LinkStatus.WARNING
                elif response.status_code in self.WARNING_STATUS_CODES:
                    status = LinkStatus.REDIRECT
                elif response.status_code in self.IGNORE_STATUS_CODES:
                    status = LinkStatus.WARNING
                else:
                    status = LinkStatus.BROKEN
                
                return LinkResult(
                    link=link,
                    status=status,
                    status_code=response.status_code,
                    response_time_ms=elapsed_ms,
                    final_url=response.url if response.url != url else None,
                    redirect_chain=redirect_chain
                )
                
            except Timeout:
                last_error = "Request timed out"
                return LinkResult(
                    link=link,
                    status=LinkStatus.TIMEOUT,
                    error_message=last_error
                )
            except SSLError as e:
                last_error = f"SSL Error: {str(e)}"
                return LinkResult(
                    link=link,
                    status=LinkStatus.BROKEN,
                    error_message=last_error
                )
            except RequestException as e:
                last_error = str(e)
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
        
        return LinkResult(
            link=link,
            status=LinkStatus.BROKEN,
            error_message=last_error
        )
    
    def _rate_limit_domain(self, domain: str):
        """Apply rate limiting for a domain."""
        now = time.time()
        if domain in self._domain_requests:
            elapsed = now - self._domain_requests[domain]
            min_interval = 1.0 / self.rate_limit
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
        self._domain_requests[domain] = time.time()
    
    def _check_internal_link(
        self, 
        link: ExtractedLink, 
        base_path: Optional[Path] = None
    ) -> LinkResult:
        """Check an internal file reference."""
        url = link.url
        
        # Handle anchor in internal link
        anchor = None
        if '#' in url:
            url, anchor = url.split('#', 1)
        
        # Resolve relative path
        if base_path:
            source_dir = Path(link.file_path).parent
            target_path = (source_dir / url).resolve()
        else:
            target_path = Path(url).resolve()
        
        # Check if file exists
        if not target_path.exists():
            # Try common variations
            suggestions = self._find_similar_files(target_path)
            return LinkResult(
                link=link,
                status=LinkStatus.BROKEN,
                error_message="File not found",
                suggestion=suggestions[0] if suggestions else None
            )
        
        # If there's an anchor, validate it
        if anchor:
            anchors = self._extract_anchors_from_file(target_path)
            if anchor not in anchors:
                similar = self._find_similar_anchor(anchor, anchors)
                return LinkResult(
                    link=link,
                    status=LinkStatus.BROKEN,
                    error_message=f"Anchor #{anchor} not found",
                    available_anchors=list(anchors)[:10],
                    suggestion=f"#{similar}" if similar else None
                )
        
        return LinkResult(
            link=link,
            status=LinkStatus.OK
        )
    
    def _check_anchor_link(self, link: ExtractedLink) -> LinkResult:
        """Check an anchor link within the same document."""
        anchor = link.url.lstrip('#')
        file_path = Path(link.file_path)
        
        anchors = self._extract_anchors_from_file(file_path)
        
        if anchor in anchors:
            return LinkResult(
                link=link,
                status=LinkStatus.OK
            )
        
        # Find similar anchors
        similar = self._find_similar_anchor(anchor, anchors)
        
        return LinkResult(
            link=link,
            status=LinkStatus.BROKEN,
            error_message=f"Anchor #{anchor} not found in document",
            available_anchors=list(anchors)[:10],
            suggestion=f"#{similar}" if similar else None
        )
    
    def _extract_anchors_from_file(self, file_path: Path) -> Set[str]:
        """Extract all anchor targets from a markdown file."""
        cache_key = str(file_path)
        if cache_key in self._anchor_cache:
            return self._anchor_cache[cache_key]
        
        anchors = set()
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except (IOError, UnicodeDecodeError):
            return anchors
        
        # Extract headings and convert to anchor format
        heading_pattern = re.compile(r'^#{1,6}\s+(.+)$', re.MULTILINE)
        for match in heading_pattern.finditer(content):
            heading = match.group(1).strip()
            anchor = self._heading_to_anchor(heading)
            anchors.add(anchor)
        
        # Extract explicit anchor tags
        anchor_pattern = re.compile(r'<a\s+(?:name|id)=["\']([^"\']+)["\']', re.IGNORECASE)
        for match in anchor_pattern.finditer(content):
            anchors.add(match.group(1))
        
        self._anchor_cache[cache_key] = anchors
        return anchors
    
    def _heading_to_anchor(self, heading: str) -> str:
        """Convert a heading to GitHub-style anchor."""
        # Remove special characters and convert to lowercase
        anchor = heading.lower()
        anchor = re.sub(r'[^\w\s-]', '', anchor)
        anchor = re.sub(r'\s+', '-', anchor)
        anchor = anchor.strip('-')
        return anchor
    
    def _find_similar_files(self, target_path: Path) -> List[str]:
        """Find files with similar names."""
        suggestions = []
        parent = target_path.parent
        
        if not parent.exists():
            return suggestions
        
        target_name = target_path.name.lower()
        
        for file in parent.iterdir():
            if file.is_file():
                similarity = self._string_similarity(
                    target_name, 
                    file.name.lower()
                )
                if similarity > 0.6:
                    suggestions.append(str(file.relative_to(parent)))
        
        return sorted(suggestions, key=lambda x: self._string_similarity(target_name, x.lower()), reverse=True)
    
    def _find_similar_anchor(
        self, 
        anchor: str, 
        available: Set[str]
    ) -> Optional[str]:
        """Find the most similar anchor from available options."""
        if not available:
            return None
        
        best_match = None
        best_score = 0.0
        
        for candidate in available:
            score = self._string_similarity(anchor.lower(), candidate.lower())
            if score > best_score and score > 0.5:
                best_score = score
                best_match = candidate
        
        return best_match
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate Levenshtein-based similarity ratio."""
        if not s1 or not s2:
            return 0.0
        
        if s1 == s2:
            return 1.0
        
        len1, len2 = len(s1), len(s2)
        
        # Simple Levenshtein distance
        if len1 < len2:
            s1, s2 = s2, s1
            len1, len2 = len2, len1
        
        distances = range(len2 + 1)
        for i, c1 in enumerate(s1):
            new_distances = [i + 1]
            for j, c2 in enumerate(s2):
                if c1 == c2:
                    new_distances.append(distances[j])
                else:
                    new_distances.append(1 + min(
                        distances[j],
                        distances[j + 1],
                        new_distances[-1]
                    ))
            distances = new_distances
        
        distance = distances[-1]
        max_len = max(len1, len2)
        return 1.0 - (distance / max_len)
    
    def close(self):
        """Close the session."""
        self._session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
