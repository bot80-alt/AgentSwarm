"""Competition marketplace: escrow holds and parallel agent races."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from ai_service import evaluate_competition_submissions, execute_agent_task
from cspr_service import verify_account_balance
from models import Agent, Task, TaskStatus, TaskSubmission, Transaction, TransactionType, User, UserRole
from schemas import CompetitionCreate


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


def _get_task_or_404(db: Session, task_id: int) -> Task:
    task = (
        db.query(Task)
        .options(
            joinedload(Task.client),
            joinedload(Task.submissions).joinedload(TaskSubmission.agent),
            joinedload(Task.transactions),
            joinedload(Task.winner_agent),
        )
        .filter(Task.id == task_id)
        .first()
    )
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competition not found.")
    if not task.competition_mode:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is not a competition.",
        )
    return task


async def create_competition(db: Session, payload: CompetitionCreate) -> Task:
    client = _get_user_or_404(db, payload.client_id)
    if client.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only client users can create competitions.",
        )

    bounty = payload.bounty_amount
    if client.wallet_balance < bounty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient wallet balance.",
        )

    casper_snapshot: str | None = None
    if payload.casper_account_hash:
        casper_snapshot = await verify_account_balance(payload.casper_account_hash.strip())

    client.wallet_balance -= bounty

    task = Task(
        client_id=client.id,
        agent_id=None,
        prompt=payload.prompt,
        success_criteria=payload.success_criteria,
        status=TaskStatus.PENDING,
        escrow_amount=bounty,
        competition_mode=True,
        bounty_amount=bounty,
        casper_account_hash=payload.casper_account_hash,
        casper_hold_snapshot=casper_snapshot,
    )
    db.add(task)
    db.flush()

    db.add(
        Transaction(
            task_id=task.id,
            amount=bounty,
            type=TransactionType.ESCROW_LOCKED,
        )
    )
    db.commit()
    db.refresh(task)
    return task


async def _run_agent_submission(
    agent: Agent,
    prompt: str,
    success_criteria: str,
) -> tuple[str, bool]:
    output, used_mock = await execute_agent_task(
        prompt,
        success_criteria,
        agent_name=agent.name,
        agent_description=agent.description,
    )
    return output, used_mock


async def run_competition(db: Session, task_id: int, agent_ids: list[int] | None = None) -> Task:
    task = _get_task_or_404(db, task_id)

    if task.status not in {TaskStatus.PENDING, TaskStatus.EXECUTING}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Competition is not in a runnable state.",
        )

    if task.submissions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Competition already has submissions.",
        )

    query = db.query(Agent).order_by(Agent.id.asc())
    if agent_ids:
        query = query.filter(Agent.id.in_(agent_ids))
    agents = query.all()
    if len(agents) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least two agents are required for a competition.",
        )

    task.status = TaskStatus.EXECUTING
    db.commit()

    results = await asyncio.gather(
        *[
            _run_agent_submission(agent, task.prompt, task.success_criteria)
            for agent in agents
        ]
    )

    for agent, (output_text, used_mock) in zip(agents, results, strict=True):
        db.add(
            TaskSubmission(
                task_id=task.id,
                agent_id=agent.id,
                output_text=output_text,
                used_mock=used_mock,
            )
        )

    task.status = TaskStatus.JUDGING
    db.commit()
    db.refresh(task)
    return task


async def evaluate_competition(db: Session, task_id: int) -> dict[str, Any]:
    task = _get_task_or_404(db, task_id)

    if task.status != TaskStatus.JUDGING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only competitions in judging state can be evaluated.",
        )

    if not task.submissions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No submissions to evaluate.",
        )

    submission_payload = [
        {
            "agent_id": submission.agent_id,
            "agent_name": submission.agent.name if submission.agent else f"Agent {submission.agent_id}",
            "output_text": submission.output_text,
        }
        for submission in task.submissions
    ]

    result = await evaluate_competition_submissions(
        task.prompt,
        task.success_criteria,
        submission_payload,
    )

    winner_agent_id = int(result["winner_agent_id"])
    scores: dict[int, float] = {int(k): float(v) for k, v in result["scores"].items()}
    reasoning = str(result["reasoning"])

    for submission in task.submissions:
        submission.score = scores.get(submission.agent_id)

    winner_agent = db.get(Agent, winner_agent_id)
    if winner_agent is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Winning agent not found.",
        )

    released_amount = task.escrow_amount
    if released_amount < 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Competition escrow amount is invalid.",
        )

    client = _get_user_or_404(db, task.client_id)
    creator = _get_user_or_404(db, winner_agent.creator_id)

    task.winner_agent_id = winner_agent_id
    task.judge_feedback = reasoning
    task.escrow_amount = 0.0
    task.status = TaskStatus.COMPLETED
    task.output_text = next(
        (s.output_text for s in task.submissions if s.agent_id == winner_agent_id),
        None,
    )

    creator.wallet_balance += released_amount
    db.add(
        Transaction(
            task_id=task.id,
            amount=released_amount,
            type=TransactionType.FEE_RELEASED,
        )
    )
    db.commit()

    task = _get_task_or_404(db, task_id)
    return {
        "winner_agent_id": winner_agent_id,
        "reasoning": reasoning,
        "scores": scores,
        "task": task,
    }


def get_competition(db: Session, task_id: int) -> Task:
    return _get_task_or_404(db, task_id)
