"""User domain Pydantic v2 schemas for request validation and response serialization."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """Schema for user registration requests."""

    email: EmailStr
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")

    @field_validator("password")
    @classmethod
    def password_fits_hash_algorithm(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 UTF-8 bytes")
        return value


class UserLogin(BaseModel):
    """Schema for user authentication/login requests."""

    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_fits_hash_algorithm(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 UTF-8 bytes")
        return value


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

