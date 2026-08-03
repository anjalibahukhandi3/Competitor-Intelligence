"""Report repository — persistence layer for the Report domain.

Contains ONLY database access logic. No business rules, no HTTP exceptions,
no validation. Every method speaks directly to PostgreSQL via SQLAlchemy 2.0
async ORM and returns plain ORM entities (or None / int).
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.reports.models import Report, REPORT_STATUS_COMPLETED


class ReportRepository:
    """Handles all database operations for the Report entity."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    async def create(self, report: Report) -> Report:
        """Persists a new Report row and returns the refreshed entity.

        The caller is responsible for building the Report ORM object;
        this method only handles the INSERT → commit → refresh cycle.
        """
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return report

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    async def get_by_id(self, report_id: str) -> Report | None:
        """Retrieves a single Report by its UUID primary key.

        Returns None when no row matches — callers decide what that means.
        """
        statement = select(Report).where(Report.id == report_id)
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_competitor(self, competitor_id: str) -> list[Report]:
        """Returns all reports for a competitor, newest first.

        Used by the report list endpoint and by the monitoring service
        to inspect the full history for a given competitor.
        """
        statement = (
            select(Report)
            .where(Report.competitor_id == competitor_id)
            .order_by(Report.created_at.desc())
        )
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def get_latest_completed(self, competitor_id: str) -> Report | None:
        """Returns the most recent *completed* report for a competitor.

        Used by:
        - The monitoring scheduler to decide whether a fresh report is needed.
        - The PDF and email modules to fetch content that is guaranteed to
          have all AI fields populated (status == 'completed').

        Returns None when no completed report exists yet.
        """
        statement = (
            select(Report)
            .where(
                Report.competitor_id == competitor_id,
                Report.status == REPORT_STATUS_COMPLETED,
            )
            .order_by(Report.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def count_by_competitor(self, competitor_id: str) -> int:
        """Returns the total number of reports for a competitor.

        Used by the report list endpoint to populate the 'total' field
        in ReportListResponse for client-side pagination controls.
        """
        statement = (
            select(func.count())
            .select_from(Report)
            .where(Report.competitor_id == competitor_id)
        )
        result = await self.db.execute(statement)
        return result.scalar() or 0

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    async def update(self, report: Report) -> Report:
        """Flushes in-memory mutations to the database and refreshes state.

        The caller mutates the ORM object's attributes (e.g. status,
        strengths, summary) and then calls this method. No field-level
        arguments are accepted — the repository is unaware of which fields
        changed, keeping it completely generic.
        """
        await self.db.commit()
        await self.db.refresh(report)
        return report

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    async def delete(self, report: Report) -> None:
        """Permanently removes a Report row from the database."""
        await self.db.delete(report)
        await self.db.commit()
