"""Repository for Conversation persistence."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation


class ConversationRepository:
    """Data access layer for the Conversation model."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self, *, user_id: uuid.UUID, document_id: uuid.UUID | None, title: str
    ) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(user_id=user_id, document_id=document_id, title=title)
        self._db.add(conversation)
        await self._db.flush()
        await self._db.refresh(conversation)
        return conversation

    async def get_by_id(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> Conversation | None:
        """Fetch a conversation by id, scoped to its owner."""
        result = await self._db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id, Conversation.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: uuid.UUID, *, limit: int = 50) -> list[Conversation]:
        """List a user's conversations, most recently updated first."""
        result = await self._db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def touch(self, conversation: Conversation) -> None:
        """Bump updated_at, e.g. after a new message is added."""
        conversation.updated_at = datetime.now(timezone.utc)
        await self._db.flush()

    async def delete(self, conversation: Conversation) -> None:
        """Delete a conversation (its messages cascade-delete)."""
        await self._db.delete(conversation)
        await self._db.flush()

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._db.commit()
