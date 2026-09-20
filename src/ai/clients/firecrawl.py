"""Async Firecrawl API client for web scraping and content extraction."""

from __future__ import annotations

import asyncio
import time
import httpx
import structlog

from src.ai.exceptions import AIConfigurationException, FirecrawlException
from src.config import settings

logger = structlog.get_logger(__name__)


class FirecrawlClient:
    """Async HTTP client for Firecrawl REST API (api.firecrawl.dev)."""

    BASE_URL = "https://api.firecrawl.dev/v1"

    def __init__(self, api_key: str | None = None, timeout: float = 30.0) -> None:
        self.api_key = api_key or settings.external.firecrawl_api_key
        self.timeout = timeout

    def _is_key_valid(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("your_"))

    async def scrape(self, url: str, retries: int = 3) -> dict[str, str]:
        """Scrapes a URL and returns its markdown content and page metadata.

        Parameters
        ----------
        url : str
            The website URL to scrape.
        retries : int
            Number of retries for transient errors (5xx / 429).

        Returns
        -------
        dict[str, str]
            Dictionary containing 'markdown', 'title', and 'description'.
        """
        log = logger.bind(target_url=url, client="FirecrawlClient")

        if not self._is_key_valid():
            log.warning("Firecrawl API key is missing or default placeholder")
            raise AIConfigurationException("Firecrawl API key is not configured.")

        endpoint = f"{self.BASE_URL}/scrape"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "url": url,
            "formats": ["markdown"],
        }

        start_time = time.perf_counter()
        attempt = 0

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            while attempt < retries:
                attempt += 1
                try:
                    log.info("Requesting Firecrawl scrape", attempt=attempt)
                    response = await client.post(endpoint, json=payload, headers=headers)
                    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

                    if response.status_code == 200:
                        data = response.json().get("data", {})
                        markdown = data.get("markdown", "")
                        metadata = data.get("metadata", {})
                        title = metadata.get("title", "")
                        description = metadata.get("description", "")

                        log.info(
                            "Firecrawl scrape succeeded",
                            status_code=200,
                            duration_ms=duration_ms,
                            content_length=len(markdown),
                        )
                        return {
                            "markdown": markdown,
                            "title": title,
                            "description": description,
                        }

                    log.warning(
                        "Firecrawl API returned non-200 status",
                        status_code=response.status_code,
                        duration_ms=duration_ms,
                    )

                    if response.status_code in (429, 500, 502, 503, 504) and attempt < retries:
                        await asyncio.sleep(2 ** attempt)
                        continue

                    raise FirecrawlException(
                        f"Firecrawl API scrape failed with status {response.status_code}: {response.text}"
                    )

                except (httpx.RequestError, httpx.TimeoutException) as exc:
                    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                    log.error(
                        "Firecrawl network error",
                        attempt=attempt,
                        duration_ms=duration_ms,
                        error=str(exc),
                    )
                    if attempt < retries:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    raise FirecrawlException(f"Firecrawl network error: {exc}") from exc

        raise FirecrawlException("Firecrawl scrape retries exhausted.")
