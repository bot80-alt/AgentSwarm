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
  tools: string[];
};

export type WorkflowNodeRun = {
  id: number;
  node_id: string;
  node_name: string;
  output_key: string;
  task: string;
  persona: string;
  configured_model: string;
  configured_tools: string[];
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
  mcp_workspace: string | null;
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
  mcp_workspace?: string | null;
  nodes: EditableNodeConfig[];
};

export type SwarmHealth = {
  message: string;
  templates: string[];
  llm_mode: string;
  mcp_enabled: boolean;
  mcp_workspace: string | null;
};

export type MCPTool = {
  name: string;
  description: string;
  group: string;
};

export type MCPStatus = {
  enabled: boolean;
  workspace_root: string | null;
  tool_groups: string[];
  tools: MCPTool[];
  error: string | null;
};

export type ActivityEntry = {
  id: string;
  timestamp: string;
  kind: "info" | "parallel" | "start" | "finish" | "error" | "complete";
  message: string;
};

export type User = {
  id: number;
  username: string;
  wallet_balance: number;
  role: "developer" | "client";
};

export type Agent = {
  id: number;
  name: string;
  description: string;
  creator_id: number;
  execution_fee: number;
};

export type SeedResponse = {
  message: string;
  client: User;
  developer: User;
  agents: Agent[];
};

export type TaskStatus = "pending" | "executing" | "judging" | "completed" | "failed";

export type Submission = {
  id: number;
  task_id: number;
  agent_id: number;
  output_text: string;
  score: number | null;
  used_mock: boolean;
  submitted_at: string;
};

export type Competition = {
  id: number;
  client_id: number;
  agent_id: number | null;
  prompt: string;
  success_criteria: string;
  status: TaskStatus;
  escrow_amount: number;
  output_text: string | null;
  judge_feedback: string | null;
  competition_mode: boolean;
  bounty_amount: number | null;
  winner_agent_id: number | null;
  casper_account_hash: string | null;
  casper_hold_snapshot: string | null;
  submissions?: Submission[];
  transactions?: { id: number; task_id: number; amount: number; type: string }[];
  winner_agent?: Agent | null;
};

export type CompetitionCreateInput = {
  client_id: number;
  prompt: string;
  success_criteria: string;
  bounty_amount: number;
  casper_account_hash?: string | null;
  agent_ids?: number[] | null;
};

export type CompetitionEvaluateResult = {
  winner_agent_id: number;
  reasoning: string;
  scores: Record<string, number>;
  task: Competition;
};

export type CSPRStatus = {
  enabled: boolean;
  url: string;
  network: string;
  connected: boolean;
  tool_count: number;
  error: string | null;
};
