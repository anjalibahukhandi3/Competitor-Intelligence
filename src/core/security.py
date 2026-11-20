"""Security layer providing password hashing and JWT token management."""

from datetime import datetime, timedelta, timezone
import bcrypt
from jose import JWTError, jwt
from passlib.context import CryptContext

from src.config import settings

# bcrypt 4.x removed ``__about__``; Passlib 1.7 still reads it during backend setup.
if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = type("about", (), {"__version__": getattr(bcrypt, "__version__", "4.1.2")})()

# Passlib Crypt Context configured for bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hashes a plain-text password using bcrypt."""
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password must be at most 72 UTF-8 bytes")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a hashed password."""
    if len(plain_password.encode("utf-8")) > 72:
        return False
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, email: str | None = None) -> str:
    """Generates a signed JWT access token containing subject ('sub') and expiration ('exp') claims."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.security.access_token_expire_minutes
    )
    payload = {
        "sub": str(subject),
        "exp": expire,
    }
    if email:
        payload["email"] = email
    return jwt.encode(
        payload,
        settings.security.secret_key,
        algorithm=settings.security.algorithm,
    )


def decode_access_token(token: str) -> dict:
    """Decodes and validates a JWT access token, returning its payload dictionary.

    Raises JWTError if the token signature is invalid or expired.
    """
    return jwt.decode(
        token,
        settings.security.secret_key,
        algorithms=[settings.security.algorithm],
    )

