"""PricingAgent — pricing page extraction and tier analysis using Firecrawl and Gemini."""

from __future__ import annotations

from src.ai.agents.base import BaseAgent
from src.ai.clients.firecrawl import FirecrawlClient
from src.ai.clients.gemini import GeminiClient
from src.ai.exceptions import FirecrawlException
from src.ai.schemas import PricingAgentInput, PricingAgentOutput


class PricingAgent(BaseAgent[PricingAgentInput, PricingAgentOutput]):
    """Extracts and structures the competitor's pricing model via Firecrawl and Gemini.

    Identifies all tiers, prices, billing cycles, and key feature differentiators.
    """

    agent_name = "PricingAgent"

    def __init__(
        self,
        firecrawl_client: FirecrawlClient | None = None,
        gemini_client: GeminiClient | None = None,
    ) -> None:
        self.firecrawl = firecrawl_client or FirecrawlClient()
        self.gemini = gemini_client or GeminiClient()

    async def _execute(self, input: PricingAgentInput) -> PricingAgentOutput:  # noqa: A002
        """Crawl competitor pricing page and normalize tiers using Gemini."""
        pricing_url = f"{input.competitor_url.rstrip('/')}/pricing"

        try:
            scrape_result = await self.firecrawl.scrape(pricing_url)
        except FirecrawlException:
            # Fallback to main URL if /pricing URL fails or doesn't exist
            scrape_result = await self.firecrawl.scrape(input.competitor_url)

        markdown_content = scrape_result.get("markdown", "")

        prompt = (
            f"Competitor Name: {input.competitor_name}\n"
            f"Pricing URL: {pricing_url}\n\n"
            f"Scraped Pricing Page Content:\n"
            f"{markdown_content[:10000]}\n\n"
            f"Extract all pricing tiers, prices, billing cycles, key features, and determine "
            f"whether a free tier or enterprise tier exists, along with overall pricing model."
        )

        system_prompt = (
            "You are a SaaS pricing strategy analyst. "
            "Extract and normalize pricing models, plans, and tier feature lists into structured JSON."
        )

        return await self.gemini.extract_structured(
            prompt=prompt,
            schema_class=PricingAgentOutput,
            system_prompt=system_prompt,
        )
