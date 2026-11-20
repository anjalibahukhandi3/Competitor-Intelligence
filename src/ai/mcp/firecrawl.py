from src.ai.dependencies import AgentDeps

async def scrape_url_mcp_tool(deps: AgentDeps, url: str) -> str:
    """Explicitly report that the optional MCP adapter is not implemented.

    Production scraping uses ``FirecrawlClient`` directly. Returning fabricated
    page content here could otherwise make an agent report false findings.
    """
    raise NotImplementedError("Firecrawl MCP adapter is not configured; use FirecrawlClient")
