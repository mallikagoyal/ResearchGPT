export interface SourceReference {
  document_id: string;
  document_title: string;
  chunk_index: number;
  snippet: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources: SourceReference[] | null;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  document_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: ChatMessage[];
}

export interface ConversationListResponse {
  conversations: Conversation[];
}

export interface ChatQueryRequest {
  message: string;
  conversation_id?: string;
  document_id?: string;
}
