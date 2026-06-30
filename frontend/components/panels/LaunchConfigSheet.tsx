"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";
import type { SwarmHealth, WorkflowTemplate } from "@/types";

type LaunchConfigSheetProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  template: WorkflowTemplate | null;
  targetAudience: string;
  brandVoice: string;
  mcpWorkspace: string;
  health: SwarmHealth | null;
  disabled?: boolean;
  onTargetAudienceChange: (value: string) => void;
  onBrandVoiceChange: (value: string) => void;
  onMcpWorkspaceChange: (value: string) => void;
};

export function LaunchConfigSheet({
  open,
  onOpenChange,
  template,
  targetAudience,
  brandVoice,
  mcpWorkspace,
  health,
  disabled,
  onTargetAudienceChange,
  onBrandVoiceChange,
  onMcpWorkspaceChange,
}: LaunchConfigSheetProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Launch settings</SheetTitle>
          <SheetDescription>Global context injected into agent prompts.</SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-4">
          <div className="space-y-2">
            <Label>Template</Label>
            <Input value={template?.name ?? ""} readOnly disabled />
          </div>

          <div className="space-y-2">
            <Label htmlFor="target-audience">Target audience</Label>
            <Textarea
              id="target-audience"
              value={targetAudience}
              onChange={(e) => onTargetAudienceChange(e.target.value)}
              disabled={disabled}
              rows={3}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="brand-voice">Brand voice</Label>
            <Input
              id="brand-voice"
              value={brandVoice}
              onChange={(e) => onBrandVoiceChange(e.target.value)}
              disabled={disabled}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="mcp-workspace">MCP workspace</Label>
            <Input
              id="mcp-workspace"
              value={mcpWorkspace}
              onChange={(e) => onMcpWorkspaceChange(e.target.value)}
              placeholder={health?.mcp_workspace ?? "Repo root (default)"}
              disabled={disabled}
            />
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
