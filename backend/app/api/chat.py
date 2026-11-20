"""Chat endpoints: RAG query (streaming) and conversation history."""

import logging
import uuid

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from app.auth.dependencies import get_conversation_service, get_current_user
from app.models.user import User
from app.schemas.chat import (
    ChatQueryRequest,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    MessageResponse,
)
from app.services.chat_service import stream_chat_response
from app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/query")
async def chat_query(
    request: ChatQueryRequest,
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Send a chat message and stream back a RAG-grounded response.

    Streams Server-Sent-Events (`text/event-stream`). Event types:
    `start` (conversation resolved), `token` (one per text fragment),
    `done` (final message id + source citations), `error` (failure).

    If no relevant content is found in the user's documents, responds with
    a fixed "I don't have that information" message rather than calling
    the LLM — the assistant never answers outside the retrieved context.
    """
    return StreamingResponse(
        stream_chat_response(user_id=current_user.id, request=request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ConversationListResponse:
    """List the current user's conversations, most recently active first."""
    conversations = await conversation_service.list_conversations(user_id=current_user.id)
    return ConversationListResponse(
        conversations=[ConversationResponse.model_validate(c) for c in conversations]
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ConversationDetailResponse:
    """Fetch a conversation and its full message history.

    Raises HTTP 404 (via the centralized exception handler) if the
    conversation doesn't exist or doesn't belong to the current user.
    """
    conversation, messages = await conversation_service.get_conversation_with_messages(
        conversation_id=conversation_id, user_id=current_user.id
    )
    return ConversationDetailResponse(
        id=conversation.id,
        title=conversation.title,
        document_id=conversation.document_id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[MessageResponse.model_validate(m) for m in messages],
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> None:
    """Delete a conversation and its messages.

    Raises HTTP 404 (via the centralized exception handler) if the
    conversation doesn't exist or doesn't belong to the current user.
    """
    await conversation_service.delete_conversation(conversation_id=conversation_id, user_id=current_user.id)
