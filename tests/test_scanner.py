"""Tests for the markdown scanner module."""

import pytest
from pathlib import Path

from docdoctor.scanner import MarkdownScanner, LinkType, ExtractedLink


class TestMarkdownScanner:
    """Tests for MarkdownScanner class."""
    
    @pytest.fixture
    def fixtures_dir(self):
        return Path(__file__).parent / "fixtures" / "markdown"
    
    @pytest.fixture
    def scanner(self, fixtures_dir):
        return MarkdownScanner(str(fixtures_dir))
    
    def test_discover_markdown_files(self, scanner):
        """Test that markdown files are discovered."""
        files = list(scanner.discover_files())
        assert len(files) >= 1
        assert all(f.suffix == '.md' for f in files)
    
    def test_extract_links_from_file(self, fixtures_dir):
        """Test link extraction from a markdown file."""
        scanner = MarkdownScanner(str(fixtures_dir))
        sample_file = fixtures_dir / "sample.md"
        
        links = scanner.extract_links(sample_file)
        
        assert len(links) > 0
        assert all(isinstance(link, ExtractedLink) for link in links)
    
    def test_link_type_classification(self, fixtures_dir):
        """Test that links are correctly classified by type."""
        scanner = MarkdownScanner(str(fixtures_dir))
        sample_file = fixtures_dir / "sample.md"
        
        links = scanner.extract_links(sample_file)
        
        # Should have external links
        external = [l for l in links if l.link_type == LinkType.EXTERNAL]
        assert len(external) > 0
        
        # Should have internal links
        internal = [l for l in links if l.link_type == LinkType.INTERNAL]
        assert len(internal) > 0
        
        # Should have anchor links
        anchors = [l for l in links if l.link_type == LinkType.ANCHOR]
        assert len(anchors) > 0
    
    def test_extract_link_text(self, fixtures_dir):
        """Test that link text is extracted correctly."""
        scanner = MarkdownScanner(str(fixtures_dir))
        sample_file = fixtures_dir / "sample.md"
        
        links = scanner.extract_links(sample_file)
        
        # Find a specific link
        example_link = next(
            (l for l in links if "example.com" in l.url), 
            None
        )
        assert example_link is not None
        assert example_link.text == "Working External Link"
    
    def test_line_numbers_are_correct(self, fixtures_dir):
        """Test that line numbers are captured correctly."""
        scanner = MarkdownScanner(str(fixtures_dir))
        sample_file = fixtures_dir / "sample.md"
        
        links = scanner.extract_links(sample_file)
        
        for link in links:
            assert link.line_number > 0
            assert link.column > 0
    
    def test_scan_all_files(self, scanner):
        """Test scanning all files in directory."""
        all_links = scanner.scan_all()
        
        assert len(all_links) > 0
        
        # Should have links from multiple files
        file_paths = set(link.file_path for link in all_links)
        assert len(file_paths) >= 1
