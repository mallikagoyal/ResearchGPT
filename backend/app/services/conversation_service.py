"""Conversation history management (list, get, delete).

Kept separate from ChatService: this handles simple CRUD-style reads over
request-scoped sessions via normal dependency injection, whereas
ChatService's streaming write path needs its own session lifecycle (see
chat_service.py for why).
"""

import logging
import uuid

from app.core.exceptions import NotFoundError
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository

logger = logging.getLogger(__name__)


class ConversationService:
    """Handles conversation history listing, retrieval, and deletion."""

    def __init__(
        self, conversation_repository: ConversationRepository, message_repository: MessageRepository
    ) -> None:
        self._conversations = conversation_repository
        self._messages = message_repository

    async def list_conversations(self, *, user_id: uuid.UUID):
        """List a user's conversations, most recently active first."""
        return await self._conversations.list_by_user(user_id)

    async def get_conversation_with_messages(self, *, conversation_id: uuid.UUID, user_id: uuid.UUID):
        """Fetch a conversation and its full message history.

        Raises:
            NotFoundError: If no such conversation exists for this user.
        """
        conversation = await self._conversations.get_by_id(conversation_id, user_id)
        if conversation is None:
            raise NotFoundError(f"Conversation {conversation_id} not found.")
        messages = await self._messages.list_by_conversation(conversation_id)
        return conversation, messages

    async def delete_conversation(self, *, conversation_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete a conversation and its messages (cascade).

        Raises:
            NotFoundError: If no such conversation exists for this user.
        """
        conversation = await self._conversations.get_by_id(conversation_id, user_id)
        if conversation is None:
            raise NotFoundError(f"Conversation {conversation_id} not found.")
        await self._conversations.delete(conversation)
        logger.info("Deleted conversation %s for user %s", conversation_id, user_id)
