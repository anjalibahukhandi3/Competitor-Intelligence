"""Pydantic v2 schemas for Competitor domain requests and responses."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class CompetitorCreate(BaseModel):
    """Schema for creating a new competitor profile."""

    company_name: str = Field(
        ..., min_length=2, description="Name of competitor company (min 2 chars)"
    )
    website: HttpUrl = Field(
        ..., description="Valid website domain or URL (e.g. https://example.com)"
    )
    industry: str | None = Field(
        default=None, description="Industry sector (optional)"
    )
    country: str | None = Field(
        default=None, description="Headquarters country (optional)"
    )
    description: str | None = Field(
        default=None, description="Brief description or notes (optional)"
    )


class CompetitorUpdate(BaseModel):
    """Schema for updating an existing competitor profile (all fields optional)."""

    company_name: str | None = Field(
        default=None, min_length=2, description="Updated company name"
    )
    website: HttpUrl | None = Field(
        default=None, description="Updated website URL"
    )
    industry: str | None = Field(
        default=None, description="Updated industry sector"
    )
    country: str | None = Field(
        default=None, description="Updated country location"
    )
    description: str | None = Field(
        default=None, description="Updated notes/description"
    )
    is_active: bool | None = Field(
        default=None, description="Active status for automated tracking"
    )


class CompetitorResponse(BaseModel):
    """Schema for returning competitor details in API responses."""

    id: str
    user_id: str
    company_name: str
    website: str
    industry: str | None = None
    country: str | None = None
    description: str | None = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompetitorListResponse(BaseModel):
    """Paginated response wrapper for competitor lists."""

    items: list[CompetitorResponse]
    total: int
    page: int
    page_size: int

