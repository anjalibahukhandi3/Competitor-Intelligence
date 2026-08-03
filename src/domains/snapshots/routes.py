"""Snapshots, Changes, and Monitoring API endpoints.

Routes registered in src/api/router.py under:
  - /competitors/{id}/timeline   → GET (timeline for a competitor)
  - /snapshots/{id}              → GET (single snapshot detail)
  - /monitor/run                 → POST (trigger monitoring for competitors)
  - /changes                     → GET (recent change events across all competitors)
  - /reports/history             → handled in reports.py via /{competitor_id}/list

All routes follow the thin-router pattern: delegate to services, convert ValueError → HTTPException.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.database import get_db
from src.domains.competitors.repositories import CompetitorRepository
from src.domains.reports.repositories import ReportRepository
from src.domains.snapshots.repositories import ChangeEventRepository, SnapshotRepository
from src.domains.snapshots.schemas import (
    ChangeEventListResponse,
    ChangeEventResponse,
    MonitoringRunRequest,
    MonitoringRunResult,
    SnapshotResponse,
    TimelineResponse,
)
from src.domains.snapshots.services import (
    MonitoringService,
    SnapshotService,
    TimelineService,
)
from src.domains.users.models import User

router = APIRouter()


# ---------------------------------------------------------------------------
# Internal factory — builds all services from the active DB session
# ---------------------------------------------------------------------------


def _make_timeline_service(db: AsyncSession) -> TimelineService:
    return TimelineService(
        snapshot_repository=SnapshotRepository(db),
        change_event_repository=ChangeEventRepository(db),
        report_repository=ReportRepository(db),
        competitor_repository=CompetitorRepository(db),
    )


def _make_monitoring_service(db: AsyncSession) -> MonitoringService:
    return MonitoringService(
        snapshot_repository=SnapshotRepository(db),
        change_event_repository=ChangeEventRepository(db),
        report_repository=ReportRepository(db),
        competitor_repository=CompetitorRepository(db),
    )


# ---------------------------------------------------------------------------
# GET /competitors/{competitor_id}/timeline
# ---------------------------------------------------------------------------


@router.get(
    "/competitors/{competitor_id}/timeline",
    response_model=TimelineResponse,
    status_code=status.HTTP_200_OK,
    tags=["Monitoring"],
    summary="Get the intelligence timeline for a competitor",
    description=(
        "Returns a unified, chronological timeline of all monitoring events for the "
        "given competitor: snapshots taken, changes detected, and AI reports generated. "
        "Newest events appear first."
    ),
)
async def get_competitor_timeline(
    competitor_id: str,
    limit: int = Query(default=50, ge=1, le=200, description="Max timeline items to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TimelineResponse:
    """Returns the unified intelligence timeline for a competitor."""
    service = _make_timeline_service(db)
    try:
        return await service.get_timeline(
            competitor_id=competitor_id,
            user_id=current_user.id,
            limit=limit,
        )
    except ValueError as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)


# ---------------------------------------------------------------------------
# GET /snapshots/{snapshot_id}
# ---------------------------------------------------------------------------


@router.get(
    "/snapshots/{snapshot_id}",
    response_model=SnapshotResponse,
    status_code=status.HTTP_200_OK,
    tags=["Monitoring"],
    summary="Retrieve a specific website snapshot",
    description=(
        "Returns the full content of a competitor website snapshot including "
        "homepage markdown, pricing page markdown, and the content hash."
    ),
)
async def get_snapshot(
    snapshot_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SnapshotResponse:
    """Returns a single competitor website snapshot by ID."""
    snapshot_repo = SnapshotRepository(db)
    competitor_repo = CompetitorRepository(db)
    service = SnapshotService(
        snapshot_repository=snapshot_repo,
        competitor_repository=competitor_repo,
    )
    try:
        return await service.get_snapshot(snapshot_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# ---------------------------------------------------------------------------
# POST /monitor/run
# ---------------------------------------------------------------------------


@router.post(
    "/monitor/run",
    response_model=MonitoringRunResult,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Monitoring"],
    summary="Trigger a monitoring run for one or more competitors",
    description=(
        "Enqueues background monitoring tasks for the specified competitors. "
        "If no `competitor_ids` are provided, ALL active competitors are monitored. "
        "Returns immediately (HTTP 202) — monitoring runs asynchronously via Celery."
    ),
)
async def trigger_monitoring_run(
    body: MonitoringRunRequest = MonitoringRunRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MonitoringRunResult:
    """Enqueues monitoring jobs for the requested competitors."""
    service = _make_monitoring_service(db)
    return await service.run_monitoring(competitor_ids=body.competitor_ids or None)


# ---------------------------------------------------------------------------
# GET /changes
# ---------------------------------------------------------------------------


@router.get(
    "/changes",
    response_model=ChangeEventListResponse,
    status_code=status.HTTP_200_OK,
    tags=["Monitoring"],
    summary="List recent change events across all competitors",
    description=(
        "Returns the most recent change events detected across all monitored competitors. "
        "Optionally filter by `category` (Pricing, Features, Homepage, Hiring, "
        "Marketing, Product, Documentation) or `impact` (High, Medium, Low)."
    ),
)
async def list_change_events(
    limit: int = Query(default=50, ge=1, le=200, description="Max events to return"),
    category: str | None = Query(default=None, description="Filter by change category"),
    impact: str | None = Query(default=None, description="Filter by impact level: High | Medium | Low"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChangeEventListResponse:
    """Returns recent change events across all competitors, with optional filters."""
    event_repo = ChangeEventRepository(db)
    events = await event_repo.get_all_recent(limit=limit, category=category, impact=impact)
    return ChangeEventListResponse(
        items=[ChangeEventResponse.model_validate(e) for e in events],
        total=len(events),
    )
