"use client";

import { AlertCircle, FileText, Search, Trash2, MessageSquare } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { DocumentStatusBadge } from "@/components/documents/document-status-badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useDeleteDocument, useDocuments } from "@/hooks/use-documents";
import { formatFileSize } from "@/lib/utils";
import type { Document } from "@/types/document";

function DocumentRow({ document, index }: { document: Document; index: number }) {
  const deleteMutation = useDeleteDocument();
  const [confirming, setConfirming] = useState(false);

  return (
    <div
      className="animate-fade-in flex items-center justify-between gap-4 rounded-xl border border-border/60 bg-card p-4 transition-all hover:border-border hover:shadow-sm"
      style={{ animationDelay: `${index * 40}ms` }}
    >
      <div className="flex min-w-0 items-center gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-muted">
          <FileText className="h-5 w-5 text-muted-foreground" />
        </div>
        <div className="min-w-0">
          <p className="truncate font-medium text-sm">{document.title ?? document.original_filename}</p>
          <p className="truncate text-xs text-muted-foreground mt-0.5">
            {document.original_filename}
            {" · "}
            {formatFileSize(document.file_size_bytes)}
            {document.page_count ? ` · ${document.page_count} pages` : ""}
          </p>
          {document.status === "failed" && document.error_message && (
            <p className="mt-1 flex items-center gap-1.5 text-xs text-destructive">
              <AlertCircle className="h-3 w-3 shrink-0" />
              {document.error_message}
            </p>
          )}
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-2">
        <DocumentStatusBadge status={document.status} />

        {document.status === "processed" && (
          <Button asChild variant="ghost" size="sm" className="gap-1.5 text-xs text-muted-foreground hover:text-foreground">
            <Link href="/dashboard/chat">
              <MessageSquare className="h-3.5 w-3.5" />
              Chat
            </Link>
          </Button>
        )}

        {confirming ? (
          <div className="flex items-center gap-1.5">
            <Button
              variant="destructive"
              size="sm"
              isLoading={deleteMutation.isPending}
              onClick={() => deleteMutation.mutate(document.id, { onSettled: () => setConfirming(false) })}
            >
              Delete
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setConfirming(false)}>
              Cancel
            </Button>
          </div>
        ) : (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-muted-foreground/60 hover:text-destructive hover:bg-destructive/10"
            aria-label={`Delete ${document.original_filename}`}
            onClick={() => setConfirming(true)}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
}

export function DocumentList({ searchable = true }: { searchable?: boolean }) {
  const [search, setSearch] = useState("");
  const { data, isLoading, isError } = useDocuments(search || undefined);

  return (
    <div className="space-y-4">
      {searchable && (
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground/60" />
          <Input
            placeholder="Search documents…"
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      )}

      {isLoading && (
        <div className="space-y-2">
          <Skeleton className="h-[72px] w-full rounded-xl" />
          <Skeleton className="h-[72px] w-full rounded-xl" />
          <Skeleton className="h-[72px] w-full rounded-xl" />
        </div>
      )}

      {isError && (
        <Alert variant="destructive" className="rounded-xl">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Failed to load documents. Please try again.</AlertDescription>
        </Alert>
      )}

      {!isLoading && !isError && data && data.documents.length === 0 && (
        <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-border py-14 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-muted">
            <FileText className="h-6 w-6 text-muted-foreground" />
          </div>
          <div>
            <p className="font-medium">
              {search ? "No documents match your search" : "No documents yet"}
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              {search ? "Try a different search term." : "Upload a PDF to get started."}
            </p>
          </div>
        </div>
      )}

      {!isLoading && !isError && data && data.documents.length > 0 && (
        <div className="space-y-2">
          {data.documents.map((document, i) => (
            <DocumentRow key={document.id} document={document} index={i} />
          ))}
        </div>
      )}
    </div>
  );
}
