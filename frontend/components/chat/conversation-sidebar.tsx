"use client";

import { MessageSquarePlus, Trash2, MessageSquare } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useConversations, useDeleteConversation } from "@/hooks/use-conversations";
import { cn } from "@/lib/utils";

export function ConversationSidebar({
  activeConversationId,
  onSelect,
  onNew,
}: {
  activeConversationId: string | null;
  onSelect: (conversationId: string) => void;
  onNew: () => void;
}) {
  const { data, isLoading } = useConversations();
  const deleteMutation = useDeleteConversation();

  return (
    <div className="flex h-full w-56 shrink-0 flex-col border-r border-border bg-background">
      {/* Header */}
      <div className="p-3 border-b border-border">
        <button
          onClick={onNew}
          className="flex w-full items-center gap-2.5 rounded-lg border border-border bg-card px-3 py-2.5 text-sm font-medium text-foreground shadow-sm transition-all hover:border-primary/40 hover:bg-accent/60 hover:shadow-md"
        >
          <MessageSquarePlus className="h-4 w-4 text-primary" />
          New conversation
        </button>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto p-2">
        {isLoading && (
          <div className="space-y-1.5 p-1">
            <Skeleton className="h-9 w-full rounded-lg" />
            <Skeleton className="h-9 w-full rounded-lg" />
            <Skeleton className="h-9 w-full rounded-lg" />
          </div>
        )}

        {!isLoading && data?.conversations.length === 0 && (
          <div className="flex flex-col items-center gap-2 px-3 py-10 text-center">
            <MessageSquare className="h-6 w-6 text-muted-foreground/40" />
            <p className="text-xs text-muted-foreground">No conversations yet.</p>
            <p className="text-[11px] text-muted-foreground/60">Start one to see it here.</p>
          </div>
        )}

        {data?.conversations.map((conversation) => {
          const isActive = conversation.id === activeConversationId;
          return (
            <div
              key={conversation.id}
              className={cn(
                "group relative flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2.5 text-sm transition-all",
                isActive
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:bg-accent/60 hover:text-foreground"
              )}
              onClick={() => onSelect(conversation.id)}
            >
              {isActive && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 h-4 w-0.5 rounded-r-full bg-primary" />
              )}
              <MessageSquare className={cn("h-3.5 w-3.5 shrink-0", isActive ? "text-primary" : "text-muted-foreground/60")} />
              <span className="flex-1 truncate text-[13px]">{conversation.title}</span>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  deleteMutation.mutate(conversation.id);
                  if (isActive) onNew();
                }}
                className="shrink-0 rounded p-0.5 opacity-0 transition-opacity hover:bg-destructive/10 hover:text-destructive group-hover:opacity-100"
                aria-label={`Delete ${conversation.title}`}
              >
                <Trash2 className="h-3 w-3" />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
