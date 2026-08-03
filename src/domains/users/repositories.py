"""User repository layer responsible for database interaction."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.users.models import User


class UserRepository:
    """Repository handling database operations for the User entity."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user: User) -> User:
        """Persists a new user record in the database."""
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_by_email(self, email: str) -> User | None:
        """Retrieves a user by their email address."""
        statement = select(User).where(User.email == email)
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> User | None:
        """Retrieves a user by their unique primary key ID."""
        statement = select(User).where(User.id == user_id)
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def exists_by_email(self, email: str) -> bool:
        """Checks if a user with the given email already exists."""
        user = await self.get_by_email(email)
        return user is not None

