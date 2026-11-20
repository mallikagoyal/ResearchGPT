import { CheckCircle2, Clock, Loader2, XCircle } from "lucide-react";

import type { DocumentStatus } from "@/types/document";
import { cn } from "@/lib/utils";

const STATUS_CONFIG: Record<
  DocumentStatus,
  { label: string; icon: React.ElementType; className: string; dotClass: string }
> = {
  pending: {
    label: "Pending",
    icon: Clock,
    className: "bg-orange-50 text-orange-700 border-orange-200",
    dotClass: "bg-orange-400",
  },
  processing: {
    label: "Processing",
    icon: Loader2,
    className: "bg-blue-50 text-blue-700 border-blue-200",
    dotClass: "bg-blue-400",
  },
  processed: {
    label: "Processed",
    icon: CheckCircle2,
    className: "bg-green-50 text-green-700 border-green-200",
    dotClass: "bg-green-400",
  },
  failed: {
    label: "Failed",
    icon: XCircle,
    className: "bg-red-50 text-red-700 border-red-200",
    dotClass: "bg-red-400",
  },
};

export function DocumentStatusBadge({ status }: { status: DocumentStatus }) {
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium",
        config.className
      )}
    >
      <Icon
        className={cn(
          "h-3 w-3",
          status === "processing" && "animate-spin"
        )}
      />
      {config.label}
    </span>
  );
}
