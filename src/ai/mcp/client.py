class MCPClientManager:
    """Orchestrates communication with local/remote MCP Servers.
    
    Establishes transport client protocols for Firecrawl and Tavily connections.
    """
    def __init__(self) -> None:
        """Construct an adapter placeholder without opening connections."""
        
    async def connect_servers(self) -> None:
        """Fail clearly until a supported MCP transport is implemented."""
        raise NotImplementedError("MCP server connections are not implemented")
        
    async def close_connections(self) -> None:
        """Fail clearly until a supported MCP transport is implemented."""
        raise NotImplementedError("MCP server connections are not implemented")
