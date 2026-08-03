"""ResearchAgent — homepage and product page analysis using Firecrawl and Gemini."""

from __future__ import annotations

from src.ai.agents.base import BaseAgent
from src.ai.clients.firecrawl import FirecrawlClient
from src.ai.clients.gemini import GeminiClient
from src.ai.schemas import ResearchAgentInput, ResearchAgentOutput


class ResearchAgent(BaseAgent[ResearchAgentInput, ResearchAgentOutput]):
    """Analyses the competitor's homepage and product pages via Firecrawl and Gemini.

    Produces a structured profile of their value proposition, tech stack
    signals, and target customer segments.
    """

    agent_name = "ResearchAgent"

    def __init__(
        self,
        firecrawl_client: FirecrawlClient | None = None,
        gemini_client: GeminiClient | None = None,
    ) -> None:
        self.firecrawl = firecrawl_client or FirecrawlClient()
        self.gemini = gemini_client or GeminiClient()

    async def _execute(self, input: ResearchAgentInput) -> ResearchAgentOutput:  # noqa: A002
        """Crawl competitor site and extract structured research output."""
        scrape_result = await self.firecrawl.scrape(input.competitor_url)
        markdown_content = scrape_result.get("markdown", "")

        prompt = (
            f"Competitor Name: {input.competitor_name}\n"
            f"Competitor Website: {input.competitor_url}\n"
            f"Page Title: {scrape_result.get('title', '')}\n"
            f"Page Description: {scrape_result.get('description', '')}\n\n"
            f"Scraped Website Markdown Content:\n"
            f"{markdown_content[:10000]}\n\n"
            f"Extract and analyze {input.competitor_name}'s product offerings, value proposition, "
            f"tech stack signals, target customers, and key differentiators."
        )

        system_prompt = (
            "You are an expert competitive intelligence research analyst. "
            "Examine the provided website content and extract accurate structural data."
        )

        return await self.gemini.extract_structured(
            prompt=prompt,
            schema_class=ResearchAgentOutput,
            system_prompt=system_prompt,
        )
