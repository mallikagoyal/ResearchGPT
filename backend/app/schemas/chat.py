"""Pydantic schemas for chat, conversations, and messages."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatQueryRequest(BaseModel):
    """Request body for POST /chat/query."""

    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: uuid.UUID | None = Field(
        default=None, description="Continue an existing conversation. Omit to start a new one."
    )
    document_id: uuid.UUID | None = Field(
        default=None, description="Scope retrieval to a single document. Omit to search all documents."
    )


class SourceReference(BaseModel):
    """A single retrieved-chunk citation attached to an assistant message."""

    document_id: uuid.UUID
    document_title: str
    chunk_index: int
    snippet: str


class MessageResponse(BaseModel):
    """A single message within a conversation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    sources: list[SourceReference] | None
    created_at: datetime


class ConversationResponse(BaseModel):
    """Summary representation of a conversation (for list views)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    document_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    """Response body for GET /chat/conversations."""

    conversations: list[ConversationResponse]


class ConversationDetailResponse(ConversationResponse):
    """Full conversation including its message history."""

    messages: list[MessageResponse]
