"""Domain-specific exceptions for AI agent operations and external API integrations."""

from src.exceptions import AIExecutionException


class FirecrawlException(AIExecutionException):
    """Raised when Firecrawl web crawling or scraping API operations fail."""
    pass


class TavilyException(AIExecutionException):
    """Raised when Tavily search or news retrieval API operations fail."""
    pass


class GeminiException(AIExecutionException):
    """Raised when Google Gemini LLM generation or extraction fails."""
    pass
