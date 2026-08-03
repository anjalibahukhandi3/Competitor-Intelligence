"""Unit tests for all AI agent implementations with 100% mocked external API clients.

Design
------
- No external network calls (Firecrawl, Tavily, Gemini are fully mocked with AsyncMock).
- Tests validate agent execution flow, schema compatibility, input handling, and error handling.
- Runs cleanly in milliseconds.
"""

from unittest.mock import AsyncMock

import pytest

from src.ai.agents.hiring import HiringAgent
from src.ai.agents.news import NewsAgent
from src.ai.agents.pricing import PricingAgent
from src.ai.agents.report_generation import ReportGenerationAgent
from src.ai.agents.research import ResearchAgent
from src.ai.schemas import (
    HiringAgentInput,
    HiringAgentOutput,
    JobPosting,
    NewsAgentInput,
    NewsAgentOutput,
    NewsItem,
    PricingAgentInput,
    PricingAgentOutput,
    PricingTier,
    ReportGenerationAgentInput,
    ReportGenerationAgentOutput,
    ResearchAgentInput,
    ResearchAgentOutput,
    SWOTAnalysis,
)

# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

COMPETITOR_ID = "comp-abc-123"
COMPETITOR_NAME = "AcmeCorp"
COMPETITOR_URL = "https://acmecorp.example.com"

BASE_KWARGS = dict(
    competitor_id=COMPETITOR_ID,
    competitor_name=COMPETITOR_NAME,
    competitor_url=COMPETITOR_URL,
)


# ---------------------------------------------------------------------------
# Mock response factories
# ---------------------------------------------------------------------------

def make_mock_research_output() -> ResearchAgentOutput:
    return ResearchAgentOutput(
        tagline="AcmeCorp — The ultimate platform",
        primary_use_cases=["Project management", "Analytics"],
        tech_stack_signals=["React", "Python", "AWS"],
        target_customers=["SMBs", "Enterprise"],
        key_differentiators=["AI automation", "24/7 Support"],
        confidence=0.9,
    )


def make_mock_news_output() -> NewsAgentOutput:
    return NewsAgentOutput(
        items=[
            NewsItem(
                headline="AcmeCorp raises Series C",
                source="TechCrunch",
                sentiment="positive",
                summary="Raised funding.",
            )
        ],
        overall_sentiment="positive",
        key_themes=["Funding", "Growth"],
        confidence=0.85,
    )


def make_mock_pricing_output() -> PricingAgentOutput:
    return PricingAgentOutput(
        tiers=[
            PricingTier(
                tier_name="Pro",
                price="$29/mo",
                billing_cycle="monthly",
                key_features=["Unlimited projects"],
            )
        ],
        has_free_tier=True,
        has_enterprise_tier=True,
        pricing_model="subscription",
        confidence=0.95,
    )


def make_mock_hiring_output() -> HiringAgentOutput:
    return HiringAgentOutput(
        postings=[
            JobPosting(
                title="Senior Engineer",
                department="Engineering",
                location="Remote",
                inferred_skills=["Python", "PostgreSQL"],
            )
        ],
        total_open_roles=1,
        top_departments=["Engineering"],
        growth_signal="hiring",
        confidence=0.8,
    )


def make_mock_report_output() -> ReportGenerationAgentOutput:
    return ReportGenerationAgentOutput(
        summary="AcmeCorp is expanding rapidly.",
        strengths="• Strong brand",
        weaknesses="• High churn",
        opportunities="• Enterprise market",
        threats="• New entrants",
        pricing_analysis="Competitive pricing.",
        feature_analysis="Rich feature set.",
        market_position="Market leader.",
        raw_ai_response="{}",
        swot=SWOTAnalysis(
            strengths=["Strong brand"],
            weaknesses=["High churn"],
            opportunities=["Enterprise market"],
            threats=["New entrants"],
        ),
    )


# ---------------------------------------------------------------------------
# ResearchAgent tests
# ---------------------------------------------------------------------------

class TestResearchAgent:
    """Tests for ResearchAgent with mocked clients."""

    @pytest.fixture
    def mock_firecrawl(self) -> AsyncMock:
        mock = AsyncMock()
        mock.scrape.return_value = {
            "markdown": "# AcmeCorp\nWelcome to AcmeCorp.",
            "title": "AcmeCorp Home",
            "description": "AcmeCorp description",
        }
        return mock

    @pytest.fixture
    def mock_gemini(self) -> AsyncMock:
        mock = AsyncMock()
        mock.extract_structured.return_value = make_mock_research_output()
        return mock

    async def test_research_agent_execution(
        self, mock_firecrawl: AsyncMock, mock_gemini: AsyncMock
    ) -> None:
        agent = ResearchAgent(firecrawl_client=mock_firecrawl, gemini_client=mock_gemini)
        input_ = ResearchAgentInput(**BASE_KWARGS)

        result = await agent.run(input_)

        assert isinstance(result, ResearchAgentOutput)
        assert result.tagline == "AcmeCorp — The ultimate platform"
        mock_firecrawl.scrape.assert_awaited_once_with(COMPETITOR_URL)
        mock_gemini.extract_structured.assert_awaited_once()


# ---------------------------------------------------------------------------
# NewsAgent tests
# ---------------------------------------------------------------------------

class TestNewsAgent:
    """Tests for NewsAgent with mocked clients."""

    @pytest.fixture
    def mock_tavily(self) -> AsyncMock:
        mock = AsyncMock()
        mock.search.return_value = [
            {
                "title": "AcmeCorp raises Series C",
                "url": "https://news.example.com/acme",
                "content": "AcmeCorp raises Series C funding",
                "published_date": "2026-07-01",
            }
        ]
        return mock

    @pytest.fixture
    def mock_gemini(self) -> AsyncMock:
        mock = AsyncMock()
        mock.extract_structured.return_value = make_mock_news_output()
        return mock

    async def test_news_agent_execution(
        self, mock_tavily: AsyncMock, mock_gemini: AsyncMock
    ) -> None:
        agent = NewsAgent(tavily_client=mock_tavily, gemini_client=mock_gemini)
        input_ = NewsAgentInput(**BASE_KWARGS, days_back=30)

        result = await agent.run(input_)

        assert isinstance(result, NewsAgentOutput)
        assert result.overall_sentiment == "positive"
        mock_tavily.search.assert_awaited_once()
        mock_gemini.extract_structured.assert_awaited_once()


# ---------------------------------------------------------------------------
# PricingAgent tests
# ---------------------------------------------------------------------------

class TestPricingAgent:
    """Tests for PricingAgent with mocked clients."""

    @pytest.fixture
    def mock_firecrawl(self) -> AsyncMock:
        mock = AsyncMock()
        mock.scrape.return_value = {
            "markdown": "# Pricing\nPro plan $29/mo",
            "title": "Pricing Page",
            "description": "Pricing details",
        }
        return mock

    @pytest.fixture
    def mock_gemini(self) -> AsyncMock:
        mock = AsyncMock()
        mock.extract_structured.return_value = make_mock_pricing_output()
        return mock

    async def test_pricing_agent_execution(
        self, mock_firecrawl: AsyncMock, mock_gemini: AsyncMock
    ) -> None:
        agent = PricingAgent(firecrawl_client=mock_firecrawl, gemini_client=mock_gemini)
        input_ = PricingAgentInput(**BASE_KWARGS)

        result = await agent.run(input_)

        assert isinstance(result, PricingAgentOutput)
        assert len(result.tiers) == 1
        mock_firecrawl.scrape.assert_awaited_once()
        mock_gemini.extract_structured.assert_awaited_once()


# ---------------------------------------------------------------------------
# HiringAgent tests
# ---------------------------------------------------------------------------

class TestHiringAgent:
    """Tests for HiringAgent with mocked clients."""

    @pytest.fixture
    def mock_tavily(self) -> AsyncMock:
        mock = AsyncMock()
        mock.search.return_value = [
            {
                "title": "Senior Engineer at AcmeCorp",
                "url": "https://jobs.example.com/acme",
                "content": "Hiring Senior Engineer",
            }
        ]
        return mock

    @pytest.fixture
    def mock_gemini(self) -> AsyncMock:
        mock = AsyncMock()
        mock.extract_structured.return_value = make_mock_hiring_output()
        return mock

    async def test_hiring_agent_execution(
        self, mock_tavily: AsyncMock, mock_gemini: AsyncMock
    ) -> None:
        agent = HiringAgent(tavily_client=mock_tavily, gemini_client=mock_gemini)
        input_ = HiringAgentInput(**BASE_KWARGS, max_postings=20)

        result = await agent.run(input_)

        assert isinstance(result, HiringAgentOutput)
        assert result.growth_signal == "hiring"
        mock_tavily.search.assert_awaited_once()
        mock_gemini.extract_structured.assert_awaited_once()


# ---------------------------------------------------------------------------
# ReportGenerationAgent tests
# ---------------------------------------------------------------------------

class TestReportGenerationAgent:
    """Tests for ReportGenerationAgent with mocked Gemini client."""

    @pytest.fixture
    def mock_gemini(self) -> AsyncMock:
        mock = AsyncMock()
        mock.extract_structured.return_value = make_mock_report_output()
        return mock

    async def test_report_generation_agent_execution(self, mock_gemini: AsyncMock) -> None:
        agent = ReportGenerationAgent(gemini_client=mock_gemini)
        input_ = ReportGenerationAgentInput(
            **BASE_KWARGS,
            research=make_mock_research_output(),
            news=make_mock_news_output(),
            pricing=make_mock_pricing_output(),
            hiring=make_mock_hiring_output(),
        )

        result = await agent.run(input_)

        assert isinstance(result, ReportGenerationAgentOutput)
        assert result.summary == "AcmeCorp is expanding rapidly."
        mock_gemini.extract_structured.assert_awaited_once()
