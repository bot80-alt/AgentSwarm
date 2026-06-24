import type { ExecutionMode, WorkflowNodeStatus, WorkflowTopology } from "@/types";

type DagGraphProps = {
  topology: WorkflowTopology;
  nodeStatus: Record<string, WorkflowNodeStatus>;
  nodeMeta: Record<string, { model: string; execution_mode: ExecutionMode }>;
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string) => void;
};

type NodeLayout = {
  id: string;
  name: string;
  x: number;
  y: number;
  layer: number;
};

const NODE_WIDTH = 168;
const NODE_HEIGHT = 88;
const LAYER_GAP = 120;
const NODE_GAP = 40;

function buildLayout(topology: WorkflowTopology): NodeLayout[] {
  const nodeMap = new Map(topology.nodes.map((node) => [node.id, node]));
  const layouts: NodeLayout[] = [];

  topology.layers.forEach((layer, layerIndex) => {
    const layerWidth = layer.length * NODE_WIDTH + (layer.length - 1) * NODE_GAP;
    const startX = -layerWidth / 2 + NODE_WIDTH / 2;

    layer.forEach((nodeId, index) => {
      const node = nodeMap.get(nodeId);
      if (!node) {
        return;
      }
      layouts.push({
        id: nodeId,
        name: node.name,
        x: startX + index * (NODE_WIDTH + NODE_GAP),
        y: layerIndex * LAYER_GAP,
        layer: layerIndex,
      });
    });
  });

  return layouts;
}

function statusColor(status: WorkflowNodeStatus) {
  switch (status) {
    case "running":
      return "var(--node-running)";
    case "completed":
      return "var(--node-done)";
    case "failed":
      return "var(--node-failed)";
    default:
      return "var(--node-pending)";
  }
}

export function DagGraph({ topology, nodeStatus, nodeMeta, selectedNodeId, onSelectNode }: DagGraphProps) {
  const layouts = buildLayout(topology);
  const layoutMap = new Map(layouts.map((layout) => [layout.id, layout]));
  const width = Math.max(
    720,
    ...layouts.map((layout) => Math.abs(layout.x) * 2 + NODE_WIDTH),
  );
  const height = topology.layers.length * LAYER_GAP + NODE_HEIGHT + 40;
  const originX = width / 2;
  const originY = 36;

  return (
    <div className="dag-shell">
      <svg
        className="dag-canvas"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label="Workflow DAG visualization"
      >
        <defs>
          <marker
            id="arrowhead"
            markerWidth="8"
            markerHeight="8"
            refX="7"
            refY="4"
            orient="auto"
          >
            <polygon points="0 0, 8 4, 0 8" fill="var(--edge-color)" />
          </marker>
        </defs>

        {topology.edges.map((edge) => {
          const from = layoutMap.get(edge.from);
          const to = layoutMap.get(edge.to);
          if (!from || !to) {
            return null;
          }

          const x1 = originX + from.x;
          const y1 = originY + from.y + NODE_HEIGHT / 2;
          const x2 = originX + to.x;
          const y2 = originY + to.y - NODE_HEIGHT / 2;
          const midY = (y1 + y2) / 2;

          return (
            <path
              key={`${edge.from}-${edge.to}`}
              className="dag-edge"
              d={`M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`}
              markerEnd="url(#arrowhead)"
            />
          );
        })}

        {layouts.map((layout) => {
          const status = nodeStatus[layout.id] ?? "pending";
          const meta = nodeMeta[layout.id];
          const isSelected = selectedNodeId === layout.id;
          const x = originX + layout.x - NODE_WIDTH / 2;
          const y = originY + layout.y - NODE_HEIGHT / 2;

          return (
            <g
              key={layout.id}
              className={`dag-node-group ${status} ${isSelected ? "selected" : ""}`}
              transform={`translate(${x}, ${y})`}
              onClick={() => onSelectNode(layout.id)}
            >
              <rect
                className="dag-node-bg"
                width={NODE_WIDTH}
                height={NODE_HEIGHT}
                rx={14}
                fill={statusColor(status)}
              />
              <text className="dag-node-layer" x={14} y={20}>
                Layer {layout.layer + 1}
              </text>
              <text className="dag-node-title" x={14} y={40}>
                {layout.name}
              </text>
              <text className="dag-node-status" x={14} y={58}>
                {status} | {meta?.execution_mode ?? "parallel"}
              </text>
              <text className="dag-node-model" x={14} y={74}>
                {meta?.model ?? "default"}
              </text>
              {status === "running" ? (
                <circle className="dag-node-pulse" cx={NODE_WIDTH - 18} cy={18} r={6} />
              ) : null}
            </g>
          );
        })}
      </svg>

      <div className="dag-legend">
        <span><i className="dot pending" /> Pending</span>
        <span><i className="dot running" /> Running</span>
        <span><i className="dot completed" /> Completed</span>
        <span><i className="dot failed" /> Failed</span>
      </div>
    </div>
  );
}
