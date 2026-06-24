"""Async orchestration engine for parallel DAG node execution."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from swarm.agents import AgentContext, BaseLLMAgent, NodeResult
from swarm.graph import Node, WorkflowGraph

WorkflowEventType = Literal[
    "workflow_started",
    "batch_started",
    "node_finished",
    "workflow_completed",
    "workflow_failed",
]

EventHandler = Callable[["WorkflowEvent"], Awaitable[None]]


@dataclass
class WorkflowEvent:
    type: WorkflowEventType
    graph_name: str
    node_ids: list[str] = field(default_factory=list)
    node_id: str | None = None
    result: NodeResult | None = None
    elapsed_seconds: float | None = None
    error: str | None = None


@dataclass
class WorkflowRunResult:
    """Aggregate result of a full workflow execution."""

    graph_name: str
    node_results: dict[str, NodeResult] = field(default_factory=dict)
    outputs_by_key: dict[str, NodeResult] = field(default_factory=dict)
    elapsed_seconds: float = 0.0


class WorkflowEngine:
    """
    Dynamically schedules DAG nodes for parallel execution.

    Nodes start the moment all predecessor outputs are available — not only
    at fixed topological layers — so independent branches run concurrently.
    """

    def __init__(self, agent: BaseLLMAgent | None = None) -> None:
        self.agent = agent or BaseLLMAgent()

    async def run(
        self,
        graph: WorkflowGraph,
        *,
        global_context: dict[str, Any] | None = None,
        on_event: EventHandler | None = None,
        quiet: bool = False,
    ) -> WorkflowRunResult:
        graph.validate()
        shared_context = dict(global_context or {})

        completed: dict[str, NodeResult] = {}
        in_flight: dict[str, asyncio.Task[NodeResult]] = {}
        pending: set[str] = set(graph.node_ids)
        completion_lock = asyncio.Lock()

        started_at = time.perf_counter()
        if not quiet:
            self._log_header(graph)

        async def emit(event: WorkflowEvent) -> None:
            if on_event is not None:
                await on_event(event)

        await emit(WorkflowEvent(type="workflow_started", graph_name=graph.name))

        async def launch_ready_nodes() -> None:
            async with completion_lock:
                ready = self._ready_nodes(graph, pending, completed, in_flight)
                if not ready:
                    return

                to_launch = self._nodes_to_launch(graph, ready, in_flight)
                if not to_launch:
                    return

                batch_label = ", ".join(graph.get_node(node_id).name for node_id in to_launch)
                if not quiet:
                    if len(to_launch) > 1:
                        print(f"\n[PARALLEL BATCH START] {batch_label}")
                    else:
                        print(f"\n[NODE START] {batch_label}")

                await emit(
                    WorkflowEvent(
                        type="batch_started",
                        graph_name=graph.name,
                        node_ids=list(to_launch),
                    )
                )

                for node_id in to_launch:
                    pending.discard(node_id)
                    node = graph.get_node(node_id)
                    upstream = self._collect_upstream(node, completed)
                    in_flight[node_id] = asyncio.create_task(
                        self._execute_node(node, upstream, shared_context),
                        name=f"node:{node_id}",
                    )

        try:
            await launch_ready_nodes()

            while in_flight:
                done, _ = await asyncio.wait(
                    in_flight.values(),
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in done:
                    node_id = self._task_node_id(task, in_flight)
                    result = task.result()
                    completed[node_id] = result
                    del in_flight[node_id]
                    if not quiet:
                        print(
                            f"[NODE FINISH] {result.node_name} "
                            f"(output_key={result.output_key!r}, mock={result.used_mock})"
                        )
                    await emit(
                        WorkflowEvent(
                            type="node_finished",
                            graph_name=graph.name,
                            node_id=node_id,
                            result=result,
                        )
                    )

                await launch_ready_nodes()
        except Exception as exc:
            await emit(
                WorkflowEvent(
                    type="workflow_failed",
                    graph_name=graph.name,
                    error=str(exc),
                )
            )
            raise

        elapsed = time.perf_counter() - started_at
        outputs_by_key = {result.output_key: result for result in completed.values()}

        if not quiet:
            print(f"\n[WORKFLOW COMPLETE] '{graph.name}' in {elapsed:.2f}s")
            print(f"   Nodes executed: {len(completed)} | Parallel roots: {len(graph.roots())}")

        run_result = WorkflowRunResult(
            graph_name=graph.name,
            node_results=completed,
            outputs_by_key=outputs_by_key,
            elapsed_seconds=elapsed,
        )
        await emit(
            WorkflowEvent(
                type="workflow_completed",
                graph_name=graph.name,
                elapsed_seconds=elapsed,
            )
        )
        return run_result

    def _ready_nodes(
        self,
        graph: WorkflowGraph,
        pending: set[str],
        completed: dict[str, NodeResult],
        in_flight: dict[str, asyncio.Task[NodeResult]],
    ) -> list[str]:
        ready = [
            node_id
            for node_id in pending
            if node_id not in in_flight
            and all(dep in completed for dep in graph.get_node(node_id).dependencies)
        ]
        return sorted(ready, key=lambda node_id: graph.get_node(node_id).name)

    def _nodes_to_launch(
        self,
        graph: WorkflowGraph,
        ready: list[str],
        in_flight: dict[str, asyncio.Task[NodeResult]],
    ) -> list[str]:
        parallel_ready = [
            node_id
            for node_id in ready
            if graph.get_node(node_id).execution_mode == "parallel"
        ]
        serial_ready = [
            node_id
            for node_id in ready
            if graph.get_node(node_id).execution_mode == "serial"
        ]
        serial_running = any(
            graph.get_node(node_id).execution_mode == "serial" for node_id in in_flight
        )

        to_launch = list(parallel_ready)
        if serial_ready and not serial_running:
            to_launch.append(serial_ready[0])
        return to_launch

    def _collect_upstream(
        self,
        node: Node,
        completed: dict[str, NodeResult],
    ) -> dict[str, Any]:
        upstream: dict[str, Any] = {}
        for dep_id in node.dependencies:
            dep_result = completed[dep_id]
            upstream[dep_result.output_key] = dep_result
        return upstream

    async def _execute_node(
        self,
        node: Node,
        upstream: dict[str, Any],
        global_context: dict[str, Any],
    ) -> NodeResult:
        context = AgentContext(
            node_id=node.id,
            node_name=node.name,
            persona=node.persona,
            task=node.task,
            tools=node.tools,
            upstream_outputs=upstream,
            global_context=global_context,
            model=node.model,
        )
        return await self.agent.run(context, output_key=node.output_key, model=node.model)

    def _task_node_id(
        self,
        task: asyncio.Task[NodeResult],
        in_flight: dict[str, asyncio.Task[NodeResult]],
    ) -> str:
        for node_id, running_task in in_flight.items():
            if running_task is task:
                return node_id
        raise RuntimeError("Completed task not found in in-flight registry.")

    def _log_header(self, graph: WorkflowGraph) -> None:
        layers = graph.topological_layers()
        print("=" * 72)
        print(f"Swarm Engine — workflow: {graph.name}")
        print(f"Nodes: {len(graph.node_ids)} | Topological layers: {len(layers)}")
        for index, layer in enumerate(layers, start=1):
            names = [graph.get_node(node_id).name for node_id in layer]
            parallel = " (parallel)" if len(layer) > 1 else ""
            print(f"  Layer {index}{parallel}: {', '.join(names)}")
        print("=" * 72)
