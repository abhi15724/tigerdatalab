"""Small, bounded graph orchestration with routing and resumable checkpoints.

This runtime is synchronous and in-process by default. It deliberately does not
claim distributed durability, parallel scheduling, or exactly-once side effects.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Protocol


class GraphError(RuntimeError):
    """Raised when a graph definition or checkpoint is invalid."""


@dataclass(frozen=True)
class GraphNode:
    """One named operation. Retries require an explicit safety declaration."""

    name: str
    action: Callable[[dict[str, Any]], Any]
    output_key: str | None = None
    retries: int = 0
    retry_safe: bool = False
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Graph node name cannot be empty")
        if self.retries < 0:
            raise ValueError("Node retries cannot be negative")
        if self.retries and not self.retry_safe:
            raise ValueError("Retries require retry_safe=True")


@dataclass(frozen=True)
class GraphEdge:
    """Directed edge. Conditional edges are checked in declaration order."""

    source: str
    target: str
    condition: Callable[[dict[str, Any]], bool] | None = None
    label: str = ""


@dataclass
class GraphCheckpoint:
    """Snapshot saved after each successful node, suitable for an external store."""

    graph_name: str
    graph_version: str
    current_node: str | None
    state: dict[str, Any]
    completed_nodes: list[str] = field(default_factory=list)
    steps: int = 0
    status: str = "running"
    error: str | None = None


class CheckpointStore(Protocol):
    """Storage interface for graph snapshots."""

    def save(self, run_id: str, checkpoint: GraphCheckpoint) -> None: ...
    def load(self, run_id: str) -> GraphCheckpoint | None: ...


class InMemoryCheckpointStore:
    """Copy-isolated checkpoints for tests and single-process applications."""

    def __init__(self) -> None:
        self._items: dict[str, GraphCheckpoint] = {}

    def save(self, run_id: str, checkpoint: GraphCheckpoint) -> None:
        self._items[run_id] = deepcopy(checkpoint)

    def load(self, run_id: str) -> GraphCheckpoint | None:
        item = self._items.get(run_id)
        return deepcopy(item) if item is not None else None


@dataclass
class GraphResult:
    graph: str
    status: str
    state: dict[str, Any]
    executed_nodes: list[str] = field(default_factory=list)
    error: str | None = None
    run_id: str | None = None
    steps: int = 0


class Graph:
    """A validated directed graph with conditional routing and bounded execution.

    Actions receive the current mutable state. Return a mapping to merge fields,
    return another value with \x60output_key\x60 to store it, or return None.
    Use a stable run_id with resume=True to continue from the last successful
    node checkpoint.
    """

    def __init__(
        self,
        name: str,
        nodes: list[GraphNode] | None = None,
        edges: list[GraphEdge] | None = None,
        *,
        start: str | None = None,
        max_steps: int = 100,
        version: str = "1",
        checkpoint_store: CheckpointStore | None = None,
    ) -> None:
        if not name.strip():
            raise ValueError("Graph name cannot be empty")
        if max_steps < 1:
            raise ValueError("max_steps must be positive")
        if not version.strip():
            raise ValueError("Graph version cannot be empty")
        self.name = name
        self.version = version
        self.max_steps = max_steps
        self.nodes: dict[str, GraphNode] = {}
        self.edges: list[GraphEdge] = list(edges or [])
        self.start = start
        self.checkpoint_store = checkpoint_store or InMemoryCheckpointStore()
        for node in nodes or []:
            self.add_node(node)

    def add_node(self, node: GraphNode) -> "Graph":
        if node.name in self.nodes:
            raise GraphError(f"Duplicate graph node: {node.name}")
        self.nodes[node.name] = node
        if self.start is None:
            self.start = node.name
        return self

    def add_edge(self, source: str, target: str, condition=None, label: str = "") -> "Graph":
        self.edges.append(GraphEdge(source, target, condition, label))
        return self

    def validate(self) -> None:
        if not self.nodes:
            raise GraphError("Graph must contain at least one node")
        if self.start not in self.nodes:
            raise GraphError(f"Start node does not exist: {self.start!r}")
        for edge in self.edges:
            if edge.source not in self.nodes:
                raise GraphError(f"Edge source does not exist: {edge.source}")
            if edge.target not in self.nodes:
                raise GraphError(f"Edge target does not exist: {edge.target}")
        outgoing: dict[str, list[GraphEdge]] = {}
        for edge in self.edges:
            outgoing.setdefault(edge.source, []).append(edge)
        for source, edges in outgoing.items():
            unconditional = [edge for edge in edges if edge.condition is None]
            if len(unconditional) > 1:
                raise GraphError(
                    f"Node {source!r} has multiple unconditional edges; use conditions"
                )

    def _next_node(self, current: str, state: dict[str, Any]) -> str | None:
        outgoing = [edge for edge in self.edges if edge.source == current]
        if not outgoing:
            return None
        fallback = None
        for edge in outgoing:
            if edge.condition is None:
                fallback = edge.target
            elif edge.condition(state):
                return edge.target
        return fallback

    def _result(self, checkpoint: GraphCheckpoint, run_id: str | None) -> GraphResult:
        return GraphResult(
            graph=self.name,
            status=checkpoint.status,
            state=deepcopy(checkpoint.state),
            executed_nodes=list(checkpoint.completed_nodes),
            error=checkpoint.error,
            run_id=run_id,
            steps=checkpoint.steps,
        )

    def run(
        self,
        inputs: Mapping[str, Any] | None = None,
        *,
        run_id: str | None = None,
        resume: bool = False,
    ) -> GraphResult:
        self.validate()
        if resume and not run_id:
            raise GraphError("resume=True requires a run_id")

        if resume:
            checkpoint = self.checkpoint_store.load(run_id)  # type: ignore[arg-type]
            if checkpoint is None:
                raise GraphError(f"No checkpoint found for run_id {run_id!r}")
            if checkpoint.graph_name != self.name or checkpoint.graph_version != self.version:
                raise GraphError("Checkpoint graph name/version does not match this graph")
            if checkpoint.status == "completed":
                return self._result(checkpoint, run_id)
            if checkpoint.status == "running" and checkpoint.current_node is None:
                raise GraphError("Checkpoint is missing its current node")
            checkpoint.status = "running"
            checkpoint.error = None
        else:
            checkpoint = GraphCheckpoint(
                graph_name=self.name,
                graph_version=self.version,
                current_node=self.start,
                state=dict(inputs or {}),
            )

        while checkpoint.current_node is not None:
            if checkpoint.steps >= self.max_steps:
                checkpoint.status = "failed"
                checkpoint.error = f"Graph exceeded max_steps={self.max_steps}"
                if run_id:
                    self.checkpoint_store.save(run_id, checkpoint)
                return self._result(checkpoint, run_id)

            node_name = checkpoint.current_node
            node = self.nodes[node_name]
            checkpoint.steps += 1
            attempt = 0
            while True:
                try:
                    value = node.action(checkpoint.state)
                    if node.output_key:
                        checkpoint.state[node.output_key] = value
                    elif isinstance(value, Mapping):
                        checkpoint.state.update(value)
                    break
                except Exception as exc:
                    if attempt < node.retries and node.retry_safe:
                        attempt += 1
                        continue
                    checkpoint.status = "failed"
                    checkpoint.error = f"Node {node_name!r} failed: {exc}"
                    if run_id:
                        self.checkpoint_store.save(run_id, checkpoint)
                    return self._result(checkpoint, run_id)

            checkpoint.completed_nodes.append(node_name)
            try:
                checkpoint.current_node = self._next_node(node_name, checkpoint.state)
            except Exception as exc:
                checkpoint.status = "failed"
                checkpoint.error = f"Routing after node {node_name!r} failed: {exc}"
                if run_id:
                    self.checkpoint_store.save(run_id, checkpoint)
                return self._result(checkpoint, run_id)

            checkpoint.status = "completed" if checkpoint.current_node is None else "running"
            checkpoint.error = None
            if run_id:
                self.checkpoint_store.save(run_id, checkpoint)

        return self._result(checkpoint, run_id)
