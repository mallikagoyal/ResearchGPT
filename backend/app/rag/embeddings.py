"""Embedding generation using HuggingFace sentence-transformers.

The model is loaded lazily and cached process-wide (lru_cache), since
loading a sentence-transformers model takes real time and this function
is called once per document processed, not once per chunk.
"""

import logging
from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_embedding_model() -> HuggingFaceEmbeddings:
    """Return the process-wide embedding model instance.

    Cached so the (relatively expensive) model load happens once per
    process rather than once per document.
    """
    settings = get_settings()
    logger.info("Loading embedding model: %s (device=%s)", settings.EMBEDDING_MODEL_NAME, settings.EMBEDDING_DEVICE)
    return HuggingFaceEmbeddings(
        model_name=settings.EMBEDDING_MODEL_NAME,
        model_kwargs={"device": settings.EMBEDDING_DEVICE},
        encode_kwargs={"normalize_embeddings": True},
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of chunk texts for storage.

    Args:
        texts: Chunk strings to embed.

    Returns:
        One embedding vector per input text, same order.
    """
    if not texts:
        return []
    model = get_embedding_model()
    return model.embed_documents(texts)


def embed_query(text: str) -> list[float]:
    """Embed a single query string for similarity search (used by RAG, Phase 6)."""
    model = get_embedding_model()
    return model.embed_query(text)
