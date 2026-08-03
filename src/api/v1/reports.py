"""Report API router — HTTP layer for the report pipeline.

Architecture principles enforced here
--------------------------------------
THIN ROUTER:
  This file only translates HTTP ↔ domain. It must not contain business
  rules, SQL queries, or AI logic. All of that belongs in the service and
  repository layers.  A thin router means:
  - Easy to unit-test the service in isolation (no HTTP needed).
  - Route changes never ripple into business logic files.
  - Security concerns (JWT, CORS) are centralized in dependencies.py.

HTTPException boundary:
  ValueError is the contract raised by the service layer. This router is
  the ONLY place those are caught and converted to HTTP status codes.
  Keeping HTTP exceptions out of services ensures those classes remain
  reusable by CLI scripts, background workers, or other adapters that do
  not use FastAPI at all.

Request lifecycle
-----------------
  Client → ASGI → Middleware (CORS, auth-failure 401) →
  Dependency injection (get_db opens session, get_current_user decodes JWT) →
  Route function (builds repos/service, calls service method) →
  Service (business logic, raises ValueError on domain errors) →
  Route function (catches ValueError → HTTPException, or serialises response) →
  FastAPI serialises Pydantic model to JSON →
  Client receives HTTP response
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.database import get_db
from src.domains.competitors.repositories import CompetitorRepository
from src.domains.reports.repositories import ReportRepository
from src.domains.reports.schemas import (
    ReportListResponse,
    ReportResponse,
    ReportTriggerResponse,
)
from src.domains.reports.services import ReportService
from src.domains.users.models import User

router = APIRouter()


# ---------------------------------------------------------------------------
# Internal factory — keeps each endpoint body to 2-3 lines
# ---------------------------------------------------------------------------

def _get_service(db: AsyncSession) -> ReportService:
    """Wires ReportRepository + CompetitorRepository into ReportService.

    Called inside each route function with the per-request DB session so
    that all objects share the same transaction and are garbage-collected
    at the end of the request.
    """
    return ReportService(
        report_repository=ReportRepository(db),
        competitor_repository=CompetitorRepository(db),
    )


# ---------------------------------------------------------------------------
# POST /reports/trigger/{competitor_id}
# ---------------------------------------------------------------------------

@router.post(
    "/trigger/{competitor_id}",
    response_model=ReportTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger an AI intelligence report for a competitor",
    description=(
        "Enqueues a new AI analysis job for the given competitor. "
        "Returns immediately with a `report_id` and status=`pending`. "
        "Poll `GET /reports/{report_id}` to track progress."
    ),
)
async def trigger_report(
    competitor_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportTriggerResponse:
    """Creates a pending Report row and queues the AI generation pipeline.

    - **202 Accepted** — report job was accepted and is queued.
    - **404 Not Found** — competitor_id does not exist.
    - **403 Forbidden** — competitor belongs to a different user.
    """
    service = _get_service(db)
    try:
        return await service.trigger_report(
            user_id=current_user.id,
            competitor_id=competitor_id,
        )
    except ValueError as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)


# ---------------------------------------------------------------------------
# GET /reports/{report_id}
# ---------------------------------------------------------------------------

@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch a single report by ID",
    description=(
        "Returns the full report including all AI-generated sections. "
        "AI fields are `null` while the pipeline is still running. "
        "Check the `status` field to know when the report is complete."
    ),
)
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportResponse:
    """Retrieves a single report by its UUID.

    - **200 OK** — report found and returned.
    - **404 Not Found** — report_id does not exist.
    - **403 Forbidden** — report belongs to a competitor owned by another user.
    """
    service = _get_service(db)
    try:
        return await service.get_report(
            user_id=current_user.id,
            report_id=report_id,
        )
    except ValueError as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)


# ---------------------------------------------------------------------------
# GET /reports/{report_id}/download
# ---------------------------------------------------------------------------

@router.get(
    "/{report_id}/download",
    response_class=FileResponse,
    status_code=status.HTTP_200_OK,
    summary="Download the generated PDF report",
    description=(
        "Returns the generated PDF report file for the given report ID. "
        "Returns 404 if the report or PDF file does not exist."
    ),
)
async def download_report_pdf(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """Streams the generated PDF file for a report owned by the authenticated user.

    - **200 OK** — PDF file returned.
    - **404 Not Found** — report_id or PDF file does not exist.
    - **403 Forbidden** — report belongs to a competitor owned by another user.
    """
    service = _get_service(db)
    try:
        pdf_path = await service.get_report_pdf_path(
            user_id=current_user.id,
            report_id=report_id,
        )
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"competitor_report_{report_id}.pdf",
        )
    except ValueError as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)


# ---------------------------------------------------------------------------
# GET /reports/{competitor_id}/list
# ---------------------------------------------------------------------------

@router.get(
    "/{competitor_id}/list",
    response_model=ReportListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all reports for a competitor (paginated)",
    description=(
        "Returns a paginated list of AI reports generated for the specified "
        "competitor, ordered newest-first. Use `page` and `size` query params "
        "to paginate through large result sets."
    ),
)
async def list_reports(
    competitor_id: str,
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportListResponse:
    """Returns paginated reports for a competitor owned by the authenticated user.

    - **200 OK** — list returned (may be empty if no reports yet).
    - **404 Not Found** — competitor_id does not exist.
    - **403 Forbidden** — competitor belongs to a different user.
    """
    service = _get_service(db)
    try:
        return await service.list_reports(
            user_id=current_user.id,
            competitor_id=competitor_id,
            page=page,
            size=size,
        )
    except ValueError as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)


# ---------------------------------------------------------------------------
# PATCH /reports/{report_id}/status
# ---------------------------------------------------------------------------

@router.patch(
    "/{report_id}/status",
    response_model=ReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Update the lifecycle status of a report",
    description=(
        "Advances a report through its AI pipeline lifecycle: "
        "`pending` → `processing` → `completed` | `failed`. "
        "Intended to be called by internal workers or admins, not end users."
    ),
)
async def update_report_status(
    report_id: str,
    status_update: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportResponse:
    """Updates the status field of an existing report.

    Expects a JSON body: `{"status": "processing"}`.

    - **200 OK** — status updated and full report returned.
    - **400 Bad Request** — body is missing the `status` field.
    - **404 Not Found** — report_id does not exist.
    """
    new_status = status_update.get("status")
    if not new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request body must contain a 'status' field.",
        )

    service = _get_service(db)
    try:
        return await service.update_status(
            report_id=report_id,
            status=new_status,
        )
    except ValueError as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
