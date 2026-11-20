"use client";

import { useCallback, useRef, useState } from "react";

import { streamChatQuery } from "@/services/chat-service";
import type { ChatMessage, SourceReference } from "@/types/chat";

/**
 * Manages an active chat conversation: message list, streaming state, and
 * sending new messages via SSE. Optimistically appends the user's message
 * and a placeholder assistant message immediately, then fills the
 * assistant message in as tokens arrive.
 */
export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const loadConversation = useCallback((msgs: ChatMessage[], convId: string) => {
    setMessages(msgs);
    setConversationId(convId);
    setError(null);
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
    setConversationId(null);
    setError(null);
    setIsStreaming(false);
  }, []);

  const sendMessage = useCallback(
    async (text: string, documentId?: string) => {
      setError(null);

      const userMessage: ChatMessage = {
        id: `temp-user-${Date.now()}`,
        role: "user",
        content: text,
        sources: null,
        created_at: new Date().toISOString(),
      };
      const assistantTempId = `temp-assistant-${Date.now()}`;
      const assistantMessage: ChatMessage = {
        id: assistantTempId,
        role: "assistant",
        content: "",
        sources: null,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setIsStreaming(true);

      const controller = new AbortController();
      abortRef.current = controller;
      let accumulated = "";

      try {
        await streamChatQuery(
          { message: text, conversation_id: conversationId ?? undefined, document_id: documentId },
          {
            onStart: (convId) => setConversationId(convId),
            onToken: (delta) => {
              accumulated += delta;
              const snapshot = accumulated;
              setMessages((prev) =>
                prev.map((m) => (m.id === assistantTempId ? { ...m, content: snapshot } : m))
              );
            },
            onDone: (messageId, sources) => {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantTempId
                    ? { ...m, id: messageId, sources: sources as SourceReference[] }
                    : m
                )
              );
            },
            onError: (message) => setError(message),
          },
          controller.signal
        );
      } catch (err) {
        if (!(err instanceof DOMException && err.name === "AbortError")) {
          setError("Failed to get a response. Please try again.");
        }
      } finally {
        setIsStreaming(false);
      }
    },
    [conversationId]
  );

  const stop = useCallback(() => {
    abortRef.current?.abort();
    setIsStreaming(false);
  }, []);

  return { messages, conversationId, isStreaming, error, sendMessage, loadConversation, reset, stop };
}
