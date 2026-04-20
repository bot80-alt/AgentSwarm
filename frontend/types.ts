export type UserRole = "developer" | "client";
export type TaskStatus = "pending" | "executing" | "judging" | "completed" | "failed";
export type TransactionType = "escrow_locked" | "fee_released" | "refund_issued";

export type User = {
  id: number;
  username: string;
  wallet_balance: number;
  role: UserRole;
};

export type Agent = {
  id: number;
  name: string;
  description: string;
  creator_id: number;
  execution_fee: number;
};

export type TaskRead = {
  id: number;
  client_id: number;
  agent_id: number;
  prompt: string;
  success_criteria: string;
  status: TaskStatus;
  escrow_amount: number;
  output_text: string | null;
  judge_feedback: string | null;
};

export type Transaction = {
  id: number;
  task_id: number;
  amount: number;
  type: TransactionType;
};

export type TaskDetail = TaskRead & {
  client: User;
  agent: Agent;
  transactions: Transaction[];
};

export type SeedResponse = {
  message: string;
  client: User;
  developer: User;
  agents: Agent[];
};

export type EvaluationResponse = {
  passed: boolean;
  reasoning: string;
  task: TaskDetail;
};

export type TaskCreateInput = {
  client_id: number;
  agent_id: number;
  prompt: string;
  success_criteria: string;
};
