"use client";

import { FileText, BookMarked } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { cn } from "@/lib/utils";
import type { ChatMessage } from "@/types/chat";

function TypingIndicator() {
  return (
    <span className="inline-flex items-center gap-1 py-1.5 px-1">
      <span className="typing-dot h-2 w-2 rounded-full bg-muted-foreground/60" />
      <span className="typing-dot h-2 w-2 rounded-full bg-muted-foreground/60" />
      <span className="typing-dot h-2 w-2 rounded-full bg-muted-foreground/60" />
    </span>
  );
}

function AIAvatar() {
  return (
    <div className="logo-gradient flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-white text-xs font-bold shadow-sm">
      R
    </div>
  );
}

export function ChatMessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex gap-3 animate-fade-in", isUser ? "justify-end" : "justify-start")}>
      {!isUser && <AIAvatar />}

      <div className={cn("max-w-[78%] space-y-2", isUser && "flex flex-col items-end")}>
        {/* Bubble */}
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm shadow-sm",
            isUser
              ? "rounded-tr-sm bg-primary text-primary-foreground"
              : "rounded-tl-sm bg-card border border-border/60 text-foreground"
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
          ) : message.content ? (
            <div className="prose prose-sm max-w-none dark:prose-invert prose-p:my-1.5 prose-pre:my-2 prose-headings:my-2 prose-headings:text-foreground prose-ul:my-1.5 prose-ol:my-1.5 prose-li:my-0.5 prose-code:text-primary prose-code:bg-muted prose-code:rounded prose-code:px-1 prose-code:py-0.5 prose-code:text-xs prose-code:before:content-none prose-code:after:content-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            </div>
          ) : (
            <TypingIndicator />
          )}
        </div>

        {/* Sources */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="w-full space-y-2">
            <div className="flex items-center gap-1.5">
              <BookMarked className="h-3 w-3 text-muted-foreground" />
              <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                Sources
              </p>
            </div>
            <div className="grid gap-1.5">
              {message.sources.map((source, index) => (
                <div
                  key={`${source.document_id}-${source.chunk_index}-${index}`}
                  className="flex items-start gap-2.5 rounded-lg border border-border/60 bg-muted/40 p-2.5 text-xs transition-colors hover:bg-muted/70"
                >
                  <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary font-semibold text-[10px]">
                    {index + 1}
                  </div>
                  <div className="min-w-0">
                    <p className="font-medium text-foreground truncate">{source.document_title}</p>
                    <p className="mt-0.5 line-clamp-2 text-muted-foreground leading-relaxed">{source.snippet}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-muted border border-border shadow-sm">
          <span className="text-xs font-semibold text-foreground">U</span>
        </div>
      )}
    </div>
  );
}
