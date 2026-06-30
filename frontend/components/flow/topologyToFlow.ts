import dagre from "@dagrejs/dagre";
import type { Edge, Node } from "@xyflow/react";

import type { ExecutionMode, WorkflowNodeStatus, WorkflowTopology } from "@/types";

export type AgentNodeData = {
  label: string;
  model: string;
  executionMode: ExecutionMode;
  status: WorkflowNodeStatus;
  selected: boolean;
};

const NODE_WIDTH = 200;
const NODE_HEIGHT = 72;

export function topologyToFlow(
  topology: WorkflowTopology,
  nodeStatus: Record<string, WorkflowNodeStatus>,
  nodeMeta: Record<string, { model: string; execution_mode: ExecutionMode }>,
  selectedNodeId: string | null,
): { nodes: Node<AgentNodeData>[]; edges: Edge[] } {
  const graph = new dagre.graphlib.Graph();
  graph.setDefaultEdgeLabel(() => ({}));
  graph.setGraph({ rankdir: "TB", nodesep: 48, ranksep: 72 });

  for (const node of topology.nodes) {
    graph.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  }

  for (const edge of topology.edges) {
    graph.setEdge(edge.from, edge.to);
  }

  dagre.layout(graph);

  const nodes: Node<AgentNodeData>[] = topology.nodes.map((node) => {
    const position = graph.node(node.id);
    const meta = nodeMeta[node.id];
    return {
      id: node.id,
      type: "agent",
      position: {
        x: position.x - NODE_WIDTH / 2,
        y: position.y - NODE_HEIGHT / 2,
      },
      data: {
        label: node.name,
        model: meta?.model ?? node.model,
        executionMode: meta?.execution_mode ?? node.execution_mode,
        status: nodeStatus[node.id] ?? "pending",
        selected: selectedNodeId === node.id,
      },
    };
  });

  const edges: Edge[] = topology.edges.map((edge, index) => ({
    id: `e-${edge.from}-${edge.to}-${index}`,
    source: edge.from,
    target: edge.to,
    type: "smoothstep",
    animated: nodeStatus[edge.to] === "running",
    style: { stroke: "hsl(var(--border))", strokeWidth: 1.5 },
  }));

  return { nodes, edges };
}
