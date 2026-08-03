from src.ai.dependencies import AgentDeps

async def scrape_url_mcp_tool(deps: AgentDeps, url: str) -> str:
    """Crawler tool exposed to PydanticAI agents.
    
    Requests Firecrawl MCP server nodes to fetch full markdown summaries.
    """
    return "Parsed site markdown output placeholder"
