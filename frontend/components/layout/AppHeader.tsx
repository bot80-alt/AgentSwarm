"use client";

import { PanelLeft } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import type { SwarmHealth } from "@/types";

type AppHeaderProps = {
  activeView: "swarm" | "competitions";
  onViewChange: (view: "swarm" | "competitions") => void;
  health: SwarmHealth | null;
  completedCount: number;
  totalNodes: number;
  activeRunId: number | null;
  activeRunStatus: string | null;
  onToggleSidebar: () => void;
};

export function AppHeader({
  activeView,
  onViewChange,
  health,
  completedCount,
  totalNodes,
  activeRunId,
  activeRunStatus,
  onToggleSidebar,
}: AppHeaderProps) {
  const llmLive = health?.llm_mode === "openai";

  return (
    <header className="flex h-12 shrink-0 items-center gap-3 border-b border-border px-3">
      <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0" onClick={onToggleSidebar} aria-label="Toggle sidebar">
        <PanelLeft className="h-4 w-4" />
      </Button>

      <span className="text-sm font-medium">Swarm</span>

      <nav className="flex items-center gap-1 rounded-md bg-secondary p-0.5">
        <button
          type="button"
          className={cn(
            "rounded px-3 py-1 text-xs transition-colors",
            activeView === "swarm" ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground",
          )}
          onClick={() => onViewChange("swarm")}
        >
          Runs
        </button>
        <button
          type="button"
          className={cn(
            "rounded px-3 py-1 text-xs transition-colors",
            activeView === "competitions"
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground",
          )}
          onClick={() => onViewChange("competitions")}
        >
          Competitions
        </button>
      </nav>

      <div className="ml-auto flex items-center gap-3 text-xs text-muted-foreground">
        <Tooltip>
          <TooltipTrigger asChild>
            <span className="flex items-center gap-1.5">
              <span className={cn("h-1.5 w-1.5 rounded-full", llmLive ? "bg-emerald-400" : "bg-amber-400")} />
              {health?.llm_mode ?? "…"}
            </span>
          </TooltipTrigger>
          <TooltipContent>
            MCP: {health?.mcp_enabled ? health.mcp_workspace ?? "repo root" : "off"}
          </TooltipContent>
        </Tooltip>

        {totalNodes > 0 && (
          <span>
            {completedCount}/{totalNodes} nodes
          </span>
        )}

        {activeRunId && (
          <span>
            #{activeRunId} {activeRunStatus}
          </span>
        )}
      </div>
    </header>
  );
}
