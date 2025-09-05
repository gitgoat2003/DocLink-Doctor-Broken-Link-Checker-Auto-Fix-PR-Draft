"""Tests for auto-fix module."""

import pytest
from pathlib import Path

from docdoctor.scanner import ExtractedLink, LinkType
from docdoctor.checker import LinkResult, LinkStatus
from docdoctor.autofix import AutoFixer, FixSuggestion, FixConfidence


class TestAutoFixer:
    """Tests for AutoFixer class."""
    
    @pytest.fixture
    def fixer(self):
        return AutoFixer()
    
    def test_generate_redirect_suggestion(self, fixer):
        """Test generating suggestion for redirected URLs."""
        link = ExtractedLink(
            url='https://old-url.com/page',
            text='Link',
            line_number=1,
            column=1,
            link_type=LinkType.EXTERNAL,
            file_path='test.md'
        )
        
        result = LinkResult(
            link=link,
            status=LinkStatus.REDIRECT,
            status_code=301,
            final_url='https://new-url.com/page'
        )
        
        suggestions = fixer.generate_suggestions([result])
        
        assert len(suggestions) == 1
        assert suggestions[0].suggested_url == 'https://new-url.com/page'
        assert suggestions[0].confidence == FixConfidence.HIGH
    
    def test_generate_http_to_https_suggestion(self, fixer):
        """Test suggesting HTTPS upgrade."""
        link = ExtractedLink(
            url='http://insecure-site.com/page',
            text='Link',
            line_number=1,
            column=1,
            link_type=LinkType.EXTERNAL,
            file_path='test.md'
        )
        
        result = LinkResult(
            link=link,
            status=LinkStatus.BROKEN,
            status_code=None
        )
        
        suggestions = fixer.generate_suggestions([result])
        
        assert len(suggestions) == 1
        assert suggestions[0].suggested_url == 'https://insecure-site.com/page'
        assert 'https' in suggestions[0].reason.lower()
    
    def test_generate_diff(self, fixer, tmp_path):
        """Test diff generation for fixes."""
        test_file = tmp_path / "test.md"
        test_file.write_text("Visit [link](http://example.com) for info.\n")
        
        link = ExtractedLink(
            url='http://example.com',
            text='link',
            line_number=1,
            column=7,
            link_type=LinkType.EXTERNAL,
            file_path=str(test_file)
        )
        
        result = LinkResult(link=link, status=LinkStatus.BROKEN)
        
        suggestions = fixer.generate_suggestions([result])
        diffs = fixer.generate_diff(suggestions)
        
        assert str(test_file) in diffs
        diff = diffs[str(test_file)]
        assert 'https://example.com' in diff.modified_content
    
    def test_apply_fixes_dry_run(self, fixer, tmp_path):
        """Test dry-run mode doesn't modify files."""
        test_file = tmp_path / "test.md"
        original = "Visit [link](http://example.com) for info.\n"
        test_file.write_text(original)
        
        link = ExtractedLink(
            url='http://example.com',
            text='link',
            line_number=1,
            column=7,
            link_type=LinkType.EXTERNAL,
            file_path=str(test_file)
        )
        
        result = LinkResult(link=link, status=LinkStatus.BROKEN)
        suggestions = fixer.generate_suggestions([result])
        
        stats = fixer.apply_fixes(suggestions, dry_run=True)
        
        # File should not be modified
        assert test_file.read_text() == original
        assert stats['applied'] > 0
