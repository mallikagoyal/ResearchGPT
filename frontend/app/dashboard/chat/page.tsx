"use client";

import { MessageSquare, UploadCloud, Sparkles } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { ChatInput } from "@/components/chat/chat-input";
import { ChatMessageBubble } from "@/components/chat/chat-message";
import { ConversationSidebar } from "@/components/chat/conversation-sidebar";
import { DocumentScopeSelector } from "@/components/chat/document-scope-selector";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useChat } from "@/hooks/use-chat";
import { useDocuments } from "@/hooks/use-documents";
import { chatService } from "@/services/chat-service";
import { cn } from "@/lib/utils";

const SUGGESTED_QUESTIONS = [
  "Summarize the key findings of this document",
  "What methodology was used in this research?",
  "What are the main conclusions and recommendations?",
];

export default function ChatPage() {
  const [scopeDocumentId, setScopeDocumentId] = useState<string | undefined>(undefined);
  const { messages, conversationId, isStreaming, error, sendMessage, loadConversation, reset, stop } = useChat();
  const { data: documentsData } = useDocuments();
  const processedDocs = (documentsData?.documents ?? []).filter((d) => d.status === "processed");
  const hasProcessedDocuments = processedDocs.length > 0;
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSelectConversation(id: string) {
    const detail = await chatService.getConversation(id);
    loadConversation(detail.messages, detail.id);
    setScopeDocumentId(detail.document_id ?? undefined);
  }

  function handleNewChat() {
    reset();
    setScopeDocumentId(undefined);
  }

  return (
    <div className="-m-4 flex h-[calc(100vh-3.5rem)] md:-m-8">
      <ConversationSidebar
        activeConversationId={conversationId}
        onSelect={handleSelectConversation}
        onNew={handleNewChat}
      />

      <div className="flex flex-1 flex-col min-w-0">
        {/* Chat header */}
        <div className="flex items-center justify-between border-b border-border bg-background/80 backdrop-blur-sm px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="logo-gradient flex h-6 w-6 items-center justify-center rounded-lg text-white text-[10px] font-bold">
              R
            </div>
            <span className="font-semibold text-sm">Research Chat</span>
            {isStreaming && (
              <span className="flex items-center gap-1.5 text-xs text-primary">
                <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
                Generating…
              </span>
            )}
          </div>
          <DocumentScopeSelector value={scopeDocumentId} onChange={setScopeDocumentId} />
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center gap-6 p-8 text-center">
              <div className="space-y-3">
                <div className="logo-gradient mx-auto flex h-14 w-14 items-center justify-center rounded-2xl text-white text-xl font-bold shadow-md">
                  R
                </div>
                <div>
                  <p className="font-semibold text-lg">
                    {hasProcessedDocuments ? "Ask anything about your research" : "No documents ready yet"}
                  </p>
                  <p className="mt-1 max-w-sm text-sm text-muted-foreground leading-relaxed">
                    {hasProcessedDocuments
                      ? "Answers are grounded in your uploaded PDFs with inline citations."
                      : "Upload a PDF and wait for it to finish processing, then come back to chat."}
                  </p>
                </div>
              </div>

              {hasProcessedDocuments ? (
                <div className="w-full max-w-md space-y-2">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">Try asking</p>
                  {SUGGESTED_QUESTIONS.map((q) => (
                    <button
                      key={q}
                      onClick={() => sendMessage(q, scopeDocumentId)}
                      className="flex w-full items-center gap-3 rounded-xl border border-border bg-card px-4 py-3 text-left text-sm transition-all hover:border-primary/40 hover:bg-accent/60 hover:shadow-sm"
                    >
                      <Sparkles className="h-4 w-4 shrink-0 text-primary" />
                      {q}
                    </button>
                  ))}
                </div>
              ) : (
                <Button asChild className="gap-2">
                  <Link href="/dashboard/upload">
                    <UploadCloud className="h-4 w-4" />
                    Upload a document
                  </Link>
                </Button>
              )}
            </div>
          ) : (
            <div className="mx-auto max-w-3xl space-y-6 p-4 md:p-6">
              {messages.map((message, i) => (
                <ChatMessageBubble
                  key={message.id}
                  message={message}
                />
              ))}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="mx-auto w-full max-w-3xl px-4 pb-2">
            <Alert variant="destructive" className="rounded-xl">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          </div>
        )}

        {/* Input */}
        <div className={cn(messages.length > 0 && "border-t border-border/60")}>
          <div className="mx-auto max-w-3xl">
            <ChatInput
              onSend={(text) => sendMessage(text, scopeDocumentId)}
              onStop={stop}
              isStreaming={isStreaming}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
