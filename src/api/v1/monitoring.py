"""User-facing monitoring actions."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.database import get_db
from src.domains.competitors.repositories import CompetitorRepository
from src.domains.reports.repositories import ReportRepository
from src.domains.snapshots.repositories import ChangeEventRepository, SnapshotRepository
from src.domains.snapshots.services import MonitoringService
from src.domains.users.models import User

router = APIRouter()

@router.post("/{competitor_id}/trigger")
async def trigger_manual_monitoring_run(
    competitor_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Enqueues a monitoring run for one competitor owned by the caller."""
    service = MonitoringService(
        snapshot_repository=SnapshotRepository(db),
        change_event_repository=ChangeEventRepository(db),
        report_repository=ReportRepository(db),
        competitor_repository=CompetitorRepository(db),
    )
    try:
        return await service.run_monitoring(
            user_id=current_user.id, competitor_ids=[competitor_id]
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
