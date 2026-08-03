"""ChangeDetectionAgent — stub for semantic comparison between historical and fresh crawls."""

from __future__ import annotations

from src.ai.agents.base import BaseAgent
from src.ai.clients.gemini import GeminiClient


class ChangeDetectionAgent:
    """Semantic comparison change detector agent (future milestone)."""

    def __init__(self, gemini_client: GeminiClient | None = None) -> None:
        self.gemini = gemini_client or GeminiClient()
