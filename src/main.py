from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
import structlog

from src.config import settings
from src.database import verify_db_connection, engine
from src.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)
from src.logging_config import setup_logging
from src.redis import redis_manager

# Setup Logging config
setup_logging(env=settings.env)
logger = structlog.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown lifespan events for DB and Redis connections."""
    logger.info("Initializing Competitor Intelligence application...")
    
    # 1. Verify PostgreSQL Database connectivity
    try:
        await verify_db_connection()
    except Exception as e:
        logger.critical("PostgreSQL database is unreachable. App failed to start.")
        raise e
        
    # 2. Verify Redis connectivity
    try:
        redis_manager.init_pool(settings.redis.url)
        await redis_manager.verify_connection()
        app.state.redis = redis_manager.client
    except Exception as e:
        logger.critical("Redis is unreachable. App failed to start.")
        await redis_manager.close()
        raise e

    yield

    # Shutdown lifecycle
    logger.info("Shutting down application and cleaning up connections...")
    await redis_manager.close()
    await engine.dispose()
    logger.info("Application shutdown completed.")

# Instantiate FastAPI Core App
app = FastAPI(
    title=settings.project_name,
    description="Continuous competitor tracking and intelligence platform using PydanticAI",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Register Custom Exception Handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Configure CORS Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Real implementation should restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root Endpoint
@app.get("/", tags=["Health"])
async def root_health_check():
    """Simple health-check endpoint for system pinging."""
    return {
        "status": "healthy",
        "app": settings.project_name,
        "env": settings.env
    }

# Include versioned routers (registered in src/api/router.py)
from src.api.router import api_router

app.include_router(api_router)


