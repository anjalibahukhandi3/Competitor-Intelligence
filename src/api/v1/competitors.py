"""Competitor API endpoints — authenticated CRUD operations."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.database import get_db
from src.domains.competitors.repositories import CompetitorRepository
from src.domains.competitors.schemas import (
    CompetitorCreate,
    CompetitorListResponse,
    CompetitorResponse,
    CompetitorUpdate,
)
from src.domains.competitors.services import CompetitorService
from src.domains.users.models import User

router = APIRouter()


def _get_service(db: AsyncSession) -> CompetitorService:
    """Instantiates CompetitorRepository + CompetitorService from the active session."""
    return CompetitorService(CompetitorRepository(db))


# ---------------------------------------------------------------------------
# POST /competitors — Create a new competitor
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=CompetitorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a competitor to track",
)
async def create_competitor(
    data: CompetitorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CompetitorResponse:
    """Creates a competitor profile owned by the authenticated user."""
    service = _get_service(db)
    try:
        competitor = await service.create_competitor(user_id=current_user.id, data=data)
        return competitor
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ---------------------------------------------------------------------------
# GET /competitors — Paginated list of competitors
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=CompetitorListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all tracked competitors (paginated)",
)
async def list_competitors(
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CompetitorListResponse:
    """Returns a paginated list of competitors owned by the authenticated user."""
    service = _get_service(db)
    return await service.list_competitors(
        user_id=current_user.id, page=page, page_size=size
    )


# ---------------------------------------------------------------------------
# GET /competitors/{competitor_id} — Retrieve single competitor
# ---------------------------------------------------------------------------
@router.get(
    "/{competitor_id}",
    response_model=CompetitorResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific competitor by ID",
)
async def get_competitor(
    competitor_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CompetitorResponse:
    """Returns a single competitor. Only the owner can access it."""
    service = _get_service(db)
    try:
        return await service.get_competitor(
            competitor_id=competitor_id, user_id=current_user.id
        )
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)


# ---------------------------------------------------------------------------
# PATCH /competitors/{competitor_id} — Partial update
# ---------------------------------------------------------------------------
@router.patch(
    "/{competitor_id}",
    response_model=CompetitorResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update a competitor",
)
async def update_competitor(
    competitor_id: str,
    data: CompetitorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CompetitorResponse:
    """Applies partial changes to a competitor profile. Only supplied fields are updated."""
    service = _get_service(db)
    try:
        return await service.update_competitor(
            competitor_id=competitor_id, user_id=current_user.id, data=data
        )
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)


# ---------------------------------------------------------------------------
# DELETE /competitors/{competitor_id} — Delete a competitor
# ---------------------------------------------------------------------------
@router.delete(
    "/{competitor_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a tracked competitor",
)
async def delete_competitor(
    competitor_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Permanently removes a competitor profile. Only the owner can delete it."""
    service = _get_service(db)
    try:
        await service.delete_competitor(
            competitor_id=competitor_id, user_id=current_user.id
        )
        return {"message": "Competitor deleted successfully"}
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)

