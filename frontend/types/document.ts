export type DocumentStatus = "pending" | "processing" | "processed" | "failed";

export interface Document {
  id: string;
  original_filename: string;
  status: DocumentStatus;
  title: string | null;
  page_count: number | null;
  file_size_bytes: number;
  error_message: string | null;
  chunk_size: number;
  chunk_overlap: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentDetail extends Document {
  extracted_text: string | null;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
}
