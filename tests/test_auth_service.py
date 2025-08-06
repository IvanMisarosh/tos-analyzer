import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
from fastapi import HTTPException, status
import jwt
from app.auth.service import AuthService
from app.config import settings


class TestPasswordOperations:
    def test_password_verification_with_correct_password(self, auth_service):
        password = "test_password_123"
        hashed = auth_service.get_password_hash(password)

        assert auth_service.verify_password(password, hashed) is True

    def test_password_verification_with_incorrect_password(self, auth_service):
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = auth_service.get_password_hash(password)

        assert auth_service.verify_password(wrong_password, hashed) is False

    def test_same_password_creates_different_hashes(self, auth_service):
        password = "test_password_123"
        hash1 = auth_service.get_password_hash(password)
        hash2 = auth_service.get_password_hash(password)

        assert hash1 != hash2
        assert auth_service.verify_password(password, hash1) is True
        assert auth_service.verify_password(password, hash2) is True


class TestUserOperations:

    def test_get_user_by_username_existing_user(self, auth_service, mock_db, sample_user):
        mock_db.query().filter().first.return_value = sample_user

        result = auth_service.get_user_by_username(mock_db, "testuser")

        assert result == sample_user

    def test_get_user_by_username_non_existing_user(self, auth_service, mock_db):
        mock_db.query().filter().first.return_value = None

        result = auth_service.get_user_by_username(mock_db, "nonexistent")

        assert result is None

    @patch.object(AuthService, 'get_user_by_username')
    @patch.object(AuthService, 'get_password_hash')
    def test_create_user_success(
            self,
            mock_hash,
            mock_get_user,
            auth_service,
            mock_db,
            user_create_data):
        mock_get_user.return_value = None  # User doesn't exist
        mock_hash.return_value = "hashed_password"
        mock_db.refresh = Mock()

        result = auth_service.create_user(mock_db, user_create_data)

        mock_get_user.assert_called_once_with(mock_db, "newuser")
        mock_hash.assert_called_once_with("password123")
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        assert result.username == "newuser"
        assert result.hashed_password == "hashed_password"

    @patch.object(AuthService, 'get_user_by_username')
    def test_create_user_username_already_exists(
            self,
            mock_get_user,
            auth_service,
            mock_db,
            user_create_data,
            sample_user):
        mock_get_user.return_value = sample_user  # User already exists

        with pytest.raises(HTTPException) as exc_info:
            auth_service.create_user(mock_db, user_create_data)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Username already registered" in exc_info.value.detail
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()


class TestAuthentication:

    @patch.object(AuthService, 'get_user_by_username')
    @patch.object(AuthService, 'verify_password')
    def test_authenticate_user_success(
            self,
            mock_verify,
            mock_get_user,
            auth_service,
            mock_db,
            sample_user):
        mock_get_user.return_value = sample_user
        mock_verify.return_value = True

        result = auth_service.authenticate_user(mock_db, "testuser", "correct_password")

        assert result == sample_user
        mock_get_user.assert_called_once_with(mock_db, "testuser")
        mock_verify.assert_called_once_with("correct_password", sample_user.hashed_password)

    @patch.object(AuthService, 'get_user_by_username')
    def test_authenticate_user_not_found(self, mock_get_user, auth_service, mock_db):
        mock_get_user.return_value = None

        result = auth_service.authenticate_user(mock_db, "nonexistent", "password")

        assert result is None

    @patch.object(AuthService, 'get_user_by_username')
    @patch.object(AuthService, 'verify_password')
    def test_authenticate_user_wrong_password(
            self,
            mock_verify,
            mock_get_user,
            auth_service,
            mock_db,
            sample_user):
        mock_get_user.return_value = sample_user
        mock_verify.return_value = False

        result = auth_service.authenticate_user(mock_db, "testuser", "wrong_password")

        assert result is None


class TestTokenOperations:

    @patch('app.auth.service.datetime')
    def test_create_access_token_with_expiration(self, mock_datetime, auth_service):
        """Test access token creation with custom expiration."""
        # Use current time to avoid expiration issues during decode
        fixed_time = datetime.now(timezone.utc)
        mock_datetime.now.return_value = fixed_time

        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=30)

        token = auth_service.create_access_token(data, expires_delta)

        # Decode token without expiration verification to test content
        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False}
        )
        assert decoded["sub"] == "testuser"
        # Verify expiration is set correctly
        expected_exp = int((fixed_time + expires_delta).timestamp())
        assert decoded["exp"] == expected_exp

    @patch('app.auth.service.datetime')
    def test_create_access_token_default_expiration(self, mock_datetime, auth_service):
        """Test access token creation with default expiration."""
        fixed_time = datetime.now(timezone.utc)
        mock_datetime.now.return_value = fixed_time

        data = {"sub": "testuser"}

        token = auth_service.create_access_token(data)

        # Decode without expiration verification to test content
        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False}
        )
        expected_exp = int(
            (fixed_time
             + timedelta(
                 minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp())
        assert decoded["exp"] == expected_exp

    def test_decode_access_token_valid(self, auth_service):
        data = {"sub": "testuser"}
        token = auth_service.create_access_token(data)

        decoded = auth_service.decode_access_token(token)

        assert decoded["sub"] == "testuser"
        assert "exp" in decoded

    def test_decode_access_token_invalid(self, auth_service):
        invalid_token = "invalid.token.here"

        with pytest.raises(HTTPException) as exc_info:
            auth_service.decode_access_token(invalid_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in exc_info.value.detail

    def test_decode_access_token_expired(self, auth_service):
        # Create token with very short expiration
        data = {"sub": "testuser"}
        expired_delta = timedelta(seconds=-1)  # Already expired
        token = auth_service.create_access_token(data, expired_delta)

        with pytest.raises(HTTPException) as exc_info:
            auth_service.decode_access_token(token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
