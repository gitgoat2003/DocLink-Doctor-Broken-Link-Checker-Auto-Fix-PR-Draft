"""
Tests for link checker - includes Required Test #1.

Required Test #1: Finds broken external link with mocked HTTP response
"""

import pytest
import responses
from pathlib import Path

from docdoctor.scanner import MarkdownScanner, ExtractedLink, LinkType
from docdoctor.checker import LinkChecker, LinkStatus, LinkResult


class TestLinkChecker:
    """Tests for LinkChecker class."""
    
    @pytest.fixture
    def checker(self):
        return LinkChecker(timeout_seconds=5, retry_attempts=1)
    
    @responses.activate
    def test_detect_broken_external_link(self):
        """
        REQUIRED TEST #1: Finds broken external link with mocked HTTP response.
        
        This test verifies that DocLink Doctor can detect a broken external
        link by mocking an HTTP 404 response.
        """
        # Mock HTTP 404 response
        responses.add(
            responses.GET,
            'https://broken-example.com/notfound',
            status=404
        )
        
        # Create a link to check
        link = ExtractedLink(
            url='https://broken-example.com/notfound',
            text='Broken Link',
            line_number=10,
            column=5,
            link_type=LinkType.EXTERNAL,
            file_path='test.md'
        )
        
        # Check the link
        checker = LinkChecker(timeout_seconds=5, retry_attempts=1)
        results = checker.check_links([link])
        
        # Verify the link is detected as broken
        assert len(results) == 1
        result = results[0]
        
        assert result.status == LinkStatus.BROKEN
        assert result.status_code == 404
        assert 'broken-example.com' in result.link.url
    
    @responses.activate
    def test_detect_working_external_link(self):
        """Test that working links are correctly identified."""
        responses.add(
            responses.GET,
            'https://working-example.com/page',
            status=200
        )
        
        link = ExtractedLink(
            url='https://working-example.com/page',
            text='Working Link',
            line_number=5,
            column=1,
            link_type=LinkType.EXTERNAL,
            file_path='test.md'
        )
        
        checker = LinkChecker(timeout_seconds=5, retry_attempts=1)
        results = checker.check_links([link])
        
        assert len(results) == 1
        assert results[0].status == LinkStatus.OK
        assert results[0].status_code == 200
    
    @responses.activate
    def test_detect_redirect(self):
        """Test that redirects are detected."""
        responses.add(
            responses.GET,
            'https://old-url.com/page',
            status=301,
            headers={'Location': 'https://new-url.com/page'}
        )
        responses.add(
            responses.GET,
            'https://new-url.com/page',
            status=200
        )
        
        link = ExtractedLink(
            url='https://old-url.com/page',
            text='Redirect Link',
            line_number=1,
            column=1,
            link_type=LinkType.EXTERNAL,
            file_path='test.md'
        )
        
        checker = LinkChecker(timeout_seconds=5, retry_attempts=1)
        results = checker.check_links([link])
        
        assert len(results) == 1
        # After following redirect, should be OK
        assert results[0].status in (LinkStatus.OK, LinkStatus.REDIRECT)
    
    @responses.activate
    def test_handle_timeout(self):
        """Test that timeouts are handled gracefully."""
        import requests
        
        responses.add(
            responses.GET,
            'https://slow-server.com/page',
            body=requests.exceptions.Timeout()
        )
        
        link = ExtractedLink(
            url='https://slow-server.com/page',
            text='Slow Link',
            line_number=1,
            column=1,
            link_type=LinkType.EXTERNAL,
            file_path='test.md'
        )
        
        checker = LinkChecker(timeout_seconds=1, retry_attempts=1)
        results = checker.check_links([link])
        
        assert len(results) == 1
        assert results[0].status == LinkStatus.TIMEOUT
    
    def test_check_internal_link_exists(self, tmp_path):
        """Test checking internal links that exist."""
        # Create a test file
        test_file = tmp_path / "test.md"
        target_file = tmp_path / "target.md"
        target_file.write_text("# Target File\n\nContent here.")
        
        link = ExtractedLink(
            url='./target.md',
            text='Target',
            line_number=1,
            column=1,
            link_type=LinkType.INTERNAL,
            file_path=str(test_file)
        )
        
        checker = LinkChecker()
        results = checker.check_links([link], base_path=tmp_path)
        
        assert len(results) == 1
        assert results[0].status == LinkStatus.OK
    
    def test_check_internal_link_missing(self, tmp_path):
        """Test checking internal links that don't exist."""
        test_file = tmp_path / "test.md"
        
        link = ExtractedLink(
            url='./nonexistent.md',
            text='Missing',
            line_number=1,
            column=1,
            link_type=LinkType.INTERNAL,
            file_path=str(test_file)
        )
        
        checker = LinkChecker()
        results = checker.check_links([link], base_path=tmp_path)
        
        assert len(results) == 1
        assert results[0].status == LinkStatus.BROKEN
        assert "not found" in results[0].error_message.lower()
