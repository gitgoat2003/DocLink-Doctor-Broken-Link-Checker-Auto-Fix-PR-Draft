"""
Tests for ignore file patterns - includes Required Test #3.

Required Test #3: Respects ignore file patterns
"""

import pytest
from pathlib import Path

from docdoctor.ignore import IgnoreParser, IgnoreRule
from docdoctor.scanner import ExtractedLink, LinkType
from docdoctor.checker import LinkChecker, LinkStatus


class TestIgnorePatterns:
    """Tests for ignore file pattern handling."""
    
    def test_respect_ignore_patterns(self, tmp_path):
        """
        REQUIRED TEST #3: Respects ignore file patterns.
        
        This test verifies that DocLink Doctor respects patterns
        defined in the .doctorignore file and skips matching URLs.
        """
        # Create .doctorignore with patterns
        ignore_content = """# Ignore file for testing
https://example.com/*
*localhost*
192.168.*.*
"""
        
        ignore_file = tmp_path / ".doctorignore"
        ignore_file.write_text(ignore_content)
        
        # Parse the ignore file
        parser = IgnoreParser(str(ignore_file), use_defaults=False)
        
        # Test URLs that should be ignored
        should_ignore, reason = parser.should_ignore("https://example.com/page")
        assert should_ignore is True
        assert reason is not None
        
        should_ignore, reason = parser.should_ignore("http://localhost:3000/api")
        assert should_ignore is True
        
        should_ignore, reason = parser.should_ignore("http://192.168.1.1/config")
        assert should_ignore is True
        
        # Test URL that should NOT be ignored
        should_ignore, reason = parser.should_ignore("https://github.com/user/repo")
        assert should_ignore is False
    
    def test_checker_uses_ignore_patterns(self, tmp_path):
        """Test that the checker actually ignores URLs matching patterns."""
        ignore_file = tmp_path / ".doctorignore"
        ignore_file.write_text("*example.com*\n*localhost*\n")
        
        parser = IgnoreParser(str(ignore_file), use_defaults=False)
        ignore_patterns = parser.get_patterns()
        
        links = [
            ExtractedLink(
                url='https://example.com/ignored',
                text='Ignored',
                line_number=1,
                column=1,
                link_type=LinkType.EXTERNAL,
                file_path='test.md'
            ),
            ExtractedLink(
                url='http://localhost:8080/api',
                text='Local',
                line_number=2,
                column=1,
                link_type=LinkType.EXTERNAL,
                file_path='test.md'
            ),
        ]
        
        checker = LinkChecker(ignore_patterns=ignore_patterns)
        results = checker.check_links(links)
        
        # Both should be ignored
        assert len(results) == 2
        assert all(r.status == LinkStatus.IGNORED for r in results)
    
    def test_glob_pattern_matching(self):
        """Test glob pattern matching in ignore rules."""
        parser = IgnoreParser(use_defaults=False)
        parser.add_pattern("*.internal.company.com")
        parser.add_pattern("docs/draft/*")
        
        # Should match
        assert parser.should_ignore("https://api.internal.company.com/v1")[0] is True
        assert parser.should_ignore("docs/draft/wip.md")[0] is True
        
        # Should not match
        assert parser.should_ignore("https://company.com/public")[0] is False
        assert parser.should_ignore("docs/published/guide.md")[0] is False
    
    def test_regex_pattern_matching(self):
        """Test regex pattern support."""
        parser = IgnoreParser(use_defaults=False)
        parser.rules.append(IgnoreRule(
            pattern=r"https://api\.example\.com/v\d+/.*",
            is_regex=True
        ))
        
        assert parser.should_ignore("https://api.example.com/v1/users")[0] is True
        assert parser.should_ignore("https://api.example.com/v2/items")[0] is True
        assert parser.should_ignore("https://api.example.com/latest/users")[0] is False
    
    def test_default_ignores(self):
        """Test that default ignores include localhost."""
        parser = IgnoreParser(use_defaults=True)
        
        assert parser.should_ignore("http://localhost:3000")[0] is True
        assert parser.should_ignore("http://127.0.0.1:8080")[0] is True
        assert parser.should_ignore("http://0.0.0.0:5000")[0] is True
    
    def test_negation_patterns(self, tmp_path):
        """Test negation patterns that un-ignore URLs."""
        ignore_file = tmp_path / ".doctorignore"
        ignore_file.write_text("""
*example.com*
!https://example.com/important
""")
        
        parser = IgnoreParser(str(ignore_file), use_defaults=False)
        
        # Should be ignored (matches first pattern)
        assert parser.should_ignore("https://example.com/random")[0] is True
        
        # Should NOT be ignored (matches negation)
        should_ignore, _ = parser.should_ignore("https://example.com/important")
        assert should_ignore is False
    
    def test_case_insensitive_matching(self):
        """Test case-insensitive pattern matching."""
        parser = IgnoreParser(use_defaults=False, case_insensitive=True)
        parser.add_pattern("*EXAMPLE.COM*")
        
        assert parser.should_ignore("https://example.com/page")[0] is True
        assert parser.should_ignore("https://EXAMPLE.COM/PAGE")[0] is True
    
    def test_load_ignore_file(self, tmp_path):
        """Test loading patterns from file."""
        ignore_file = tmp_path / ".doctorignore"
        ignore_file.write_text("""
# This is a comment
pattern1
pattern2
# Another comment
pattern3
""")
        
        parser = IgnoreParser(str(ignore_file), use_defaults=False)
        
        patterns = parser.get_patterns()
        assert len(patterns) == 3
        assert "pattern1" in patterns
        assert "pattern2" in patterns
        assert "pattern3" in patterns
    
    def test_empty_ignore_file(self, tmp_path):
        """Test handling of empty ignore file."""
        ignore_file = tmp_path / ".doctorignore"
        ignore_file.write_text("")
        
        parser = IgnoreParser(str(ignore_file), use_defaults=False)
        
        assert len(parser.get_patterns()) == 0
    
    def test_missing_ignore_file(self, tmp_path):
        """Test handling of missing ignore file."""
        parser = IgnoreParser(
            str(tmp_path / "nonexistent.ignore"),
            use_defaults=False
        )
        
        # Should not raise, just have no patterns
        assert len(parser.get_patterns()) == 0
