from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from models import TaskStatus, TransactionType, UserRole, WorkflowNodeStatus, WorkflowRunStatus


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
    agent_id: int
    prompt: str
    success_criteria: str
    status: TaskStatus
    escrow_amount: float
    output_text: str | None
    judge_feedback: str | None

    model_config = ConfigDict(from_attributes=True)


class TaskDetail(TaskRead):
    client: UserRead
    agent: AgentRead
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


class ModelOptionRead(BaseModel):
    id: str
    label: str
    provider: str


class WorkflowRunCreate(BaseModel):
    template_id: str = Field(min_length=1)
    product: str = Field(min_length=1)
    target_audience: str = Field(min_length=1)
    brand_voice: str = Field(min_length=1)
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
    execution_mode: str
    status: WorkflowNodeStatus
    content: str | None
    model: str | None
    used_mock: bool
    started_at: datetime | None
    finished_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class WorkflowRunRead(BaseModel):
    id: int
    template_id: str
    product: str
    target_audience: str
    brand_voice: str
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
