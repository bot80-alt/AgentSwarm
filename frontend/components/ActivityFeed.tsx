import type { ActivityEntry } from "@/types";

type ActivityFeedProps = {
  entries: ActivityEntry[];
};

function kindLabel(kind: ActivityEntry["kind"]) {
  switch (kind) {
    case "parallel":
      return "PARALLEL";
    case "start":
      return "START";
    case "finish":
      return "DONE";
    case "complete":
      return "COMPLETE";
    case "error":
      return "ERROR";
    default:
      return "INFO";
  }
}

export function ActivityFeed({ entries }: ActivityFeedProps) {
  return (
    <div className="activity-feed">
      <div className="panel-header">
        <h2>Execution log</h2>
        <p>Live orchestration events from the swarm engine.</p>
      </div>
      <div className="activity-list">
        {entries.length === 0 ? (
          <div className="empty-panel">Launch a workflow to see parallel batch events here.</div>
        ) : (
          entries.map((entry) => (
            <article key={entry.id} className={`activity-item ${entry.kind}`}>
              <div className="activity-meta">
                <span className="activity-kind">{kindLabel(entry.kind)}</span>
                <time>{entry.timestamp}</time>
              </div>
              <p>{entry.message}</p>
            </article>
          ))
        )}
      </div>
    </div>
  );
}
