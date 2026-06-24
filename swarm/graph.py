"""DAG node definitions and workflow graph topology."""

from __future__ import annotations

from collections import deque
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

ExecutionMode = Literal["parallel", "serial"]


class Node(BaseModel):
    """A single agent node within a workflow DAG."""

    id: str = Field(..., min_length=1, description="Unique node identifier.")
    name: str = Field(..., min_length=1, description="Human-readable node label.")
    persona: str = Field(..., min_length=1, description="System prompt / agent role.")
    task: str = Field(..., min_length=1, description="Task instruction for this node.")
    dependencies: list[str] = Field(
        default_factory=list,
        description="IDs of predecessor nodes whose outputs feed this node.",
    )
    input_keys: list[str] = Field(
        default_factory=list,
        description="Named slots this node expects from upstream outputs.",
    )
    output_key: str = Field(
        ...,
        min_length=1,
        description="Key under which this node's result is stored for downstream nodes.",
    )
    tools: list[str] = Field(
        default_factory=list,
        description="Optional tool identifiers available to this agent.",
    )
    model: str | None = Field(
        default=None,
        description="LLM model id for this node's sampling call.",
    )
    execution_mode: ExecutionMode = Field(
        default="parallel",
        description="parallel: run with siblings concurrently; serial: one at a time per batch.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("dependencies", "input_keys", "tools")
    @classmethod
    def _strip_empty(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]


class WorkflowGraph:
    """Directed acyclic graph of agent nodes with dependency validation."""

    def __init__(self, name: str = "workflow") -> None:
        self.name = name
        self._nodes: dict[str, Node] = {}

    @property
    def nodes(self) -> dict[str, Node]:
        return dict(self._nodes)

    @property
    def node_ids(self) -> list[str]:
        return list(self._nodes.keys())

    def add_node(self, node: Node) -> None:
        if node.id in self._nodes:
            raise ValueError(f"Duplicate node id: {node.id!r}")
        self._nodes[node.id] = node

    def get_node(self, node_id: str) -> Node:
        try:
            return self._nodes[node_id]
        except KeyError as exc:
            raise KeyError(f"Unknown node id: {node_id!r}") from exc

    def roots(self) -> list[str]:
        """Nodes with no dependencies (can start immediately)."""
        return [node_id for node_id, node in self._nodes.items() if not node.dependencies]

    def dependents(self, node_id: str) -> list[str]:
        """Nodes that directly depend on ``node_id``."""
        return [
            other_id
            for other_id, node in self._nodes.items()
            if node_id in node.dependencies
        ]

    def validate(self) -> None:
        """Ensure the graph is a valid DAG with resolvable dependencies."""
        if not self._nodes:
            raise ValueError("Workflow graph has no nodes.")

        for node in self._nodes.values():
            for dep in node.dependencies:
                if dep not in self._nodes:
                    raise ValueError(
                        f"Node {node.id!r} depends on unknown node {dep!r}."
                    )
                if dep == node.id:
                    raise ValueError(f"Node {node.id!r} cannot depend on itself.")

        indegree = {node_id: len(node.dependencies) for node_id, node in self._nodes.items()}
        queue: deque[str] = deque(node_id for node_id, degree in indegree.items() if degree == 0)
        visited = 0

        while queue:
            current = queue.popleft()
            visited += 1
            for child_id in self.dependents(current):
                indegree[child_id] -= 1
                if indegree[child_id] == 0:
                    queue.append(child_id)

        if visited != len(self._nodes):
            raise ValueError("Workflow graph contains a cycle; only DAGs are supported.")

    def topological_layers(self) -> list[list[str]]:
        """Return nodes grouped by parallel execution layer (for diagnostics)."""
        self.validate()
        indegree = {node_id: len(node.dependencies) for node_id, node in self._nodes.items()}
        layers: list[list[str]] = []
        ready = [node_id for node_id, degree in indegree.items() if degree == 0]

        while ready:
            layers.append(list(ready))
            next_ready: list[str] = []
            for node_id in ready:
                for child_id in self.dependents(node_id):
                    indegree[child_id] -= 1
                    if indegree[child_id] == 0:
                        next_ready.append(child_id)
            ready = next_ready

        return layers
