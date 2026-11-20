from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from src.domains.competitors.schemas import CompetitorCreate
from src.domains.competitors.services import CompetitorService


@pytest.mark.asyncio
async def test_list_competitors_returns_only_repository_page() -> None:
    repository = AsyncMock()
    repository.get_by_user_paginated.return_value = []
    repository.count_by_user.return_value = 0
    service = CompetitorService(repository)

    result = await service.list_competitors(user_id="user-1", page=2, page_size=10)

    assert result.items == []
    assert result.total == 0
    repository.get_by_user_paginated.assert_awaited_once_with(
        "user-1", offset=10, limit=10
    )


def test_add_competitor_rejects_invalid_website_url() -> None:
    with pytest.raises(ValidationError):
        CompetitorCreate(company_name="Acme", website="not a url")
