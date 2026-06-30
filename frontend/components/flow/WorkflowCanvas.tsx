"use client";

import {
  Background,
  BackgroundVariant,
  Panel,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
  type NodeTypes,
} from "@xyflow/react";
import { useEffect, useMemo } from "react";

import { ZoomSlider } from "@/components/ui/zoom-slider";
import type { ExecutionMode, WorkflowNodeStatus, WorkflowTopology } from "@/types";

import { AgentNode } from "./AgentNode";
import { topologyToFlow } from "./topologyToFlow";

const nodeTypes: NodeTypes = {
  agent: AgentNode,
};

type WorkflowCanvasProps = {
  topology: WorkflowTopology;
  nodeStatus: Record<string, WorkflowNodeStatus>;
  nodeMeta: Record<string, { model: string; execution_mode: ExecutionMode }>;
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string) => void;
};

function FitViewOnLoad() {
  const { fitView } = useReactFlow();

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void fitView({ padding: 0.2, duration: 300 });
    }, 50);
    return () => window.clearTimeout(timer);
  }, [fitView]);

  return null;
}

function WorkflowCanvasInner({
  topology,
  nodeStatus,
  nodeMeta,
  selectedNodeId,
  onSelectNode,
}: WorkflowCanvasProps) {
  const { nodes, edges } = useMemo(
    () => topologyToFlow(topology, nodeStatus, nodeMeta, selectedNodeId),
    [topology, nodeStatus, nodeMeta, selectedNodeId],
  );

  return (
    <div className="h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable
        panOnScroll
        zoomOnScroll
        minZoom={0.3}
        maxZoom={1.5}
        onNodeClick={(_, node) => onSelectNode(node.id)}
        proOptions={{ hideAttribution: true }}
        fitView
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="hsl(0 0% 20%)" />
        <FitViewOnLoad />
        <Panel position="bottom-right" className="!m-4">
          <ZoomSlider />
        </Panel>
      </ReactFlow>
    </div>
  );
}

export function WorkflowCanvas(props: WorkflowCanvasProps) {
  return (
    <ReactFlowProvider>
      <WorkflowCanvasInner {...props} />
    </ReactFlowProvider>
  );
}
