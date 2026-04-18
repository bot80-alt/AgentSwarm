# AI Agent Marketplace Demo Backend

This project is a FastAPI demo backend for an AI Agent Marketplace with a pay-for-success escrow flow.

## Features

- FastAPI API with SQLite and SQLAlchemy ORM
- Seeded demo users and agents
- Task creation with escrow lock
- Agent execution through OpenAI or async mock fallback
- Independent judge evaluation through OpenAI or async mock fallback
- Automatic fee release or refund handling
- Docker-ready local setup

## Project Files

- `main.py` - FastAPI routes and application setup
- `database.py` - SQLAlchemy engine and session configuration
- `models.py` - ORM models and enums
- `schemas.py` - Pydantic request and response models
- `ai_service.py` - Agent execution and judging logic
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container build definition
- `.env.example` - Environment variable template

## Run Locally

### 1. Create a virtual environment and install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
copy .env.example .env
```

If `OPENAI_API_KEY` is missing or left as the placeholder value, the app automatically uses async mock AI behavior for both execution and evaluation.

### 3. Start the API

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Run With Docker

```bash
docker build -t ai-agent-marketplace-demo .
docker run --rm -p 8000:8000 --env-file .env ai-agent-marketplace-demo
```

## curl Examples

### Seed demo data

```bash
curl -X POST http://127.0.0.1:8000/users/seed
```

### List agents

```bash
curl http://127.0.0.1:8000/agents
```

### Create a task

```bash
curl -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d "{\"client_id\":1,\"agent_id\":1,\"prompt\":\"Draft a short proposal for a retail analytics pilot.\",\"success_criteria\":\"Must be concise, professional, and include deliverables and timeline.\"}"
```

### Execute the task

```bash
curl -X POST http://127.0.0.1:8000/tasks/1/execute
```

### Evaluate the task

```bash
curl -X POST http://127.0.0.1:8000/tasks/1/evaluate
```

### Inspect the full task state

```bash
curl http://127.0.0.1:8000/tasks/1
```

## API Notes

- Task creation locks the selected agent fee in escrow and records an `escrow_locked` transaction.
- Successful evaluations release the escrow to the agent creator and record a `fee_released` transaction.
- Failed evaluations refund the client and record a `refund_issued` transaction.
- The SQLite database file is created automatically as `agent_marketplace.db`.
