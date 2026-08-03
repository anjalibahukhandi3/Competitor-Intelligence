"""Security layer providing password hashing and JWT token management."""

from datetime import datetime, timedelta, timezone
import bcrypt
from jose import JWTError, jwt
from passlib.context import CryptContext

from src.config import settings

# Fix passlib compatibility with bcrypt 4.x
if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = type("about", (), {"__version__": getattr(bcrypt, "__version__", "4.1.2")})()

_orig_hashpw = bcrypt.hashpw


def _safe_hashpw(password: bytes, salt: bytes) -> bytes:
    if isinstance(password, bytes) and len(password) > 72:
        password = password[:72]
    return _orig_hashpw(password, salt)


bcrypt.hashpw = _safe_hashpw

# Passlib Crypt Context configured for bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hashes a plain-text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str) -> str:
    """Generates a signed JWT access token containing subject ('sub') and expiration ('exp') claims."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.security.access_token_expire_minutes
    )
    payload = {
        "sub": str(subject),
        "exp": expire,
    }
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

