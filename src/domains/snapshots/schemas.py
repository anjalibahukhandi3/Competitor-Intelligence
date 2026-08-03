"""Snapshots & Change Events domain — Pydantic v2 request/response schemas.

All schema classes follow the same patterns used in the reports and competitors
domains: strict `from_attributes=True` for ORM compatibility, no raw model
exposure across HTTP boundaries.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Change categories
# ---------------------------------------------------------------------------

ChangeCategory = Literal[
    "Pricing", "Features", "Homepage", "Hiring", "Marketing", "Product", "Documentation"
]

ImpactLevel = Literal["High", "Medium", "Low"]


# ---------------------------------------------------------------------------
# Snapshot schemas
# ---------------------------------------------------------------------------


class SnapshotResponse(BaseModel):
    """Serialised view of a CompetitorSnapshot ORM row."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    competitor_id: str
    content_hash: str
    homepage_content: str | None = None
    pricing_content: str | None = None
    created_at: datetime


class SnapshotListResponse(BaseModel):
    """Paginated list of snapshots."""

    items: list[SnapshotResponse]
    total: int


# ---------------------------------------------------------------------------
# Change event schemas
# ---------------------------------------------------------------------------


class ChangeEventResponse(BaseModel):
    """Serialised view of a ChangeEvent ORM row."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    competitor_id: str
    snapshot_id: str | None = None
    category: str
    summary: str
    added_content: str | None = None
    removed_content: str | None = None
    impact_score: str | None = "Medium"
    created_at: datetime


class ChangeEventListResponse(BaseModel):
    """Paginated list of change events."""

    items: list[ChangeEventResponse]
    total: int


# ---------------------------------------------------------------------------
# Timeline schemas
# ---------------------------------------------------------------------------


class TimelineItemResponse(BaseModel):
    """A single chronological item in a competitor's intelligence timeline.

    Each item is one of: snapshot taken, change detected, or report generated.
    """

    event_type: Literal["snapshot", "change", "report"]
    event_id: str
    competitor_id: str
    title: str
    description: str
    category: str | None = None
    impact_score: str | None = None
    created_at: datetime


class TimelineResponse(BaseModel):
    """Chronological intelligence timeline for a competitor."""

    competitor_id: str
    items: list[TimelineItemResponse]
    total: int


# ---------------------------------------------------------------------------
# Monitoring run schemas
# ---------------------------------------------------------------------------


class MonitoringRunRequest(BaseModel):
    """Body for `POST /monitor/run`."""

    competitor_ids: list[str] = Field(
        default_factory=list,
        description="Specific competitor IDs to monitor. Empty list = monitor ALL active competitors.",
    )


class MonitoringRunResult(BaseModel):
    """Result summary for a monitoring run trigger."""

    enqueued: int = Field(description="Number of monitoring jobs enqueued")
    competitor_ids: list[str] = Field(description="Competitor IDs that were enqueued")
    message: str


# ---------------------------------------------------------------------------
# Gemini change analysis schema (used internally by ChangeDetector)
# ---------------------------------------------------------------------------


class DetectedChangeAnalysis(BaseModel):
    """Structured output expected from Gemini when classifying a content diff."""

    categories: list[ChangeCategory] = Field(
        description="List of change categories detected (can be multiple)"
    )
    summary: str = Field(description="Concise 2-3 sentence human-readable summary of what changed")
    added_highlights: str | None = Field(
        default=None,
        description="Key added content highlights (bullet points)",
    )
    removed_highlights: str | None = Field(
        default=None,
        description="Key removed content highlights (bullet points)",
    )
    impact_score: ImpactLevel = Field(
        default="Medium",
        description="Business impact level: High (direct revenue/product) | Medium | Low (minor)",
    )
