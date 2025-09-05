"""
Tests for anchor link detection - includes Required Test #2.

Required Test #2: Finds missing anchor link in markdown
"""

import pytest
from pathlib import Path

from docdoctor.scanner import ExtractedLink, LinkType
from docdoctor.checker import LinkChecker, LinkStatus


class TestAnchorLinks:
    """Tests for anchor link validation."""
    
    def test_detect_missing_anchor(self, tmp_path):
        """
        REQUIRED TEST #2: Finds missing anchor link in markdown.
        
        This test verifies that DocLink Doctor can detect when an anchor
        link points to a heading that doesn't exist in the document.
        """
        # Create markdown file with broken anchor link
        content = """# Header One

Some content here.

## Header Two

More content.

[Link to nonexistent](#header-three)

This link should be detected as broken.
"""
        
        test_file = tmp_path / "test.md"
        test_file.write_text(content)
        
        # Create link representing the broken anchor
        link = ExtractedLink(
            url='#header-three',
            text='Link to nonexistent',
            line_number=10,
            column=1,
            link_type=LinkType.ANCHOR,
            file_path=str(test_file)
        )
        
        checker = LinkChecker()
        results = checker.check_links([link])
        
        # Verify missing anchor is detected
        assert len(results) == 1
        result = results[0]
        
        assert result.status == LinkStatus.BROKEN
        assert "header-three" in result.error_message.lower() or "not found" in result.error_message.lower()
        assert result.link.link_type == LinkType.ANCHOR
    
    def test_detect_valid_anchor(self, tmp_path):
        """Test that valid anchors are correctly identified."""
        content = """# Header One

Some content.

## Configuration Reference

Config info here.

[Valid Link](#configuration-reference)
"""
        
        test_file = tmp_path / "test.md"
        test_file.write_text(content)
        
        link = ExtractedLink(
            url='#configuration-reference',
            text='Valid Link',
            line_number=10,
            column=1,
            link_type=LinkType.ANCHOR,
            file_path=str(test_file)
        )
        
        checker = LinkChecker()
        results = checker.check_links([link])
        
        assert len(results) == 1
        assert results[0].status == LinkStatus.OK
    
    def test_suggest_similar_anchor(self, tmp_path):
        """Test that similar anchors are suggested for typos."""
        content = """# Getting Started

## Configuration-Reference

Content here.
"""
        
        test_file = tmp_path / "test.md"
        test_file.write_text(content)
        
        # Typo in anchor name
        link = ExtractedLink(
            url='#configuration-options',  # Wrong name
            text='Config',
            line_number=1,
            column=1,
            link_type=LinkType.ANCHOR,
            file_path=str(test_file)
        )
        
        checker = LinkChecker()
        results = checker.check_links([link])
        
        assert len(results) == 1
        result = results[0]
        
        assert result.status == LinkStatus.BROKEN
        # Should suggest the similar anchor
        if result.suggestion:
            assert 'configuration' in result.suggestion.lower()
    
    def test_case_insensitive_anchor_matching(self, tmp_path):
        """Test anchor matching is case-insensitive for GitHub compatibility."""
        content = """# My Awesome Header

Content here.
"""
        
        test_file = tmp_path / "test.md"
        test_file.write_text(content)
        
        # GitHub converts to lowercase with dashes
        link = ExtractedLink(
            url='#my-awesome-header',
            text='Link',
            line_number=1,
            column=1,
            link_type=LinkType.ANCHOR,
            file_path=str(test_file)
        )
        
        checker = LinkChecker()
        results = checker.check_links([link])
        
        assert len(results) == 1
        assert results[0].status == LinkStatus.OK
    
    def test_internal_link_with_anchor(self, tmp_path):
        """Test internal file links that include anchors."""
        # Create target file
        target = tmp_path / "target.md"
        target.write_text("""# Target

## Section One

Content.
""")
        
        source = tmp_path / "source.md"
        
        link = ExtractedLink(
            url='./target.md#section-one',
            text='Link',
            line_number=1,
            column=1,
            link_type=LinkType.INTERNAL,
            file_path=str(source)
        )
        
        checker = LinkChecker()
        results = checker.check_links([link], base_path=tmp_path)
        
        assert len(results) == 1
        assert results[0].status == LinkStatus.OK
    
    def test_internal_link_with_missing_anchor(self, tmp_path):
        """Test internal file links with non-existent anchors."""
        target = tmp_path / "target.md"
        target.write_text("""# Target

## Section One

Content.
""")
        
        source = tmp_path / "source.md"
        
        link = ExtractedLink(
            url='./target.md#section-two',  # Doesn't exist
            text='Link',
            line_number=1,
            column=1,
            link_type=LinkType.INTERNAL,
            file_path=str(source)
        )
        
        checker = LinkChecker()
        results = checker.check_links([link], base_path=tmp_path)
        
        assert len(results) == 1
        assert results[0].status == LinkStatus.BROKEN
