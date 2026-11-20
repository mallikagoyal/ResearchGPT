import type { AxiosProgressEvent } from "axios";

import { apiClient } from "@/lib/axios";
import type { Document, DocumentDetail, DocumentListResponse } from "@/types/document";

/**
 * Thin wrapper around the backend's document endpoints. Components/hooks
 * should call these functions rather than using apiClient directly, so
 * the request/response shapes are defined in exactly one place.
 */
export const documentService = {
  async upload(files: File[], onProgress?: (percent: number) => void): Promise<Document[]> {
    const formData = new FormData();
    for (const file of files) {
      formData.append("files", file);
    }

    const { data } = await apiClient.post<Document[]>("/documents/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (event: AxiosProgressEvent) => {
        if (onProgress && event.total) {
          onProgress(Math.round((event.loaded / event.total) * 100));
        }
      },
    });
    return data;
  },

  async list(search?: string): Promise<DocumentListResponse> {
    const { data } = await apiClient.get<DocumentListResponse>("/documents", {
      params: search ? { search } : undefined,
    });
    return data;
  },

  async getById(documentId: string): Promise<DocumentDetail> {
    const { data } = await apiClient.get<DocumentDetail>(`/documents/${documentId}`);
    return data;
  },

  async remove(documentId: string): Promise<void> {
    await apiClient.delete(`/documents/${documentId}`);
  },
};
