import type {
  Agent,
  EvaluationResponse,
  SeedResponse,
  TaskCreateInput,
  TaskDetail,
  TaskRead,
} from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type RequestInitWithBody = RequestInit & {
  body?: string;
};

async function request<T>(path: string, init?: RequestInitWithBody): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = "Request failed.";
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      detail = response.statusText || detail;
    }
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

export const api = {
  seed: () => request<SeedResponse>("/users/seed", { method: "POST" }),
  listAgents: () => request<Agent[]>("/agents"),
  createTask: (payload: TaskCreateInput) =>
    request<TaskRead>("/tasks", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  executeTask: (taskId: number) =>
    request<{ message: string; task: TaskRead }>(`/tasks/${taskId}/execute`, {
      method: "POST",
    }),
  evaluateTask: (taskId: number) =>
    request<EvaluationResponse>(`/tasks/${taskId}/evaluate`, {
      method: "POST",
    }),
  getTask: (taskId: number) => request<TaskDetail>(`/tasks/${taskId}`),
};
