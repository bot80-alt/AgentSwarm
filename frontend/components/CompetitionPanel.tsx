"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

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
    <div className="competition-panel">
      <header className="panel-header">
        <div>
          <h2>Escrow Competition</h2>
          <p className="muted">
            Post a task, lock bounty escrow, and let developer agents race. CSPR MCP verifies optional
            on-chain account linkage.
          </p>
        </div>
        <div className="badge-row">
          {csprStatus && (
            <span className={`badge ${csprStatus.connected ? "badge-ok" : "badge-warn"}`}>
              CSPR MCP: {csprStatus.connected ? "connected" : "offline"} ({csprStatus.network})
            </span>
          )}
          {seed && (
            <span className="badge">
              Client wallet: ${seed.client.wallet_balance.toFixed(2)}
            </span>
          )}
        </div>
      </header>

      {error && <p className="error-banner">{error}</p>}

      <div className="competition-actions">
        <button type="button" onClick={() => void handleSeed()} disabled={busy}>
          Seed demo users
        </button>
      </div>

      <form className="competition-form" onSubmit={(e) => void handleCreate(e)}>
        <label>
          Task prompt
          <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={3} required />
        </label>
        <label>
          Success criteria
          <textarea
            value={successCriteria}
            onChange={(e) => setSuccessCriteria(e.target.value)}
            rows={2}
            required
          />
        </label>
        <label>
          Bounty (USD demo wallet)
          <input
            type="number"
            min="1"
            step="0.01"
            value={bounty}
            onChange={(e) => setBounty(e.target.value)}
            required
          />
        </label>
        <label>
          Casper account hash (optional)
          <input
            type="text"
            value={casperAccountHash}
            onChange={(e) => setCasperAccountHash(e.target.value)}
            placeholder="account-hash for CSPR balance verification"
          />
        </label>
        <button type="submit" disabled={busy}>
          Create competition & lock escrow
        </button>
      </form>

      {competition && (
        <section className="competition-detail">
          <h3>Competition #{competition.id}</h3>
          <p>
            Status: <strong>{competition.status}</strong> | Escrow: ${competition.escrow_amount.toFixed(2)}
          </p>
          <div className="competition-buttons">
            <button
              type="button"
              onClick={() => void handleCompete()}
              disabled={busy || competition.status !== "pending"}
            >
              Start agent race
            </button>
            <button
              type="button"
              onClick={() => void handleEvaluate()}
              disabled={busy || competition.status !== "judging"}
            >
              Judge & release bounty
            </button>
          </div>

          {competition.submissions && competition.submissions.length > 0 && (
            <div className="submissions-list">
              <h4>Submissions ({agents.length} agents registered)</h4>
              {competition.submissions.map((submission) => (
                <article
                  key={submission.id}
                  className={
                    competition.winner_agent_id === submission.agent_id ? "submission winner" : "submission"
                  }
                >
                  <header>
                    Agent #{submission.agent_id}
                    {submission.score != null && <span> — score {submission.score.toFixed(1)}</span>}
                    {competition.winner_agent_id === submission.agent_id && (
                      <span className="winner-tag">Winner</span>
                    )}
                  </header>
                  <pre>{submission.output_text}</pre>
                </article>
              ))}
            </div>
          )}

          {evaluateResult && (
            <p className="judge-reasoning">
              <strong>Judge:</strong> {evaluateResult.reasoning}
            </p>
          )}
        </section>
      )}
    </div>
  );
}
