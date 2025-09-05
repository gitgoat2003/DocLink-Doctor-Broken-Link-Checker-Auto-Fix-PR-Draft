"""
Ignore pattern parser for .doctorignore files.
"""

import re
import fnmatch
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple


@dataclass
class IgnoreRule:
    pattern: str
    is_regex: bool = False
    is_negation: bool = False
    reason: Optional[str] = None
    source_file: Optional[str] = None
    line_number: int = 0


class IgnoreParser:
    """Parses .doctorignore files and matches URLs/paths against patterns."""
    
    DEFAULT_IGNORES = [
        'localhost', '127.0.0.1', '0.0.0.0',
        '*.local', '10.*.*.*', '192.168.*.*',
    ]
    
    def __init__(
        self,
        ignore_file: Optional[str] = None,
        use_defaults: bool = True,
        case_insensitive: bool = True
    ):
        self.rules: List[IgnoreRule] = []
        self.case_insensitive = case_insensitive
        
        if use_defaults:
            for pattern in self.DEFAULT_IGNORES:
                self.rules.append(IgnoreRule(pattern, reason="default"))
        
        if ignore_file:
            self.load_file(ignore_file)
    
    def load_file(self, file_path: str) -> int:
        path = Path(file_path)
        if not path.exists():
            return 0
        
        count = 0
        for i, line in enumerate(path.read_text().splitlines(), 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            rule = self._parse_line(line, str(path), i)
            if rule:
                self.rules.append(rule)
                count += 1
        
        return count
    
    def _parse_line(self, line: str, source: str, line_num: int) -> Optional[IgnoreRule]:
        is_negation = line.startswith('!')
        if is_negation:
            line = line[1:]
        
        is_regex = line.startswith('regex:')
        if is_regex:
            line = line[6:]
        
        return IgnoreRule(
            pattern=line,
            is_regex=is_regex,
            is_negation=is_negation,
            source_file=source,
            line_number=line_num
        )
    
    def should_ignore(self, url: str) -> Tuple[bool, Optional[str]]:
        """Check if URL should be ignored. Returns (should_ignore, reason)."""
        test_url = url.lower() if self.case_insensitive else url
        
        for rule in self.rules:
            pattern = rule.pattern.lower() if self.case_insensitive else rule.pattern
            
            matched = False
            if rule.is_regex:
                try:
                    matched = bool(re.search(pattern, test_url))
                except re.error:
                    continue
            elif '*' in pattern:
                matched = fnmatch.fnmatch(test_url, pattern)
            else:
                matched = pattern in test_url
            
            if matched:
                if rule.is_negation:
                    return False, None
                return True, rule.reason or f"Matched: {rule.pattern}"
        
        return False, None
    
    def add_pattern(self, pattern: str, reason: Optional[str] = None):
        self.rules.append(IgnoreRule(pattern, reason=reason))
    
    def get_patterns(self) -> List[str]:
        return [r.pattern for r in self.rules if not r.is_negation]
