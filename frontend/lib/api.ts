import type {
  ModelOption,
  SwarmHealth,
  WorkflowRun,
  WorkflowRunCreateInput,
  WorkflowRunSummary,
  WorkflowTemplate,
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
  swarmHealth: () => request<SwarmHealth>("/swarm/health"),
  listModels: () => request<ModelOption[]>("/swarm/models"),
  listTemplates: () => request<WorkflowTemplate[]>("/swarm/templates"),
  getTemplate: (templateId: string) => request<WorkflowTemplate>(`/swarm/templates/${templateId}`),
  createRun: (payload: WorkflowRunCreateInput) =>
    request<WorkflowRun>("/swarm/runs", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listRuns: () => request<WorkflowRunSummary[]>("/swarm/runs"),
  getRun: (runId: number) => request<WorkflowRun>(`/swarm/runs/${runId}`),
};
