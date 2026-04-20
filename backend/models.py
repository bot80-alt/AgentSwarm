from enum import Enum

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class UserRole(str, Enum):
    DEVELOPER = "developer"
    CLIENT = "client"


class TaskStatus(str, Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    JUDGING = "judging"
    COMPLETED = "completed"
    FAILED = "failed"


class TransactionType(str, Enum):
    ESCROW_LOCKED = "escrow_locked"
    FEE_RELEASED = "fee_released"
    REFUND_ISSUED = "refund_issued"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False)
    wallet_balance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False)

    created_agents: Mapped[list["Agent"]] = relationship(
        "Agent",
        back_populates="creator",
        cascade="all, delete-orphan",
    )
    client_tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="client",
        foreign_keys="Task.client_id",
    )


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    execution_fee: Mapped[float] = mapped_column(Float, nullable=False)

    creator: Mapped[User] = relationship("User", back_populates="created_agents")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="agent")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    success_criteria: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus),
        nullable=False,
        default=TaskStatus.PENDING,
    )
    escrow_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    output_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    judge_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    client: Mapped[User] = relationship(
        "User",
        back_populates="client_tasks",
        foreign_keys=[client_id],
    )
    agent: Mapped[Agent] = relationship("Agent", back_populates="tasks")
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="Transaction.id",
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    type: Mapped[TransactionType] = mapped_column(SQLEnum(TransactionType), nullable=False)

    task: Mapped[Task] = relationship("Task", back_populates="transactions")
