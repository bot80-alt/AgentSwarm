"use client";

import { useReactFlow, useStore } from "@xyflow/react";
import { Minus, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type ZoomSliderProps = {
  className?: string;
};

export function ZoomSlider({ className }: ZoomSliderProps) {
  const { zoomIn, zoomOut, zoomTo } = useReactFlow();
  const zoom = useStore((state) => state.transform[2]);

  return (
    <div
      className={cn(
        "flex items-center gap-1 rounded-lg border border-border bg-card p-1 shadow-sm",
        className,
      )}
    >
      <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => zoomOut()} aria-label="Zoom out">
        <Minus className="h-3.5 w-3.5" />
      </Button>
      <button
        type="button"
        className="min-w-[3rem] text-center text-xs text-muted-foreground hover:text-foreground"
        onClick={() => zoomTo(1)}
      >
        {Math.round(zoom * 100)}%
      </button>
      <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => zoomIn()} aria-label="Zoom in">
        <Plus className="h-3.5 w-3.5" />
      </Button>
    </div>
  );
}
