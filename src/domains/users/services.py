"""User service layer containing core authentication and domain business logic."""

from src.core.security import create_access_token, hash_password, verify_password
from src.domains.users.models import User
from src.domains.users.repositories import UserRepository
from src.domains.users.schemas import UserCreate, UserLogin


class UserService:
    """Service handling business rules, user registration, and authentication."""

    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def register(self, data: UserCreate) -> User:
        """Registers a new user account if the email is not already registered."""
        if await self.repository.exists_by_email(data.email):
            raise ValueError("Email already registered")

        hashed_pwd = hash_password(data.password)
        user = User(
            email=data.email,
            hashed_password=hashed_pwd,
        )
        return await self.repository.create(user)

    async def login(self, data: UserLogin) -> str:
        """Authenticates user credentials and returns a JWT access token."""
        user = await self.repository.get_by_email(data.email)
        if not user:
            raise ValueError("Invalid email or password")

        if not verify_password(data.password, user.hashed_password):
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("User account is inactive")

        return create_access_token(user.id)

    async def get_user(self, user_id: str) -> User:
        """Retrieves user profile by ID or raises an error if not found."""
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return user

