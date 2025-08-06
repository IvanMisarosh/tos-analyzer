import pytest
from unittest.mock import Mock
from app.analyzer.pdf_parser import PDFParser
from app.auth.service import AuthService
from app.auth import schemas
from app import models
from sqlalchemy.orm import Session


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


@pytest.fixture
def auth_service():
    """Create AuthService instance for testing."""
    return AuthService()


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return models.User(
        id=1,
        username="testuser",
        hashed_password="$2b$12$hash"  # Mock bcrypt hash
    )


@pytest.fixture
def user_create_data():
    """Create sample user creation data."""
    return schemas.UserCreate(
        username="newuser",
        password="password123"
    )
