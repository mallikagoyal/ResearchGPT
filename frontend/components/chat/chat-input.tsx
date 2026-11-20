"use client";

import { Send, Square, Paperclip } from "lucide-react";
import { useRef, useState, type KeyboardEvent, useEffect } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function ChatInput({
  onSend,
  onStop,
  isStreaming,
}: {
  onSend: (text: string) => void;
  onStop: () => void;
  isStreaming: boolean;
}) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize the textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [value]);

  function handleSend() {
    const trimmed = value.trim();
    if (!trimmed || isStreaming) return;
    onSend(trimmed);
    setValue("");
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  }

  const isEmpty = !value.trim();

  return (
    <div className="border-t border-border bg-background/80 backdrop-blur-sm p-3 md:p-4">
      <div
        className={cn(
          "flex items-end gap-2 rounded-xl border bg-card transition-all duration-200",
          isStreaming
            ? "border-primary/40 shadow-sm shadow-primary/10"
            : "border-border focus-within:border-primary/50 focus-within:shadow-sm focus-within:shadow-primary/10"
        )}
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your documents…"
          rows={1}
          disabled={isStreaming}
          className="flex-1 resize-none bg-transparent px-4 py-3 text-sm placeholder:text-muted-foreground/60 focus-visible:outline-none disabled:opacity-50"
          style={{ minHeight: "44px", maxHeight: "160px" }}
        />
        <div className="flex items-center gap-1.5 p-2">
          {isStreaming ? (
            <Button
              variant="destructive"
              size="icon"
              onClick={onStop}
              aria-label="Stop generating"
              className="h-8 w-8 rounded-lg"
            >
              <Square className="h-3.5 w-3.5 fill-current" />
            </Button>
          ) : (
            <Button
              size="icon"
              onClick={handleSend}
              disabled={isEmpty}
              aria-label="Send message"
              className={cn(
                "h-8 w-8 rounded-lg transition-all duration-150",
                isEmpty
                  ? "opacity-40"
                  : "opacity-100 shadow-sm"
              )}
            >
              <Send className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>
      </div>
      <p className="mt-2 text-center text-[10px] text-muted-foreground/50">
        Press <kbd className="rounded border border-border bg-muted px-1 py-0.5 font-mono text-[10px]">Enter</kbd> to send · <kbd className="rounded border border-border bg-muted px-1 py-0.5 font-mono text-[10px]">Shift+Enter</kbd> for new line
      </p>
    </div>
  );
}
