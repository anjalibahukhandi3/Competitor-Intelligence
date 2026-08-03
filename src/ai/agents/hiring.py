"""HiringAgent — job posting trend analysis using Tavily and Gemini."""

from __future__ import annotations

import json
from src.ai.agents.base import BaseAgent
from src.ai.clients.gemini import GeminiClient
from src.ai.clients.tavily import TavilyClient
from src.ai.schemas import HiringAgentInput, HiringAgentOutput


class HiringAgent(BaseAgent[HiringAgentInput, HiringAgentOutput]):
    """Analyses competitor hiring activity and open roles via Tavily and Gemini."""

    agent_name = "HiringAgent"

    def __init__(
        self,
        tavily_client: TavilyClient | None = None,
        gemini_client: GeminiClient | None = None,
    ) -> None:
        self.tavily = tavily_client or TavilyClient()
        self.gemini = gemini_client or GeminiClient()

    async def _execute(self, input: HiringAgentInput) -> HiringAgentOutput:  # noqa: A002
        """Query Tavily for careers/jobs and analyze growth signals using Gemini."""
        search_query = f"{input.competitor_name} careers open positions job listings hiring"
        search_results = await self.tavily.search(
            query=search_query,
            days=90,
            max_results=5,
        )

        formatted_results = json.dumps(search_results, indent=2)

        prompt = (
            f"Competitor Name: {input.competitor_name}\n"
            f"Max Postings Requested: {input.max_postings}\n\n"
            f"Raw Search Results from Tavily (Careers & Jobs):\n{formatted_results}\n\n"
            f"Extract active job postings for {input.competitor_name}, infer departments, locations, "
            f"and key technology/skill requirements. Infer overall hiring growth signal (hiring, stable, contracting)."
        )

        system_prompt = (
            "You are a tech industry recruitment and organizational strategy analyst. "
            "Extract job openings and organizational hiring signals from search data."
        )

        return await self.gemini.extract_structured(
            prompt=prompt,
            schema_class=HiringAgentOutput,
            system_prompt=system_prompt,
        )
