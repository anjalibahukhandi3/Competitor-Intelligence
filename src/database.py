from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
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

