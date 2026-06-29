from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from models import TaskStatus, TransactionType, UserRole, WorkflowNodeStatus, WorkflowRunStatus
from mcp_service import deserialize_tools


class UserBase(BaseModel):
    username: str
    wallet_balance: float
    role: UserRole


class UserRead(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class AgentBase(BaseModel):
    name: str
    description: str
    execution_fee: float = Field(ge=0)


class AgentRead(AgentBase):
    id: int
    creator_id: int

    model_config = ConfigDict(from_attributes=True)


class TransactionRead(BaseModel):
    id: int
    task_id: int
    amount: float
    type: TransactionType

    model_config = ConfigDict(from_attributes=True)


class TaskCreate(BaseModel):
    client_id: int
    agent_id: int
    prompt: str = Field(min_length=1)
    success_criteria: str = Field(min_length=1)


class TaskRead(BaseModel):
    id: int
    client_id: int
    agent_id: int | None
    prompt: str
    success_criteria: str
    status: TaskStatus
    escrow_amount: float
    output_text: str | None
    judge_feedback: str | None
    competition_mode: bool = False
    bounty_amount: float | None = None
    winner_agent_id: int | None = None
    casper_account_hash: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SubmissionRead(BaseModel):
    id: int
    task_id: int
    agent_id: int
    output_text: str
    score: float | None
    used_mock: bool
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompetitionCreate(BaseModel):
    client_id: int
    prompt: str = Field(min_length=1)
    success_criteria: str = Field(min_length=1)
    bounty_amount: float = Field(gt=0)
    casper_account_hash: str | None = None
    agent_ids: list[int] | None = None


class CompetitionRead(TaskRead):
    casper_hold_snapshot: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CompetitionDetail(CompetitionRead):
    client: UserRead
    submissions: list[SubmissionRead]
    transactions: list[TransactionRead]
    winner_agent: AgentRead | None = None

    model_config = ConfigDict(from_attributes=True)


class CompetitionEvaluateResponse(BaseModel):
    winner_agent_id: int
    reasoning: str
    scores: dict[int, float]
    task: CompetitionDetail


class CSPRStatusRead(BaseModel):
    enabled: bool
    url: str
    network: str
    connected: bool
    tool_count: int
    error: str | None = None


class TaskDetail(TaskRead):
    client: UserRead
    agent: AgentRead | None
    transactions: list[TransactionRead]

    model_config = ConfigDict(from_attributes=True)


class SeedResponse(BaseModel):
    message: str
    client: UserRead
    developer: UserRead
    agents: list[AgentRead]


class ExecutionResponse(BaseModel):
    task: TaskRead
    message: str


class EvaluationResponse(BaseModel):
    passed: bool
    reasoning: str
    task: TaskDetail


class WorkflowNodeTopology(BaseModel):
    id: str
    name: str
    dependencies: list[str]
    output_key: str
    tools: list[str]
    persona: str
    task: str
    model: str
    execution_mode: str


class NodeConfigInput(BaseModel):
    node_id: str = Field(min_length=1)
    task: str = Field(min_length=1)
    persona: str = Field(min_length=1)
    model: str = Field(min_length=1)
    execution_mode: str = Field(pattern="^(parallel|serial)$")
    tools: list[str] = Field(default_factory=list)


class ModelOptionRead(BaseModel):
    id: str
    label: str
    provider: str


class WorkflowRunCreate(BaseModel):
    template_id: str = Field(min_length=1)
    product: str = Field(min_length=1)
    target_audience: str = Field(min_length=1)
    brand_voice: str = Field(min_length=1)
    mcp_workspace: str | None = None
    nodes: list[NodeConfigInput] = Field(default_factory=list)


class WorkflowEdge(BaseModel):
    from_node: str = Field(alias="from")
    to: str

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)


class WorkflowTopology(BaseModel):
    name: str
    layers: list[list[str]]
    nodes: list[WorkflowNodeTopology]
    edges: list[WorkflowEdge]

    model_config = ConfigDict(ser_json_by_alias=True)


class WorkflowTemplateRead(BaseModel):
    id: str
    name: str
    description: str
    default_product: str
    default_target_audience: str
    default_brand_voice: str
    final_output_key: str
    topology: WorkflowTopology


class WorkflowNodeRunRead(BaseModel):
    id: int
    node_id: str
    node_name: str
    output_key: str
    task: str
    persona: str
    configured_model: str
    configured_tools: list[str] = Field(default_factory=list)
    execution_mode: str
    status: WorkflowNodeStatus
    content: str | None
    model: str | None
    used_mock: bool
    started_at: datetime | None
    finished_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def _hydrate_tools(cls, value: object) -> object:
        if isinstance(value, dict):
            raw = value.get("configured_tools", "[]")
            if isinstance(raw, str):
                value = {**value, "configured_tools": deserialize_tools(raw)}
            return value
        raw = getattr(value, "configured_tools", "[]")
        return {
            "id": value.id,
            "node_id": value.node_id,
            "node_name": value.node_name,
            "output_key": value.output_key,
            "task": value.task,
            "persona": value.persona,
            "configured_model": value.configured_model,
            "configured_tools": deserialize_tools(raw),
            "execution_mode": value.execution_mode,
            "status": value.status,
            "content": value.content,
            "model": value.model,
            "used_mock": value.used_mock,
            "started_at": value.started_at,
            "finished_at": value.finished_at,
        }


class WorkflowRunRead(BaseModel):
    id: int
    template_id: str
    product: str
    target_audience: str
    brand_voice: str
    mcp_workspace: str | None
    status: WorkflowRunStatus
    elapsed_seconds: float | None
    final_output_key: str | None
    final_output_content: str | None
    error_message: str | None
    created_at: datetime
    node_runs: list[WorkflowNodeRunRead]

    model_config = ConfigDict(from_attributes=True)


class WorkflowRunSummary(BaseModel):
    id: int
    template_id: str
    product: str
    status: WorkflowRunStatus
    elapsed_seconds: float | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SwarmHealthRead(BaseModel):
    message: str
    templates: list[str]
    llm_mode: str
    mcp_enabled: bool = True
    mcp_workspace: str | None = None


class MCPToolRead(BaseModel):
    name: str
    description: str
    group: str


class MCPStatusRead(BaseModel):
    enabled: bool
    workspace_root: str | None
    tool_groups: list[str]
    tools: list[MCPToolRead]
    error: str | None = None
