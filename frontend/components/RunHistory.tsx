import type { WorkflowRunSummary } from "@/types";

type RunHistoryProps = {
  runs: WorkflowRunSummary[];
  activeRunId: number | null;
  onSelectRun: (runId: number) => void;
  isLoading: boolean;
};

function statusLabel(status: WorkflowRunSummary["status"]) {
  return status.charAt(0).toUpperCase() + status.slice(1);
}

export function RunHistory({ runs, activeRunId, onSelectRun, isLoading }: RunHistoryProps) {
  return (
    <section className="run-history">
      <div className="panel-header">
        <h2>Recent runs</h2>
        <p>Reload a previous swarm execution.</p>
      </div>

      {isLoading ? <div className="empty-panel">Loading run history...</div> : null}

      {!isLoading && runs.length === 0 ? (
        <div className="empty-panel">No runs yet. Launch your first workflow.</div>
      ) : null}

      <div className="run-history-list">
        {runs.map((run) => (
          <button
            key={run.id}
            type="button"
            className={`run-history-item ${activeRunId === run.id ? "active" : ""}`}
            onClick={() => onSelectRun(run.id)}
          >
            <div className="run-history-row">
              <strong>#{run.id}</strong>
              <span className={`run-status ${run.status}`}>{statusLabel(run.status)}</span>
            </div>
            <p>{run.product}</p>
            <div className="run-history-meta">
              <span>{run.template_id}</span>
              <span>{run.elapsed_seconds ? `${run.elapsed_seconds.toFixed(1)}s` : "--"}</span>
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}
