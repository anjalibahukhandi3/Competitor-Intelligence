"""Unit tests for the Celery task-scoped async engine factory.

These guard against the regression that caused
``RuntimeError: Event loop is closed`` / ``AttributeError: 'NoneType' object
has no attribute 'send'`` in Celery workers: a single global SQLAlchemy async
engine's asyncpg connection pool was being reused across the different event
loops that ``asyncio.run()`` creates per Celery task. The fix
(``src.database.create_task_engine`` + ``src.jobs.tasks._task_db_session_maker``)
builds a brand-new engine per task and disposes it before the task's event
loop closes, instead of sharing the FastAPI process's long-lived engine.
"""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from sqlalchemy.pool import NullPool

from src.database import create_task_engine
from src.jobs.tasks import _task_db_session_maker


def test_create_task_engine_returns_a_new_engine_each_call() -> None:
    """Every call must build a brand-new engine — never a cached/shared one.

    Sharing one engine's connection pool across multiple `asyncio.run()`
    calls (i.e. multiple event loops) is exactly the bug this factory exists
    to avoid, so identity must differ call to call.
    """
    engine_a, session_maker_a = create_task_engine()
    engine_b, session_maker_b = create_task_engine()

    assert isinstance(engine_a, AsyncEngine)
    assert isinstance(session_maker_a, async_sessionmaker)
    assert engine_a is not engine_b
    assert session_maker_a is not session_maker_b


def test_create_task_engine_uses_nullpool() -> None:
    """NullPool means every checkout opens/closes its own asyncpg connection
    instead of pooling one across calls — the property that makes
    create-and-dispose-per-task safe across different event loops.
    """
    engine, _ = create_task_engine()
    assert isinstance(engine.pool, NullPool)


@pytest.mark.asyncio
async def test_task_db_session_maker_yields_independent_engines_per_call() -> None:
    """Two separate `async with _task_db_session_maker()` entries — modelling
    two separate Celery tasks, each with its own `asyncio.run()` — must never
    share an engine or session_maker instance.
    """
    async with _task_db_session_maker() as first:
        pass

    async with _task_db_session_maker() as second:
        pass

    assert first is not second


@pytest.mark.asyncio
async def test_task_db_session_maker_disposes_engine_on_success() -> None:
    """The engine acquired for a task must be disposed when the task's
    `async with` block exits normally, so nothing outlives that task's loop.
    """
    fake_engine = AsyncMock()
    fake_session_maker = object()

    with patch("src.jobs.tasks.create_task_engine", return_value=(fake_engine, fake_session_maker)):
        async with _task_db_session_maker() as session_maker:
            assert session_maker is fake_session_maker

        fake_engine.dispose.assert_awaited_once()


@pytest.mark.asyncio
async def test_task_db_session_maker_disposes_engine_on_exception() -> None:
    """A failure inside the task must still dispose its engine — a crashed
    task must never leak connections into the next task's event loop.
    """
    fake_engine = AsyncMock()
    fake_session_maker = object()

    with patch("src.jobs.tasks.create_task_engine", return_value=(fake_engine, fake_session_maker)):
        with pytest.raises(ValueError, match="boom"):
            async with _task_db_session_maker():
                raise ValueError("boom")

        fake_engine.dispose.assert_awaited_once()


@pytest.mark.asyncio
async def test_three_sequential_tasks_each_get_a_fresh_engine() -> None:
    """Simulates the exact regression scenario: Celery task #1, #2, #3 running
    one after another (each via its own `asyncio.run()` in production, here
    driven directly since we're already inside a loop) must each acquire and
    dispose an independent engine — no task's DB resources leak into the next.
    """
    engines = []
    for _ in range(3):
        async with _task_db_session_maker() as session_maker:
            assert isinstance(session_maker, async_sessionmaker)
        # Nothing raised — this is what previously surfaced as
        # "RuntimeError: Event loop is closed" / "'NoneType' object has no
        # attribute 'send'" once a second task reused a stale connection.
        engines.append(session_maker)

    assert len(set(id(e) for e in engines)) == 3
