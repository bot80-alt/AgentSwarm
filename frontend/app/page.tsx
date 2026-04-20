"use client";

import { FormEvent, useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { Agent, SeedResponse, TaskCreateInput, TaskDetail } from "@/types";

const defaultPrompt =
  "Draft a short proposal for a retail analytics pilot focused on improving in-store conversions.";
const defaultCriteria =
  "Keep it concise, professional, and include deliverables, timeline, and expected business impact.";

function currency(value: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

function statusClass(status: string) {
  return `status-pill ${status}`;
}

export default function HomePage() {
  const [seedData, setSeedData] = useState<SeedResponse | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);
  const [taskDetail, setTaskDetail] = useState<TaskDetail | null>(null);
  const [taskIdInput, setTaskIdInput] = useState("");
  const [prompt, setPrompt] = useState(defaultPrompt);
  const [successCriteria, setSuccessCriteria] = useState(defaultCriteria);
  const [isBusy, setIsBusy] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const selectedAgent = agents.find((agent) => agent.id === selectedAgentId) ?? null;

  useEffect(() => {
    void loadAgents();
  }, []);

  async function loadAgents() {
    try {
      const nextAgents = await api.listAgents();
      setAgents(nextAgents);
      setSelectedAgentId((current) => current ?? nextAgents[0]?.id ?? null);
    } catch (error) {
      setMessage({
        type: "error",
        text: error instanceof Error ? error.message : "Could not load agents.",
      });
    }
  }

  function showMessage(type: "success" | "error", text: string) {
    setMessage({ type, text });
  }

  async function runAction<T>(action: () => Promise<T>) {
    setIsBusy(true);
    setMessage(null);
    try {
      return await action();
    } catch (error) {
      showMessage("error", error instanceof Error ? error.message : "Something went wrong.");
      return null;
    } finally {
      setIsBusy(false);
    }
  }

  async function handleSeed() {
    const result = await runAction(() => api.seed());
    if (!result) {
      return;
    }

    setSeedData(result);
    setAgents(result.agents);
    setSelectedAgentId(result.agents[0]?.id ?? null);
    showMessage("success", result.message);
  }

  async function handleCreateTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedAgentId) {
      showMessage("error", "Choose an agent before creating a task.");
      return;
    }

    const clientId = seedData?.client.id ?? 1;
    const payload: TaskCreateInput = {
      client_id: clientId,
      agent_id: selectedAgentId,
      prompt,
      success_criteria: successCriteria,
    };

    const createdTask = await runAction(() => api.createTask(payload));
    if (!createdTask) {
      return;
    }

    setTaskIdInput(String(createdTask.id));
    const task = await runAction(() => api.getTask(createdTask.id));
    if (task) {
      setTaskDetail(task);
      showMessage("success", `Task #${createdTask.id} created and escrow locked.`);
    }
  }

  async function handleLoadTask() {
    const taskId = Number(taskIdInput);
    if (!taskId) {
      showMessage("error", "Enter a valid task id.");
      return;
    }

    const task = await runAction(() => api.getTask(taskId));
    if (task) {
      setTaskDetail(task);
      showMessage("success", `Loaded task #${task.id}.`);
    }
  }

  async function handleExecuteTask() {
    if (!taskDetail) {
      showMessage("error", "Load or create a task first.");
      return;
    }

    const result = await runAction(() => api.executeTask(taskDetail.id));
    if (!result) {
      return;
    }

    const refreshedTask = await runAction(() => api.getTask(taskDetail.id));
    if (refreshedTask) {
      setTaskDetail(refreshedTask);
      showMessage("success", result.message);
    }
  }

  async function handleEvaluateTask() {
    if (!taskDetail) {
      showMessage("error", "Load or create a task first.");
      return;
    }

    const result = await runAction(() => api.evaluateTask(taskDetail.id));
    if (!result) {
      return;
    }

    setTaskDetail(result.task);
    showMessage(
      result.passed ? "success" : "error",
      result.passed
        ? "Judge approved the task and released the fee."
        : "Judge rejected the task and refunded the client.",
    );
  }

  return (
    <main className="page-shell">
      <section className="hero">
        <div className="hero-kicker">Escrow-backed agent hiring</div>
        <h1>Agent Swarm Marketplace</h1>
        <p>
          This frontend lets you seed demo users, choose an agent, lock escrow, execute the
          task, and run an independent evaluation against your FastAPI marketplace backend.
        </p>

        <div className="hero-grid">
          <article className="stat-card">
            <p className="stat-label">Demo client wallet</p>
            <p className="stat-value">
              {seedData ? currency(seedData.client.wallet_balance) : "Seed required"}
            </p>
          </article>
          <article className="stat-card">
            <p className="stat-label">Developer wallet</p>
            <p className="stat-value">
              {seedData ? currency(seedData.developer.wallet_balance) : "Seed required"}
            </p>
          </article>
          <article className="stat-card">
            <p className="stat-label">Published agents</p>
            <p className="stat-value">{agents.length}</p>
          </article>
        </div>
      </section>

      <section className="content-grid">
        <div className="stack">
          <section className="panel">
            <div className="section-heading">
              <div>
                <h2>Bootstrap demo state</h2>
                <p>
                  Seed the client, developer, and starter agents. If the backend already has data,
                  this safely reuses it.
                </p>
              </div>
              <button className="primary-button" type="button" onClick={handleSeed} disabled={isBusy}>
                {isBusy ? "Working..." : "Seed marketplace"}
              </button>
            </div>

            {message ? (
              <div className={`message ${message.type}`}>{message.text}</div>
            ) : null}
          </section>

          <section className="panel">
            <div className="section-heading">
              <div>
                <h2>Available agents</h2>
                <p>Pick one agent to hire for the next task.</p>
              </div>
              <button
                className="secondary-button"
                type="button"
                onClick={() => void loadAgents()}
                disabled={isBusy}
              >
                Refresh list
              </button>
            </div>

            {agents.length ? (
              <div className="agent-list">
                {agents.map((agent) => (
                  <button
                    key={agent.id}
                    type="button"
                    className={`agent-card ${selectedAgentId === agent.id ? "selected" : ""}`}
                    onClick={() => setSelectedAgentId(agent.id)}
                  >
                    <div className="agent-card-header">
                      <div>
                        <h3>{agent.name}</h3>
                        <p>{agent.description}</p>
                      </div>
                      <span className="price-pill">{currency(agent.execution_fee)}</span>
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                No agents are loaded yet. Seed the marketplace or start the backend first.
              </div>
            )}
          </section>
        </div>

        <div className="stack">
          <section className="panel">
            <div className="section-heading">
              <div>
                <h2>Create task</h2>
                <p>
                  Escrow will lock the selected agent fee as soon as you submit the task.
                  {selectedAgent ? ` Current fee: ${currency(selectedAgent.execution_fee)}.` : ""}
                </p>
              </div>
            </div>

            <form className="field-grid" onSubmit={handleCreateTask}>
              <div className="field">
                <label htmlFor="agent">Selected agent</label>
                <select
                  id="agent"
                  value={selectedAgentId ?? ""}
                  onChange={(event) => setSelectedAgentId(Number(event.target.value))}
                >
                  <option value="" disabled>
                    Choose an agent
                  </option>
                  {agents.map((agent) => (
                    <option key={agent.id} value={agent.id}>
                      {agent.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="field">
                <label htmlFor="prompt">Task prompt</label>
                <textarea
                  id="prompt"
                  value={prompt}
                  onChange={(event) => setPrompt(event.target.value)}
                />
              </div>

              <div className="field">
                <label htmlFor="criteria">Success criteria</label>
                <textarea
                  id="criteria"
                  value={successCriteria}
                  onChange={(event) => setSuccessCriteria(event.target.value)}
                />
              </div>

              <div className="button-row">
                <button className="primary-button" type="submit" disabled={isBusy}>
                  {isBusy ? "Submitting..." : "Create task"}
                </button>
                <button
                  className="ghost-button"
                  type="button"
                  onClick={() => {
                    setPrompt(defaultPrompt);
                    setSuccessCriteria(defaultCriteria);
                  }}
                  disabled={isBusy}
                >
                  Reset copy
                </button>
              </div>
            </form>
          </section>

          <section className="panel">
            <div className="section-heading">
              <div>
                <h2>Load task</h2>
                <p>Fetch any existing task by id and continue its workflow from the UI.</p>
              </div>
            </div>

            <div className="field-grid">
              <div className="field">
                <label htmlFor="task-id">Task id</label>
                <input
                  id="task-id"
                  value={taskIdInput}
                  onChange={(event) => setTaskIdInput(event.target.value)}
                  placeholder="1"
                />
              </div>

              <div className="button-row">
                <button
                  className="secondary-button"
                  type="button"
                  onClick={handleLoadTask}
                  disabled={isBusy}
                >
                  Load task
                </button>
              </div>
            </div>
          </section>

          <section className="task-card">
            <div className="section-heading">
              <div>
                <h2>Task lifecycle</h2>
                <p>Execute the hired agent, judge the result, and inspect escrow transactions.</p>
              </div>
              {taskDetail ? <span className={statusClass(taskDetail.status)}>{taskDetail.status}</span> : null}
            </div>

            {taskDetail ? (
              <>
                <div className="task-grid">
                  <div className="task-block">
                    <strong>Prompt</strong>
                    <p>{taskDetail.prompt}</p>
                  </div>
                  <div className="task-block">
                    <strong>Success criteria</strong>
                    <p>{taskDetail.success_criteria}</p>
                  </div>
                  <div className="task-block">
                    <strong>Selected agent</strong>
                    <p>{taskDetail.agent.name}</p>
                  </div>
                  <div className="task-block">
                    <strong>Escrow remaining</strong>
                    <p>{currency(taskDetail.escrow_amount)}</p>
                  </div>
                </div>

                <div className="task-actions">
                  <button
                    className="primary-button"
                    type="button"
                    onClick={handleExecuteTask}
                    disabled={isBusy || taskDetail.status !== "pending"}
                  >
                    Execute task
                  </button>
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={handleEvaluateTask}
                    disabled={isBusy || taskDetail.status !== "judging"}
                  >
                    Evaluate task
                  </button>
                  <button
                    className="ghost-button"
                    type="button"
                    onClick={handleLoadTask}
                    disabled={isBusy}
                  >
                    Refresh task
                  </button>
                </div>

                <div className="task-block">
                  <strong>Agent output</strong>
                  <p className="task-meta">
                    {taskDetail.output_text ?? "No output yet. Execute the task to generate work."}
                  </p>
                </div>

                <div className="task-block">
                  <strong>Judge feedback</strong>
                  <p className="task-meta">
                    {taskDetail.judge_feedback ?? "No evaluation yet. Evaluate once the task enters judging."}
                  </p>
                </div>

                <div>
                  <strong>Transactions</strong>
                  <div className="transaction-list" style={{ marginTop: 12 }}>
                    {taskDetail.transactions.map((transaction) => (
                      <div className="transaction-item" key={transaction.id}>
                        <span>{transaction.type}</span>
                        <span>{currency(transaction.amount)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div className="empty-state">
                Create a task or load one by id to view the full escrow workflow here.
              </div>
            )}
          </section>
        </div>
      </section>
    </main>
  );
}
