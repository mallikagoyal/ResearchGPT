"use client";

import Link from "next/link";
import { BookOpen, FileText, UploadCloud, Zap } from "lucide-react";

import { DocumentStatusBadge } from "@/components/documents/document-status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/use-auth";
import { useDocuments } from "@/hooks/use-documents";
import { formatFileSize } from "@/lib/utils";

function StatCard({
  title,
  value,
  icon: Icon,
  isLoading,
  description,
}: {
  title: string;
  value: React.ReactNode;
  icon: React.ElementType;
  isLoading: boolean;
  description?: string;
}) {
  return (
    <Card className="card-shadow border-border/60">
      <CardContent className="pt-5 pb-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{title}</p>
            <div className="mt-1.5">
              {isLoading ? (
                <Skeleton className="h-8 w-14" />
              ) : (
                <p className="text-3xl font-bold tracking-tight text-foreground">{value}</p>
              )}
            </div>
            {description && <p className="mt-1 text-xs text-muted-foreground">{description}</p>}
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent">
            <Icon className="h-5 w-5 text-primary" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const { data, isLoading } = useDocuments();

  const documents = data?.documents ?? [];
  const totalDocuments = data?.total ?? 0;
  const processedCount = documents.filter((d) => d.status === "processed").length;
  const pendingCount = documents.filter((d) => d.status === "pending" || d.status === "processing").length;
  const recentDocuments = documents.slice(0, 5);

  const firstName = user?.full_name?.split(" ")[0] ?? "";

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">
          {firstName ? `Good to see you, ${firstName} 👋` : "Welcome back"}
        </h1>
        <p className="text-sm text-muted-foreground">
          Here&apos;s an overview of your research workspace.
        </p>
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard
          title="Total Documents"
          value={totalDocuments}
          icon={FileText}
          isLoading={isLoading}
        />
        <StatCard
          title="Processed"
          value={processedCount}
          icon={Zap}
          isLoading={isLoading}
          description={pendingCount > 0 ? `${pendingCount} processing…` : undefined}
        />
        <StatCard
          title="Chat Ready"
          value={processedCount}
          icon={BookOpen}
          isLoading={isLoading}
          description="Documents you can query"
        />
      </div>

      {/* Quick actions */}
      <div className="grid gap-3 sm:grid-cols-2">
        <Link
          href="/dashboard/upload"
          className="group flex items-center gap-4 rounded-xl border border-border bg-card p-4 card-shadow transition-all hover:border-primary/40 hover:card-shadow-md"
        >
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent group-hover:bg-primary/10 transition-colors">
            <UploadCloud className="h-5 w-5 text-primary" />
          </div>
          <div className="min-w-0">
            <p className="font-medium text-sm">Upload Documents</p>
            <p className="text-xs text-muted-foreground mt-0.5">Add PDFs to your research library</p>
          </div>
          <span className="ml-auto text-muted-foreground/40 group-hover:text-primary transition-colors text-lg">→</span>
        </Link>
        <Link
          href="/dashboard/chat"
          className="group flex items-center gap-4 rounded-xl border border-border bg-card p-4 card-shadow transition-all hover:border-primary/40 hover:card-shadow-md"
        >
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent group-hover:bg-primary/10 transition-colors">
            <BookOpen className="h-5 w-5 text-primary" />
          </div>
          <div className="min-w-0">
            <p className="font-medium text-sm">Chat with Documents</p>
            <p className="text-xs text-muted-foreground mt-0.5">Ask questions, get cited answers</p>
          </div>
          <span className="ml-auto text-muted-foreground/40 group-hover:text-primary transition-colors text-lg">→</span>
        </Link>
      </div>

      {/* Recent Documents */}
      <Card className="card-shadow border-border/60">
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <CardTitle className="text-base font-semibold">Recent Documents</CardTitle>
          {documents.length > 0 && (
            <Button asChild variant="ghost" size="sm" className="text-xs text-muted-foreground hover:text-foreground">
              <Link href="/dashboard/documents">View all →</Link>
            </Button>
          )}
        </CardHeader>
        <CardContent>
          {isLoading && (
            <div className="space-y-2">
              <Skeleton className="h-14 w-full rounded-lg" />
              <Skeleton className="h-14 w-full rounded-lg" />
              <Skeleton className="h-14 w-full rounded-lg" />
            </div>
          )}

          {!isLoading && recentDocuments.length === 0 && (
            <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-border py-14 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
                <FileText className="h-6 w-6 text-muted-foreground" />
              </div>
              <div>
                <p className="font-medium text-sm">No documents yet</p>
                <p className="text-sm text-muted-foreground mt-1 max-w-xs">
                  Upload a PDF to start chatting with your research.
                </p>
              </div>
              <Button asChild className="mt-2 gap-2">
                <Link href="/dashboard/upload">
                  <UploadCloud className="h-4 w-4" />
                  Upload document
                </Link>
              </Button>
            </div>
          )}

          {!isLoading && recentDocuments.length > 0 && (
            <div className="space-y-2">
              {recentDocuments.map((document, i) => (
                <div
                  key={document.id}
                  className="animate-fade-in flex items-center justify-between gap-4 rounded-lg border border-border/60 bg-background px-4 py-3 transition-colors hover:border-border hover:bg-muted/30"
                  style={{ animationDelay: `${i * 50}ms` }}
                >
                  <div className="flex min-w-0 items-center gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">
                        {document.title ?? document.original_filename}
                      </p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {formatFileSize(document.file_size_bytes)}
                      </p>
                    </div>
                  </div>
                  <DocumentStatusBadge status={document.status} />
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
