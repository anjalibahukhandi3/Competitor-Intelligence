"""Authentication API endpoints for user registration and login."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.domains.users.repositories import UserRepository
from src.domains.users.schemas import TokenResponse, UserCreate, UserLogin, UserResponse
from src.domains.users.services import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])


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
    repository = UserRepository(db)
    service = UserService(repository)
    try:
        user = await service.register(data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


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
    repository = UserRepository(db)
    service = UserService(repository)
    try:
        token = await service.login(data)
        return TokenResponse(access_token=token, token_type="bearer")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

