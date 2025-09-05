"""
Auto-fix suggestion engine for broken links.
"""

import difflib
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from datetime import datetime

from .scanner import ExtractedLink, LinkType
from .checker import LinkResult, LinkStatus


class FixConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class FixSuggestion:
    link_result: LinkResult
    original_url: str
    suggested_url: str
    confidence: FixConfidence
    confidence_score: float
    reason: str
    fix_type: str
    verified: bool = False
    alternatives: List[str] = field(default_factory=list)


@dataclass
class FileDiff:
    file_path: str
    original_content: str
    modified_content: str
    unified_diff: str
    changes: List[Tuple[int, str, str]]


class AutoFixer:
    """Generates and applies fix suggestions for broken links."""
    
    def __init__(
        self,
        confidence_threshold: float = 0.8,
        enable_http_to_https: bool = True,
        enable_trailing_slash: bool = True,
        backup_dir: Optional[str] = None
    ):
        self.confidence_threshold = confidence_threshold
        self.enable_http_to_https = enable_http_to_https
        self.enable_trailing_slash = enable_trailing_slash
        self.backup_dir = Path(backup_dir) if backup_dir else None
        if self.backup_dir:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_suggestions(self, results: List[LinkResult]) -> List[FixSuggestion]:
        suggestions = []
        for result in results:
            if result.status not in (LinkStatus.BROKEN, LinkStatus.WARNING, LinkStatus.REDIRECT):
                continue
            suggestion = self._try_generate_suggestion(result)
            if suggestion:
                suggestions.append(suggestion)
        return suggestions
    
    def _try_generate_suggestion(self, result: LinkResult) -> Optional[FixSuggestion]:
        link = result.link
        
        if result.final_url:
            return FixSuggestion(
                link_result=result, original_url=link.url,
                suggested_url=result.final_url, confidence=FixConfidence.HIGH,
                confidence_score=0.95, reason="Redirect found",
                fix_type="redirect_resolution", verified=True
            )
        
        if self.enable_http_to_https and link.url.startswith('http://'):
            return FixSuggestion(
                link_result=result, original_url=link.url,
                suggested_url=link.url.replace('http://', 'https://', 1),
                confidence=FixConfidence.MEDIUM, confidence_score=0.75,
                reason="Upgrade to HTTPS", fix_type="http_to_https"
            )
        
        if result.suggestion:
            score = 0.85 if '#' in result.suggestion else 0.78
            return FixSuggestion(
                link_result=result, original_url=link.url,
                suggested_url=result.suggestion,
                confidence=FixConfidence.HIGH if score > 0.8 else FixConfidence.MEDIUM,
                confidence_score=score, reason="Similar match found",
                fix_type="fuzzy_match",
                alternatives=result.available_anchors[:5] if result.available_anchors else []
            )
        return None
    
    def generate_diff(self, suggestions: List[FixSuggestion]) -> Dict[str, FileDiff]:
        by_file: Dict[str, List[FixSuggestion]] = {}
        for s in suggestions:
            fp = s.link_result.link.file_path
            by_file.setdefault(fp, []).append(s)
        
        diffs = {}
        for fp, sugs in by_file.items():
            diff = self._generate_file_diff(fp, sugs)
            if diff:
                diffs[fp] = diff
        return diffs
    
    def _generate_file_diff(self, file_path: str, suggestions: List[FixSuggestion]) -> Optional[FileDiff]:
        try:
            original = Path(file_path).read_text(encoding='utf-8')
        except (IOError, UnicodeDecodeError):
            return None
        
        lines = original.split('\n')
        changes = []
        suggestions.sort(key=lambda s: s.link_result.link.line_number, reverse=True)
        
        for s in suggestions:
            idx = s.link_result.link.line_number - 1
            if 0 <= idx < len(lines):
                old = lines[idx]
                new = old.replace(s.original_url, s.suggested_url)
                if old != new:
                    lines[idx] = new
                    changes.append((idx + 1, old, new))
        
        modified = '\n'.join(lines)
        unified = '\n'.join(difflib.unified_diff(
            original.split('\n'), modified.split('\n'),
            fromfile=f"a/{Path(file_path).name}",
            tofile=f"b/{Path(file_path).name}", lineterm=''
        ))
        
        return FileDiff(file_path, original, modified, unified, changes)
    
    def apply_fixes(self, suggestions: List[FixSuggestion], dry_run: bool = False) -> Dict[str, int]:
        applicable = [s for s in suggestions if s.confidence_score >= self.confidence_threshold]
        stats = {'total': len(suggestions), 'applicable': len(applicable), 'applied': 0, 'errors': 0}
        
        if dry_run:
            stats['applied'] = len(applicable)
            return stats
        
        for fp, diff in self.generate_diff(applicable).items():
            try:
                if self.backup_dir:
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    p = Path(fp)
                    (self.backup_dir / f"{p.stem}_{ts}{p.suffix}").write_text(diff.original_content)
                Path(fp).write_text(diff.modified_content, encoding='utf-8')
                stats['applied'] += len(diff.changes)
            except Exception:
                stats['errors'] += 1
        return stats
