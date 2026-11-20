"""Builds the system prompt that grounds LLM answers in retrieved chunks."""

from app.rag.retrieval import RetrievedChunk

_SYSTEM_PROMPT_TEMPLATE = """You are ResearchGPT, an assistant that answers questions strictly using the numbered document excerpts provided below.

Rules you MUST follow:
- Only use information contained in the excerpts below to answer. Do not use outside knowledge, even if you know the answer.
- If the excerpts do not contain enough information to answer the question, say so plainly rather than guessing.
- When your answer uses information from an excerpt, cite it inline using its number in square brackets, e.g. [1] or [2][3].
- Be direct and concise.
- Respond in Markdown.

Document excerpts:
{context}
"""


def build_context_block(chunks: list[RetrievedChunk]) -> str:
    """Format retrieved chunks as a numbered context block for the prompt.

    Chunks are numbered starting at 1, matching the citation numbers the
    model is instructed to use (e.g. "[1]") and the order sources are
    returned to the client, so a citation number always maps to the same
    source on both ends.
    """
    parts = []
    for index, chunk in enumerate(chunks, start=1):
        parts.append(f"[{index}] (Source: {chunk.title})\n{chunk.content}")
    return "\n\n".join(parts)


def build_system_prompt(chunks: list[RetrievedChunk]) -> str:
    """Build the full system prompt, embedding the retrieved context."""
    context = build_context_block(chunks)
    return _SYSTEM_PROMPT_TEMPLATE.format(context=context)
