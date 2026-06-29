import type { EditableNodeConfig, ExecutionMode, ModelOption, WorkflowNodeTopology } from "@/types";

type NodeInspectorProps = {
  node: WorkflowNodeTopology | null;
  config: EditableNodeConfig | null;
  models: ModelOption[];
  disabled?: boolean;
  onChange: (nodeId: string, patch: Partial<EditableNodeConfig>) => void;
};

export function NodeInspector({ node, config, models, disabled, onChange }: NodeInspectorProps) {
  if (!node || !config) {
    return (
      <section className="node-inspector empty">
        <div className="panel-header">
          <h2>Node sampling</h2>
          <p>Select a node on the graph to edit its model, execution mode, and prompt.</p>
        </div>
        <div className="empty-panel">No node selected.</div>
      </section>
    );
  }

  const hasFilesystem = config.tools.includes("filesystem");
  const hasCasper = config.tools.includes("casper");

  return (
    <section className="node-inspector">
      <div className="panel-header">
        <h2>{node.name}</h2>
        <p>
          Agent config for <code>{node.id}</code>
        </p>
      </div>

      <div className="inspector-grid">
        <label>
          Model
          <select
            value={config.model}
            disabled={disabled}
            onChange={(event) => onChange(node.id, { model: event.target.value })}
          >
            {models.map((model) => (
              <option key={model.id} value={model.id}>
                {model.label}
              </option>
            ))}
          </select>
        </label>

        <fieldset className="execution-toggle" disabled={disabled}>
          <legend>Execution with siblings</legend>
          <label className="radio-chip">
            <input
              type="radio"
              name={`mode-${node.id}`}
              checked={config.execution_mode === "parallel"}
              onChange={() => onChange(node.id, { execution_mode: "parallel" as ExecutionMode })}
            />
            Parallel
          </label>
          <label className="radio-chip">
            <input
              type="radio"
              name={`mode-${node.id}`}
              checked={config.execution_mode === "serial"}
              onChange={() => onChange(node.id, { execution_mode: "serial" as ExecutionMode })}
            />
            Serial
          </label>
        </fieldset>

        <label className="checkbox-chip">
          <input
            type="checkbox"
            checked={hasFilesystem}
            disabled={disabled}
            onChange={(event) => {
              const tools = event.target.checked
                ? [...new Set([...config.tools, "filesystem"])]
                : config.tools.filter((tool) => tool !== "filesystem");
              onChange(node.id, { tools });
            }}
          />
          MCP local filesystem (read files in workspace)
        </label>

        <label className="checkbox-chip">
          <input
            type="checkbox"
            checked={hasCasper}
            disabled={disabled}
            onChange={(event) => {
              const tools = event.target.checked
                ? [...new Set([...config.tools, "casper"])]
                : config.tools.filter((tool) => tool !== "casper");
              onChange(node.id, { tools });
            }}
          />
          CSPR.cloud Casper MCP (on-chain read tools)
        </label>

        <label>
          System persona
          <textarea
            value={config.persona}
            disabled={disabled}
            rows={4}
            onChange={(event) => onChange(node.id, { persona: event.target.value })}
          />
        </label>

        <label>
          Sampling prompt
          <textarea
            className="prompt-input"
            value={config.task}
            disabled={disabled}
            rows={8}
            onChange={(event) => onChange(node.id, { task: event.target.value })}
            placeholder="Task instruction passed to the LLM for this node..."
          />
        </label>
      </div>
    </section>
  );
}
