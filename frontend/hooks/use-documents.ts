"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { documentService } from "@/services/document-service";
import type { DocumentListResponse } from "@/types/document";

const DOCUMENTS_QUERY_KEY = (search?: string) => ["documents", search ?? ""] as const;

const ACTIVE_STATUSES = new Set(["pending", "processing"]);

/**
 * Lists the current user's documents. Polls every 2s while any document is
 * still pending/processing, so upload status updates appear automatically
 * without the user needing to refresh.
 */
export function useDocuments(search?: string) {
  return useQuery({
    queryKey: DOCUMENTS_QUERY_KEY(search),
    queryFn: () => documentService.list(search),
    refetchInterval: (query) => {
      const data = query.state.data as DocumentListResponse | undefined;
      const hasActiveDocument = data?.documents.some((doc) => ACTIVE_STATUSES.has(doc.status));
      return hasActiveDocument ? 2000 : false;
    },
  });
}

export function useUploadDocuments() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ files, onProgress }: { files: File[]; onProgress?: (percent: number) => void }) =>
      documentService.upload(files, onProgress),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (documentId: string) => documentService.remove(documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}
