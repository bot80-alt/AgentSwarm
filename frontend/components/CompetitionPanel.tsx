"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import type { Agent, Competition, CompetitionEvaluateResult, CSPRStatus, SeedResponse } from "@/types";

const DEFAULT_CLIENT_ID = 1;

export function CompetitionPanel() {
  const [seed, setSeed] = useState<SeedResponse | null>(null);
  const [csprStatus, setCsprStatus] = useState<CSPRStatus | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [competition, setCompetition] = useState<Competition | null>(null);
  const [evaluateResult, setEvaluateResult] = useState<CompetitionEvaluateResult | null>(null);
  const [prompt, setPrompt] = useState(
    "Write a concise API design for a task escrow microservice with health checks.",
  );
  const [successCriteria, setSuccessCriteria] = useState(
    "Includes endpoints, data model, and escrow state machine in bullet form.",
  );
  const [bounty, setBounty] = useState("20");
  const [casperAccountHash, setCasperAccountHash] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshCompetition = useCallback(async (id: number) => {
    const detail = await api.getCompetition(id);
    setCompetition(detail);
    return detail;
  }, []);

  const bootstrap = useCallback(async () => {
    try {
      const [cspr, agentList] = await Promise.all([api.csprStatus(), api.listAgents()]);
      setCsprStatus(cspr);
      setAgents(agentList);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load competition data.");
    }
  }, []);

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  useEffect(() => {
    if (!competition || competition.status === "completed" || competition.status === "failed") {
      return;
    }
    const timer = setInterval(() => {
      void refreshCompetition(competition.id).catch(() => undefined);
    }, 1500);
    return () => clearInterval(timer);
  }, [competition, refreshCompetition]);

  async function handleSeed() {
    setBusy(true);
    setError(null);
    try {
      const response = await api.seedUsers();
      setSeed(response);
      const agentList = await api.listAgents();
      setAgents(agentList);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Seed failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setEvaluateResult(null);
    try {
      const clientId = seed?.client.id ?? DEFAULT_CLIENT_ID;
      const created = await api.createCompetition({
        client_id: clientId,
        prompt,
        success_criteria: successCriteria,
        bounty_amount: Number(bounty),
        casper_account_hash: casperAccountHash.trim() || null,
      });
      setCompetition(created);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create competition failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleCompete() {
    if (!competition) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await api.startCompetition(competition.id);
      setCompetition(updated);
      await refreshCompetition(competition.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Start competition failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleEvaluate() {
    if (!competition) return;
    setBusy(true);
    setError(null);
    try {
      const result = await api.evaluateCompetition(competition.id);
      setEvaluateResult(result);
      setCompetition(result.task);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Evaluate competition failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Escrow Competition</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Post a task, lock bounty escrow, and let developer agents race.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {csprStatus && (
            <Badge variant={csprStatus.connected ? "success" : "warning"}>
              CSPR: {csprStatus.connected ? "connected" : "offline"} ({csprStatus.network})
            </Badge>
          )}
          {seed && <Badge variant="secondary">Wallet: ${seed.client.wallet_balance.toFixed(2)}</Badge>}
        </div>
      </div>

      {error && (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 px-4 py-2 text-sm text-destructive">
          {error}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Setup</CardTitle>
          <CardDescription>Seed demo users before creating a competition.</CardDescription>
        </CardHeader>
        <CardContent>
          <Button type="button" onClick={() => void handleSeed()} disabled={busy}>
            Seed demo users
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Create competition</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={(e) => void handleCreate(e)}>
            <div className="space-y-2">
              <Label htmlFor="comp-prompt">Task prompt</Label>
              <Textarea id="comp-prompt" value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={3} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="comp-criteria">Success criteria</Label>
              <Textarea
                id="comp-criteria"
                value={successCriteria}
                onChange={(e) => setSuccessCriteria(e.target.value)}
                rows={2}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="comp-bounty">Bounty (USD demo wallet)</Label>
              <Input
                id="comp-bounty"
                type="number"
                min="1"
                step="0.01"
                value={bounty}
                onChange={(e) => setBounty(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="comp-casper">Casper account hash (optional)</Label>
              <Input
                id="comp-casper"
                type="text"
                value={casperAccountHash}
                onChange={(e) => setCasperAccountHash(e.target.value)}
                placeholder="account-hash for CSPR balance verification"
              />
            </div>
            <Button type="submit" disabled={busy}>
              Create competition & lock escrow
            </Button>
          </form>
        </CardContent>
      </Card>

      {competition && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Competition #{competition.id}</CardTitle>
            <CardDescription>
              Status: {competition.status} · Escrow: ${competition.escrow_amount.toFixed(2)}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                onClick={() => void handleCompete()}
                disabled={busy || competition.status !== "pending"}
              >
                Start agent race
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => void handleEvaluate()}
                disabled={busy || competition.status !== "judging"}
              >
                Judge & release bounty
              </Button>
            </div>

            {competition.submissions && competition.submissions.length > 0 && (
              <div className="space-y-3">
                <h4 className="text-sm font-medium">Submissions ({agents.length} agents registered)</h4>
                {competition.submissions.map((submission) => {
                  const isWinner = competition.winner_agent_id === submission.agent_id;
                  return (
                    <Card key={submission.id} className={isWinner ? "border-emerald-500/50" : undefined}>
                      <CardHeader className="py-3">
                        <div className="flex items-center gap-2 text-sm">
                          <span className="font-medium">Agent #{submission.agent_id}</span>
                          {submission.score != null && (
                            <span className="text-muted-foreground">score {submission.score.toFixed(1)}</span>
                          )}
                          {isWinner && <Badge variant="success">Winner</Badge>}
                        </div>
                      </CardHeader>
                      <CardContent className="pt-0">
                        <pre className="max-h-48 overflow-auto rounded-md bg-secondary/50 p-3 text-xs">
                          {submission.output_text}
                        </pre>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}

            {evaluateResult && (
              <p className="text-sm text-muted-foreground">
                <span className="font-medium text-foreground">Judge:</span> {evaluateResult.reasoning}
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
