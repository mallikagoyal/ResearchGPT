"""Repository for Document persistence.

All direct database access for the Document aggregate lives here. Every
read/delete is scoped by user_id so one user can never see or modify
another user's documents.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus


class DocumentRepository:
    """Data access layer for the Document model."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        original_filename: str,
        stored_filename: str,
        file_path: str,
        file_size_bytes: int,
        mime_type: str,
        chunk_size: int,
        chunk_overlap: int,
    ) -> Document:
        """Persist a new document row in PENDING status."""
        document = Document(
            user_id=user_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_size_bytes=file_size_bytes,
            mime_type=mime_type,
            status=DocumentStatus.PENDING,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        self._db.add(document)
        await self._db.flush()
        await self._db.refresh(document)
        return document

    async def get_by_id(self, document_id: uuid.UUID, user_id: uuid.UUID) -> Document | None:
        """Fetch a document by id, scoped to its owner."""
        result = await self._db.execute(
            select(Document).where(Document.id == document_id, Document.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_unscoped(self, document_id: uuid.UUID) -> Document | None:
        """Fetch a document by id with no ownership check.

        Used only by the background processing task, which already knows
        the id from a just-created row and has no HTTP request/user context.
        """
        result = await self._db.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()

    async def list_by_user(
        self, user_id: uuid.UUID, *, search: str | None = None, limit: int = 100
    ) -> tuple[list[Document], int]:
        """List a user's documents, optionally filtered by filename/title search.

        Returns:
            A tuple of (documents, total_count_matching_filter).
        """
        base_filter = [Document.user_id == user_id]
        if search:
            pattern = f"%{search.strip()}%"
            base_filter.append(
                (Document.original_filename.ilike(pattern)) | (Document.title.ilike(pattern))
            )

        count_result = await self._db.execute(
            select(func.count()).select_from(Document).where(*base_filter)
        )
        total = count_result.scalar_one()

        result = await self._db.execute(
            select(Document)
            .where(*base_filter)
            .order_by(Document.created_at.desc())
            .limit(limit)
        )
        documents = list(result.scalars().all())
        return documents, total

    async def delete(self, document: Document) -> None:
        """Delete a document row."""
        await self._db.delete(document)
        await self._db.flush()

    async def commit(self) -> None:
        """Commit the current transaction.

        Used after upload so newly-created rows are durably visible to the
        background processing task's own database session, rather than
        relying on FastAPI's implicit commit-after-response (which runs
        AFTER background tasks, not before).
        """
        await self._db.commit()

    async def mark_processing(self, document: Document) -> None:
        """Transition a document to PROCESSING."""
        document.status = DocumentStatus.PROCESSING
        await self._db.flush()

    async def mark_processed(
        self, document: Document, *, title: str, page_count: int, extracted_text: str
    ) -> None:
        """Persist successful extraction results and mark PROCESSED."""
        document.title = title
        document.page_count = page_count
        document.extracted_text = extracted_text
        document.status = DocumentStatus.PROCESSED
        document.error_message = None
        await self._db.flush()

    async def mark_failed(self, document: Document, *, error_message: str) -> None:
        """Mark a document as FAILED with a stored error message."""
        document.status = DocumentStatus.FAILED
        document.error_message = error_message[:1000]
        await self._db.flush()
