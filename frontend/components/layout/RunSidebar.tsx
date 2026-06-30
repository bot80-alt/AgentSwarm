"use client";

import { Plus } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import type { WorkflowRunSummary, WorkflowRunStatus } from "@/types";

const SIDEBAR_WIDTH_KEY = "swarm-sidebar-width";
const DEFAULT_WIDTH = 256;
const MIN_WIDTH = 200;
const MAX_WIDTH = 480;

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

function readStoredWidth(): number {
  if (typeof window === "undefined") {
    return DEFAULT_WIDTH;
  }
  const stored = Number(localStorage.getItem(SIDEBAR_WIDTH_KEY));
  if (Number.isFinite(stored) && stored >= MIN_WIDTH && stored <= MAX_WIDTH) {
    return stored;
  }
  return DEFAULT_WIDTH;
}

export function RunSidebar({
  runs,
  activeRunId,
  isLoading,
  collapsed,
  onSelectRun,
  onNewRun,
}: RunSidebarProps) {
  const [width, setWidth] = useState(DEFAULT_WIDTH);
  const isResizing = useRef(false);
  const startX = useRef(0);
  const startWidth = useRef(DEFAULT_WIDTH);

  useEffect(() => {
    setWidth(readStoredWidth());
  }, []);

  const handleResizeMove = useCallback((event: MouseEvent) => {
    if (!isResizing.current) {
      return;
    }
    const next = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, startWidth.current + event.clientX - startX.current));
    setWidth(next);
  }, []);

  const handleResizeEnd = useCallback(() => {
    if (!isResizing.current) {
      return;
    }
    isResizing.current = false;
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
    window.removeEventListener("mousemove", handleResizeMove);
    window.removeEventListener("mouseup", handleResizeEnd);
    setWidth((current) => {
      localStorage.setItem(SIDEBAR_WIDTH_KEY, String(current));
      return current;
    });
  }, [handleResizeMove]);

  const handleResizeStart = useCallback(
    (event: React.MouseEvent) => {
      event.preventDefault();
      isResizing.current = true;
      startX.current = event.clientX;
      startWidth.current = width;
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
      window.addEventListener("mousemove", handleResizeMove);
      window.addEventListener("mouseup", handleResizeEnd);
    },
    [width, handleResizeMove, handleResizeEnd],
  );

  useEffect(() => {
    return () => {
      window.removeEventListener("mousemove", handleResizeMove);
      window.removeEventListener("mouseup", handleResizeEnd);
    };
  }, [handleResizeMove, handleResizeEnd]);

  if (collapsed) {
    return null;
  }

  return (
    <aside
      className="relative flex shrink-0 flex-col border-r border-border bg-card"
      style={{ width }}
    >
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

      <div
        role="separator"
        aria-orientation="vertical"
        aria-label="Resize sidebar"
        onMouseDown={handleResizeStart}
        className="absolute -right-1 top-0 z-10 h-full w-2 cursor-col-resize touch-none hover:bg-border/60 active:bg-border"
      />
    </aside>
  );
}
