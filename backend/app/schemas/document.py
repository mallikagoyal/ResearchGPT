"""Pydantic schemas for document resources."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.document import DocumentStatus


class DocumentResponse(BaseModel):
    """Public-facing representation of an uploaded document."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    status: DocumentStatus
    title: str | None
    page_count: int | None
    file_size_bytes: int
    error_message: str | None
    chunk_size: int
    chunk_overlap: int
    chunk_count: int = Field(
        default=0, description="Number of embedded chunks. >0 once ready for chat."
    )
    created_at: datetime
    updated_at: datetime


class DocumentDetailResponse(DocumentResponse):
    """Document representation including extracted text (for a single-document view)."""

    extracted_text: str | None


class DocumentListResponse(BaseModel):
    """Response body for GET /documents."""

    documents: list[DocumentResponse]
    total: int


class DocumentUploadOptions(BaseModel):
    """Optional per-upload overrides for chunking configuration."""

    chunk_size: int = Field(default=1000, ge=100, le=4000)
    chunk_overlap: int = Field(default=200, ge=0, le=1000)
