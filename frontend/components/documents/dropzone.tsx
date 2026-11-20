"use client";

import { AlertCircle, FileText, UploadCloud, X, CheckCircle2 } from "lucide-react";
import { useCallback, useRef, useState, type DragEvent } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useUploadDocuments } from "@/hooks/use-documents";
import { formatFileSize, cn } from "@/lib/utils";
import { getApiErrorMessage } from "@/lib/axios";

const MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024;
const ALLOWED_EXTENSION = ".pdf";

interface StagedFile {
  file: File;
  error?: string;
}

function validateFile(file: File): string | undefined {
  if (!file.name.toLowerCase().endsWith(ALLOWED_EXTENSION)) {
    return "Only PDF files are supported.";
  }
  if (file.size > MAX_FILE_SIZE_BYTES) {
    return "File exceeds the 25MB size limit.";
  }
  if (file.size === 0) {
    return "File is empty.";
  }
  return undefined;
}

export function DocumentDropzone({ onUploaded }: { onUploaded?: () => void }) {
  const [staged, setStaged] = useState<StagedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const uploadMutation = useUploadDocuments();

  const addFiles = useCallback((fileList: FileList | File[]) => {
    setServerError(null);
    setUploadSuccess(false);
    const next: StagedFile[] = Array.from(fileList).map((file) => ({
      file,
      error: validateFile(file),
    }));
    setStaged((prev) => [...prev, ...next]);
  }, []);

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);
    if (event.dataTransfer.files.length > 0) {
      addFiles(event.dataTransfer.files);
    }
  }

  function removeStaged(index: number) {
    setStaged((prev) => prev.filter((_, i) => i !== index));
  }

  const validFiles = staged.filter((s) => !s.error);
  const hasInvalidFiles = staged.some((s) => s.error);

  async function handleUpload() {
    if (validFiles.length === 0) return;
    setServerError(null);
    setUploadSuccess(false);
    setUploadProgress(0);
    try {
      await uploadMutation.mutateAsync({
        files: validFiles.map((s) => s.file),
        onProgress: setUploadProgress,
      });
      setStaged([]);
      setUploadSuccess(true);
      onUploaded?.();
      setTimeout(() => setUploadSuccess(false), 4000);
    } catch (err) {
      setServerError(getApiErrorMessage(err, "Upload failed. Please try again."));
    } finally {
      setUploadProgress(null);
    }
  }

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center gap-4 rounded-2xl border-2 border-dashed py-14 text-center transition-all duration-200",
          isDragging
            ? "border-primary bg-accent scale-[1.01]"
            : "border-border hover:border-primary/40 hover:bg-accent/40"
        )}
      >
        <div
          className={cn(
            "flex h-14 w-14 items-center justify-center rounded-2xl transition-colors",
            isDragging ? "bg-primary/10" : "bg-muted"
          )}
        >
          <UploadCloud
            className={cn(
              "h-7 w-7 transition-colors",
              isDragging ? "text-primary" : "text-muted-foreground"
            )}
          />
        </div>
        <div>
          <p className="font-semibold text-foreground">
            {isDragging ? "Drop files here" : "Drag & drop PDF files"}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            or{" "}
            <span className="text-primary font-medium hover:underline">browse files</span>
            {" "}· max 25MB per file
          </p>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          multiple
          className="hidden"
          onChange={(e) => {
            if (e.target.files) addFiles(e.target.files);
            e.target.value = "";
          }}
        />
      </div>

      {/* Success banner */}
      {uploadSuccess && (
        <div className="animate-fade-in flex items-center gap-3 rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-green-600" />
          <span>Files uploaded successfully! Processing will begin shortly.</span>
        </div>
      )}

      {/* Error banner */}
      {serverError && (
        <Alert variant="destructive" className="rounded-xl">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{serverError}</AlertDescription>
        </Alert>
      )}

      {/* Staged files */}
      {staged.length > 0 && (
        <div className="animate-fade-in space-y-2 rounded-xl border border-border bg-card p-3">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground px-1 pb-1">
            Ready to upload ({staged.length})
          </p>
          {staged.map((item, index) => (
            <div
              key={`${item.file.name}-${index}`}
              className={cn(
                "flex items-center justify-between gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                item.error ? "bg-destructive/5 border border-destructive/20" : "bg-background border border-border/60"
              )}
            >
              <div className="flex min-w-0 items-center gap-2.5">
                <div className={cn(
                  "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
                  item.error ? "bg-destructive/10" : "bg-muted"
                )}>
                  <FileText className={cn("h-4 w-4", item.error ? "text-destructive" : "text-muted-foreground")} />
                </div>
                <div className="min-w-0">
                  <p className="truncate font-medium text-sm">{item.file.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {item.error ? (
                      <span className="text-destructive">{item.error}</span>
                    ) : (
                      formatFileSize(item.file.size)
                    )}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => removeStaged(index)}
                className="shrink-0 rounded-md p-1 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
                aria-label={`Remove ${item.file.name}`}
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}

          {hasInvalidFiles && (
            <p className="px-2 text-xs text-muted-foreground">
              ⚠ Files with errors will be skipped.
            </p>
          )}

          {uploadProgress !== null && (
            <div className="space-y-1.5 px-1 pt-1">
              <Progress value={uploadProgress} className="h-1.5" />
              <p className="text-xs text-muted-foreground">Uploading… {uploadProgress}%</p>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2 border-t border-border/60">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setStaged([])}
              disabled={uploadMutation.isPending}
            >
              Clear all
            </Button>
            <Button
              size="sm"
              onClick={handleUpload}
              disabled={validFiles.length === 0}
              isLoading={uploadMutation.isPending}
              className="gap-2"
            >
              {!uploadMutation.isPending && <UploadCloud className="h-4 w-4" />}
              Upload {validFiles.length > 0 ? `(${validFiles.length})` : ""}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
