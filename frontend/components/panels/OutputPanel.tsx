type OutputPanelProps = {
  title: string;
  subtitle?: string;
  content: string | null | undefined;
  emptyMessage?: string;
  highlight?: boolean;
};

export function OutputPanel({ title, subtitle, content, emptyMessage, highlight }: OutputPanelProps) {
  return (
    <div className="space-y-2">
      <div>
        <h3 className="text-sm font-medium">{title}</h3>
        {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
      </div>
      {content ? (
        <pre
          className={`max-h-64 overflow-auto rounded-md border border-border p-3 text-xs leading-relaxed ${
            highlight ? "bg-accent/30" : "bg-secondary/50"
          }`}
        >
          {content}
        </pre>
      ) : (
        <p className="text-xs text-muted-foreground">{emptyMessage ?? "No output yet."}</p>
      )}
    </div>
  );
}
