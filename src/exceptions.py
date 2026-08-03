from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger(__name__)

class AppException(Exception):
    """Base exception for all application errors."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class DomainException(AppException):
    """Exception raised during business logic operations."""
    pass

class RepositoryException(AppException):
    """Exception raised during database constraints or persistence failures."""
    pass

class AIExecutionException(AppException):
    """Exception raised when an agent run, LLM, or scraper fails."""
    pass

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Global exception handler for parsing custom AppExceptions to JSON responses."""
    logger.warning(
        "Application exception occurred",
        path=request.url.path,
        error=exc.message,
        error_type=exc.__class__.__name__
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.message,
            "error_type": exc.__class__.__name__
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handles FastAPI input validation errors and formats them into a clean JSON response."""
    errors = exc.errors()
    formatted_errors = [
        {
            "loc": err.get("loc"),
            "msg": err.get("msg"),
            "type": err.get("type")
        }
        for err in errors
    ]
    logger.warning(
        "Validation exception occurred",
        path=request.url.path,
        errors=formatted_errors
    )
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation failed",
            "error_type": "RequestValidationError",
            "details": formatted_errors
        }
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Fallback handler for uncaught system exceptions to avoid leaking details and enforce JSON responses."""
    logger.exception(
        "Uncaught system exception occurred",
        path=request.url.path,
        error=str(exc)
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "An unexpected error occurred. Please contact support.",
            "error_type": "InternalServerError"
        }
    )

