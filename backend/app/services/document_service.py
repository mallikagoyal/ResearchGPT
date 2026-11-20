"""Document upload, storage, and processing business logic."""

import logging
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import FileProcessingError, NotFoundError, ValidationFailedError
from app.database.session import AsyncSessionLocal
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.rag.chunking import chunk_text
from app.rag.embeddings import embed_texts
from app.rag.vector_store import delete_document_chunks, upsert_chunks
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.utils.pdf_extractor import extract_pdf

logger = logging.getLogger(__name__)
settings = get_settings()

_BYTES_PER_MB = 1024 * 1024


class DocumentService:
    """Handles document upload validation/storage and orchestrates processing."""

    def __init__(
        self,
        document_repository: DocumentRepository,
        chunk_repository: DocumentChunkRepository,
    ) -> None:
        self._documents = document_repository
        self._chunks = chunk_repository

    def _validate_upload(self, file: UploadFile, content: bytes) -> None:
        """Validate a single uploaded file's extension and size.

        Raises:
            ValidationFailedError: If the extension is not allowed or the
                file exceeds the configured size limit.
        """
        if not file.filename:
            raise ValidationFailedError("Uploaded file is missing a filename.")

        extension = Path(file.filename).suffix.lower()
        if extension not in settings.ALLOWED_UPLOAD_EXTENSIONS:
            allowed = ", ".join(settings.ALLOWED_UPLOAD_EXTENSIONS)
            raise ValidationFailedError(
                f"File '{file.filename}' has an unsupported extension. Allowed: {allowed}."
            )

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * _BYTES_PER_MB
        if len(content) > max_bytes:
            raise ValidationFailedError(
                f"File '{file.filename}' exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB size limit."
            )

        if len(content) == 0:
            raise ValidationFailedError(f"File '{file.filename}' is empty.")

    async def upload_documents(
        self,
        *,
        files: list[UploadFile],
        user_id: uuid.UUID,
        chunk_size: int,
        chunk_overlap: int,
    ) -> list[Document]:
        """Validate, store, and create PENDING document rows for each upload.

        Text extraction is NOT performed here — callers should schedule
        `process_document_background(document.id)` (e.g. via FastAPI
        BackgroundTasks) for each returned document.

        Args:
            files: The uploaded files (multipart/form-data).
            user_id: The owning user's id.
            chunk_size: Chunk size to record for later embedding (Phase 5).
            chunk_overlap: Chunk overlap to record for later embedding.

        Returns:
            The created Document rows, in PENDING status.

        Raises:
            ValidationFailedError: If any file fails validation. Files
                validated before the failing one are still persisted (an
                "all or nothing" batch is unnecessary complexity for an MVP
                and would be surprising if 9 of 10 valid files got rejected
                because file #10 was too large).
        """
        user_upload_dir = Path(settings.UPLOAD_DIR) / str(user_id)
        user_upload_dir.mkdir(parents=True, exist_ok=True)

        created: list[Document] = []
        for file in files:
            content = await file.read()
            self._validate_upload(file, content)

            stored_filename = f"{uuid.uuid4()}.pdf"
            destination = user_upload_dir / stored_filename
            destination.write_bytes(content)

            document = await self._documents.create(
                user_id=user_id,
                original_filename=file.filename,  # type: ignore[arg-type]  # validated non-None above
                stored_filename=stored_filename,
                file_path=str(destination),
                file_size_bytes=len(content),
                mime_type=file.content_type or "application/pdf",
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            created.append(document)
            logger.info("Stored upload %s for user %s -> %s", document.id, user_id, destination)

        # Commit explicitly here rather than relying on the request's
        # implicit commit-after-response: FastAPI runs BackgroundTasks
        # BEFORE that implicit commit, so without this, the background
        # processing task's separate DB session would not yet see these
        # rows and would fail with "document not found".
        await self._documents.commit()

        return created

    async def list_documents(
        self, *, user_id: uuid.UUID, search: str | None, limit: int
    ) -> tuple[list[Document], int]:
        """List a user's documents, optionally filtered by search term."""
        return await self._documents.list_by_user(user_id, search=search, limit=limit)

    async def get_chunk_counts(self, document_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
        """Look up chunk counts for a batch of documents (one query, not N)."""
        return await self._chunks.count_by_documents(document_ids)

    async def get_document(self, *, document_id: uuid.UUID, user_id: uuid.UUID) -> Document:
        """Fetch a single document, enforcing ownership.

        Raises:
            NotFoundError: If no such document exists for this user.
        """
        document = await self._documents.get_by_id(document_id, user_id)
        if document is None:
            raise NotFoundError(f"Document {document_id} not found.")
        return document

    async def delete_document(self, *, document_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete a document's DB row, its chunk rows, its stored file, and its vectors.

        Chunk rows in Postgres cascade-delete automatically via the
        document_id foreign key, but Chroma has no knowledge of that FK,
        so its vectors are purged explicitly here.

        Raises:
            NotFoundError: If no such document exists for this user.
        """
        document = await self.get_document(document_id=document_id, user_id=user_id)

        file_path = Path(document.file_path)
        try:
            if file_path.exists():
                file_path.unlink()
        except OSError as exc:
            # Best-effort: don't block deletion of the DB record on a
            # filesystem hiccup, but do log it for operators to notice.
            logger.warning("Failed to delete file %s for document %s: %s", file_path, document.id, exc)

        try:
            delete_document_chunks(user_id=user_id, document_id=document_id)
        except Exception as exc:  # noqa: BLE001 - best-effort; don't block deletion on Chroma being unreachable
            logger.warning("Failed to delete Chroma vectors for document %s: %s", document.id, exc)

        await self._documents.delete(document)
        logger.info("Deleted document %s for user %s", document_id, user_id)


async def process_document_background(document_id: uuid.UUID) -> None:
    """Extract, chunk, embed, and store a document's content.

    Runs as a FastAPI background task, after the HTTP response has already
    been sent, so it opens its own database session rather than reusing
    the (already-closed) request-scoped one.

    Pipeline: extract text (PyMuPDF) -> chunk (recursive splitter) -> embed
    (HuggingFace sentence-transformers) -> write vectors to Chroma -> write
    chunk metadata to Postgres -> mark PROCESSED.

    Vectors are written to Chroma BEFORE chunk metadata is written to
    Postgres. If the Chroma write fails, nothing is left behind in
    Postgres to go stale; a failure in the (cheaper, local) Postgres write
    after a successful Chroma write is a rarer and lower-cost inconsistency
    to accept for an MVP than the reverse.
    """
    async with AsyncSessionLocal() as db:
        document_repository = DocumentRepository(db)
        chunk_repository = DocumentChunkRepository(db)
        document = await document_repository.get_by_id_unscoped(document_id)
        if document is None:
            logger.error("process_document_background: document %s not found", document_id)
            return

        try:
            await document_repository.mark_processing(document)
            await db.commit()

            fallback_title = Path(document.original_filename).stem
            extracted = extract_pdf(Path(document.file_path), fallback_title=fallback_title)

            chunks = chunk_text(
                extracted.text,
                chunk_size=document.chunk_size,
                chunk_overlap=document.chunk_overlap,
            )
            if not chunks:
                raise FileProcessingError(
                    "No extractable text was found in this PDF. It may be a scanned "
                    "or image-only document, which isn't supported yet."
                )

            embeddings = embed_texts(chunks)

            chunk_rows = [
                DocumentChunk(
                    id=uuid.uuid4(),
                    document_id=document.id,
                    user_id=document.user_id,
                    chunk_index=index,
                    content=chunk,
                    char_count=len(chunk),
                )
                for index, chunk in enumerate(chunks)
            ]

            upsert_chunks(
                user_id=document.user_id,
                ids=[str(row.id) for row in chunk_rows],
                embeddings=embeddings,
                documents=chunks,
                metadatas=[
                    {
                        "document_id": str(document.id),
                        "chunk_index": row.chunk_index,
                        "title": extracted.title,
                    }
                    for row in chunk_rows
                ],
            )

            await chunk_repository.create_many(chunk_rows)

            await document_repository.mark_processed(
                document,
                title=extracted.title,
                page_count=extracted.page_count,
                extracted_text=extracted.text,
            )
            await db.commit()
            logger.info(
                "Processed document %s: %d pages, %d chunks embedded",
                document.id,
                extracted.page_count,
                len(chunk_rows),
            )
        except FileProcessingError as exc:
            await document_repository.mark_failed(document, error_message=exc.message)
            await db.commit()
            logger.warning("Document %s failed processing: %s", document.id, exc.message)
        except Exception as exc:  # noqa: BLE001 - never let a background task crash silently
            await document_repository.mark_failed(
                document, error_message="An unexpected error occurred during processing."
            )
            await db.commit()
            logger.exception("Unexpected error processing document %s: %s", document.id, exc)
