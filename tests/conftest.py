import pytest
from unittest.mock import Mock
from app.analyzer.pdf_parser import PDFParser


@pytest.fixture
def parser():
    """Standard parser instance for testing."""
    return PDFParser(min_chapter_lenght=50, max_chapter_heading_lenght=80, max_words_per_heading=4)


@pytest.fixture
def mock_doc():
    """Mock PDF document for testing."""
    mock_doc = Mock()
    mock_doc.__len__ = Mock(return_value=2)  # 2 pages
    mock_doc.__iter__ = Mock(return_value=iter([Mock(), Mock()]))
    return mock_doc
