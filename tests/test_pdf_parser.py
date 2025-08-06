import pytest
from unittest.mock import Mock, patch
from app.analyzer import schemas


class TestPDFParser:
    def test_match_any_pattern_valid_headings(self, parser):
        """Test that valid chapter headings are correctly identified."""
        valid_headings = [
            "TERMS AND CONDITIONS",
            "PRIVACY POLICY OVERVIEW",
            "A. TERMS; PRIVACY",
            "USER RESPONSIBILITIES"
        ]

        for heading in valid_headings:
            assert parser._match_any_pattern(heading), f"Should match: {heading}"

    def test_match_any_pattern_invalid_headings(self, parser):
        """Test that invalid patterns are rejected."""
        invalid_headings = [
            "This is a regular sentence.",  # Ends with period
            "short",  # Too short
            "This is a very long heading that exceeds the maximum length limit",  # Too long
            "This has too many words to be a valid heading pattern",  # Too many words
            "lowercase heading"  # Not all caps
        ]

        for heading in invalid_headings:
            assert not parser._match_any_pattern(heading), f"Should not match: {heading}"

    def test_is_chapter_valid(self, parser):
        """Test chapter length validation."""
        # Valid chapter (above minimum length)
        long_text = "This is a long chapter " * 10  # Well above 50 chars
        assert parser._is_chapter_valid(long_text)

        # Invalid chapter (below minimum length)
        short_text = "Short"
        assert not parser._is_chapter_valid(short_text)

    # Test file operations with mocking
    @patch('pymupdf.open')
    def test_iter_text_yields_page_content(self, mock_pymupdf_open, parser):
        """Test that iter_text correctly yields text from each page."""
        # Setup mock
        mock_page1 = Mock()
        mock_page1.get_text.return_value = "Page 1 content"
        mock_page2 = Mock()
        mock_page2.get_text.return_value = "Page 2 content"

        mock_doc = Mock()
        mock_doc.__iter__ = Mock(return_value=iter([mock_page1, mock_page2]))
        mock_pymupdf_open.return_value = mock_doc

        # Test
        result = list(parser.iter_text("dummy_path.pdf"))

        # Assertions
        assert result == ["Page 1 content", "Page 2 content"]
        mock_pymupdf_open.assert_called_once_with("dummy_path.pdf")
        mock_page1.get_text.assert_called_once()
        mock_page2.get_text.assert_called_once()

    @patch('pymupdf.open')
    def test_has_identifiable_chapters_found(self, mock_pymupdf_open, parser):
        """Test detection of identifiable chapters when they exist."""
        # Mock page with a valid chapter heading
        mock_page = Mock()
        mock_block = {
            "lines": [{
                "spans": [{"text": "TERMS"}, {"text": " AND"}, {"text": " CONDITIONS"}]
            }]
        }
        mock_page.get_text.return_value = {"blocks": [mock_block]}

        mock_doc = Mock()
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_pymupdf_open.return_value = mock_doc

        result = parser.has_identifiable_chapters("dummy.pdf")

        assert result is True
        mock_pymupdf_open.assert_called_once_with("dummy.pdf")

    @patch('pymupdf.open')
    def test_has_identifiable_chapters_not_found(self, mock_pymupdf_open, parser):
        """Test when no identifiable chapters are found."""
        # Mock page with no valid headings
        mock_page = Mock()
        mock_block = {
            "lines": [{
                "spans": [{"text": "Regular text that is not a heading"}]
            }]
        }
        mock_page.get_text.return_value = {"blocks": [mock_block]}

        mock_doc = Mock()
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_pymupdf_open.return_value = mock_doc

        result = parser.has_identifiable_chapters("dummy.pdf")

        assert result is False

    @patch('pymupdf.open')
    def test_parse_using_re_basic_flow(self, mock_pymupdf_open, parser):
        """Test the main parsing logic with a simple scenario."""
        # Create mock pages with chapter heading and content
        mock_page1 = Mock()
        mock_page1.get_text.return_value = {
            "blocks": [{
                "lines": [
                    {"spans": [{"text": "INTRODUCTION"}]},  # Chapter heading
                    {"spans": [{"text": "This is the introduction content " * 5}]}  # Content
                ]
            }]
        }

        mock_page2 = Mock()
        mock_page2.get_text.return_value = {
            "blocks": [{
                "lines": [
                    {"spans": [{"text": "TERMS AND CONDITIONS"}]},  # New chapter
                    {"spans": [{"text": "These are the terms " * 8}]}  # Content
                ]
            }]
        }

        mock_doc = Mock()
        mock_doc.__len__ = Mock(return_value=2)
        mock_doc.__getitem__ = Mock(side_effect=[mock_page1, mock_page2])
        mock_doc.__iter__ = Mock(return_value=iter([mock_page1, mock_page2]))
        mock_pymupdf_open.return_value = mock_doc

        # Test
        chapters = list(parser.parse_using_re("dummy.pdf"))

        # Assertions
        assert len(chapters) >= 1  # Should have at least one chapter
        assert all(isinstance(chapter, schemas.DocumentChapter) for chapter in chapters)

        # Check first chapter structure
        first_chapter = chapters[0]
        assert hasattr(first_chapter, 'chapter_name')
        assert hasattr(first_chapter, 'chapter_text')
        assert hasattr(first_chapter, 'page_start')
        assert hasattr(first_chapter, 'page_end')

    # Test error handling
    @patch('pymupdf.open')
    def test_handles_missing_file(self, mock_pymupdf_open, parser):
        """Test that file not found errors are properly raised."""
        mock_pymupdf_open.side_effect = FileNotFoundError("File not found")

        with pytest.raises(FileNotFoundError):
            list(parser.iter_text("nonexistent.pdf"))

    @patch('pymupdf.open')
    def test_handles_empty_blocks(self, mock_pymupdf_open, parser):
        """Test handling of pages with no text blocks."""
        mock_page = Mock()
        mock_page.get_text.return_value = {"blocks": []}  # Empty blocks

        mock_doc = Mock()
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_pymupdf_open.return_value = mock_doc

        result = parser.has_identifiable_chapters("dummy.pdf")
        assert result is False  # Should handle gracefully

    @patch('pymupdf.open')
    def test_handles_blocks_without_lines(self, mock_pymupdf_open, parser):
        """Test handling of blocks that don't contain text lines."""
        mock_page = Mock()
        # Block without 'lines' key (e.g., image block)
        mock_page.get_text.return_value = {"blocks": [{"type": "image"}]}

        mock_doc = Mock()
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_pymupdf_open.return_value = mock_doc

        result = parser.has_identifiable_chapters("dummy.pdf")
        assert result is False  # Should handle gracefully

    def test_chapter_validation_edge_cases(self, parser):
        """Test chapter validation with edge cases."""
        # Exactly at minimum length
        text_at_limit = "x" * parser.min_chapter_lenght
        assert parser._is_chapter_valid(text_at_limit)

        # Just below minimum length
        text_below_limit = "x" * (parser.min_chapter_lenght - 1)
        assert not parser._is_chapter_valid(text_below_limit)

        # Empty text
        assert not parser._is_chapter_valid("")

        # Whitespace only
        assert not parser._is_chapter_valid("   ")
