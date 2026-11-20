from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from src.domains.users.schemas import UserCreate, UserLogin
from src.domains.users.services import UserService


@pytest.mark.asyncio
async def test_user_registration_hashes_password_before_persistence() -> None:
    user = SimpleNamespace(id="user-1", email="user@example.com", is_active=True)
    repository = AsyncMock()
    repository.exists_by_email.return_value = False
    repository.create.return_value = user
    service = UserService(repository)

    with patch("src.domains.users.services.hash_password", return_value="hashed") as hash_pwd:
        result = await service.register(UserCreate(email="user@example.com", password="password123"))

    assert result is user
    hash_pwd.assert_called_once_with("password123")
    repository.create.assert_awaited_once()
    assert repository.create.await_args.args[0].hashed_password == "hashed"


@pytest.mark.asyncio
async def test_user_login_returns_token_for_valid_credentials() -> None:
    user = SimpleNamespace(
        id="user-1", email="user@example.com", hashed_password="hashed", is_active=True
    )
    repository = AsyncMock()
    repository.get_by_email.return_value = user
    service = UserService(repository)

    with (
        patch("src.domains.users.services.verify_password", return_value=True),
        patch("src.domains.users.services.create_access_token", return_value="jwt-token") as token,
    ):
        result = await service.login(UserLogin(email="user@example.com", password="password123"))

    assert result == "jwt-token"
    token.assert_called_once_with("user-1", email="user@example.com")
