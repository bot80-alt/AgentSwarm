# AI Agent Swarm

Parallel DAG multi-agent orchestration with a FastAPI backend and Next.js control console. The `swarm/` package powers async node execution; the backend exposes run APIs; the frontend visualizes the graph and streams live node status.

## Repo Structure

- `swarm/` - Core DAG framework (`graph`, `engine`, `agents`, `workflows`)
- `backend/` - FastAPI API integrating the swarm engine with SQLite persistence
- `frontend/` - Next.js orchestration console with live DAG visualization

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload
```

API: `http://127.0.0.1:8000`

Set `OPENAI_API_KEY` in `.env` for real LLM calls. Without it, nodes run in mock mode with simulated latency (parallel batches still execute concurrently).

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

UI: `http://127.0.0.1:3000`

Optional: create `frontend/.env.local` with `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000` if the backend uses a different host.

### 3. CLI (optional)

Run the marketing pipeline directly without the UI:

```bash
pip install -r swarm/requirements.txt
python -m swarm.main
```

## Swarm API

- `GET /swarm/health` — engine status and LLM mode
- `GET /swarm/templates` — available workflow templates with DAG topology
- `GET /swarm/templates/{template_id}` — single template
- `POST /swarm/runs` — create and start a workflow run (background execution)
- `GET /swarm/runs` — recent runs
- `GET /swarm/runs/{run_id}` — run detail with per-node status and outputs

Legacy marketplace endpoints (`/users/seed`, `/agents`, `/tasks`, etc.) remain available.

## UI workflow

1. Start backend and frontend.
2. Open the control console — it loads the Marketing Launch Pipeline template.
3. Configure product, audience, and brand voice.
4. Click **Launch swarm run** — Market Researcher and Competitor Analyst start in parallel.
5. Watch the DAG, execution log, and node outputs update live (polls every second).
6. Inspect the final marketing copy when the Copywriter node completes.

## Notes

- Workflow runs are stored in SQLite (`agent_marketplace.db` at repo root by default).
- The DAG engine schedules nodes as soon as dependencies are satisfied, not only by fixed layers.
- Windows consoles may not render Unicode symbols in CLI output; the web UI uses ASCII-safe labels.
