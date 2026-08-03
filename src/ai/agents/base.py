"""Abstract base class for all AI agents.

Every agent in the system is a subclass of ``BaseAgent[InputT, OutputT]``.
The single public method ``run(input: InputT) -> OutputT`` is the only
interface the orchestrator depends on — making every agent independently
testable and trivially swappable.

Extensibility contract
-----------------------
Milestone 7: agents return hardcoded mock data.
Milestone 8: agents call Firecrawl / Tavily / Claude inside ``run()``.
The orchestrator, Celery task, and tests are untouched in both cases.
"""

from __future__ import annotations

import abc
from typing import Generic, TypeVar

import structlog

from src.ai.schemas import AgentInput

InputT = TypeVar("InputT", bound=AgentInput)
OutputT = TypeVar("OutputT")

logger = structlog.get_logger(__name__)


class BaseAgent(abc.ABC, Generic[InputT, OutputT]):
    """Abstract base for all competitor intelligence agents.

    Subclasses must implement ``_execute(input: InputT) -> OutputT``.
    ``run()`` wraps ``_execute`` with structured logging and any shared
    cross-cutting concerns (metrics, retries) added here in the future.
    """

    #: Human-readable name used in log messages and error reports.
    agent_name: str = "BaseAgent"

    async def run(self, input: InputT) -> OutputT:  # noqa: A002
        """Public entry point called by the orchestrator.

        Wraps ``_execute`` with observability so individual agents stay
        free of logging boilerplate.
        """
        log = logger.bind(
            agent=self.agent_name,
            competitor_id=getattr(input, "competitor_id", None),
        )
        log.info("Agent starting")
        try:
            result = await self._execute(input)
            log.info("Agent completed successfully")
            return result
        except Exception as exc:
            log.error("Agent failed", error=str(exc))
            raise

    @abc.abstractmethod
    async def _execute(self, input: InputT) -> OutputT:  # noqa: A002
        """Perform the actual agent work and return a typed output model.

        Raise any exception on failure — ``run()`` will log it and re-raise.
        """
