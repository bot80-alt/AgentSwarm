"use client";

import { Settings } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type LaunchBarProps = {
  product: string;
  onProductChange: (value: string) => void;
  onLaunch: () => void;
  onOpenSettings: () => void;
  isLaunching: boolean;
  isRunLocked: boolean;
};

export function LaunchBar({
  product,
  onProductChange,
  onLaunch,
  onOpenSettings,
  isLaunching,
  isRunLocked,
}: LaunchBarProps) {
  const disabled = isLaunching || isRunLocked || !product.trim();

  return (
    <div className="shrink-0 border-t border-border bg-background p-3">
      <div className="mx-auto flex max-w-3xl items-center gap-2">
        <Input
          value={product}
          onChange={(e) => onProductChange(e.target.value)}
          placeholder="Product name"
          disabled={isRunLocked}
          className="flex-1"
          onKeyDown={(e) => {
            if (e.key === "Enter" && !disabled) {
              e.preventDefault();
              onLaunch();
            }
          }}
        />
        <Button variant="outline" size="icon" onClick={onOpenSettings} aria-label="Launch settings">
          <Settings className="h-4 w-4" />
        </Button>
        <Button onClick={onLaunch} disabled={disabled} className="shrink-0">
          {isLaunching ? "Launching…" : isRunLocked ? "Running…" : "Launch"}
        </Button>
      </div>
    </div>
  );
}
