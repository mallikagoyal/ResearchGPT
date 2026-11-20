"""Repository for User persistence.

All direct database access for the User aggregate lives here. Services
depend on this interface rather than issuing SQLAlchemy queries directly,
so business logic stays testable and decoupled from the ORM.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Data access layer for the User model."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Fetch a user by primary key, or None if not found."""
        result = await self._db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by email (case-insensitive), or None if not found."""
        normalized = email.strip().lower()
        result = await self._db.execute(select(User).where(User.email == normalized))
        return result.scalar_one_or_none()

    async def create(self, *, email: str, hashed_password: str, full_name: str) -> User:
        """Persist a new user and flush so its generated id/timestamps are available."""
        user = User(
            email=email.strip().lower(),
            hashed_password=hashed_password,
            full_name=full_name.strip(),
        )
        self._db.add(user)
        await self._db.flush()
        await self._db.refresh(user)
        return user
