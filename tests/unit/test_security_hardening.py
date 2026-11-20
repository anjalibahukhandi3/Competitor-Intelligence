"""Regression coverage for authentication configuration and password limits."""

import pytest
from pydantic import ValidationError

from src.config import SecuritySettings, Settings
from src.core.security import create_access_token, decode_access_token, hash_password
from src.domains.users.schemas import UserCreate, UserLogin


def test_production_settings_reject_development_jwt_secret():
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(
            ENV="production",
            security=SecuritySettings(
                JWT_SECRET_KEY="development_only_change_this_jwt_secret_key"
            ),
        )


def test_passwords_over_bcrypt_byte_limit_are_rejected():
    with pytest.raises(ValidationError, match="72 UTF-8 bytes"):
        UserCreate(email="user@example.com", password="x" * 73)
    with pytest.raises(ValidationError, match="72 UTF-8 bytes"):
        UserLogin(email="user@example.com", password="x" * 73)
    with pytest.raises(ValueError, match="72 UTF-8 bytes"):
        hash_password("x" * 73)


def test_access_token_includes_email_separately_from_user_id():
    token = create_access_token("user-id-123", email="user@example.com")
    payload = decode_access_token(token)

    assert payload["sub"] == "user-id-123"
    assert payload["email"] == "user@example.com"
