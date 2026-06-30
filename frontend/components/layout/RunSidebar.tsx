"use client";

import { Plus } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import type { WorkflowRunSummary, WorkflowRunStatus } from "@/types";

type RunSidebarProps = {
  runs: WorkflowRunSummary[];
  activeRunId: number | null;
  isLoading: boolean;
  collapsed: boolean;
  onSelectRun: (runId: number) => void;
  onNewRun: () => void;
};

function statusVariant(status: WorkflowRunStatus) {
  switch (status) {
    case "completed":
      return "success" as const;
    case "failed":
      return "destructive" as const;
    case "running":
      return "warning" as const;
    default:
      return "secondary" as const;
  }
}

export function RunSidebar({
  runs,
  activeRunId,
  isLoading,
  collapsed,
  onSelectRun,
  onNewRun,
}: RunSidebarProps) {
  if (collapsed) {
    return null;
  }

  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-border bg-card">
      <div className="p-3">
        <Button variant="outline" className="w-full justify-start gap-2" size="sm" onClick={onNewRun}>
          <Plus className="h-4 w-4" />
          New run
        </Button>
      </div>
      <Separator />
      <ScrollArea className="flex-1">
        <div className="space-y-0.5 p-2">
          {isLoading && <p className="px-2 py-4 text-xs text-muted-foreground">Loading…</p>}
          {!isLoading && runs.length === 0 && (
            <p className="px-2 py-4 text-xs text-muted-foreground">No runs yet.</p>
          )}
          {runs.map((run) => (
            <button
              key={run.id}
              type="button"
              className={cn(
                "w-full rounded-md px-2 py-2 text-left transition-colors hover:bg-accent",
                activeRunId === run.id && "bg-accent",
              )}
              onClick={() => onSelectRun(run.id)}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="truncate text-sm">{run.product}</span>
                <Badge variant={statusVariant(run.status)} className="shrink-0 text-[10px]">
                  {run.status}
                </Badge>
              </div>
              <p className="mt-0.5 truncate text-xs text-muted-foreground">
                #{run.id} · {run.elapsed_seconds ? `${run.elapsed_seconds.toFixed(1)}s` : "—"}
              </p>
            </button>
          ))}
        </div>
      </ScrollArea>
    </aside>
  );
}
