"""Strongly-typed Pydantic schemas for AI agent inputs and outputs.

Design principles
-----------------
- Every agent has a dedicated *Input* and *Output* model.
- All fields are documented so the contract is self-describing.
- Output models are composed at the orchestrator level into
  ``OrchestratorResult``, which maps 1-to-1 onto the Report ORM columns.
- Adding a new agent means adding two models here and wiring them in the
  orchestrator — nothing else changes.

Extensibility note
------------------
When real data sources (Firecrawl, Tavily, Claude) are added in Milestone 8,
these models are the only place field shapes need to be adjusted.  The agent
contracts, orchestrator, Celery task, and service layer remain unchanged.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


# ---------------------------------------------------------------------------
# Shared / primitive types
# ---------------------------------------------------------------------------

class PricingTier(BaseModel):
    """One pricing plan tier extracted from the competitor's pricing page."""

    tier_name: str = Field(description="Name of the plan (e.g. 'Starter', 'Pro', 'Enterprise')")
    price: str = Field(description="Price string as displayed (e.g. '$29/mo', 'Contact us')")
    billing_cycle: Literal["monthly", "annual", "one-time", "custom", "unknown"] = Field(
        default="unknown",
        description="Billing frequency",
    )
    key_features: list[str] = Field(
        default_factory=list,
        description="Key features included in this tier",
    )


class JobPosting(BaseModel):
    """A single job posting found on the competitor's careers page or LinkedIn."""

    title: str = Field(description="Job title (e.g. 'Senior Backend Engineer')")
    department: str = Field(description="Team or department (e.g. 'Engineering', 'Sales')")
    location: str = Field(description="Office location or 'Remote'")
    inferred_skills: list[str] = Field(
        default_factory=list,
        description="Tech stack / skills inferred from the job description",
    )
    posted_at: datetime | None = Field(
        default=None,
        description="Date the posting was published (None if not found)",
    )


class NewsItem(BaseModel):
    """A single press release, blog post, or news mention about the competitor."""

    headline: str = Field(description="Article or press release headline")
    source: str = Field(description="Publication name (e.g. 'TechCrunch', 'company blog')")
    published_at: datetime | None = Field(default=None, description="Publication date")
    sentiment: Literal["positive", "neutral", "negative", "unknown"] = Field(
        default="unknown",
        description="Inferred sentiment of the article relative to the competitor",
    )
    summary: str = Field(description="One-sentence summary of the news item")


class SWOTAnalysis(BaseModel):
    """SWOT breakdown for a competitor."""

    strengths: list[str] = Field(description="Internal strengths of the competitor")
    weaknesses: list[str] = Field(description="Internal weaknesses")
    opportunities: list[str] = Field(description="External market opportunities they can exploit")
    threats: list[str] = Field(description="Threats they pose to our business")


# ---------------------------------------------------------------------------
# Agent Input models
# ---------------------------------------------------------------------------

class AgentInput(BaseModel):
    """Base input shared by every agent.

    All agents receive at minimum the competitor identifier and URL so they
    can fetch data from the appropriate source.
    """

    competitor_id: str = Field(description="UUID of the Competitor row")
    competitor_name: str = Field(description="Human-readable company name")
    competitor_url: str = Field(description="Primary website URL")


class ResearchAgentInput(AgentInput):
    """Input for the ResearchAgent — homepage and product page analysis."""
    pass  # inherits all fields from AgentInput


class NewsAgentInput(AgentInput):
    """Input for the NewsAgent — press release and news mention collection."""
    days_back: int = Field(
        default=30,
        description="How many days of news history to collect",
    )


class PricingAgentInput(AgentInput):
    """Input for the PricingAgent — pricing page extraction."""
    pass


class HiringAgentInput(AgentInput):
    """Input for the HiringAgent — job posting trend analysis."""
    max_postings: int = Field(
        default=20,
        description="Maximum number of job postings to return",
    )


class ReportGenerationAgentInput(BaseModel):
    """Aggregated signals fed into the ReportGenerationAgent.

    Composed by the orchestrator after all parallel agents complete.
    """

    competitor_id: str
    competitor_name: str
    competitor_url: str
    research: ResearchAgentOutput
    news: NewsAgentOutput
    pricing: PricingAgentOutput
    hiring: HiringAgentOutput


# ---------------------------------------------------------------------------
# Agent Output models
# ---------------------------------------------------------------------------

class ResearchAgentOutput(BaseModel):
    """Structured findings from the competitor's homepage and product pages."""

    tagline: str = Field(description="The competitor's marketing tagline or value proposition")
    primary_use_cases: list[str] = Field(
        description="Top use cases the competitor targets",
    )
    tech_stack_signals: list[str] = Field(
        description="Detected technology signals (e.g. 'React', 'AWS', 'Stripe')",
    )
    target_customers: list[str] = Field(
        description="Customer segments prominently featured (e.g. 'SMBs', 'Enterprise')",
    )
    key_differentiators: list[str] = Field(
        description="Unique selling points highlighted on the site",
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Agent's confidence in the findings (0.0–1.0)",
    )


class NewsAgentOutput(BaseModel):
    """Curated news and press release intelligence."""

    items: list[NewsItem] = Field(description="List of relevant news items found")
    overall_sentiment: Literal["positive", "neutral", "negative", "mixed", "unknown"] = Field(
        default="unknown",
        description="Aggregate sentiment across all news items",
    )
    key_themes: list[str] = Field(
        description="Recurring topics or themes across the news coverage",
    )
    confidence: float = Field(ge=0.0, le=1.0)


class PricingAgentOutput(BaseModel):
    """Structured pricing intelligence."""

    tiers: list[PricingTier] = Field(description="All detected pricing tiers")
    has_free_tier: bool = Field(description="Whether a free plan is offered")
    has_enterprise_tier: bool = Field(description="Whether a custom enterprise plan exists")
    pricing_model: Literal["subscription", "usage-based", "one-time", "freemium", "unknown"] = Field(
        default="unknown",
    )
    confidence: float = Field(ge=0.0, le=1.0)


class HiringAgentOutput(BaseModel):
    """Job posting trend intelligence."""

    postings: list[JobPosting] = Field(description="All detected job postings")
    total_open_roles: int = Field(description="Total count of active open roles found")
    top_departments: list[str] = Field(description="Departments with the most open roles")
    growth_signal: Literal["hiring", "stable", "contracting", "unknown"] = Field(
        default="unknown",
        description="Inferred hiring trajectory",
    )
    confidence: float = Field(ge=0.0, le=1.0)


class ReportGenerationAgentOutput(BaseModel):
    """Final synthesised intelligence report produced by the ReportGenerationAgent.

    Fields map directly onto the ``reports`` table columns so the orchestrator
    can write them without any transformation.
    """

    summary: str = Field(description="Executive summary of the full competitive analysis")
    strengths: str = Field(description="Competitor strengths (serialised for DB storage)")
    weaknesses: str = Field(description="Competitor weaknesses")
    opportunities: str = Field(description="Market opportunities relative to them")
    threats: str = Field(description="Threats they pose to us")
    pricing_analysis: str = Field(description="Narrative analysis of their pricing strategy")
    feature_analysis: str = Field(description="Product feature comparison narrative")
    market_position: str = Field(description="Assessment of their market positioning")
    raw_ai_response: str = Field(description="Full JSON of the aggregated signal for audit")
    swot: SWOTAnalysis = Field(description="Structured SWOT breakdown")


# ---------------------------------------------------------------------------
# Orchestrator-level result
# ---------------------------------------------------------------------------

class OrchestratorResult(BaseModel):
    """The complete output produced by IntelligenceOrchestrator.run_pipeline().

    Returned to the Celery task which writes it to the DB.
    """

    report_generation: ReportGenerationAgentOutput
    research: ResearchAgentOutput
    news: NewsAgentOutput
    pricing: PricingAgentOutput
    hiring: HiringAgentOutput


# ---------------------------------------------------------------------------
# Forward references — resolve after all models are defined
# ---------------------------------------------------------------------------
ReportGenerationAgentInput.model_rebuild()
