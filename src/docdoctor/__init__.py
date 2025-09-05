"""
DocLink Doctor - Documentation Link Health Checker

A CLI tool that scans documentation files for broken links,
missing anchors, and generates auto-fix suggestions.
"""

__version__ = "1.0.0"
__author__ = "DocLink Doctor Team"

from .scanner import MarkdownScanner, LinkType
from .checker import LinkChecker, LinkStatus
from .autofix import AutoFixer, FixSuggestion
from .reporter import Reporter, ReportFormat
from .ignore import IgnoreParser

__all__ = [
    "MarkdownScanner",
    "LinkType",
    "LinkChecker", 
    "LinkStatus",
    "AutoFixer",
    "FixSuggestion",
    "Reporter",
    "ReportFormat",
    "IgnoreParser",
]
