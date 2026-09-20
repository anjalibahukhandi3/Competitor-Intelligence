from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
import structlog

from src.config import settings

logger = structlog.get_logger(__name__)

import sys
from sqlalchemy.pool import NullPool

is_testing = "pytest" in sys.modules

# Async Engine Initialization with Connection Pooling
pool_kwargs = (
    {"poolclass": NullPool}
    if is_testing
    else {
        "pool_size": settings.db.pool_size,
        "max_overflow": settings.db.max_overflow,
        "pool_timeout": settings.db.pool_timeout,
    }
)

engine = create_async_engine(
    settings.db.url,
    pool_recycle=settings.db.pool_recycle,
    pool_pre_ping=True,
    future=True,
    echo=settings.debug,
    **pool_kwargs,
)

# Async Session Factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base Declarative Model Class
Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency generator for database sessions in FastAPI controllers."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def verify_db_connection() -> None:
    """Verifies PostgreSQL connectivity by executing a SELECT 1 query."""
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        logger.info("Successfully connected to the PostgreSQL database.")
    except Exception as e:
        logger.critical("PostgreSQL database connection check failed", error=str(e))
        raise


def create_task_engine() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Builds a new AsyncEngine + async_sessionmaker scoped to the CALLER's event loop.

    FastAPI runs one long-lived event loop for the life of the process, so the
    module-level `engine` / `async_session_maker` above are safe to share across every
    request there. Celery workers are different: `src/jobs/tasks.py` drives each task
    through its own `asyncio.run(...)` call, so a brand-new event loop is created and
    destroyed per task. asyncpg binds its connections to the event loop that opened
    them, so reusing the FastAPI process's pooled `engine` inside a Celery task
    corrupts the pool the moment a *second* task runs on a *different* loop — this is
    what previously surfaced as `RuntimeError: Event loop is closed` and
    `AttributeError: 'NoneType' object has no attribute 'send'`.

    Call this once per Celery task (after `asyncio.run` has already started the loop),
    use the returned `async_sessionmaker` for all DB work in that task, then
    `await engine.dispose()` before the task's coroutine returns — never keep the
    engine alive past the event loop that created it. `NullPool` means every checkout
    opens and closes its own asyncpg connection instead of pooling one across calls,
    which is what makes create-and-throw-away-per-task safe.
    """
    task_engine = create_async_engine(
        settings.db.url,
        pool_pre_ping=True,
        future=True,
        echo=settings.debug,
        poolclass=NullPool,
    )
    task_session_maker = async_sessionmaker(
        task_engine, class_=AsyncSession, expire_on_commit=False
    )
    return task_engine, task_session_maker

# ---------------------------------------------------------------------------
# SQLAlchemy Mapper Registration
# ---------------------------------------------------------------------------
# We import all models here at the bottom of the file (after Base is defined)
# to ensure they are registered with SQLAlchemy's metadata registry.
# This prevents mapper initialization errors (e.g. InvalidRequestError) in 
# background processes like Celery which might otherwise not import every model.
try:
    from src.domains.users.models import User
    from src.domains.competitors.models import Competitor
    from src.domains.reports.models import Report
    from src.domains.snapshots.models import CompetitorSnapshot, ChangeEvent  # noqa: F401

    from sqlalchemy.orm import configure_mappers
    configure_mappers()
except ImportError:
    pass

