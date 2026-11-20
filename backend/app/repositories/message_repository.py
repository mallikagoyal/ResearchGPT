"""Repository for Message persistence."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message, MessageRole


class MessageRepository:
    """Data access layer for the Message model."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        *,
        conversation_id: uuid.UUID,
        role: MessageRole,
        content: str,
        sources: list[dict[str, Any]] | None = None,
    ) -> Message:
        """Persist a new message."""
        message = Message(conversation_id=conversation_id, role=role, content=content, sources=sources)
        self._db.add(message)
        await self._db.flush()
        await self._db.refresh(message)
        return message

    async def list_by_conversation(self, conversation_id: uuid.UUID) -> list[Message]:
        """List all messages in a conversation, oldest first."""
        result = await self._db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        return list(result.scalars().all())

    async def list_recent(
        self, conversation_id: uuid.UUID, *, limit: int, exclude_message_id: uuid.UUID | None = None
    ) -> list[Message]:
        """List the most recent messages in a conversation (oldest-first order),
        used to build bounded conversational context for the LLM prompt.
        """
        query = select(Message).where(Message.conversation_id == conversation_id)
        if exclude_message_id is not None:
            query = query.where(Message.id != exclude_message_id)
        result = await self._db.execute(query.order_by(Message.created_at.desc()).limit(limit))
        messages = list(result.scalars().all())
        messages.reverse()  # back to chronological order
        return messages

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._db.commit()
