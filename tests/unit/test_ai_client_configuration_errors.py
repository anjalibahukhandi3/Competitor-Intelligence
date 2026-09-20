"""Unit tests confirming Firecrawl/Tavily/Gemini clients raise the permanent,
non-retryable ``AIConfigurationException`` (not their transient-failure
exception types) when an API key is missing or still the default placeholder.

This distinction matters for `src/jobs/tasks.py`'s Celery retry policy:
`RETRYABLE_PIPELINE_EXCEPTIONS` deliberately excludes `AIConfigurationException`
so a bad key fails a report immediately instead of burning three wasted
60-second retries that could never succeed.
"""

from unittest.mock import patch

import pytest

from src.ai.clients.firecrawl import FirecrawlClient
from src.ai.clients.gemini import GeminiClient
from src.ai.clients.tavily import TavilyClient
from src.ai.exceptions import AIConfigurationException, FirecrawlException, GeminiException, TavilyException


@pytest.mark.asyncio
async def test_firecrawl_raises_configuration_exception_for_placeholder_key() -> None:
    client = FirecrawlClient(api_key="your_firecrawl_api_key_here")
    with pytest.raises(AIConfigurationException):
        await client.scrape("https://example.com")


@pytest.mark.asyncio
async def test_firecrawl_raises_configuration_exception_for_missing_key() -> None:
    """`api_key=None` alone isn't enough to prove "missing" — the client falls
    back to `settings.external.firecrawl_api_key`, which may be a real
    configured key in this environment. Patch the settings fallback too.
    """
    with patch("src.ai.clients.firecrawl.settings.external.firecrawl_api_key", None):
        client = FirecrawlClient(api_key=None)
        with pytest.raises(AIConfigurationException):
            await client.scrape("https://example.com")


@pytest.mark.asyncio
async def test_tavily_raises_configuration_exception_for_placeholder_key() -> None:
    client = TavilyClient(api_key="your_tavily_api_key_here")
    with pytest.raises(AIConfigurationException):
        await client.search("query")


@pytest.mark.asyncio
async def test_gemini_generate_text_raises_configuration_exception_for_placeholder_key() -> None:
    client = GeminiClient(api_key="your_gemini_api_key_here")
    with pytest.raises(AIConfigurationException):
        await client.generate_text("prompt")


@pytest.mark.asyncio
async def test_gemini_extract_structured_raises_configuration_exception_for_placeholder_key() -> None:
    from pydantic import BaseModel

    class _Schema(BaseModel):
        value: str

    client = GeminiClient(api_key="your_gemini_api_key_here")
    with pytest.raises(AIConfigurationException):
        await client.extract_structured(prompt="prompt", schema_class=_Schema)


def test_ai_configuration_exception_is_not_a_service_specific_exception() -> None:
    """AIConfigurationException must be a sibling of, not a subclass of,
    FirecrawlException / TavilyException / GeminiException — this is what
    keeps it out of a bare `except FirecrawlException` (or similar) handler
    written to catch only transient per-service failures.
    """
    assert not issubclass(AIConfigurationException, FirecrawlException)
    assert not issubclass(AIConfigurationException, TavilyException)
    assert not issubclass(AIConfigurationException, GeminiException)
