"""OpenAI-compatible LLM client for streaming chat completions.

Works with any provider that implements the OpenAI chat completions API
shape (OpenAI itself, or a local/self-hosted OpenAI-compatible endpoint
such as vLLM, Ollama with its OpenAI-compat mode, LiteLLM, etc.) —
configure via LLM_BASE_URL / LLM_API_KEY / LLM_MODEL_NAME.
"""

import logging
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def get_llm_client() -> AsyncOpenAI:
    """Build an AsyncOpenAI client pointed at the configured provider."""
    settings = get_settings()
    return AsyncOpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)


async def stream_chat_completion(
    *, system_prompt: str, history: list[dict[str, str]], user_message: str
) -> AsyncIterator[str]:
    """Stream a chat completion, yielding text deltas as they arrive.

    Args:
        system_prompt: The grounding system prompt (includes retrieved context).
        history: Prior turns in the conversation, as [{"role": ..., "content": ...}, ...].
        user_message: The current user message.

    Yields:
        Text fragments (deltas) as the model generates them.
    """
    settings = get_settings()
    client = get_llm_client()

    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": user_message},
    ]

    stream = await client.chat.completions.create(
        model=settings.LLM_MODEL_NAME,
        messages=messages,  # type: ignore[arg-type]
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
        stream=True,
    )

    async for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
