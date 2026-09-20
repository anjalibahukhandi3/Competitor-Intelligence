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
import re
from typing import Generic, TypeVar

import structlog

from src.ai.schemas import AgentInput

InputT = TypeVar("InputT", bound=AgentInput)
OutputT = TypeVar("OutputT")

logger = structlog.get_logger(__name__)

_CAMEL_CASE_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")


def _stage_slug(agent_name: str) -> str:
    """Converts an agent's CamelCase name into a snake_case log-event slug.

    e.g. ``"ResearchAgent"`` -> ``"research_agent"``, so pipeline logs read
    as ``research_agent_started`` / ``research_agent_completed`` /
    ``research_agent_failed`` for every agent without each one needing to
    write its own logging boilerplate.
    """
    return _CAMEL_CASE_BOUNDARY.sub("_", agent_name).lower()


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
        stage = _stage_slug(self.agent_name)
        log.info(f"{stage}_started")
        try:
            result = await self._execute(input)
            log.info(f"{stage}_completed")
            return result
        except Exception as exc:
            log.error(f"{stage}_failed", error=str(exc))
            raise

    @abc.abstractmethod
    async def _execute(self, input: InputT) -> OutputT:  # noqa: A002
        """Perform the actual agent work and return a typed output model.

        Raise any exception on failure — ``run()`` will log it and re-raise.
        """
