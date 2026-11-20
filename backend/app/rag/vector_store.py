"""ChromaDB vector store access.

Each user gets their own Chroma collection (named with
CHROMA_COLLECTION_PREFIX + user_id), rather than one shared collection
filtered by a user_id metadata field. This means similarity search is
structurally scoped to a single user's documents — a bug in query-building
elsewhere cannot leak another user's chunks, because they simply aren't in
the collection being queried.
"""

import logging
import uuid
from functools import lru_cache
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_chroma_client() -> chromadb.ClientAPI:
    """Return the process-wide Chroma client, connecting to the ChromaDB service."""
    settings = get_settings()
    return chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)


def _collection_name(user_id: uuid.UUID) -> str:
    settings = get_settings()
    return f"{settings.CHROMA_COLLECTION_PREFIX}{user_id}"


def get_user_collection(user_id: uuid.UUID) -> Collection:
    """Get or create the Chroma collection for a given user."""
    client = get_chroma_client()
    return client.get_or_create_collection(name=_collection_name(user_id))


def upsert_chunks(
    *,
    user_id: uuid.UUID,
    ids: list[str],
    embeddings: list[list[float]],
    documents: list[str],
    metadatas: list[dict[str, Any]],
) -> None:
    """Add (or overwrite) chunk embeddings in a user's collection.

    Args:
        user_id: Owner of the collection to write into.
        ids: Chunk ids (must match the corresponding Postgres DocumentChunk.id).
        embeddings: One embedding vector per chunk, same order as ids.
        documents: The chunk text itself (Chroma stores this for retrieval).
        metadatas: Per-chunk metadata (document_id, chunk_index, title, ...).
    """
    if not ids:
        return
    collection = get_user_collection(user_id)
    collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    logger.info("Upserted %d chunks into Chroma collection for user %s", len(ids), user_id)


def delete_document_chunks(*, user_id: uuid.UUID, document_id: uuid.UUID) -> None:
    """Delete all chunk embeddings belonging to a document from Chroma."""
    collection = get_user_collection(user_id)
    collection.delete(where={"document_id": str(document_id)})
    logger.info("Deleted Chroma chunks for document %s (user %s)", document_id, user_id)


def query_similar_chunks(
    *,
    user_id: uuid.UUID,
    query_embedding: list[float],
    top_k: int,
    where: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Query a user's collection for the top_k most similar chunks.

    Args:
        user_id: Owner of the collection to search.
        query_embedding: The embedded query vector.
        top_k: Maximum number of results to return.
        where: Optional Chroma metadata filter, e.g. {"document_id": "..."}
            to scope retrieval to a single document.
    """
    collection = get_user_collection(user_id)
    return collection.query(query_embeddings=[query_embedding], n_results=top_k, where=where)
