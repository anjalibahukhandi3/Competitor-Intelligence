from typing import AsyncGenerator
from fastapi import Request
from redis import asyncio as aioredis
import structlog

from src.config import settings

logger = structlog.get_logger(__name__)

class RedisManager:
    """Manages Redis connection pool and client instances."""
    
    def __init__(self) -> None:
        self.pool: aioredis.ConnectionPool | None = None
        self.client: aioredis.Redis | None = None

    def init_pool(self, url: str) -> None:
        """Initializes the Redis connection pool."""
        logger.info("Initializing Redis connection pool...")
        self.pool = aioredis.ConnectionPool.from_url(
            url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,  # Production-ready connection limit
        )
        self.client = aioredis.Redis(connection_pool=self.pool)

    async def verify_connection(self) -> None:
        """Pings Redis to check if connection is active."""
        if not self.client:
            raise RuntimeError("Redis client is not initialized.")
        try:
            await self.client.ping()
            logger.info("Successfully connected to Redis.")
        except Exception as e:
            logger.critical("Redis connection check failed", error=str(e))
            raise

    async def close(self) -> None:
        """Closes the Redis pool and connections."""
        if self.pool:
            logger.info("Closing Redis connection pool...")
            await self.pool.disconnect()
            self.pool = None
            self.client = None

# Global Redis manager instance
redis_manager = RedisManager()

async def get_redis(request: Request) -> aioredis.Redis:
    """Dependency helper to retrieve the Redis client from app state."""
    redis_client = getattr(request.app.state, "redis", None)
    if redis_client is None:
        raise RuntimeError("Redis client not initialized in application state.")
    return redis_client
