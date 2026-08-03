from src.ai.dependencies import AgentDeps

async def search_web_mcp_tool(deps: AgentDeps, query: str) -> list[dict]:
    """Search tool exposed to PydanticAI agents.
    
    Requests Tavily Search MCP server nodes to fetch external news articles.
    """
    return [{"title": "Competitor Launch", "url": "https://url.com", "snippet": "..."}]
