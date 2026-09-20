"""Pydantic v2 schemas for the Report domain.

Reports are AI-generated artifacts. Most content fields are Optional
because a Report row is created before the AI worker runs — fields
are populated asynchronously as each analysis section completes.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from src.domains.reports.models import (
    REPORT_STATUS_COMPLETED,
    REPORT_STATUS_FAILED,
    REPORT_STATUS_PENDING,
    REPORT_STATUS_PROCESSING,
)

# Re-export status constants so routers/services import from one place
__all__ = [
    "ReportResponse",
    "ReportListResponse",
    "ReportTriggerResponse",
    "REPORT_STATUS_PENDING",
    "REPORT_STATUS_PROCESSING",
    "REPORT_STATUS_COMPLETED",
    "REPORT_STATUS_FAILED",
]


class ReportResponse(BaseModel):
    """Full report details returned to the client.

    AI-generated section fields are Optional — they are None until the
    background AI worker writes them and flips status to 'completed'.
    """

    model_config = ConfigDict(
        from_attributes=True,   # Converts SQLAlchemy ORM objects directly
        populate_by_name=True,  # Allows either alias or field name on input
    )

    # ------------------------------------------------------------------
    # Identifiers
    # ------------------------------------------------------------------
    id: str = Field(description="UUID of the report")
    competitor_id: str = Field(description="UUID of the parent competitor")

    # ------------------------------------------------------------------
    # Pipeline State
    # ------------------------------------------------------------------
    status: str = Field(
        description=(
            "Lifecycle status of the AI pipeline: "
            f"{REPORT_STATUS_PENDING} | {REPORT_STATUS_PROCESSING} | "
            f"{REPORT_STATUS_COMPLETED} | {REPORT_STATUS_FAILED}"
        )
    )

    # ------------------------------------------------------------------
    # AI-generated Analysis Sections (Optional — filled asynchronously)
    # ------------------------------------------------------------------
    summary: Optional[str] = Field(
        default=None,
        description="Executive summary of the competitive analysis",
    )
    strengths: Optional[str] = Field(
        default=None,
        description="SWOT — competitor strengths identified by the AI agent",
    )
    weaknesses: Optional[str] = Field(
        default=None,
        description="SWOT — competitor weaknesses identified by the AI agent",
    )
    opportunities: Optional[str] = Field(
        default=None,
        description="SWOT — market opportunities relative to the competitor",
    )
    threats: Optional[str] = Field(
        default=None,
        description="SWOT — threats the competitor poses to the user's business",
    )
    pricing_analysis: Optional[str] = Field(
        default=None,
        description="AI analysis of the competitor's pricing strategy and tiers",
    )
    feature_analysis: Optional[str] = Field(
        default=None,
        description="Comparison of the competitor's product features vs user's",
    )
    market_position: Optional[str] = Field(
        default=None,
        description="Assessment of the competitor's standing in the market",
    )
    pdf_path: Optional[str] = Field(
        default=None,
        description="File path to the generated PDF report",
    )
    email_status: Optional[str] = Field(
        default=None,
        description="Email delivery status for this report: pending | sent | failed",
    )

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------
    created_at: datetime = Field(description="UTC timestamp of report creation")


class ReportListResponse(BaseModel):
    """Paginated list of reports for a competitor.

    Kept separate from ReportResponse so the list endpoint can add
    pagination metadata (total) without changing the item schema.
    """

    items: list[ReportResponse] = Field(
        description="Page of report records"
    )
    total: int = Field(
        description="Total number of reports matching the query"
    )


class ReportTriggerResponse(BaseModel):
    """Returned immediately when a report generation job is queued.

    The client receives this thin response right away (HTTP 202 Accepted)
    and then polls GET /reports/{report_id} to track progress via 'status'.

    Example:
        {
            "report_id": "3fa85f64-...",
            "status": "pending",
            "message": "Report generation started"
        }
    """

    report_id: str = Field(description="UUID of the newly created report row")
    status: str = Field(
        default=REPORT_STATUS_PENDING,
        description="Initial pipeline status — always 'pending' at dispatch time",
    )
    message: str = Field(
        default="Report generation started",
        description="Human-readable confirmation message for the client",
    )
