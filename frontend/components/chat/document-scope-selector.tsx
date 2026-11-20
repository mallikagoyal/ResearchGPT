"use client";

import { BookOpen, ChevronDown } from "lucide-react";
import { useDocuments } from "@/hooks/use-documents";
import { cn } from "@/lib/utils";

export function DocumentScopeSelector({
  value,
  onChange,
}: {
  value: string | undefined;
  onChange: (documentId: string | undefined) => void;
}) {
  const { data } = useDocuments();
  const processedDocuments = (data?.documents ?? []).filter((doc) => doc.status === "processed");

  if (processedDocuments.length === 0) return null;

  return (
    <div className="relative flex items-center">
      <BookOpen className="pointer-events-none absolute left-2.5 h-3.5 w-3.5 text-muted-foreground" />
      <select
        value={value ?? "all"}
        onChange={(e) => onChange(e.target.value === "all" ? undefined : e.target.value)}
        className={cn(
          "h-8 appearance-none rounded-lg border border-border bg-card pl-8 pr-7 text-xs font-medium shadow-sm",
          "focus:outline-none focus:ring-2 focus:ring-ring/40 focus:border-primary/50",
          "transition-colors hover:border-primary/30",
          value ? "text-primary border-primary/30 bg-primary/5" : "text-foreground"
        )}
        aria-label="Chat scope"
      >
        <option value="all">All documents</option>
        {processedDocuments.map((doc) => (
          <option key={doc.id} value={doc.id}>
            {doc.title ?? doc.original_filename}
          </option>
        ))}
      </select>
      <ChevronDown className="pointer-events-none absolute right-2 h-3 w-3 text-muted-foreground" />
    </div>
  );
}
