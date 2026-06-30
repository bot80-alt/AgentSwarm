"use client";

import { useState } from "react";

import { WorkflowCanvas } from "@/components/flow/WorkflowCanvas";
import { AppHeader } from "@/components/layout/AppHeader";
import { AppShell } from "@/components/layout/AppShell";
import { RunSidebar } from "@/components/layout/RunSidebar";
import { ActivityPanel } from "@/components/panels/ActivityPanel";
import { LaunchBar } from "@/components/panels/LaunchBar";
import { LaunchConfigSheet } from "@/components/panels/LaunchConfigSheet";
import { NodeInspectorSheet } from "@/components/panels/NodeInspectorSheet";
import { OutputPanel } from "@/components/panels/OutputPanel";
import { CompetitionPanel } from "@/components/CompetitionPanel";
import { useSwarmRun } from "@/hooks/useSwarmRun";

export default function HomePage() {
  const swarm = useSwarmRun();
  const [activeView, setActiveView] = useState<"swarm" | "competitions">("swarm");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [configOpen, setConfigOpen] = useState(false);
  const [inspectorOpen, setInspectorOpen] = useState(false);

  const selectedTopologyNode =
    swarm.template?.topology.nodes.find((node) => node.id === swarm.selectedNodeId) ?? null;
  const selectedConfig = swarm.selectedNodeId ? swarm.nodeConfigs[swarm.selectedNodeId] ?? null : null;
  const selectedRunNode =
    swarm.activeRun?.node_runs.find((node) => node.node_id === swarm.selectedNodeId) ?? null;

  function handleSelectNode(nodeId: string) {
    swarm.setSelectedNodeId(nodeId);
    setInspectorOpen(true);
  }

  return (
    <AppShell>
      <AppHeader
        activeView={activeView}
        onViewChange={setActiveView}
        health={swarm.health}
        completedCount={swarm.completedCount}
        totalNodes={swarm.totalNodes}
        activeRunId={swarm.activeRun?.id ?? null}
        activeRunStatus={swarm.activeRun?.status ?? null}
        onToggleSidebar={() => setSidebarCollapsed((v) => !v)}
      />

      {swarm.error && (
        <div className="shrink-0 border-b border-destructive/30 bg-destructive/10 px-4 py-2 text-sm text-destructive">
          {swarm.error}
        </div>
      )}

      {activeView === "competitions" ? (
        <main className="flex-1 overflow-y-auto p-6">
          <div className="mx-auto max-w-2xl">
            <CompetitionPanel />
          </div>
        </main>
      ) : (
        <div className="flex min-h-0 flex-1">
          <RunSidebar
            runs={swarm.recentRuns}
            activeRunId={swarm.activeRun?.id ?? null}
            isLoading={swarm.isHistoryLoading}
            collapsed={sidebarCollapsed}
            onSelectRun={swarm.handleSelectRun}
            onNewRun={swarm.handleNewRun}
          />

          <div className="flex min-w-0 flex-1 flex-col">
            <div className="relative min-h-0 flex-1">
              {swarm.template ? (
                <WorkflowCanvas
                  topology={swarm.template.topology}
                  nodeStatus={swarm.nodeStatus}
                  nodeMeta={swarm.nodeMeta}
                  selectedNodeId={swarm.selectedNodeId}
                  onSelectNode={handleSelectNode}
                />
              ) : (
                <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                  Loading workflow…
                </div>
              )}
            </div>

            {swarm.activeRun?.final_output_content && (
              <div className="shrink-0 border-t border-border p-4">
                <OutputPanel
                  title="Final deliverable"
                  subtitle={swarm.activeRun.final_output_key ?? undefined}
                  content={swarm.activeRun.final_output_content}
                  highlight
                />
              </div>
            )}

            <ActivityPanel entries={swarm.activity} />

            <LaunchBar
              product={swarm.product}
              onProductChange={swarm.setProduct}
              onLaunch={() => void swarm.handleLaunch()}
              onOpenSettings={() => setConfigOpen(true)}
              isLaunching={swarm.isLaunching}
              isRunLocked={swarm.isRunLocked}
            />
          </div>
        </div>
      )}

      <LaunchConfigSheet
        open={configOpen}
        onOpenChange={setConfigOpen}
        template={swarm.template}
        targetAudience={swarm.targetAudience}
        brandVoice={swarm.brandVoice}
        mcpWorkspace={swarm.mcpWorkspace}
        health={swarm.health}
        disabled={swarm.isRunLocked}
        onTargetAudienceChange={swarm.setTargetAudience}
        onBrandVoiceChange={swarm.setBrandVoice}
        onMcpWorkspaceChange={swarm.setMcpWorkspace}
      />

      <NodeInspectorSheet
        open={inspectorOpen}
        onOpenChange={setInspectorOpen}
        node={selectedTopologyNode}
        config={selectedConfig}
        runNode={selectedRunNode}
        models={swarm.models}
        disabled={swarm.isRunLocked}
        onChange={swarm.handleNodeConfigChange}
        onResetNodes={swarm.handleResetNodes}
      />
    </AppShell>
  );
}
