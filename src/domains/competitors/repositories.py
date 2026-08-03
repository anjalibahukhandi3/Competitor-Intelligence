"""Competitor repository layer responsible for database queries and persistence."""

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.competitors.models import Competitor


class CompetitorRepository:
    """Repository handling database operations for the Competitor entity."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, competitor: Competitor) -> Competitor:
        """Persists a new competitor record in the database."""
        self.db.add(competitor)
        await self.db.commit()
        await self.db.refresh(competitor)
        return competitor

    async def get_by_id(self, competitor_id: str) -> Competitor | None:
        """Retrieves a competitor by its unique primary key ID."""
        statement = select(Competitor).where(Competitor.id == competitor_id)
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: str) -> list[Competitor]:
        """Retrieves all competitors belonging to a specific user ordered by created_at DESC."""
        statement = (
            select(Competitor)
            .where(Competitor.user_id == user_id)
            .order_by(Competitor.created_at.desc())
        )
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def get_by_user_paginated(
        self, user_id: str, offset: int = 0, limit: int = 10
    ) -> list[Competitor]:
        """Retrieves a paginated list of competitors belonging to a user."""
        statement = (
            select(Competitor)
            .where(Competitor.user_id == user_id)
            .order_by(Competitor.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def count_by_user(self, user_id: str) -> int:
        """Returns total count of competitors owned by a user."""
        statement = (
            select(func.count())
            .select_from(Competitor)
            .where(Competitor.user_id == user_id)
        )
        result = await self.db.execute(statement)
        return result.scalar() or 0

    async def update(self, competitor: Competitor) -> Competitor:
        """Commits changes to an existing competitor model and refreshes state."""
        await self.db.commit()
        await self.db.refresh(competitor)
        return competitor

    async def delete(self, competitor: Competitor) -> None:
        """Deletes a competitor entity from the database."""
        await self.db.delete(competitor)
        await self.db.commit()

    async def get_all_active(self) -> list[Competitor]:
        """Returns all competitors with is_active=True, across all users.

        Used by the monitoring scheduler to determine which competitors need
        to be crawled in the current Celery Beat cycle.
        """
        statement = (
            select(Competitor)
            .where(Competitor.is_active.is_(True))
            .order_by(Competitor.created_at.desc())
        )
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def exists_for_user(self, user_id: str, company_name: str) -> bool:
        """Checks if a user already has a competitor registered with the given company name."""
        statement = select(Competitor).where(
            Competitor.user_id == user_id,
            func.lower(Competitor.company_name) == func.lower(company_name),
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none() is not None

