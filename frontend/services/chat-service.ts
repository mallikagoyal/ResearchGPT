import { API_BASE_URL, TOKEN_STORAGE_KEY, apiClient } from "@/lib/axios";
import type {
  ChatQueryRequest,
  ConversationDetail,
  ConversationListResponse,
} from "@/types/chat";

export interface ChatStreamHandlers {
  onStart?: (conversationId: string) => void;
  onToken?: (text: string) => void;
  onDone?: (messageId: string, sources: unknown[]) => void;
  onError?: (message: string) => void;
}

/**
 * Parse a single SSE frame ("event: X\ndata: Y") into its event name and
 * JSON-parsed payload. Returns null for blank/malformed frames.
 */
function parseSseFrame(frame: string): { event: string; data: unknown } | null {
  const eventLine = frame.split("\n").find((line) => line.startsWith("event:"));
  const dataLine = frame.split("\n").find((line) => line.startsWith("data:"));
  if (!eventLine || !dataLine) return null;

  const event = eventLine.slice("event:".length).trim();
  const rawData = dataLine.slice("data:".length).trim();
  try {
    return { event, data: JSON.parse(rawData) };
  } catch {
    return null;
  }
}

/**
 * Send a chat query and stream the response via Server-Sent-Events.
 *
 * Uses raw `fetch` + a ReadableStream reader rather than axios or the
 * browser's native EventSource, because EventSource only supports GET
 * requests — this endpoint needs a POST body (the message) and an
 * Authorization header.
 */
export async function streamChatQuery(
  request: ChatQueryRequest,
  handlers: ChatStreamHandlers,
  signal?: AbortSignal
): Promise<void> {
  const token = typeof window !== "undefined" ? window.localStorage.getItem(TOKEN_STORAGE_KEY) : null;

  const response = await fetch(`${API_BASE_URL}/chat/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(request),
    signal,
  });

  if (!response.ok || !response.body) {
    handlers.onError?.(`Request failed (${response.status}).`);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? ""; // keep any incomplete trailing frame for next read

    for (const frame of frames) {
      const parsed = parseSseFrame(frame);
      if (!parsed) continue;

      if (parsed.event === "start") {
        const data = parsed.data as { conversation_id: string };
        handlers.onStart?.(data.conversation_id);
      } else if (parsed.event === "token") {
        const data = parsed.data as { text: string };
        handlers.onToken?.(data.text);
      } else if (parsed.event === "done") {
        const data = parsed.data as { message_id: string; sources: unknown[] };
        handlers.onDone?.(data.message_id, data.sources);
      } else if (parsed.event === "error") {
        const data = parsed.data as { message: string };
        handlers.onError?.(data.message);
      }
    }
  }
}

export const chatService = {
  async listConversations(): Promise<ConversationListResponse> {
    const { data } = await apiClient.get<ConversationListResponse>("/chat/conversations");
    return data;
  },

  async getConversation(conversationId: string): Promise<ConversationDetail> {
    const { data } = await apiClient.get<ConversationDetail>(`/chat/conversations/${conversationId}`);
    return data;
  },

  async deleteConversation(conversationId: string): Promise<void> {
    await apiClient.delete(`/chat/conversations/${conversationId}`);
  },
};
