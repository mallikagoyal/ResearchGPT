"""Authentication business logic.

Orchestrates the UserRepository and the password/JWT utilities. Raises
domain exceptions (see app.core.exceptions) rather than HTTP errors, so
this service has no dependency on FastAPI and can be unit-tested directly.
"""

import logging

from app.auth.security import create_access_token, hash_password, verify_password
from app.core.exceptions import AlreadyExistsError, InvalidCredentialsError
from app.models.user import User
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class AuthService:
    """Handles user registration and authentication."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._users = user_repository

    async def register(self, *, email: str, password: str, full_name: str) -> tuple[User, str]:
        """Register a new user and issue an access token.

        Args:
            email: The new user's email address.
            password: The new user's plaintext password (will be hashed).
            full_name: The new user's display name.

        Returns:
            A tuple of (created User, access token).

        Raises:
            AlreadyExistsError: If a user with this email already exists.
        """
        existing = await self._users.get_by_email(email)
        if existing is not None:
            raise AlreadyExistsError(f"A user with email '{email}' already exists.")

        user = await self._users.create(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
        )
        logger.info("Registered new user: %s", user.id)
        token = create_access_token(subject=str(user.id))
        return user, token

    async def authenticate(self, *, email: str, password: str) -> tuple[User, str]:
        """Verify credentials and issue an access token.

        Args:
            email: The user's email address.
            password: The user's plaintext password.

        Returns:
            A tuple of (authenticated User, access token).

        Raises:
            InvalidCredentialsError: If the email is unknown, the account is
                inactive, or the password does not match. The message is
                intentionally generic to avoid leaking which case occurred.
        """
        user = await self._users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Incorrect email or password.")
        if not user.is_active:
            raise InvalidCredentialsError("Incorrect email or password.")

        logger.info("User authenticated: %s", user.id)
        token = create_access_token(subject=str(user.id))
        return user, token
