"""Document upload and management endpoints."""

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile, status

from app.auth.dependencies import get_current_user, get_document_service
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentDetailResponse, DocumentListResponse, DocumentResponse
from app.services.document_service import DocumentService, process_document_background

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


def _to_response(document: Document, chunk_count: int = 0) -> DocumentResponse:
    """Build a DocumentResponse, merging in a chunk count computed separately
    (chunk_count isn't a column on Document, so it can't come from model_validate alone).
    """
    response = DocumentResponse.model_validate(document)
    response.chunk_count = chunk_count
    return response


@router.post("/upload", response_model=list[DocumentResponse], status_code=status.HTTP_201_CREATED)
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(..., description="One or more PDF files."),
    chunk_size: int = Form(default=1000, ge=100, le=4000),
    chunk_overlap: int = Form(default=200, ge=0, le=1000),
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> list[DocumentResponse]:
    """Upload one or more PDF documents for processing.

    Returns immediately with each document in `pending` status. In the
    background: text is extracted, chunked, embedded, and stored in
    ChromaDB. Poll `GET /documents/{id}` (or `GET /documents`) to observe
    the status transition to `processing`, then `processed` (with
    `chunk_count > 0`, meaning it's ready for chat) or `failed`.
    """
    documents = await document_service.upload_documents(
        files=files,
        user_id=current_user.id,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    for document in documents:
        background_tasks.add_task(process_document_background, document.id)

    # Freshly-uploaded documents always have 0 chunks (processing hasn't
    # started yet at this point), so no chunk-count lookup is needed here.
    return [_to_response(doc, chunk_count=0) for doc in documents]


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    search: str | None = Query(default=None, description="Filter by filename or title."),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentListResponse:
    """List the current user's documents, most recent first."""
    documents, total = await document_service.list_documents(
        user_id=current_user.id, search=search, limit=limit
    )
    chunk_counts = await document_service.get_chunk_counts([doc.id for doc in documents])
    return DocumentListResponse(
        documents=[_to_response(doc, chunk_counts.get(doc.id, 0)) for doc in documents],
        total=total,
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentDetailResponse:
    """Fetch a single document, including its extracted text.

    Raises HTTP 404 (via the centralized exception handler) if the document
    doesn't exist or doesn't belong to the current user.
    """
    document = await document_service.get_document(document_id=document_id, user_id=current_user.id)
    chunk_counts = await document_service.get_chunk_counts([document.id])
    response = DocumentDetailResponse.model_validate(document)
    response.chunk_count = chunk_counts.get(document.id, 0)
    return response


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> None:
    """Delete a document (its DB record, chunk rows, stored file, and vectors).

    Raises HTTP 404 (via the centralized exception handler) if the document
    doesn't exist or doesn't belong to the current user.
    """
    await document_service.delete_document(document_id=document_id, user_id=current_user.id)
