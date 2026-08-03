"""Snapshot & ChangeEvent repositories — persistence layer only.

No business logic. No HTTP exceptions. Pure async SQLAlchemy 2.0 ORM operations.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.snapshots.models import ChangeEvent, CompetitorSnapshot


# ---------------------------------------------------------------------------
# SnapshotRepository
# ---------------------------------------------------------------------------


class SnapshotRepository:
    """All database operations for the CompetitorSnapshot entity."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    async def create(self, snapshot: CompetitorSnapshot) -> CompetitorSnapshot:
        """Persists a new snapshot row and returns the refreshed entity."""
        self.db.add(snapshot)
        await self.db.commit()
        await self.db.refresh(snapshot)
        return snapshot

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    async def get_by_id(self, snapshot_id: str) -> CompetitorSnapshot | None:
        """Returns a snapshot by UUID primary key, or None."""
        stmt = select(CompetitorSnapshot).where(CompetitorSnapshot.id == snapshot_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_by_competitor(
        self, competitor_id: str
    ) -> CompetitorSnapshot | None:
        """Returns the most recent snapshot for a competitor, or None."""
        stmt = (
            select(CompetitorSnapshot)
            .where(CompetitorSnapshot.competitor_id == competitor_id)
            .order_by(CompetitorSnapshot.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_previous_by_competitor(
        self, competitor_id: str, before_snapshot_id: str
    ) -> CompetitorSnapshot | None:
        """Returns the snapshot immediately before the given snapshot ID."""
        # First get the timestamp of the reference snapshot
        ref_stmt = select(CompetitorSnapshot.created_at).where(
            CompetitorSnapshot.id == before_snapshot_id
        )
        ref_result = await self.db.execute(ref_stmt)
        ref_ts = ref_result.scalar_one_or_none()
        if ref_ts is None:
            return None

        stmt = (
            select(CompetitorSnapshot)
            .where(
                CompetitorSnapshot.competitor_id == competitor_id,
                CompetitorSnapshot.created_at < ref_ts,
            )
            .order_by(CompetitorSnapshot.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_competitor(
        self, competitor_id: str, limit: int = 50
    ) -> list[CompetitorSnapshot]:
        """Returns snapshots for a competitor, newest first."""
        stmt = (
            select(CompetitorSnapshot)
            .where(CompetitorSnapshot.competitor_id == competitor_id)
            .order_by(CompetitorSnapshot.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def exists_with_hash(
        self, competitor_id: str, content_hash: str
    ) -> bool:
        """Returns True if a snapshot with this exact hash already exists.

        Used by SnapshotService to skip duplicate crawls when content has
        not changed since the last snapshot.
        """
        stmt = select(func.count()).select_from(CompetitorSnapshot).where(
            CompetitorSnapshot.competitor_id == competitor_id,
            CompetitorSnapshot.content_hash == content_hash,
        )
        result = await self.db.execute(stmt)
        return (result.scalar() or 0) > 0

    async def count_by_competitor(self, competitor_id: str) -> int:
        """Returns the total number of snapshots for a competitor."""
        stmt = (
            select(func.count())
            .select_from(CompetitorSnapshot)
            .where(CompetitorSnapshot.competitor_id == competitor_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0


# ---------------------------------------------------------------------------
# ChangeEventRepository
# ---------------------------------------------------------------------------


class ChangeEventRepository:
    """All database operations for the ChangeEvent entity."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    async def create(self, event: ChangeEvent) -> ChangeEvent:
        """Persists a new change event and returns the refreshed entity."""
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def bulk_create(self, events: list[ChangeEvent]) -> list[ChangeEvent]:
        """Persists multiple change events in a single transaction."""
        for ev in events:
            self.db.add(ev)
        await self.db.commit()
        for ev in events:
            await self.db.refresh(ev)
        return events

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    async def get_by_id(self, event_id: str) -> ChangeEvent | None:
        """Returns a change event by UUID primary key, or None."""
        stmt = select(ChangeEvent).where(ChangeEvent.id == event_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_competitor(
        self,
        competitor_id: str,
        limit: int = 100,
        category: str | None = None,
    ) -> list[ChangeEvent]:
        """Returns change events for a competitor, newest first.

        Optionally filter by category (e.g. 'Pricing', 'Features').
        """
        stmt = select(ChangeEvent).where(
            ChangeEvent.competitor_id == competitor_id
        )
        if category:
            stmt = stmt.where(ChangeEvent.category == category)
        stmt = stmt.order_by(ChangeEvent.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_all_recent(
        self,
        limit: int = 100,
        category: str | None = None,
        impact: str | None = None,
    ) -> list[ChangeEvent]:
        """Returns the most recent change events across all competitors.

        Supports optional filtering by category and impact_score.
        """
        stmt = select(ChangeEvent)
        if category:
            stmt = stmt.where(ChangeEvent.category == category)
        if impact:
            stmt = stmt.where(ChangeEvent.impact_score == impact)
        stmt = stmt.order_by(ChangeEvent.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_snapshot(self, snapshot_id: str) -> list[ChangeEvent]:
        """Returns all change events linked to a specific snapshot."""
        stmt = (
            select(ChangeEvent)
            .where(ChangeEvent.snapshot_id == snapshot_id)
            .order_by(ChangeEvent.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_by_competitor(self, competitor_id: str) -> int:
        """Returns the total number of change events for a competitor."""
        stmt = (
            select(func.count())
            .select_from(ChangeEvent)
            .where(ChangeEvent.competitor_id == competitor_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0
