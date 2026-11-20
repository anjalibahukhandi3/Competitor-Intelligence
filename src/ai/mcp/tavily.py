from src.ai.dependencies import AgentDeps

async def search_web_mcp_tool(deps: AgentDeps, query: str) -> list[dict]:
    """Explicitly report that the optional MCP adapter is not implemented.

    Production research uses ``TavilyClient`` directly. Never fabricate results.
    """
    raise NotImplementedError("Tavily MCP adapter is not configured; use TavilyClient")
