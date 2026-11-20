"""Chat orchestration: retrieval, prompt construction, LLM streaming, and
conversation/message persistence.

The streaming generator opens its own database session rather than reusing
the request-scoped one, for the same reason as the document background
processing task (see DocumentService): a FastAPI endpoint returns its
StreamingResponse object as soon as the generator is created, at which
point the request-scoped session's dependency lifecycle may begin
tearing down — well before the generator actually finishes streaming and
needs to write the final assistant message. A self-contained session
avoids depending on a session that may already be closing.
"""

import json
import logging
import uuid
from collections.abc import AsyncIterator

from app.core.config import get_settings
from app.database.session import AsyncSessionLocal
from app.models.message import MessageRole
from app.rag.context_builder import build_system_prompt
from app.rag.llm_client import stream_chat_completion
from app.rag.retrieval import retrieve_relevant_chunks
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.schemas.chat import ChatQueryRequest, SourceReference

logger = logging.getLogger(__name__)

# Number of prior messages included as conversational context for the LLM.
# Bounded to keep the prompt small and predictable, not because the DB
# can't hold more — full history is always available via GET /chat/conversations/{id}.
MAX_HISTORY_MESSAGES = 6

NO_CONTEXT_FALLBACK = (
    "I don't have any relevant information in your uploaded documents to answer that. "
    "Try uploading a document first, or rephrasing your question."
)


def _sse_event(event: str, data: dict) -> str:
    """Format a single Server-Sent-Events message."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def stream_chat_response(
    *, user_id: uuid.UUID, request: ChatQueryRequest
) -> AsyncIterator[str]:
    """Handle a chat query end-to-end, yielding SSE-formatted strings.

    Event types emitted:
    - `start`: {"conversation_id": "..."} — sent once the conversation is resolved/created.
    - `token`: {"text": "..."} — one per streamed text fragment.
    - `done`: {"message_id": "...", "sources": [...]} — sent once, after the full response is persisted.
    - `error`: {"message": "..."} — sent on failure; terminates the stream.
    """
    settings = get_settings()

    async with AsyncSessionLocal() as db:
        conversation_repo = ConversationRepository(db)
        message_repo = MessageRepository(db)

        try:
            # 1. Resolve or create the conversation.
            if request.conversation_id:
                conversation = await conversation_repo.get_by_id(request.conversation_id, user_id)
                if conversation is None:
                    yield _sse_event("error", {"message": "Conversation not found."})
                    return
            else:
                title = request.message.strip()[:100] or "New conversation"
                conversation = await conversation_repo.create(
                    user_id=user_id, document_id=request.document_id, title=title
                )
                await conversation_repo.commit()

            yield _sse_event("start", {"conversation_id": str(conversation.id)})

            # 2. Persist the user's message.
            user_message = await message_repo.create(
                conversation_id=conversation.id, role=MessageRole.USER, content=request.message
            )
            await message_repo.commit()

            # 3. Retrieve relevant chunks (scoped to one document if requested,
            # or the conversation's own document_id, else the whole library).
            scope_document_id = request.document_id or conversation.document_id
            chunks = retrieve_relevant_chunks(
                user_id=user_id,
                query=request.message,
                top_k=settings.RAG_TOP_K,
                document_id=scope_document_id,
            )

            # 4. No relevant context: answer with a canned message rather
            # than calling the LLM at all. This is a stronger grounding
            # guarantee than prompt instructions alone.
            if not chunks:
                yield _sse_event("token", {"text": NO_CONTEXT_FALLBACK})
                assistant_message = await message_repo.create(
                    conversation_id=conversation.id,
                    role=MessageRole.ASSISTANT,
                    content=NO_CONTEXT_FALLBACK,
                    sources=[],
                )
                await conversation_repo.touch(conversation)
                await message_repo.commit()
                yield _sse_event("done", {"message_id": str(assistant_message.id), "sources": []})
                return

            # 5. Build the grounded prompt and recent conversational history.
            system_prompt = build_system_prompt(chunks)
            history_messages = await message_repo.list_recent(
                conversation.id, limit=MAX_HISTORY_MESSAGES, exclude_message_id=user_message.id
            )
            history = [{"role": m.role.value, "content": m.content} for m in history_messages]

            # 6. Stream the LLM response.
            full_response = ""
            try:
                async for delta in stream_chat_completion(
                    system_prompt=system_prompt, history=history, user_message=request.message
                ):
                    full_response += delta
                    yield _sse_event("token", {"text": delta})
            except Exception:
                logger.exception("LLM streaming failed for conversation %s", conversation.id)
                error_text = "\n\n_Sorry, I ran into an error generating a response. Please try again._"
                full_response += error_text
                yield _sse_event("token", {"text": error_text})

            # 7. Persist the assistant message with its source citations.
            sources = [
                SourceReference(
                    document_id=chunk.document_id,
                    document_title=chunk.title,
                    chunk_index=chunk.chunk_index,
                    snippet=chunk.content[:240],
                ).model_dump(mode="json")
                for chunk in chunks
            ]
            assistant_message = await message_repo.create(
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT,
                content=full_response,
                sources=sources,
            )
            await conversation_repo.touch(conversation)
            await message_repo.commit()

            yield _sse_event("done", {"message_id": str(assistant_message.id), "sources": sources})

        except Exception:
            logger.exception("Chat streaming failed for user %s", user_id)
            yield _sse_event("error", {"message": "An unexpected error occurred."})
