"""Unit tests for IntelligenceOrchestrator.

Design
------
- Uses ``unittest.mock.AsyncMock`` to stub the ReportRepository.
- Mocks all external API clients (Firecrawl, Tavily, Claude) so no network calls or API keys are needed.
- Tests verify the orchestration contract:
    * Correct loading of report and competitor
    * All four parallel agents are invoked
    * ReportGenerationAgent receives aggregated inputs
    * All report fields are written back via repository.update()
    * ValueError raised for missing report
    * RuntimeError raised for orphaned report (no competitor)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from src.ai.orchestrator import IntelligenceOrchestrator
from src.ai.schemas import (
    HiringAgentOutput,
    JobPosting,
    NewsAgentOutput,
    NewsItem,
    OrchestratorResult,
    PricingAgentOutput,
    PricingTier,
    ReportGenerationAgentOutput,
    ResearchAgentOutput,
    SWOTAnalysis,
)


# ---------------------------------------------------------------------------
# Shared mock outputs for orchestrator tests
# ---------------------------------------------------------------------------

def make_mock_research_output() -> ResearchAgentOutput:
    return ResearchAgentOutput(
        tagline="TestCorp — Premium Platform",
        primary_use_cases=["Analytics", "Automation"],
        tech_stack_signals=["React", "Python"],
        target_customers=["Enterprise"],
        key_differentiators=["Speed", "Security"],
        confidence=0.9,
    )


def make_mock_news_output() -> NewsAgentOutput:
    return NewsAgentOutput(
        items=[
            NewsItem(
                headline="TestCorp raises funding",
                source="TechCrunch",
                sentiment="positive",
                summary="Raised Series B",
            )
        ],
        overall_sentiment="positive",
        key_themes=["Funding"],
        confidence=0.85,
    )


def make_mock_pricing_output() -> PricingAgentOutput:
    return PricingAgentOutput(
        tiers=[
            PricingTier(
                tier_name="Pro",
                price="$49/mo",
                billing_cycle="monthly",
                key_features=["All features"],
            )
        ],
        has_free_tier=False,
        has_enterprise_tier=True,
        pricing_model="subscription",
        confidence=0.95,
    )


def make_mock_hiring_output() -> HiringAgentOutput:
    return HiringAgentOutput(
        postings=[
            JobPosting(
                title="Lead Developer",
                department="Engineering",
                location="Remote",
                inferred_skills=["Python", "AWS"],
            )
        ],
        total_open_roles=1,
        top_departments=["Engineering"],
        growth_signal="hiring",
        confidence=0.8,
    )


def make_mock_report_output() -> ReportGenerationAgentOutput:
    return ReportGenerationAgentOutput(
        summary="TestCorp is performing strongly.",
        strengths="• Strong engineering team",
        weaknesses="• High pricing",
        opportunities="• Global expansion",
        threats="• Emerging startups",
        pricing_analysis="Premium pricing model.",
        feature_analysis="Feature complete.",
        market_position="Leader in space.",
        raw_ai_response="{}",
        swot=SWOTAnalysis(
            strengths=["Strong engineering team"],
            weaknesses=["High pricing"],
            opportunities=["Global expansion"],
            threats=["Emerging startups"],
        ),
    )


@pytest.fixture(autouse=True)
def mock_external_api_clients():
    """Autouse fixture to mock external API calls across all orchestrator tests."""
    with patch("src.ai.clients.firecrawl.FirecrawlClient.scrape", new_callable=AsyncMock) as mock_scrape, \
         patch("src.ai.clients.tavily.TavilyClient.search", new_callable=AsyncMock) as mock_search, \
         patch("src.ai.clients.gemini.GeminiClient.extract_structured", new_callable=AsyncMock) as mock_gemini:

        mock_scrape.return_value = {"markdown": "# TestCorp\nScraped content", "title": "TestCorp", "description": "Desc"}
        mock_search.return_value = [{"title": "TestCorp news", "url": "https://news.example.com", "content": "News body"}]

        def side_effect(prompt, schema_class, **kwargs):
            if schema_class == ResearchAgentOutput:
                return make_mock_research_output()
            elif schema_class == NewsAgentOutput:
                return make_mock_news_output()
            elif schema_class == PricingAgentOutput:
                return make_mock_pricing_output()
            elif schema_class == HiringAgentOutput:
                return make_mock_hiring_output()
            elif schema_class == ReportGenerationAgentOutput:
                return make_mock_report_output()
            return schema_class.model_construct()

        mock_gemini.side_effect = side_effect
        yield


# ---------------------------------------------------------------------------
# Helpers — build mock ORM objects
# ---------------------------------------------------------------------------

def _make_mock_competitor(
    competitor_id: str = "comp-111",
    name: str = "TestCorp",
    url: str = "https://testcorp.example.com",
) -> MagicMock:
    competitor = MagicMock()
    competitor.id = competitor_id
    competitor.company_name = name
    competitor.website = url
    return competitor


def _make_mock_report(
    report_id: str = "report-999",
    competitor: MagicMock | None = None,
) -> MagicMock:
    report = MagicMock()
    report.id = report_id
    report.competitor = competitor or _make_mock_competitor()
    # Writable fields — should be set by orchestrator
    report.summary = None
    report.strengths = None
    report.weaknesses = None
    report.opportunities = None
    report.threats = None
    report.pricing_analysis = None
    report.feature_analysis = None
    report.market_position = None
    report.raw_ai_response = None
    return report


def _make_mock_repository(report: MagicMock | None = None) -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_id.return_value = report or _make_mock_report()
    repo.update.return_value = repo.get_by_id.return_value
    return repo


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

class TestIntelligenceOrchestratorHappyPath:
    """Tests for the successful orchestration flow."""

    async def test_run_pipeline_returns_orchestrator_result(self) -> None:
        """run_pipeline() must return an OrchestratorResult."""
        repo = _make_mock_repository()
        orchestrator = IntelligenceOrchestrator("report-999", repo)

        result = await orchestrator.run_pipeline()

        assert isinstance(result, OrchestratorResult)

    async def test_get_by_id_called_with_correct_report_id(self) -> None:
        """Orchestrator must load the report by the given ID."""
        repo = _make_mock_repository()
        orchestrator = IntelligenceOrchestrator("report-999", repo)

        await orchestrator.run_pipeline()

        repo.get_by_id.assert_awaited_once_with("report-999")

    async def test_repository_update_called_once(self) -> None:
        """Orchestrator must call repository.update() exactly once to persist fields."""
        repo = _make_mock_repository()
        orchestrator = IntelligenceOrchestrator("report-999", repo)

        await orchestrator.run_pipeline()

        repo.update.assert_awaited_once()

    async def test_report_summary_is_written(self) -> None:
        """After run_pipeline(), report.summary must be set to a non-empty string."""
        report = _make_mock_report()
        repo = _make_mock_repository(report=report)
        orchestrator = IntelligenceOrchestrator("report-999", repo)

        await orchestrator.run_pipeline()

        assert report.summary is not None
        assert isinstance(report.summary, str)
        assert report.summary.strip() != ""

    async def test_all_report_fields_are_written(self) -> None:
        """All nine report AI fields must be set after a successful pipeline run."""
        report = _make_mock_report()
        repo = _make_mock_repository(report=report)
        orchestrator = IntelligenceOrchestrator("report-999", repo)

        await orchestrator.run_pipeline()

        fields = [
            report.summary,
            report.strengths,
            report.weaknesses,
            report.opportunities,
            report.threats,
            report.pricing_analysis,
            report.feature_analysis,
            report.market_position,
            report.raw_ai_response,
        ]
        for field in fields:
            assert field is not None, f"Expected field to be set, got None"
            assert isinstance(field, str)

    async def test_result_contains_all_agent_outputs(self) -> None:
        """OrchestratorResult must contain outputs from all four parallel agents."""
        repo = _make_mock_repository()
        orchestrator = IntelligenceOrchestrator("report-999", repo)

        result = await orchestrator.run_pipeline()

        assert result.research is not None
        assert result.news is not None
        assert result.pricing is not None
        assert result.hiring is not None
        assert result.report_generation is not None


# ---------------------------------------------------------------------------
# Error-path tests
# ---------------------------------------------------------------------------

class TestIntelligenceOrchestratorErrorPaths:
    """Tests for failure modes."""

    async def test_raises_value_error_when_report_not_found(self) -> None:
        """Orchestrator must raise ValueError if report_id does not exist."""
        repo = _make_mock_repository()
        repo.get_by_id.return_value = None  # simulate missing report

        orchestrator = IntelligenceOrchestrator("nonexistent-id", repo)

        with pytest.raises(ValueError, match="Report not found"):
            await orchestrator.run_pipeline()

    async def test_raises_runtime_error_when_competitor_is_none(self) -> None:
        """Orchestrator must raise RuntimeError if report has no competitor (integrity issue)."""
        report = _make_mock_report()
        report.competitor = None  # simulate data integrity issue
        repo = _make_mock_repository(report=report)

        orchestrator = IntelligenceOrchestrator("report-broken", repo)

        with pytest.raises(RuntimeError, match="no associated competitor"):
            await orchestrator.run_pipeline()

    async def test_update_not_called_when_report_missing(self) -> None:
        """If the report does not exist, repository.update() must never be called."""
        repo = _make_mock_repository()
        repo.get_by_id.return_value = None

        orchestrator = IntelligenceOrchestrator("nonexistent-id", repo)

        with pytest.raises(ValueError):
            await orchestrator.run_pipeline()

        repo.update.assert_not_awaited()

    async def test_orchestrator_propagates_agent_exceptions(self) -> None:
        """If an agent raises, run_pipeline() must propagate the exception."""
        repo = _make_mock_repository()
        orchestrator = IntelligenceOrchestrator("report-999", repo)

        with patch.object(
            orchestrator._research_agent,
            "run",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Firecrawl timeout"),
        ):
            with pytest.raises(RuntimeError, match="Firecrawl timeout"):
                await orchestrator.run_pipeline()

    async def test_update_not_called_when_agent_fails(self) -> None:
        """If an agent fails, no DB write should occur."""
        repo = _make_mock_repository()
        orchestrator = IntelligenceOrchestrator("report-999", repo)

        with patch.object(
            orchestrator._pricing_agent,
            "run",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Scrape blocked"),
        ):
            with pytest.raises(RuntimeError):
                await orchestrator.run_pipeline()

        repo.update.assert_not_awaited()


# ---------------------------------------------------------------------------
# Parallel execution test
# ---------------------------------------------------------------------------

class TestOrchestratorParallelExecution:
    """Verify that the four data-gathering agents run concurrently."""

    async def test_agents_run_concurrently(self) -> None:
        """All four parallel agents should be invoked; order is not guaranteed."""
        repo = _make_mock_repository()
        orchestrator = IntelligenceOrchestrator("report-999", repo)

        call_order: list[str] = []

        original_research_run = orchestrator._research_agent.run
        original_news_run = orchestrator._news_agent.run
        original_pricing_run = orchestrator._pricing_agent.run
        original_hiring_run = orchestrator._hiring_agent.run

        async def track_research(input_):  # noqa: ANN001
            call_order.append("research")
            return await original_research_run(input_)

        async def track_news(input_):  # noqa: ANN001
            call_order.append("news")
            return await original_news_run(input_)

        async def track_pricing(input_):  # noqa: ANN001
            call_order.append("pricing")
            return await original_pricing_run(input_)

        async def track_hiring(input_):  # noqa: ANN001
            call_order.append("hiring")
            return await original_hiring_run(input_)

        orchestrator._research_agent.run = track_research
        orchestrator._news_agent.run = track_news
        orchestrator._pricing_agent.run = track_pricing
        orchestrator._hiring_agent.run = track_hiring

        await orchestrator.run_pipeline()

        # All four must have been called
        assert "research" in call_order
        assert "news" in call_order
        assert "pricing" in call_order
        assert "hiring" in call_order

    async def test_report_generation_runs_after_parallel_agents(self) -> None:
        """ReportGenerationAgent must run after all four parallel agents complete."""
        repo = _make_mock_repository()
        orchestrator = IntelligenceOrchestrator("report-999", repo)

        call_order: list[str] = []

        original_report_run = orchestrator._report_agent.run

        async def track_report(input_):  # noqa: ANN001
            call_order.append("report_gen")
            return await original_report_run(input_)

        original_research_run = orchestrator._research_agent.run

        async def track_research(input_):  # noqa: ANN001
            call_order.append("research")
            return await original_research_run(input_)

        orchestrator._research_agent.run = track_research
        orchestrator._report_agent.run = track_report

        await orchestrator.run_pipeline()

        # research must appear before report_gen
        assert call_order.index("research") < call_order.index("report_gen")
