"use client";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";
import type {
  EditableNodeConfig,
  ExecutionMode,
  ModelOption,
  WorkflowNodeRun,
  WorkflowNodeTopology,
} from "@/types";

import { OutputPanel } from "./OutputPanel";

type NodeInspectorSheetProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  node: WorkflowNodeTopology | null;
  config: EditableNodeConfig | null;
  runNode: WorkflowNodeRun | null;
  models: ModelOption[];
  disabled?: boolean;
  onChange: (nodeId: string, patch: Partial<EditableNodeConfig>) => void;
  onResetNodes?: () => void;
};

export function NodeInspectorSheet({
  open,
  onOpenChange,
  node,
  config,
  runNode,
  models,
  disabled,
  onChange,
  onResetNodes,
}: NodeInspectorSheetProps) {
  if (!node || !config) {
    return (
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent side="right" className="sm:max-w-md">
          <SheetHeader>
            <SheetTitle>Node</SheetTitle>
            <SheetDescription>Select a node on the graph to configure it.</SheetDescription>
          </SheetHeader>
        </SheetContent>
      </Sheet>
    );
  }

  const hasFilesystem = config.tools.includes("filesystem");
  const hasCasper = config.tools.includes("casper");

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>{node.name}</SheetTitle>
          <SheetDescription>Configure model, execution mode, and prompt for {node.id}.</SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-4">
          <div className="space-y-2">
            <Label>Model</Label>
            <Select
              value={config.model}
              disabled={disabled}
              onValueChange={(value) => onChange(node.id, { model: value })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {models.map((model) => (
                  <SelectItem key={model.id} value={model.id}>
                    {model.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Execution with siblings</Label>
            <div className="flex gap-2">
              {(["parallel", "serial"] as ExecutionMode[]).map((mode) => (
                <Button
                  key={mode}
                  type="button"
                  variant={config.execution_mode === mode ? "default" : "outline"}
                  size="sm"
                  disabled={disabled}
                  onClick={() => onChange(node.id, { execution_mode: mode })}
                  className="capitalize"
                >
                  {mode}
                </Button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={hasFilesystem}
                disabled={disabled}
                onChange={(e) => {
                  const tools = e.target.checked
                    ? [...new Set([...config.tools, "filesystem"])]
                    : config.tools.filter((t) => t !== "filesystem");
                  onChange(node.id, { tools });
                }}
                className="rounded border-border"
              />
              MCP local filesystem
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={hasCasper}
                disabled={disabled}
                onChange={(e) => {
                  const tools = e.target.checked
                    ? [...new Set([...config.tools, "casper"])]
                    : config.tools.filter((t) => t !== "casper");
                  onChange(node.id, { tools });
                }}
                className="rounded border-border"
              />
              Casper MCP tools
            </label>
          </div>

          <div className="space-y-2">
            <Label htmlFor="persona">Persona</Label>
            <Textarea
              id="persona"
              value={config.persona}
              disabled={disabled}
              onChange={(e) => onChange(node.id, { persona: e.target.value })}
              rows={2}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="task">Task prompt</Label>
            <Textarea
              id="task"
              value={config.task}
              disabled={disabled}
              onChange={(e) => onChange(node.id, { task: e.target.value })}
              rows={5}
            />
          </div>

          {!disabled && onResetNodes && (
            <Button variant="outline" size="sm" onClick={onResetNodes}>
              Reset all nodes to defaults
            </Button>
          )}

          <OutputPanel
            title="Node output"
            subtitle={runNode?.node_name ?? node.name}
            content={runNode?.content}
            emptyMessage="Output appears when this node completes."
          />
        </div>
      </SheetContent>
    </Sheet>
  );
}
