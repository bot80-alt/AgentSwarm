import { cn } from "@/lib/utils";

export type StatusIndicatorProps = {
  status: "pending" | "running" | "completed" | "failed";
  className?: string;
};

const statusStyles = {
  pending: "bg-muted-foreground/40",
  running: "bg-sky-400 animate-pulse",
  completed: "bg-emerald-400",
  failed: "bg-red-400",
};

export function StatusIndicator({ status, className }: StatusIndicatorProps) {
  return (
    <span
      className={cn("inline-block h-2 w-2 shrink-0 rounded-full", statusStyles[status], className)}
      aria-label={`Status: ${status}`}
    />
  );
}
