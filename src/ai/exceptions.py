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


class AIConfigurationException(AIExecutionException):
    """Raised for permanent configuration problems (missing or placeholder API keys).

    Unlike FirecrawlException / TavilyException / GeminiException — which can also
    represent transient network or rate-limit failures worth retrying — this
    exception means retrying will never succeed until a human fixes the
    configuration. Celery's ``autoretry_for`` list (see ``src/jobs/tasks.py``)
    deliberately excludes this type so a bad or missing API key fails fast instead
    of burning through multiple 60-second retries.
    """
    pass
