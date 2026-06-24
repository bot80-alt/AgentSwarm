from contextlib import asynccontextmanager

import path_setup  # noqa: F401

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload

from ai_service import evaluate_task, execute_agent_task
from database import Base, SessionLocal, engine, migrate_schema
from models import Agent, Task, TaskStatus, Transaction, TransactionType, User, UserRole
from schemas import (
    AgentRead,
    EvaluationResponse,
    ExecutionResponse,
    SeedResponse,
    SwarmHealthRead,
    TaskCreate,
    TaskDetail,
    TaskRead,
    ModelOptionRead,
    WorkflowRunCreate,
    WorkflowRunRead,
    WorkflowRunSummary,
    WorkflowTemplateRead,
)
from swarm_service import (
    create_workflow_run,
    execute_workflow_run,
    get_models,
    get_templates,
    get_workflow_run,
    list_workflow_runs,
    llm_mode,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    migrate_schema()
    yield


app = FastAPI(
    title="Agent Swarm Orchestrator",
    description="Parallel DAG multi-agent swarm with marketplace demo endpoints.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


def _get_agent_or_404(db: Session, agent_id: int) -> Agent:
    agent = db.get(Agent, agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found.")
    return agent


def _get_task_or_404(db: Session, task_id: int) -> Task:
    task = (
        db.query(Task)
        .options(
            joinedload(Task.client),
            joinedload(Task.agent),
            joinedload(Task.transactions),
        )
        .filter(Task.id == task_id)
        .first()
    )
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    return task


@app.get("/")
def healthcheck() -> dict[str, str]:
    return {"message": "Agent Swarm orchestrator backend is running."}


@app.get("/swarm/health", response_model=SwarmHealthRead)
def swarm_health() -> SwarmHealthRead:
    templates = get_templates()
    return SwarmHealthRead(
        message="Swarm engine is ready.",
        templates=[template["id"] for template in templates],
        llm_mode=llm_mode(),
    )


@app.get("/swarm/models", response_model=list[ModelOptionRead])
def swarm_models() -> list[ModelOptionRead]:
    return [ModelOptionRead.model_validate(model) for model in get_models()]


@app.get("/swarm/templates", response_model=list[WorkflowTemplateRead])
def swarm_templates() -> list[WorkflowTemplateRead]:
    return [WorkflowTemplateRead.model_validate(template) for template in get_templates()]


@app.get("/swarm/templates/{template_id}", response_model=WorkflowTemplateRead)
def swarm_template(template_id: str) -> WorkflowTemplateRead:
    for template in get_templates():
        if template["id"] == template_id:
            return WorkflowTemplateRead.model_validate(template)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found.")


@app.post("/swarm/runs", response_model=WorkflowRunRead, status_code=status.HTTP_201_CREATED)
async def start_swarm_run(
    payload: WorkflowRunCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        run = create_workflow_run(
            db,
            {
                "template_id": payload.template_id,
                "product": payload.product,
                "target_audience": payload.target_audience,
                "brand_voice": payload.brand_voice,
                "nodes": [node.model_dump() for node in payload.nodes],
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    background_tasks.add_task(execute_workflow_run, run.id, SessionLocal)
    return get_workflow_run(db, run.id)


@app.get("/swarm/runs", response_model=list[WorkflowRunSummary])
def swarm_runs(db: Session = Depends(get_db)):
    return list_workflow_runs(db)


@app.get("/swarm/runs/{run_id}", response_model=WorkflowRunRead)
def swarm_run(run_id: int, db: Session = Depends(get_db)):
    try:
        return get_workflow_run(db, run_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.post("/users/seed", response_model=SeedResponse)
def seed_users(db: Session = Depends(get_db)):
    client = db.query(User).filter(User.username == "demo_client").first()
    if client is None:
        client = User(username="demo_client", wallet_balance=100.0, role=UserRole.CLIENT)
        db.add(client)

    developer = db.query(User).filter(User.username == "demo_developer").first()
    if developer is None:
        developer = User(username="demo_developer", wallet_balance=0.0, role=UserRole.DEVELOPER)
        db.add(developer)

    db.flush()

    sample_agents = [
        {
            "name": "Proposal Writer Agent",
            "description": "Generates structured client proposals and concise business drafts.",
            "execution_fee": 15.0,
        },
        {
            "name": "Support Triage Agent",
            "description": "Summarizes incoming support issues and recommends next actions.",
            "execution_fee": 10.0,
        },
    ]

    seeded_agents: list[Agent] = []
    for item in sample_agents:
        agent = (
            db.query(Agent)
            .filter(Agent.name == item["name"], Agent.creator_id == developer.id)
            .first()
        )
        if agent is None:
            agent = Agent(creator_id=developer.id, **item)
            db.add(agent)
            db.flush()
        seeded_agents.append(agent)

    db.commit()
    for instance in [client, developer, *seeded_agents]:
        db.refresh(instance)

    return SeedResponse(
        message="Seed data is ready.",
        client=client,
        developer=developer,
        agents=seeded_agents,
    )


@app.get("/agents", response_model=list[AgentRead])
def list_agents(db: Session = Depends(get_db)):
    return db.query(Agent).order_by(Agent.id.asc()).all()


@app.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    client = _get_user_or_404(db, payload.client_id)
    agent = _get_agent_or_404(db, payload.agent_id)

    if client.role != UserRole.CLIENT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only client users can create tasks.")

    if agent.creator_id == client.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Clients cannot hire their own agent in this demo.")

    fee = agent.execution_fee
    if client.wallet_balance < fee:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient wallet balance.")

    client.wallet_balance -= fee

    task = Task(
        client_id=client.id,
        agent_id=agent.id,
        prompt=payload.prompt,
        success_criteria=payload.success_criteria,
        status=TaskStatus.PENDING,
        escrow_amount=fee,
    )
    db.add(task)
    db.flush()

    transaction = Transaction(
        task_id=task.id,
        amount=fee,
        type=TransactionType.ESCROW_LOCKED,
    )
    db.add(transaction)
    db.commit()
    db.refresh(task)
    return task


@app.post("/tasks/{task_id}/execute", response_model=ExecutionResponse)
async def execute_task_endpoint(task_id: int, db: Session = Depends(get_db)):
    task = _get_task_or_404(db, task_id)

    if task.status != TaskStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending tasks can be executed.",
        )

    task.status = TaskStatus.EXECUTING
    db.commit()
    db.refresh(task)

    output_text = await execute_agent_task(task.prompt, task.success_criteria)

    task.output_text = output_text
    task.status = TaskStatus.JUDGING
    db.commit()
    db.refresh(task)

    return ExecutionResponse(
        task=task,
        message="Task execution finished and is ready for evaluation.",
    )


@app.post("/tasks/{task_id}/evaluate", response_model=EvaluationResponse)
async def evaluate_existing_task(task_id: int, db: Session = Depends(get_db)):
    task = _get_task_or_404(db, task_id)

    if task.status != TaskStatus.JUDGING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only tasks in judging state can be evaluated.",
        )

    if not task.output_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task output is empty; execute the task before evaluating it.",
        )

    result = await evaluate_task(task.prompt, task.success_criteria, task.output_text)
    passed = bool(result["passed"])
    reasoning = str(result["reasoning"])

    client = _get_user_or_404(db, task.client_id)
    agent = _get_agent_or_404(db, task.agent_id)
    creator = _get_user_or_404(db, agent.creator_id)

    released_amount = task.escrow_amount
    if released_amount < 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Task escrow amount is invalid.",
        )

    task.judge_feedback = reasoning
    task.escrow_amount = 0.0

    if passed:
        creator.wallet_balance += released_amount
        task.status = TaskStatus.COMPLETED
        transaction_type = TransactionType.FEE_RELEASED
    else:
        client.wallet_balance += released_amount
        task.status = TaskStatus.FAILED
        transaction_type = TransactionType.REFUND_ISSUED

    db.add(
        Transaction(
            task_id=task.id,
            amount=released_amount,
            type=transaction_type,
        )
    )
    db.commit()

    task = _get_task_or_404(db, task_id)
    return EvaluationResponse(
        passed=passed,
        reasoning=reasoning,
        task=task,
    )


@app.get("/tasks/{task_id}", response_model=TaskDetail)
def get_task(task_id: int, db: Session = Depends(get_db)):
    return _get_task_or_404(db, task_id)
