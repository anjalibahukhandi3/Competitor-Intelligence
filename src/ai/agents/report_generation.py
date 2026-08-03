"""ReportGenerationAgent — aggregated signal synthesis using Gemini."""

from __future__ import annotations

import json
from src.ai.agents.base import BaseAgent
from src.ai.clients.gemini import GeminiClient
from src.ai.schemas import (
    ReportGenerationAgentInput,
    ReportGenerationAgentOutput,
)


class ReportGenerationAgent(
    BaseAgent[ReportGenerationAgentInput, ReportGenerationAgentOutput]
):
    """Synthesises all agent outputs into the final intelligence report using Gemini.

    Receives fully-typed outputs from parallel agents and produces narrative sections
    mapping onto ``reports`` table columns.
    """

    agent_name = "ReportGenerationAgent"

    def __init__(self, gemini_client: GeminiClient | None = None) -> None:
        self.gemini = gemini_client or GeminiClient()

    async def _execute(  # noqa: A002
        self, input: ReportGenerationAgentInput
    ) -> ReportGenerationAgentOutput:
        """Synthesise research, news, pricing, and hiring outputs using Gemini."""
        aggregated_signals = {
            "competitor_id": input.competitor_id,
            "competitor_name": input.competitor_name,
            "competitor_url": input.competitor_url,
            "research": input.research.model_dump(),
            "news": input.news.model_dump(mode="json"),
            "pricing": input.pricing.model_dump(),
            "hiring": input.hiring.model_dump(mode="json"),
        }

        signals_json = json.dumps(aggregated_signals, indent=2, default=str)

        prompt = (
            f"Competitor Name: {input.competitor_name}\n"
            f"Competitor Website: {input.competitor_url}\n\n"
            f"Aggregated Intelligence Signals from Research, News, Pricing, and Hiring Agents:\n"
            f"{signals_json}\n\n"
            f"Synthesize a comprehensive, executive-grade Competitive Intelligence Report for {input.competitor_name}. "
            f"Provide:\n"
            f"1. Executive Summary\n"
            f"2. Structured SWOT Analysis (strengths, weaknesses, opportunities, threats)\n"
            f"3. Narrative strings for strengths, weaknesses, opportunities, threats (bullet points formatted with •)\n"
            f"4. Pricing Analysis narrative\n"
            f"5. Product & Feature Analysis narrative\n"
            f"6. Market Positioning assessment narrative\n"
            f"7. Raw AI Response payload preserving the JSON signals."
        )

        system_prompt = (
            "You are a Chief Strategy Officer and Senior Competitive Intelligence Executive. "
            "Synthesize raw data into strategic, actionable, high-impact business insights."
        )

        output = await self.gemini.extract_structured(
            prompt=prompt,
            schema_class=ReportGenerationAgentOutput,
            system_prompt=system_prompt,
        )

        # Ensure raw_ai_response is populated if LLM returns empty for it
        if not output.raw_ai_response or len(output.raw_ai_response) < 10:
            output.raw_ai_response = signals_json

        return output
