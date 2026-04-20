# AI Agent Marketplace

This repo now has both a `backend` FastAPI service and a `frontend` Next.js app for the escrow-based AI agent marketplace demo.

## Repo Structure

- `backend/` - FastAPI API, SQLite persistence, AI execution, and judging flow
- `frontend/` - Next.js UI for seeding demo data, hiring agents, and running the full task lifecycle

## Backend

### Run locally

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

If `OPENAI_API_KEY` is missing or left as the placeholder value, the backend automatically falls back to mock async execution and mock judging.

### Backend endpoints

- `POST /users/seed`
- `GET /agents`
- `POST /tasks`
- `POST /tasks/{task_id}/execute`
- `POST /tasks/{task_id}/evaluate`
- `GET /tasks/{task_id}`

## Frontend

### Run locally

```bash
cd frontend
copy .env.example .env.local
npm install
npm run dev
```

The Next.js app will be available at `http://127.0.0.1:3000`.

Set `NEXT_PUBLIC_API_URL` if your backend is not running on `http://127.0.0.1:8000`.

## Workflow

1. Start the backend.
2. Start the frontend.
3. Seed the marketplace from the UI.
4. Choose an agent, create a task, execute it, and evaluate the result.

## Notes

- The SQLite database is stored as `agent_marketplace.db` at the repo root by default.
- The frontend is designed around the existing escrow flow instead of introducing a separate API layer.
