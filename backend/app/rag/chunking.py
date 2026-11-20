"""Recursive text chunking, used to split cleaned document text before
embedding.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_text(text: str, *, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Split cleaned document text into overlapping chunks.

    Uses LangChain's RecursiveCharacterTextSplitter, which tries splitting
    on paragraph breaks first, then sentences, then words, falling back to
    raw characters only as a last resort — so chunks stay as semantically
    coherent as possible rather than cutting mid-sentence whenever it can
    be avoided.

    Args:
        text: The cleaned full text of a document.
        chunk_size: Target maximum characters per chunk.
        chunk_overlap: Characters of overlap between consecutive chunks,
            so context isn't lost at chunk boundaries.

    Returns:
        A list of non-empty, whitespace-trimmed chunk strings, in order.
        Empty for blank/whitespace-only input.
    """
    if not text or not text.strip():
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(text)
    return [chunk.strip() for chunk in chunks if chunk.strip()]
