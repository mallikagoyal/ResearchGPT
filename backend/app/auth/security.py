"""Password hashing and JWT token utilities.

Kept framework-agnostic and dependency-free (beyond bcrypt/jose) so it can
be unit-tested in isolation and reused outside of FastAPI request handlers.
"""

import logging
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# bcrypt has a hard 72-byte input limit; truncate defensively rather than
# raising, since Pydantic already caps password length at 128 chars.
_BCRYPT_MAX_BYTES = 72


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Args:
        plain_password: The user-supplied plaintext password.

    Returns:
        A bcrypt hash string, safe to store in the database.
    """
    password_bytes = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash.

    Args:
        plain_password: The password supplied at login.
        hashed_password: The bcrypt hash stored for the user.

    Returns:
        True if the password matches, False otherwise (including on any
        malformed-hash error, which is treated as a non-match rather than
        raised, to avoid leaking internal state to callers).
    """
    try:
        password_bytes = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
        return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))
    except ValueError:
        logger.warning("Password verification failed due to malformed hash.")
        return False


def create_access_token(subject: str) -> str:
    """Create a signed JWT access token.

    Args:
        subject: The value to embed as the `sub` claim (the user's id).

    Returns:
        An encoded JWT string.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Decode and validate a JWT access token.

    Args:
        token: The encoded JWT string.

    Returns:
        The `sub` claim (user id) if the token is valid and unexpired,
        otherwise None.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        subject = payload.get("sub")
        return str(subject) if subject is not None else None
    except JWTError as exc:
        logger.debug("JWT decode failed: %s", exc)
        return None
