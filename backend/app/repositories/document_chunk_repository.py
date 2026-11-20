"""Repository for DocumentChunk persistence."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_chunk import DocumentChunk


class DocumentChunkRepository:
    """Data access layer for the DocumentChunk model."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_many(self, chunks: list[DocumentChunk]) -> None:
        """Persist a batch of chunk rows (does not commit)."""
        self._db.add_all(chunks)
        await self._db.flush()

    async def count_by_document(self, document_id: uuid.UUID) -> int:
        """Count chunks belonging to a single document."""
        result = await self._db.execute(
            select(func.count())
            .select_from(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
        )
        return result.scalar_one()

    async def count_by_documents(self, document_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
        """Count chunks for multiple documents in one query.

        Returns:
            A mapping of document_id -> chunk count. Documents with zero
            chunks are simply absent from the returned dict (not present
            as 0) — callers should use `.get(doc_id, 0)`.
        """
        if not document_ids:
            return {}
        result = await self._db.execute(
            select(DocumentChunk.document_id, func.count())
            .where(DocumentChunk.document_id.in_(document_ids))
            .group_by(DocumentChunk.document_id)
        )
        return dict(result.all())

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._db.commit()
