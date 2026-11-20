"""Semantic retrieval for RAG chat: embed a query and fetch the most
relevant document chunks from a user's ChromaDB collection.
"""

import logging
import uuid
from dataclasses import dataclass

from app.rag.embeddings import embed_query
from app.rag.vector_store import query_similar_chunks

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetrievedChunk:
    """A single chunk retrieved for a query, with its similarity distance."""

    document_id: uuid.UUID
    chunk_index: int
    content: str
    title: str
    distance: float


def retrieve_relevant_chunks(
    *,
    user_id: uuid.UUID,
    query: str,
    top_k: int,
    document_id: uuid.UUID | None = None,
) -> list[RetrievedChunk]:
    """Embed a query and retrieve the top_k most similar chunks.

    Args:
        user_id: The requesting user (their Chroma collection is searched).
        query: The user's chat message / question.
        top_k: Maximum number of chunks to retrieve.
        document_id: If provided, scope retrieval to a single document
            instead of the user's entire library.

    Returns:
        Retrieved chunks ordered by relevance (most similar first). Empty
        if the user has no processed documents (or none matching the
        document_id filter).
    """
    query_embedding = embed_query(query)
    where = {"document_id": str(document_id)} if document_id else None

    result = query_similar_chunks(
        user_id=user_id, query_embedding=query_embedding, top_k=top_k, where=where
    )

    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]

    chunks: list[RetrievedChunk] = []
    for content, metadata, distance in zip(documents, metadatas, distances):
        try:
            chunks.append(
                RetrievedChunk(
                    document_id=uuid.UUID(metadata["document_id"]),
                    chunk_index=int(metadata.get("chunk_index", 0)),
                    content=content,
                    title=metadata.get("title") or "Untitled document",
                    distance=float(distance),
                )
            )
        except (KeyError, ValueError, TypeError) as exc:
            # Defensive: skip a malformed Chroma record rather than fail
            # the whole retrieval (should not happen in normal operation).
            logger.warning("Skipping malformed retrieved chunk metadata %s: %s", metadata, exc)

    return chunks
