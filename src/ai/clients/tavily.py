"""Async Tavily Search API client for news, press releases, and Web search."""

from __future__ import annotations

import asyncio
import time
import httpx
import structlog

from src.ai.exceptions import AIConfigurationException, TavilyException
from src.config import settings

logger = structlog.get_logger(__name__)


class TavilyClient:
    """Async HTTP client for Tavily Search REST API (api.tavily.com)."""

    BASE_URL = "https://api.tavily.com/search"

    def __init__(self, api_key: str | None = None, timeout: float = 30.0) -> None:
        self.api_key = api_key or settings.external.tavily_api_key
        self.timeout = timeout

    def _is_key_valid(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("your_"))

    async def search(
        self,
        query: str,
        days: int = 30,
        max_results: int = 5,
        retries: int = 3,
    ) -> list[dict[str, str]]:
        """Performs a web search via Tavily and returns curated search results.

        Parameters
        ----------
        query : str
            Search query string.
        days : int
            Search depth / recency window in days.
        max_results : int
            Maximum number of search result items to return.
        retries : int
            Number of retries for transient errors (5xx / 429).

        Returns
        -------
        list[dict[str, str]]
            List of dictionaries containing 'title', 'url', 'content', 'published_date'.
        """
        log = logger.bind(query=query, client="TavilyClient")

        if not self._is_key_valid():
            log.warning("Tavily API key is missing or default placeholder")
            raise AIConfigurationException("Tavily API key is not configured.")

        payload = {
            "api_key": self.api_key,
            "query": query,
            "days": days,
            "max_results": max_results,
            "search_depth": "advanced",
            "include_answer": False,
        }

        start_time = time.perf_counter()
        attempt = 0

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            while attempt < retries:
                attempt += 1
                try:
                    log.info("Requesting Tavily search", attempt=attempt)
                    response = await client.post(self.BASE_URL, json=payload)
                    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

                    if response.status_code == 200:
                        raw_results = response.json().get("results", [])
                        parsed_items = [
                            {
                                "title": item.get("title", ""),
                                "url": item.get("url", ""),
                                "content": item.get("content", ""),
                                "published_date": item.get("published_date", ""),
                            }
                            for item in raw_results
                        ]

                        log.info(
                            "Tavily search succeeded",
                            status_code=200,
                            duration_ms=duration_ms,
                            results_count=len(parsed_items),
                        )
                        return parsed_items

                    log.warning(
                        "Tavily API returned non-200 status",
                        status_code=response.status_code,
                        duration_ms=duration_ms,
                    )

                    if response.status_code in (429, 500, 502, 503, 504) and attempt < retries:
                        await asyncio.sleep(2 ** attempt)
                        continue

                    raise TavilyException(
                        f"Tavily API search failed with status {response.status_code}: {response.text}"
                    )

                except (httpx.RequestError, httpx.TimeoutException) as exc:
                    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                    log.error(
                        "Tavily network error",
                        attempt=attempt,
                        duration_ms=duration_ms,
                        error=str(exc),
                    )
                    if attempt < retries:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    raise TavilyException(f"Tavily network error: {exc}") from exc

        raise TavilyException("Tavily search retries exhausted.")
