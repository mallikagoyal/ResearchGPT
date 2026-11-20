"use client";

import { DocumentDropzone } from "@/components/documents/dropzone";
import { DocumentList } from "@/components/documents/document-list";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export default function UploadPage() {
  return (
    <div className="space-y-8 animate-fade-in">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Upload Documents</h1>
        <p className="text-sm text-muted-foreground">
          Add PDFs to your research library. They'll be processed and made available for chat.
        </p>
      </div>

      <Card>
        <CardHeader className="pb-4">
          <CardTitle>Add new documents</CardTitle>
          <CardDescription>Drag and drop or click to select PDF files up to 25MB each.</CardDescription>
        </CardHeader>
        <CardContent>
          <DocumentDropzone />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle>Your library</CardTitle>
          <CardDescription>All documents you have uploaded to this workspace.</CardDescription>
        </CardHeader>
        <CardContent>
          <DocumentList searchable={false} />
        </CardContent>
      </Card>
    </div>
  );
}
