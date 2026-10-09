"""Bounded graph orchestration with durable checkpoints and approval gates.

The runtime is synchronous. SQLite checkpoints survive process restarts, but
external side effects are not exactly-once and multi-worker scheduling is not
provided by this module.
"""
from __future__ import annotations

import json
import sqlite3
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock
from typing import Any, Callable, Mapping, Protocol


class GraphError(RuntimeError):
    """Raised when a graph definition, checkpoint, or state is invalid."""


@dataclass(frozen=True)
class GraphNode:
    """One named operation. Retries require an explicit safety declaration."""

    name: str
    action: Callable[[dict[str, Any]], Any]
    output_key: str | None = None
    retries: int = 0
    retry_safe: bool = False
    description: str = ""
    approval_required: bool = False
    approval_key: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Graph node name cannot be empty")
        if self.retries < 0:
            raise ValueError("Node retries cannot be negative")
        if self.retries and not self.retry_safe:
            raise ValueError("Retries require retry_safe=True")
        if self.approval_key is not None and not self.approval_key.strip():
            raise ValueError("approval_key cannot be empty")


@dataclass(frozen=True)
class GraphEdge:
    """Directed edge. Conditional edges are checked in declaration order."""

    source: str
    target: str
    condition: Callable[[dict[str, Any]], bool] | None = None
    label: str = ""


@dataclass
class GraphCheckpoint:
    """Persistable execution snapshot."""

    graph_name: str
    graph_version: str
    current_node: str | None
    state: dict[str, Any]
    completed_nodes: list[str] = field(default_factory=list)
    steps: int = 0
    status: str = "running"
    error: str | None = None
    pending_approval: str | None = None


class CheckpointStore(Protocol):
    """Storage interface for graph snapshots."""

    def save(self, run_id: str, checkpoint: GraphCheckpoint) -> None: ...
    def load(self, run_id: str) -> GraphCheckpoint | None: ...


class InMemoryCheckpointStore:
    """Copy-isolated checkpoints for tests and short-lived single-process runs."""

    def __init__(self) -> None:
        self._items: dict[str, GraphCheckpoint] = {}

    def save(self, run_id: str, checkpoint: GraphCheckpoint) -> None:
        self._items[run_id] = deepcopy(checkpoint)

    def load(self, run_id: str) -> GraphCheckpoint | None:
        item = self._items.get(run_id)
        return deepcopy(item) if item is not None else None


class SQLiteCheckpointStore:
    """SQLite-backed checkpoints that persist across application restarts.

    State must be JSON-serializable. The database should be stored on a durable
    local disk or persistent volume; ephemeral serverless filesystems are not
    suitable for long-lived checkpoints.
    """

    def __init__(self, database: str | Path = "tigerdatalab_checkpoints.sqlite3") -> None:
        self.database = str(database)
        if self.database != ":memory:":
            Path(self.database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._connection = sqlite3.connect(
            self.database, timeout=30, check_same_thread=False
        )
        self._connection.execute("PRAGMA busy_timeout = 30000")
        if self.database != ":memory:":
            self._connection.execute("PRAGMA journal_mode = WAL")
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS graph_checkpoints (
                run_id TEXT PRIMARY KEY,
                graph_name TEXT NOT NULL,
                graph_version TEXT NOT NULL,
                current_node TEXT,
                state_json TEXT NOT NULL,
                completed_nodes_json TEXT NOT NULL,
                steps INTEGER NOT NULL,
                status TEXT NOT NULL,
                error TEXT,
                pending_approval TEXT
            )
            """
        )
        self._connection.commit()

    def save(self, run_id: str, checkpoint: GraphCheckpoint) -> None:
        try:
            state_json = json.dumps(checkpoint.state, ensure_ascii=False, allow_nan=False)
            completed_json = json.dumps(checkpoint.completed_nodes, ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            raise GraphError(
                "SQLite checkpoint state must contain only JSON-serializable values"
            ) from exc
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO graph_checkpoints (
                    run_id, graph_name, graph_version, current_node, state_json,
                    completed_nodes_json, steps, status, error, pending_approval
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    graph_name=excluded.graph_name,
                    graph_version=excluded.graph_version,
                    current_node=excluded.current_node,
                    state_json=excluded.state_json,
                    completed_nodes_json=excluded.completed_nodes_json,
                    steps=excluded.steps,
                    status=excluded.status,
                    error=excluded.error,
                    pending_approval=excluded.pending_approval
                """,
                (
                    run_id, checkpoint.graph_name, checkpoint.graph_version,
                    checkpoint.current_node, state_json, completed_json,
                    checkpoint.steps, checkpoint.status, checkpoint.error,
                    checkpoint.pending_approval,
                ),
            )

    def load(self, run_id: str) -> GraphCheckpoint | None:
        with self._lock:
            row = self._connection.execute(
                """
                SELECT graph_name, graph_version, current_node, state_json,
                       completed_nodes_json, steps, status, error, pending_approval
                FROM graph_checkpoints WHERE run_id = ?
                """,
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        try:
            return GraphCheckpoint(
                graph_name=row[0],
                graph_version=row[1],
                current_node=row[2],
                state=json.loads(row[3]),
                completed_nodes=json.loads(row[4]),
                steps=row[5],
                status=row[6],
                error=row[7],
                pending_approval=row[8],
            )
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise GraphError(f"Checkpoint for run_id {run_id!r} is corrupt") from exc

    def close(self) -> None:
        """Close the SQLite connection. The store can be reopened for later use."""
        with self._lock:
            self._connection.close()


@dataclass
class GraphResult:
    graph: str
    status: str
    state: dict[str, Any]
    executed_nodes: list[str] = field(default_factory=list)
    error: str | None = None
    run_id: str | None = None
    steps: int = 0
    pending_approval: str | None = None


class Graph:
    """A validated directed graph with bounded execution, approval and resume.

    Actions receive the current mutable state. Return a mapping to merge fields,
    use output_key to store a scalar, or return None for no automatic update.
    Approval-gated nodes pause before execution until run(..., approvals={...})
    or run(..., resume=True, approvals={...}) supplies a decision by node name.
    A denied node is skipped and writes False to its approval key, enabling a
    conditional edge to route to a rejection/cleanup path.
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
            pending_approval=checkpoint.pending_approval,
        )

    def run(
        self,
        inputs: Mapping[str, Any] | None = None,
        *,
        run_id: str | None = None,
        resume: bool = False,
        approvals: Mapping[str, bool] | None = None,
    ) -> GraphResult:
        self.validate()
        if resume and not run_id:
            raise GraphError("resume=True requires a run_id")
        decisions = dict(approvals or {})
        if any(not isinstance(value, bool) for value in decisions.values()):
            raise GraphError("Approval decisions must be booleans")

        if resume:
            checkpoint = self.checkpoint_store.load(run_id)  # type: ignore[arg-type]
            if checkpoint is None:
                raise GraphError(f"No checkpoint found for run_id {run_id!r}")
            if checkpoint.graph_name != self.name or checkpoint.graph_version != self.version:
                raise GraphError("Checkpoint graph name/version does not match this graph")
            if checkpoint.status == "completed":
                return self._result(checkpoint, run_id)
            if checkpoint.status == "waiting_for_approval" and checkpoint.pending_approval:
                if checkpoint.pending_approval not in decisions:
                    return self._result(checkpoint, run_id)
            if checkpoint.current_node is None and checkpoint.status == "running":
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
                checkpoint.pending_approval = None
                if run_id:
                    self.checkpoint_store.save(run_id, checkpoint)
                return self._result(checkpoint, run_id)

            node_name = checkpoint.current_node
            node = self.nodes[node_name]
            if node.approval_required:
                if node_name not in decisions:
                    checkpoint.status = "waiting_for_approval"
                    checkpoint.pending_approval = node_name
                    if run_id:
                        self.checkpoint_store.save(run_id, checkpoint)
                    return self._result(checkpoint, run_id)
                approved = decisions.pop(node_name)
                approval_key = node.approval_key or f"{node_name}_approved"
                checkpoint.state[approval_key] = approved
                checkpoint.pending_approval = None
                if not approved:
                    checkpoint.steps += 1
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
                    if run_id:
                        self.checkpoint_store.save(run_id, checkpoint)
                    continue

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
                    checkpoint.pending_approval = None
                    if run_id:
                        self.checkpoint_store.save(run_id, checkpoint)
                    return self._result(checkpoint, run_id)

            if node.approval_required:
                checkpoint.state[node.approval_key or f"{node_name}_approved"] = True
            checkpoint.completed_nodes.append(node_name)
            try:
                checkpoint.current_node = self._next_node(node_name, checkpoint.state)
            except Exception as exc:
                checkpoint.status = "failed"
                checkpoint.error = f"Routing after node {node_name!r} failed: {exc}"
                checkpoint.pending_approval = None
                if run_id:
                    self.checkpoint_store.save(run_id, checkpoint)
                return self._result(checkpoint, run_id)

            checkpoint.status = "completed" if checkpoint.current_node is None else "running"
            checkpoint.error = None
            checkpoint.pending_approval = None
            if run_id:
                self.checkpoint_store.save(run_id, checkpoint)

        return self._result(checkpoint, run_id)
