"""Authentication API endpoints for user registration and login."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.database import get_db
from src.domains.users.repositories import UserRepository
from src.domains.users.schemas import TokenResponse, UserCreate, UserLogin, UserResponse
from src.domains.users.services import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = structlog.get_logger(__name__)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Registers a new user given an email and password."""
    logger.info("Register endpoint called")
    repository = UserRepository(db)
    service = UserService(repository)
    try:
        user = await service.register(data)
        logger.info("User registered successfully", user_id=user.id)
        return user
    except ValueError as e:
        if str(e) != "Email already registered":
            logger.error("Unexpected value error in registration", error_type=type(e).__name__)
            raise
        logger.warning("Registration failed", reason="account_conflict")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Unexpected error in register", error_type=type(e).__name__)
        raise


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and return access token",
)
async def login(
    data: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticates user credentials and returns a JWT access token."""
    logger.info("Login endpoint called")
    repository = UserRepository(db)
    service = UserService(repository)
    try:
        token = await service.login(data)
        logger.info("Login successful")
        return TokenResponse(access_token=token, token_type="bearer")
    except ValueError as e:
        logger.warning("Login failed", reason="invalid_credentials_or_inactive_account")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Unexpected error in login", error_type=type(e).__name__)
        raise

