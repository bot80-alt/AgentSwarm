from pydantic import BaseModel, ConfigDict, Field

from models import TaskStatus, TransactionType, UserRole


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
