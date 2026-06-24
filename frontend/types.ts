export type WorkflowNodeStatus = "pending" | "running" | "completed" | "failed";
export type WorkflowRunStatus = "pending" | "running" | "completed" | "failed";
export type ExecutionMode = "parallel" | "serial";

export type WorkflowNodeTopology = {
  id: string;
  name: string;
  dependencies: string[];
  output_key: string;
  tools: string[];
  persona: string;
  task: string;
  model: string;
  execution_mode: ExecutionMode;
};

export type WorkflowEdge = {
  from: string;
  to: string;
};

export type WorkflowTopology = {
  name: string;
  layers: string[][];
  nodes: WorkflowNodeTopology[];
  edges: WorkflowEdge[];
};

export type WorkflowTemplate = {
  id: string;
  name: string;
  description: string;
  default_product: string;
  default_target_audience: string;
  default_brand_voice: string;
  final_output_key: string;
  topology: WorkflowTopology;
};

export type ModelOption = {
  id: string;
  label: string;
  provider: string;
};

export type EditableNodeConfig = {
  node_id: string;
  task: string;
  persona: string;
  model: string;
  execution_mode: ExecutionMode;
};

export type WorkflowNodeRun = {
  id: number;
  node_id: string;
  node_name: string;
  output_key: string;
  task: string;
  persona: string;
  configured_model: string;
  execution_mode: ExecutionMode;
  status: WorkflowNodeStatus;
  content: string | null;
  model: string | null;
  used_mock: boolean;
  started_at: string | null;
  finished_at: string | null;
};

export type WorkflowRun = {
  id: number;
  template_id: string;
  product: string;
  target_audience: string;
  brand_voice: string;
  status: WorkflowRunStatus;
  elapsed_seconds: number | null;
  final_output_key: string | null;
  final_output_content: string | null;
  error_message: string | null;
  created_at: string;
  node_runs: WorkflowNodeRun[];
};

export type WorkflowRunSummary = {
  id: number;
  template_id: string;
  product: string;
  status: WorkflowRunStatus;
  elapsed_seconds: number | null;
  created_at: string;
};

export type WorkflowRunCreateInput = {
  template_id: string;
  product: string;
  target_audience: string;
  brand_voice: string;
  nodes: EditableNodeConfig[];
};

export type SwarmHealth = {
  message: string;
  templates: string[];
  llm_mode: string;
};

export type ActivityEntry = {
  id: string;
  timestamp: string;
  kind: "info" | "parallel" | "start" | "finish" | "error" | "complete";
  message: string;
};
