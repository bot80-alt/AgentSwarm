"use client";

import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import type { ActivityEntry } from "@/types";

type ActivityPanelProps = {
  entries: ActivityEntry[];
};

function kindLabel(kind: ActivityEntry["kind"]) {
  switch (kind) {
    case "parallel":
      return "PARALLEL";
    case "start":
      return "START";
    case "finish":
      return "DONE";
    case "complete":
      return "COMPLETE";
    case "error":
      return "ERROR";
    default:
      return "INFO";
  }
}

function kindColor(kind: ActivityEntry["kind"]) {
  switch (kind) {
    case "parallel":
      return "text-violet-400";
    case "start":
      return "text-sky-400";
    case "finish":
      return "text-emerald-400";
    case "complete":
      return "text-emerald-400";
    case "error":
      return "text-red-400";
    default:
      return "text-muted-foreground";
  }
}

export function ActivityPanel({ entries }: ActivityPanelProps) {
  const [expanded, setExpanded] = useState(false);

  if (entries.length === 0) {
    return null;
  }

  return (
    <div className="shrink-0 border-t border-border">
      <Button
        variant="ghost"
        className="flex h-9 w-full items-center justify-between rounded-none px-4 text-xs text-muted-foreground"
        onClick={() => setExpanded((v) => !v)}
      >
        <span>Activity log ({entries.length})</span>
        {expanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronUp className="h-3.5 w-3.5" />}
      </Button>

      {expanded && (
        <ScrollArea className="max-h-40 border-t border-border">
          <div className="space-y-1 p-3">
            {entries.map((entry) => (
              <article key={entry.id} className="flex gap-3 text-xs">
                <time className="shrink-0 text-muted-foreground">{entry.timestamp}</time>
                <span className={cn("shrink-0 font-medium", kindColor(entry.kind))}>{kindLabel(entry.kind)}</span>
                <p className="text-foreground/80">{entry.message}</p>
              </article>
            ))}
          </div>
        </ScrollArea>
      )}
    </div>
  );
}
