"""
Markdown file scanner and link extractor.

Handles recursive directory scanning, markdown file discovery,
and extraction of links with classification.
"""

import os
import re
from enum import Enum
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Generator


class LinkType(Enum):
    """Classification of link types."""
    EXTERNAL = "external"      # http:// or https://
    INTERNAL = "internal"      # Relative file paths
    ANCHOR = "anchor"          # #section-name
    MAILTO = "mailto"          # mailto: links
    GITHUB = "github"          # GitHub blob/tree URLs


@dataclass
class ExtractedLink:
    """Represents an extracted link from a markdown file."""
    url: str
    text: str
    line_number: int
    column: int
    link_type: LinkType
    file_path: str
    context_before: str = ""
    context_after: str = ""
    raw_match: str = ""


class MarkdownScanner:
    """Scans directories for markdown files and extracts links."""
    
    # Regex patterns for different markdown link formats
    MARKDOWN_LINK_PATTERN = re.compile(
        r'\[([^\]]*)\]\(([^)]+)\)',
        re.MULTILINE
    )
    
    REFERENCE_LINK_PATTERN = re.compile(
        r'\[([^\]]+)\]\[([^\]]*)\]',
        re.MULTILINE
    )
    
    REFERENCE_DEF_PATTERN = re.compile(
        r'^\[([^\]]+)\]:\s*(.+)$',
        re.MULTILINE
    )
    
    AUTOLINK_PATTERN = re.compile(
        r'<(https?://[^>]+)>',
        re.MULTILINE
    )
    
    # URL patterns
    URL_PATTERN = re.compile(
        r'^https?://',
        re.IGNORECASE
    )
    
    GITHUB_URL_PATTERN = re.compile(
        r'github\.com/[^/]+/[^/]+/(blob|tree|raw)/',
        re.IGNORECASE
    )
    
    MAILTO_PATTERN = re.compile(
        r'^mailto:',
        re.IGNORECASE
    )
    
    ANCHOR_PATTERN = re.compile(
        r'^#[\w-]+$'
    )
    
    # File extensions to scan
    MARKDOWN_EXTENSIONS = {'.md', '.markdown', '.mkd', '.mdown'}
    
    def __init__(
        self,
        root_path: str,
        recursive: bool = True,
        max_depth: Optional[int] = None,
        exclude_patterns: Optional[List[str]] = None,
        follow_symlinks: bool = False
    ):
        """
        Initialize the markdown scanner.
        
        Args:
            root_path: Root directory to scan
            recursive: Whether to scan subdirectories
            max_depth: Maximum directory depth (None for unlimited)
            exclude_patterns: Glob patterns to exclude
            follow_symlinks: Whether to follow symbolic links
        """
        self.root_path = Path(root_path).resolve()
        self.recursive = recursive
        self.max_depth = max_depth
        self.exclude_patterns = exclude_patterns or []
        self.follow_symlinks = follow_symlinks
        
        # Default exclusions
        self._default_excludes = {
            'node_modules', '.git', '.venv', 'venv', 
            '__pycache__', '.tox', 'dist', 'build'
        }
    
    def discover_files(self) -> Generator[Path, None, None]:
        """
        Discover all markdown files in the directory tree.
        
        Yields:
            Path objects for each discovered markdown file
        """
        if self.root_path.is_file():
            if self._is_markdown_file(self.root_path):
                yield self.root_path
            return
        
        for path in self._walk_directory(self.root_path, depth=0):
            if self._is_markdown_file(path) and not self._is_excluded(path):
                yield path
    
    def _walk_directory(
        self, 
        directory: Path, 
        depth: int
    ) -> Generator[Path, None, None]:
        """Recursively walk directory tree."""
        if self.max_depth is not None and depth > self.max_depth:
            return
        
        try:
            entries = list(directory.iterdir())
        except PermissionError:
            return
        
        for entry in entries:
            if entry.name in self._default_excludes:
                continue
            
            if entry.is_file():
                yield entry
            elif entry.is_dir() and self.recursive:
                if entry.is_symlink() and not self.follow_symlinks:
                    continue
                yield from self._walk_directory(entry, depth + 1)
    
    def _is_markdown_file(self, path: Path) -> bool:
        """Check if a file is a markdown file."""
        if path.suffix.lower() in self.MARKDOWN_EXTENSIONS:
            return True
        # Handle README without extension
        if path.name.upper() == 'README':
            return True
        return False
    
    def _is_excluded(self, path: Path) -> bool:
        """Check if a path matches exclusion patterns."""
        path_str = str(path)
        for pattern in self.exclude_patterns:
            if pattern in path_str:
                return True
        return False
    
    def extract_links(self, file_path: Path) -> List[ExtractedLink]:
        """
        Extract all links from a markdown file.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            List of ExtractedLink objects
        """
        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, IOError):
            try:
                content = file_path.read_text(encoding='latin-1')
            except IOError:
                return []
        
        links = []
        lines = content.split('\n')
        
        # Build reference link definitions
        reference_defs = {}
        for match in self.REFERENCE_DEF_PATTERN.finditer(content):
            ref_id = match.group(1).lower()
            ref_url = match.group(2).strip()
            reference_defs[ref_id] = ref_url
        
        # Process line by line for accurate line numbers
        char_offset = 0
        for line_num, line in enumerate(lines, start=1):
            # Standard markdown links [text](url)
            for match in self.MARKDOWN_LINK_PATTERN.finditer(line):
                url = match.group(2).strip()
                # Handle URLs with titles
                if ' ' in url:
                    url = url.split()[0].strip('"\'')
                
                link = self._create_link(
                    url=url,
                    text=match.group(1),
                    line_number=line_num,
                    column=match.start() + 1,
                    file_path=str(file_path),
                    context_before=lines[max(0, line_num-2):line_num-1],
                    context_after=lines[line_num:min(len(lines), line_num+1)],
                    raw_match=match.group(0)
                )
                if link:
                    links.append(link)
            
            # Reference-style links [text][ref]
            for match in self.REFERENCE_LINK_PATTERN.finditer(line):
                ref_id = match.group(2).lower() or match.group(1).lower()
                if ref_id in reference_defs:
                    link = self._create_link(
                        url=reference_defs[ref_id],
                        text=match.group(1),
                        line_number=line_num,
                        column=match.start() + 1,
                        file_path=str(file_path),
                        context_before=lines[max(0, line_num-2):line_num-1],
                        context_after=lines[line_num:min(len(lines), line_num+1)],
                        raw_match=match.group(0)
                    )
                    if link:
                        links.append(link)
            
            # Autolinks <https://...>
            for match in self.AUTOLINK_PATTERN.finditer(line):
                link = self._create_link(
                    url=match.group(1),
                    text=match.group(1),
                    line_number=line_num,
                    column=match.start() + 1,
                    file_path=str(file_path),
                    context_before=lines[max(0, line_num-2):line_num-1],
                    context_after=lines[line_num:min(len(lines), line_num+1)],
                    raw_match=match.group(0)
                )
                if link:
                    links.append(link)
            
            char_offset += len(line) + 1
        
        return links
    
    def _create_link(
        self,
        url: str,
        text: str,
        line_number: int,
        column: int,
        file_path: str,
        context_before: List[str],
        context_after: List[str],
        raw_match: str
    ) -> Optional[ExtractedLink]:
        """Create an ExtractedLink with proper type classification."""
        if not url:
            return None
        
        # Classify the link type
        link_type = self._classify_link(url)
        
        return ExtractedLink(
            url=url,
            text=text,
            line_number=line_number,
            column=column,
            link_type=link_type,
            file_path=file_path,
            context_before='\n'.join(context_before),
            context_after='\n'.join(context_after),
            raw_match=raw_match
        )
    
    def _classify_link(self, url: str) -> LinkType:
        """Classify a URL into a link type."""
        if self.MAILTO_PATTERN.match(url):
            return LinkType.MAILTO
        
        if self.URL_PATTERN.match(url):
            if self.GITHUB_URL_PATTERN.search(url):
                return LinkType.GITHUB
            return LinkType.EXTERNAL
        
        if url.startswith('#'):
            return LinkType.ANCHOR
        
        return LinkType.INTERNAL
    
    def scan_all(self) -> List[ExtractedLink]:
        """
        Scan all markdown files and extract all links.
        
        Returns:
            List of all extracted links from all files
        """
        all_links = []
        for file_path in self.discover_files():
            links = self.extract_links(file_path)
            all_links.extend(links)
        return all_links
    
    def get_file_count(self) -> int:
        """Get the count of markdown files to be scanned."""
        return sum(1 for _ in self.discover_files())
