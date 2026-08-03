"""NewsAgent — press release and news mention collection using Tavily and Gemini."""

from __future__ import annotations

import json
from src.ai.agents.base import BaseAgent
from src.ai.clients.gemini import GeminiClient
from src.ai.clients.tavily import TavilyClient
from src.ai.schemas import NewsAgentInput, NewsAgentOutput


class NewsAgent(BaseAgent[NewsAgentInput, NewsAgentOutput]):
    """Collects and analyses recent news coverage about the competitor via Tavily and Gemini.

    Identifies key themes, overall media sentiment, and recent strategic announcements.
    """

    agent_name = "NewsAgent"

    def __init__(
        self,
        tavily_client: TavilyClient | None = None,
        gemini_client: GeminiClient | None = None,
    ) -> None:
        self.tavily = tavily_client or TavilyClient()
        self.gemini = gemini_client or GeminiClient()

    async def _execute(self, input: NewsAgentInput) -> NewsAgentOutput:  # noqa: A002
        """Query Tavily for news and analyze sentiment / themes using Gemini."""
        search_query = f"{input.competitor_name} news press release funding announcement product launch"
        search_results = await self.tavily.search(
            query=search_query,
            days=input.days_back,
            max_results=5,
        )

        formatted_results = json.dumps(search_results, indent=2)

        prompt = (
            f"Competitor Name: {input.competitor_name}\n"
            f"Recency Window: {input.days_back} days\n\n"
            f"Raw Search Results from Tavily:\n{formatted_results}\n\n"
            f"Analyze the search results for {input.competitor_name}. Extract individual news items with "
            f"headlines, sources, publication dates (if found), sentiment, and one-sentence summaries. "
            f"Classify overall media sentiment and extract recurring themes."
        )

        system_prompt = (
            "You are a professional financial and media news analyst. "
            "Examine search results and extract accurate, structured news intelligence."
        )

        return await self.gemini.extract_structured(
            prompt=prompt,
            schema_class=NewsAgentOutput,
            system_prompt=system_prompt,
        )
