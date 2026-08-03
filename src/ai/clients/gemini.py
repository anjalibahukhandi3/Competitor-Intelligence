"""Async Google Gemini API client for structured information extraction and synthesis.

Uses the official ``google-genai`` SDK (google.genai) with async support.

Architecture notes
------------------
- ``GeminiClient`` provides async methods: ``generate_text``, ``generate_structured``, and ``extract_structured``.
- Retries, latency logging, API-key validation, and JSON cleaning all preserved.
- The Gemini SDK is instantiated per call using ``google.genai.Client``.
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from typing import TypeVar

import google.genai as genai
import google.genai.types as genai_types
from pydantic import BaseModel, ValidationError
import structlog

from src.ai.exceptions import GeminiException
from src.config import settings

logger = structlog.get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class GeminiClient:
    """Async client wrapper for Google Gemini generative AI API.

    Parameters
    ----------
    api_key : str | None
        Gemini API key. Reads ``GEMINI_API_KEY`` from settings when None.
    model : str | None
        Model name. Reads ``GEMINI_MODEL`` from settings when None.
        Defaults to ``gemini-2.0-flash``.
    timeout : float
        Per-request timeout in seconds (default 60 s).
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.api_key = api_key or settings.ai.gemini_api_key
        self.model = model or settings.ai.gemini_model
        self.timeout = timeout

    def _is_key_valid(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("your_"))

    # ------------------------------------------------------------------
    # Async methods required for text and structured generation
    # ------------------------------------------------------------------

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
        retries: int = 3,
    ) -> str:
        """Sends a text prompt to Gemini and returns the generated text response."""
        log = logger.bind(model=self.model, client="GeminiClient")

        if not self._is_key_valid():
            log.warning("Gemini API key is missing or default placeholder")
            raise GeminiException("Gemini API key is not configured.")

        client = genai.Client(api_key=self.api_key)
        start_time = time.perf_counter()
        attempt = 0

        while attempt < retries:
            attempt += 1
            try:
                log.info("Requesting Gemini text generation", attempt=attempt)
                config = genai_types.GenerateContentConfig(
                    system_instruction=system_prompt if system_prompt else None,
                    temperature=settings.ai.agent_temperature,
                    max_output_tokens=8192,
                )
                response = await client.aio.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=config,
                )
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                text = (response.text or "").strip()
                log.info("Gemini text generation succeeded", duration_ms=duration_ms)
                return text
            except Exception as api_err:
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                status_code = getattr(api_err, "code", None) or getattr(api_err, "status_code", None)
                log.error(
                    "Gemini API error during text generation",
                    attempt=attempt,
                    duration_ms=duration_ms,
                    status_code=status_code,
                    error=str(api_err),
                )
                if attempt < retries and status_code in (429, 500, 502, 503, 504):
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise GeminiException(f"Gemini API error: {api_err}") from api_err

        raise GeminiException("Gemini API retries exhausted.")

    async def generate_structured(
        self,
        prompt: str,
        schema_class: type[T],
        system_prompt: str = "",
        retries: int = 3,
    ) -> T:
        """Sends a prompt to Gemini and parses the JSON response into a Pydantic model."""
        log = logger.bind(model=self.model, schema=schema_class.__name__, client="GeminiClient")

        if not self._is_key_valid():
            log.warning("Gemini API key is missing or default placeholder")
            raise GeminiException("Gemini API key is not configured.")

        schema_json = json.dumps(schema_class.model_json_schema(), indent=2)

        system_instruction = (
            f"{system_prompt}\n\n" if system_prompt else ""
        ) + (
            "CRITICAL REQUIREMENT: You MUST respond ONLY with a valid JSON object. "
            "Do NOT wrap your output in markdown formatting codeblocks (do NOT use ```json). "
            "Do NOT include any introduction, text, or explanation outside the JSON object.\n"
            f"The JSON object MUST strictly adhere to this Pydantic JSON Schema:\n{schema_json}"
        )

        client = genai.Client(api_key=self.api_key)
        start_time = time.perf_counter()
        attempt = 0

        while attempt < retries:
            attempt += 1
            try:
                log.info("Requesting Gemini structured generation", attempt=attempt)

                response = await client.aio.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=settings.ai.agent_temperature,
                        max_output_tokens=8192,
                    ),
                )

                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                raw_text = (response.text or "").strip()

                # Clean markdown blocks Gemini sometimes inserts despite instructions
                cleaned_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
                cleaned_text = re.sub(r"\s*```$", "", cleaned_text).strip()

                usage = response.usage_metadata
                log.info(
                    "Gemini structured generation succeeded",
                    duration_ms=duration_ms,
                    prompt_tokens=getattr(usage, "prompt_token_count", None),
                    completion_tokens=getattr(usage, "candidates_token_count", None),
                )

                try:
                    return schema_class.model_validate_json(cleaned_text)
                except ValidationError as val_err:
                    log.warning(
                        "Gemini JSON output failed Pydantic validation",
                        attempt=attempt,
                        error=str(val_err),
                    )
                    if attempt < retries:
                        await asyncio.sleep(1.0)
                        continue
                    raise GeminiException(
                        f"Gemini response failed Pydantic validation for {schema_class.__name__}: {val_err}"
                    ) from val_err

            except GeminiException:
                raise

            except Exception as api_err:
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                status_code = getattr(api_err, "code", None) or getattr(api_err, "status_code", None)
                log.error(
                    "Gemini API error",
                    attempt=attempt,
                    duration_ms=duration_ms,
                    status_code=status_code,
                    error=str(api_err),
                )
                if attempt < retries and status_code in (429, 500, 502, 503, 504):
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise GeminiException(f"Gemini API error: {api_err}") from api_err

        raise GeminiException("Gemini API retries exhausted.")

    async def extract_structured(
        self,
        prompt: str,
        schema_class: type[T],
        system_prompt: str = "",
        retries: int = 3,
    ) -> T:
        """Convenience alias for ``generate_structured`` to preserve agent compatibility."""
        return await self.generate_structured(
            prompt=prompt,
            schema_class=schema_class,
            system_prompt=system_prompt,
            retries=retries,
        )
