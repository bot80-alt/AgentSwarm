"use client";

import { Position, type Node, type NodeProps } from "@xyflow/react";
import { memo } from "react";

import { BaseHandle } from "@/components/ui/base-handle";
import { BaseNode, BaseNodeContent, BaseNodeFooter, BaseNodeHeader } from "@/components/ui/base-node";
import { StatusIndicator } from "@/components/ui/status-indicator";
import { cn } from "@/lib/utils";

import type { AgentNodeData } from "./topologyToFlow";

function AgentNodeComponent({ data }: NodeProps<Node<AgentNodeData>>) {
  return (
    <BaseNode
      className={cn(
        "min-w-[180px]",
        data.selected && "ring-2 ring-ring ring-offset-2 ring-offset-background",
      )}
    >
      <BaseHandle type="target" position={Position.Top} />
      <BaseNodeHeader>
        <StatusIndicator status={data.status} />
        <span className="truncate text-sm font-medium">{data.label}</span>
      </BaseNodeHeader>
      <BaseNodeContent>
        <p className="truncate text-xs text-muted-foreground">{data.model}</p>
      </BaseNodeContent>
      <BaseNodeFooter>
        <span className="capitalize">{data.executionMode}</span>
      </BaseNodeFooter>
      <BaseHandle type="source" position={Position.Bottom} />
    </BaseNode>
  );
}

export const AgentNode = memo(AgentNodeComponent);
