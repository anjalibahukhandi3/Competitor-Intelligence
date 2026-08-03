"""User domain Pydantic v2 schemas for request validation and response serialization."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user registration requests."""

    email: EmailStr
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")


class UserLogin(BaseModel):
    """Schema for user authentication/login requests."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for returning user data (sensitive fields omitted)."""

    id: str
    email: EmailStr
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Schema for JWT access token responses."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for decoded JWT token payload structure."""

    sub: str | None = None
    exp: int | None = None

