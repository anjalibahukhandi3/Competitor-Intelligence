"""Competitor service layer containing domain business logic and ownership checks."""

from src.domains.competitors.models import Competitor
from src.domains.competitors.repositories import CompetitorRepository
from src.domains.competitors.schemas import (
    CompetitorCreate,
    CompetitorListResponse,
    CompetitorResponse,
    CompetitorUpdate,
)


class CompetitorService:
    """Service managing competitor tracking business logic and tenant isolation."""

    def __init__(self, repository: CompetitorRepository) -> None:
        self.repository = repository

    async def create_competitor(
        self, user_id: str, data: CompetitorCreate
    ) -> Competitor:
        """Registers a new competitor profile for a user after duplicate validation."""
        if await self.repository.exists_for_user(user_id, data.company_name):
            raise ValueError("Competitor already exists")

        competitor = Competitor(
            user_id=user_id,
            company_name=data.company_name,
            website=str(data.website),
            industry=data.industry,
            country=data.country,
            description=data.description,
        )
        return await self.repository.create(competitor)

    async def get_competitor(self, competitor_id: str, user_id: str) -> Competitor:
        """Retrieves a single competitor and enforces user ownership validation."""
        competitor = await self.repository.get_by_id(competitor_id)
        if not competitor:
            raise ValueError("Competitor not found")

        if competitor.user_id != user_id:
            raise ValueError("Access denied")

        return competitor

    async def list_competitors(
        self, user_id: str, page: int = 1, page_size: int = 10
    ) -> CompetitorListResponse:
        """Retrieves a paginated list of competitors belonging to a user."""
        offset = (page - 1) * page_size
        items = await self.repository.get_by_user_paginated(
            user_id, offset=offset, limit=page_size
        )
        total = await self.repository.count_by_user(user_id)

        response_items = [
            CompetitorResponse.model_validate(item) for item in items
        ]
        return CompetitorListResponse(
            items=response_items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_competitor(
        self, competitor_id: str, user_id: str, data: CompetitorUpdate
    ) -> Competitor:
        """Updates fields on an existing competitor after verifying ownership."""
        competitor = await self.get_competitor(competitor_id, user_id)

        update_data = data.model_dump(exclude_unset=True)
        if "website" in update_data and update_data["website"] is not None:
            update_data["website"] = str(update_data["website"])

        for key, value in update_data.items():
            setattr(competitor, key, value)

        return await self.repository.update(competitor)

    async def delete_competitor(self, competitor_id: str, user_id: str) -> bool:
        """Deletes a competitor profile after verifying ownership."""
        competitor = await self.get_competitor(competitor_id, user_id)
        await self.repository.delete(competitor)
        return True

    async def activate_competitor(
        self, competitor_id: str, user_id: str
    ) -> Competitor:
        """Activates automated tracking for a competitor."""
        competitor = await self.get_competitor(competitor_id, user_id)
        competitor.is_active = True
        return await self.repository.update(competitor)

    async def deactivate_competitor(
        self, competitor_id: str, user_id: str
    ) -> Competitor:
        """Deactivates automated tracking for a competitor."""
        competitor = await self.get_competitor(competitor_id, user_id)
        competitor.is_active = False
        return await self.repository.update(competitor)

