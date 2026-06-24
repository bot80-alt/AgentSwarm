"use client";

import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";

import { ActivityFeed } from "@/components/ActivityFeed";
import { DagGraph } from "@/components/DagGraph";
import { NodeInspector } from "@/components/NodeInspector";
import { RunHistory } from "@/components/RunHistory";
import { api } from "@/lib/api";
import type {
  ActivityEntry,
  EditableNodeConfig,
  ExecutionMode,
  ModelOption,
  SwarmHealth,
  WorkflowNodeStatus,
  WorkflowNodeTopology,
  WorkflowRun,
  WorkflowRunSummary,
  WorkflowTemplate,
} from "@/types";

function formatTime(value: string | null) {
  if (!value) {
    return "--:--:--";
  }
  return new Intl.DateTimeFormat("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));
}

function configsFromTopology(nodes: WorkflowNodeTopology[]): Record<string, EditableNodeConfig> {
  return Object.fromEntries(
    nodes.map((node) => [
      node.id,
      {
        node_id: node.id,
        task: node.task,
        persona: node.persona,
        model: node.model,
        execution_mode: node.execution_mode,
      },
    ]),
  );
}

function configsFromRun(run: WorkflowRun): Record<string, EditableNodeConfig> {
  return Object.fromEntries(
    run.node_runs.map((node) => [
      node.node_id,
      {
        node_id: node.node_id,
        task: node.task,
        persona: node.persona,
        model: node.configured_model,
        execution_mode: node.execution_mode,
      },
    ]),
  );
}

function buildNodeStatusMap(run: WorkflowRun | null): Record<string, WorkflowNodeStatus> {
  if (!run) {
    return {};
  }
  return Object.fromEntries(run.node_runs.map((node) => [node.node_id, node.status]));
}

function buildActivityLog(run: WorkflowRun | null, template: WorkflowTemplate | null): ActivityEntry[] {
  if (!run || !template) {
    return [];
  }

  const entries: ActivityEntry[] = [
    {
      id: `run-${run.id}-created`,
      timestamp: formatTime(run.created_at),
      kind: "info",
      message: `Workflow run #${run.id} created for "${run.product}".`,
    },
  ];

  const rootIds = new Set(template.topology.layers[0] ?? []);
  const parallelRoots = run.node_runs.filter(
    (node) => rootIds.has(node.node_id) && node.started_at,
  );
  if (parallelRoots.length > 1) {
    entries.push({
      id: `run-${run.id}-parallel`,
      timestamp: formatTime(parallelRoots[0]?.started_at ?? run.created_at),
      kind: "parallel",
      message: `Parallel batch: ${parallelRoots.map((node) => node.node_name).join(", ")}`,
    });
  }

  for (const node of run.node_runs) {
    if (node.started_at) {
      entries.push({
        id: `run-${run.id}-${node.node_id}-start`,
        timestamp: formatTime(node.started_at),
        kind: "start",
        message: `${node.node_name} started (${node.configured_model}, ${node.execution_mode}).`,
      });
    }
    if (node.finished_at) {
      entries.push({
        id: `run-${run.id}-${node.node_id}-finish`,
        timestamp: formatTime(node.finished_at),
        kind: "finish",
        message: `${node.node_name} finished (${node.used_mock ? "mock" : node.model ?? "llm"}).`,
      });
    }
  }

  if (run.status === "completed") {
    entries.push({
      id: `run-${run.id}-complete`,
      timestamp: formatTime(run.node_runs.at(-1)?.finished_at ?? run.created_at),
      kind: "complete",
      message: `Workflow completed in ${run.elapsed_seconds?.toFixed(2) ?? "?"}s.`,
    });
  }

  if (run.status === "failed" && run.error_message) {
    entries.push({
      id: `run-${run.id}-error`,
      timestamp: formatTime(run.node_runs.at(-1)?.finished_at ?? run.created_at),
      kind: "error",
      message: run.error_message,
    });
  }

  return entries.sort((a, b) => a.timestamp.localeCompare(b.timestamp));
}

export default function HomePage() {
  const [health, setHealth] = useState<SwarmHealth | null>(null);
  const [models, setModels] = useState<ModelOption[]>([]);
  const [template, setTemplate] = useState<WorkflowTemplate | null>(null);
  const [nodeConfigs, setNodeConfigs] = useState<Record<string, EditableNodeConfig>>({});
  const [product, setProduct] = useState("");
  const [targetAudience, setTargetAudience] = useState("");
  const [brandVoice, setBrandVoice] = useState("");
  const [activeRun, setActiveRun] = useState<WorkflowRun | null>(null);
  const [recentRuns, setRecentRuns] = useState<WorkflowRunSummary[]>([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState(true);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isLaunching, setIsLaunching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const seenStatusRef = useRef<Record<string, WorkflowNodeStatus>>({});

  const isRunLocked = activeRun?.status === "running" || activeRun?.status === "pending";
  const nodeStatus = useMemo(() => buildNodeStatusMap(activeRun), [activeRun]);
  const activity = useMemo(() => buildActivityLog(activeRun, template), [activeRun, template]);

  const selectedTopologyNode =
    template?.topology.nodes.find((node) => node.id === selectedNodeId) ?? null;
  const selectedConfig = selectedNodeId ? nodeConfigs[selectedNodeId] ?? null : null;
  const selectedRunNode = activeRun?.node_runs.find((node) => node.node_id === selectedNodeId) ?? null;

  const nodeMeta = useMemo(
    () =>
      Object.fromEntries(
        Object.values(nodeConfigs).map((config) => [
          config.node_id,
          { model: config.model, execution_mode: config.execution_mode },
        ]),
      ),
    [nodeConfigs],
  );

  const loadRecentRuns = useCallback(async () => {
    setIsHistoryLoading(true);
    try {
      const runs = await api.listRuns();
      setRecentRuns(runs);
    } finally {
      setIsHistoryLoading(false);
    }
  }, []);

  const loadBootstrap = useCallback(async () => {
    const [healthResponse, modelOptions, templates] = await Promise.all([
      api.swarmHealth(),
      api.listModels(),
      api.listTemplates(),
    ]);
    setHealth(healthResponse);
    setModels(modelOptions);
    const firstTemplate = templates[0] ?? null;
    setTemplate(firstTemplate);
    if (firstTemplate) {
      setProduct(firstTemplate.default_product);
      setTargetAudience(firstTemplate.default_target_audience);
      setBrandVoice(firstTemplate.default_brand_voice);
      setNodeConfigs(configsFromTopology(firstTemplate.topology.nodes));
      setSelectedNodeId(firstTemplate.topology.nodes[0]?.id ?? null);
    }
    await loadRecentRuns();
  }, [loadRecentRuns]);

  useEffect(() => {
    void loadBootstrap().catch((bootstrapError) => {
      setError(bootstrapError instanceof Error ? bootstrapError.message : "Failed to connect to backend.");
    });
  }, [loadBootstrap]);

  useEffect(() => {
    if (!activeRun || (activeRun.status !== "pending" && activeRun.status !== "running")) {
      return;
    }

    const interval = window.setInterval(() => {
      void api
        .getRun(activeRun.id)
        .then((nextRun) => {
          setActiveRun(nextRun);
          setError(null);
          if (nextRun.status === "completed" || nextRun.status === "failed") {
            void loadRecentRuns();
          }
        })
        .catch((pollError) => {
          setError(pollError instanceof Error ? pollError.message : "Polling failed.");
        });
    }, 1000);

    return () => window.clearInterval(interval);
  }, [activeRun, loadRecentRuns]);

  useEffect(() => {
    if (!activeRun) {
      return;
    }
    for (const node of activeRun.node_runs) {
      seenStatusRef.current[node.node_id] = node.status;
    }
  }, [activeRun]);

  function handleNodeConfigChange(nodeId: string, patch: Partial<EditableNodeConfig>) {
    setNodeConfigs((current) => ({
      ...current,
      [nodeId]: { ...current[nodeId], ...patch },
    }));
  }

  async function handleLaunch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!template) {
      setError("No workflow template loaded.");
      return;
    }

    setIsLaunching(true);
    setError(null);
    seenStatusRef.current = {};

    try {
      const run = await api.createRun({
        template_id: template.id,
        product,
        target_audience: targetAudience,
        brand_voice: brandVoice,
        nodes: Object.values(nodeConfigs),
      });
      setActiveRun(run);
      setNodeConfigs(configsFromRun(run));
      setSelectedNodeId(run.node_runs[0]?.node_id ?? null);
      void loadRecentRuns();
    } catch (launchError) {
      setError(launchError instanceof Error ? launchError.message : "Could not launch workflow.");
    } finally {
      setIsLaunching(false);
    }
  }

  async function handleSelectRun(runId: number) {
    setError(null);
    try {
      const run = await api.getRun(runId);
      setActiveRun(run);
      setNodeConfigs(configsFromRun(run));
      const firstCompleted = run.node_runs.find((node) => node.status === "completed");
      setSelectedNodeId(firstCompleted?.node_id ?? run.node_runs[0]?.node_id ?? null);
    } catch (selectError) {
      setError(selectError instanceof Error ? selectError.message : "Could not load run.");
    }
  }

  function handleResetNodes() {
    if (!template) {
      return;
    }
    setNodeConfigs(configsFromTopology(template.topology.nodes));
  }

  const runningCount = activeRun?.node_runs.filter((node) => node.status === "running").length ?? 0;
  const completedCount = activeRun?.node_runs.filter((node) => node.status === "completed").length ?? 0;
  const totalNodes = activeRun?.node_runs.length ?? template?.topology.nodes.length ?? 0;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <div>
            <p className="brand-kicker">Parallel DAG Orchestrator</p>
            <h1>Agent Swarm Control</h1>
          </div>
        </div>

        <div className="topbar-status">
          <div className="status-chip">
            <span className={`status-dot ${health?.llm_mode === "openai" ? "live" : "mock"}`} />
            LLM: {health?.llm_mode ?? "connecting"}
          </div>
          <div className="status-chip">
            Nodes: {completedCount}/{totalNodes}
            {runningCount > 1 ? ` | ${runningCount} parallel` : ""}
          </div>
          <div className="status-chip">
            Run: {activeRun ? `#${activeRun.id} ${activeRun.status}` : "idle"}
          </div>
        </div>
      </header>

      {error ? <div className="banner error">{error}</div> : null}

      <main className="workspace">
        <aside className="sidebar panel">
          <div className="panel-header">
            <h2>Launch config</h2>
            <p>Global context variables injected into node sampling prompts.</p>
          </div>

          <form className="config-form" onSubmit={handleLaunch}>
            <label>
              Template
              <input value={template?.name ?? ""} readOnly />
            </label>
            <label>
              Product
              <input value={product} onChange={(event) => setProduct(event.target.value)} required />
            </label>
            <label>
              Target audience
              <textarea
                value={targetAudience}
                onChange={(event) => setTargetAudience(event.target.value)}
                required
              />
            </label>
            <label>
              Brand voice
              <input value={brandVoice} onChange={(event) => setBrandVoice(event.target.value)} required />
            </label>

            <button className="launch-button" type="submit" disabled={isLaunching || !template || isRunLocked}>
              {isLaunching ? "Dispatching..." : isRunLocked ? "Run in progress..." : "Launch swarm run"}
            </button>
          </form>

          <RunHistory
            runs={recentRuns}
            activeRunId={activeRun?.id ?? null}
            onSelectRun={handleSelectRun}
            isLoading={isHistoryLoading}
          />
        </aside>

        <section className="canvas panel">
          <div className="panel-header">
            <h2>Workflow graph</h2>
            <p>Click a node to configure model, execution mode, and sampling prompt.</p>
          </div>
          {template ? (
            <DagGraph
              topology={template.topology}
              nodeStatus={nodeStatus}
              nodeMeta={nodeMeta}
              selectedNodeId={selectedNodeId}
              onSelectNode={setSelectedNodeId}
            />
          ) : (
            <div className="empty-panel">Loading workflow topology...</div>
          )}
        </section>

        <aside className="insights">
          <section className="panel node-panel">
            <NodeInspector
              node={selectedTopologyNode}
              config={selectedConfig}
              models={models}
              disabled={isRunLocked}
              onChange={handleNodeConfigChange}
            />
            {!isRunLocked ? (
              <button className="ghost-button reset-nodes" type="button" onClick={handleResetNodes}>
                Reset all nodes to template defaults
              </button>
            ) : null}
          </section>

          <section className="panel output-panel">
            <div className="panel-header">
              <h2>Node output</h2>
              <p>{selectedRunNode?.node_name ?? selectedTopologyNode?.name ?? "Run output"}</p>
            </div>
            {selectedRunNode?.content ? (
              <pre className="output-block">{selectedRunNode.content}</pre>
            ) : (
              <div className="empty-panel">
                {activeRun
                  ? "Output appears here when this node completes."
                  : "Launch a run to see node handoff payloads."}
              </div>
            )}
          </section>

          <section className="panel final-panel">
            <div className="panel-header">
              <h2>Final deliverable</h2>
              <p>
                {activeRun?.final_output_key
                  ? `Key: ${activeRun.final_output_key}`
                  : "Downstream copy appears when the workflow completes."}
              </p>
            </div>
            {activeRun?.final_output_content ? (
              <pre className="output-block highlight">{activeRun.final_output_content}</pre>
            ) : (
              <div className="empty-panel">No final output yet.</div>
            )}
          </section>

          <ActivityFeed entries={activity} />
        </aside>
      </main>
    </div>
  );
}
