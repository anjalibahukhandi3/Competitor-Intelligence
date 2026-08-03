"""IntelligenceOrchestrator — coordinates the full competitor analysis pipeline.

Architecture
------------
The orchestrator is the single entry point for the AI pipeline. It:

1. Loads the Report and its associated Competitor from the database.
2. Builds typed inputs for each parallel agent.
3. Runs Research, News, Pricing, and Hiring agents concurrently via
   ``asyncio.gather()`` — no sequential bottlenecks.
4. Passes the aggregated signal to the ReportGenerationAgent.
5. Writes all result fields back to the Report row via the repository.

Clean Architecture boundary
----------------------------
The orchestrator is constructed with a ``ReportRepository`` that is
*injected* from the Celery task. This means:
- It never creates its own DB sessions.
- It has no knowledge of Celery, FastAPI, or HTTP.
- It is unit-testable with a mock repository (no DB needed).

Extensibility
-------------
Milestone 7: all agents return mock data.
Milestone 8: swap agent internals only — this file is unchanged.
"""

from __future__ import annotations

import asyncio
import structlog

from src.ai.agents.hiring import HiringAgent
from src.ai.agents.news import NewsAgent
from src.ai.agents.pricing import PricingAgent
from src.ai.agents.report_generation import ReportGenerationAgent
from src.ai.agents.research import ResearchAgent
from src.ai.schemas import (
    HiringAgentInput,
    NewsAgentInput,
    OrchestratorResult,
    PricingAgentInput,
    ReportGenerationAgentInput,
    ResearchAgentInput,
)
from src.domains.reports.repositories import ReportRepository

logger = structlog.get_logger(__name__)


class IntelligenceOrchestrator:
    """Coordinates all AI agents and writes results to the database.

    Parameters
    ----------
    report_id:
        UUID of the ``Report`` row that has already been created and set
        to ``status='processing'`` by the Celery task before calling this.
    repository:
        A ``ReportRepository`` bound to an open ``AsyncSession``. The
        session lifecycle is managed by the Celery task, not here.
    """

    def __init__(self, report_id: str, repository: ReportRepository) -> None:
        self.report_id = report_id
        self.repository = repository
        self._log = logger.bind(report_id=report_id)

        # Agent instances — stateless, reusable
        self._research_agent = ResearchAgent()
        self._news_agent = NewsAgent()
        self._pricing_agent = PricingAgent()
        self._hiring_agent = HiringAgent()
        self._report_agent = ReportGenerationAgent()

    async def run_pipeline(self) -> OrchestratorResult:
        """Execute the full analysis pipeline and persist results.

        Steps
        -----
        1. Load the Report (and its Competitor via selectin relationship).
        2. Build per-agent inputs from the Competitor data.
        3. Run parallel agents concurrently.
        4. Synthesise with the ReportGenerationAgent.
        5. Write all output fields back to the Report row.

        Returns
        -------
        OrchestratorResult
            The full typed result — also written to DB by this method.

        Raises
        ------
        ValueError
            If the report_id does not exist in the database.
        RuntimeError
            If the associated competitor record is missing (data integrity issue).
        """
        self._log.info("Orchestrator pipeline starting")

        # ----------------------------------------------------------------
        # Step 1: Load report + competitor
        # ----------------------------------------------------------------
        report = await self.repository.get_by_id(self.report_id)
        if report is None:
            raise ValueError(f"Report not found: {self.report_id}")

        competitor = report.competitor
        if competitor is None:
            raise RuntimeError(
                f"Report {self.report_id} has no associated competitor — data integrity issue"
            )

        self._log.info(
            "Loaded report and competitor",
            competitor_id=competitor.id,
            competitor_name=competitor.company_name,
        )

        # ----------------------------------------------------------------
        # Step 2: Build agent inputs
        # ----------------------------------------------------------------
        base_kwargs = dict(
            competitor_id=competitor.id,
            competitor_name=competitor.company_name,
            competitor_url=str(competitor.website),
        )

        research_input = ResearchAgentInput(**base_kwargs)
        news_input = NewsAgentInput(**base_kwargs, days_back=30)
        pricing_input = PricingAgentInput(**base_kwargs)
        hiring_input = HiringAgentInput(**base_kwargs, max_postings=20)

        # ----------------------------------------------------------------
        # Step 3: Run parallel agents
        # ----------------------------------------------------------------
        self._log.info("Running parallel agents")

        research_result, news_result, pricing_result, hiring_result = await asyncio.gather(
            self._research_agent.run(research_input),
            self._news_agent.run(news_input),
            self._pricing_agent.run(pricing_input),
            self._hiring_agent.run(hiring_input),
        )

        self._log.info("Parallel agents completed")

        # ----------------------------------------------------------------
        # Step 4: Synthesise with ReportGenerationAgent
        # ----------------------------------------------------------------
        report_input = ReportGenerationAgentInput(
            competitor_id=competitor.id,
            competitor_name=competitor.company_name,
            competitor_url=str(competitor.website),
            research=research_result,
            news=news_result,
            pricing=pricing_result,
            hiring=hiring_result,
        )

        report_output = await self._report_agent.run(report_input)
        self._log.info("Report generation agent completed")

        # ----------------------------------------------------------------
        # Step 5: Persist all result fields to the Report row
        # ----------------------------------------------------------------
        report.summary = report_output.summary
        report.strengths = report_output.strengths
        report.weaknesses = report_output.weaknesses
        report.opportunities = report_output.opportunities
        report.threats = report_output.threats
        report.pricing_analysis = report_output.pricing_analysis
        report.feature_analysis = report_output.feature_analysis
        report.market_position = report_output.market_position
        report.raw_ai_response = report_output.raw_ai_response

        await self.repository.update(report)
        self._log.info("Report fields persisted to database")

        result = OrchestratorResult(
            report_generation=report_output,
            research=research_result,
            news=news_result,
            pricing=pricing_result,
            hiring=hiring_result,
        )

        self._log.info("Orchestrator pipeline completed successfully")
        return result
