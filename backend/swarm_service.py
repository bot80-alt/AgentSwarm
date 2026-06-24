from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

import path_setup  # noqa: F401

from sqlalchemy.orm import Session, joinedload

from models import WorkflowNodeRun, WorkflowNodeStatus, WorkflowRun, WorkflowRunStatus
from swarm.engine import WorkflowEngine, WorkflowEvent
from swarm.models_catalog import AVAILABLE_MODELS
from swarm.workflows import list_templates, resolve_template


PLACEHOLDER_KEYS = {"", "your_openai_api_key_here", "sk-placeholder"}


def llm_mode() -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key in PLACEHOLDER_KEYS:
        return "mock"
    return "openai"


def get_models() -> list[dict[str, str]]:
    return AVAILABLE_MODELS


def get_templates() -> list[dict[str, Any]]:
    return list_templates()


def _node_overrides_from_payload(nodes: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "node_id": node["node_id"],
            "task": node["task"],
            "persona": node["persona"],
            "model": node["model"],
            "execution_mode": node["execution_mode"],
        }
        for node in nodes
    ]


def _get_run_or_raise(db: Session, run_id: int) -> WorkflowRun:
    run = (
        db.query(WorkflowRun)
        .options(joinedload(WorkflowRun.node_runs))
        .filter(WorkflowRun.id == run_id)
        .first()
    )
    if run is None:
        raise LookupError(f"Workflow run {run_id} not found.")
    return run


def create_workflow_run(db: Session, payload: dict[str, Any]) -> WorkflowRun:
    template_id = payload["template_id"]
    node_overrides = _node_overrides_from_payload(payload.get("nodes") or [])
    graph, _ = resolve_template(
        template_id,
        product=payload["product"],
        target_audience=payload["target_audience"],
        brand_voice=payload["brand_voice"],
        node_overrides=node_overrides or None,
    )

    run = WorkflowRun(
        template_id=template_id,
        product=payload["product"],
        target_audience=payload["target_audience"],
        brand_voice=payload["brand_voice"],
        status=WorkflowRunStatus.PENDING,
    )
    db.add(run)
    db.flush()

    for node in graph.nodes.values():
        db.add(
            WorkflowNodeRun(
                workflow_run_id=run.id,
                node_id=node.id,
                node_name=node.name,
                output_key=node.output_key,
                task=node.task,
                persona=node.persona,
                configured_model=node.model or "gpt-4o-mini",
                execution_mode=node.execution_mode,
                status=WorkflowNodeStatus.PENDING,
            )
        )

    db.commit()
    db.refresh(run)
    return _get_run_or_raise(db, run.id)


async def execute_workflow_run(run_id: int, db_factory) -> None:
    db = db_factory()
    try:
        run = _get_run_or_raise(db, run_id)
        run.status = WorkflowRunStatus.RUNNING
        db.commit()

        stored_overrides = [
            {
                "node_id": node_run.node_id,
                "task": node_run.task,
                "persona": node_run.persona,
                "model": node_run.configured_model,
                "execution_mode": node_run.execution_mode,
            }
            for node_run in run.node_runs
        ]

        graph, context = resolve_template(
            run.template_id,
            product=run.product,
            target_audience=run.target_audience,
            brand_voice=run.brand_voice,
            node_overrides=stored_overrides,
        )

        async def on_event(event: WorkflowEvent) -> None:
            session = db_factory()
            try:
                if event.type == "batch_started":
                    now = datetime.now(UTC)
                    for node_id in event.node_ids:
                        node_run = (
                            session.query(WorkflowNodeRun)
                            .filter(
                                WorkflowNodeRun.workflow_run_id == run_id,
                                WorkflowNodeRun.node_id == node_id,
                            )
                            .first()
                        )
                        if node_run is not None:
                            node_run.status = WorkflowNodeStatus.RUNNING
                            node_run.started_at = now
                    session.commit()
                    return

                if event.type == "node_finished" and event.result is not None:
                    node_run = (
                        session.query(WorkflowNodeRun)
                        .filter(
                            WorkflowNodeRun.workflow_run_id == run_id,
                            WorkflowNodeRun.node_id == event.node_id,
                        )
                        .first()
                    )
                    if node_run is not None:
                        node_run.status = WorkflowNodeStatus.COMPLETED
                        node_run.content = event.result.content
                        node_run.model = event.result.model
                        node_run.used_mock = event.result.used_mock
                        node_run.finished_at = datetime.now(UTC)
                    session.commit()
            finally:
                session.close()

        engine = WorkflowEngine()
        result = await engine.run(graph, global_context=context, on_event=on_event, quiet=True)

        session = db_factory()
        try:
            completed_run = _get_run_or_raise(session, run_id)
            completed_run.status = WorkflowRunStatus.COMPLETED
            completed_run.elapsed_seconds = result.elapsed_seconds

            templates = {item["id"]: item for item in list_templates()}
            template = templates.get(completed_run.template_id)
            final_key = template["final_output_key"] if template else "marketing_copy"
            final_result = result.outputs_by_key.get(final_key)
            if final_result is not None:
                completed_run.final_output_key = final_key
                completed_run.final_output_content = final_result.content

            session.commit()
        finally:
            session.close()
    except Exception as exc:
        session = db_factory()
        try:
            failed_run = session.get(WorkflowRun, run_id)
            if failed_run is not None:
                failed_run.status = WorkflowRunStatus.FAILED
                failed_run.error_message = str(exc)
                session.commit()
        finally:
            session.close()
        raise
    finally:
        db.close()


def get_workflow_run(db: Session, run_id: int) -> WorkflowRun:
    return _get_run_or_raise(db, run_id)


def list_workflow_runs(db: Session, limit: int = 20) -> list[WorkflowRun]:
    return (
        db.query(WorkflowRun)
        .order_by(WorkflowRun.id.desc())
        .limit(limit)
        .all()
    )
