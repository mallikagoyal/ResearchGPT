"use client";

import Link from "next/link";
import { UploadCloud } from "lucide-react";

import { DocumentList } from "@/components/documents/document-list";
import { Button } from "@/components/ui/button";

export default function DocumentsPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">Documents</h1>
          <p className="text-sm text-muted-foreground">View, search, and manage your research library.</p>
        </div>
        <Button asChild className="gap-2">
          <Link href="/dashboard/upload">
            <UploadCloud className="h-4 w-4" />
            Upload
          </Link>
        </Button>
      </div>
      <DocumentList />
    </div>
  );
}
