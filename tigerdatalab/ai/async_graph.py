"""Asynchronous DAG execution with bounded parallelism and resumable checkpoints.

Unlike Graph, AsyncGraph treats all-unconditional outgoing edges as parallel
fan-out and requires a directed acyclic graph. Concurrent node actions receive
isolated state snapshots; returned mappings are merged deterministically, and
conflicting output keys fail the run instead of silently overwriting values.
"""
from __future__ import annotations

import asyncio
import inspect
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Mapping

from .graph import (
    CheckpointStore,
    GraphCheckpoint,
    GraphEdge,
    GraphError,
    GraphNode,
    GraphResult,
    InMemoryCheckpointStore,
)

_STATE_KEY = "__tigerdatalab_async_state__"
_META_KEY = "__tigerdatalab_async_meta__"


@dataclass
class AsyncGraphResult:
    graph: str
    status: str
    state: dict[str, Any]
    executed_nodes: list[str] = field(default_factory=list)
    skipped_nodes: list[str] = field(default_factory=list)
    error: str | None = None
    run_id: str | None = None
    steps: int = 0
    pending_approval: str | None = None


class AsyncGraph:
    """Run sync or async DAG nodes concurrently with limits, retries and resume.

    Conditional edges are evaluated after their source completes. If a node
    has conditional outgoing edges and one unconditional edge, the latter is
    a fallback used only when no conditional edge matches. If all outgoing
    edges are unconditional, they form a parallel fan-out.

    Checkpoints use the same CheckpointStore protocol as Graph. Use
    SQLiteCheckpointStore for persistence across process restarts on durable
    storage. A failed parallel wave may have already caused external side
    effects; make such actions idempotent.
    """

    def __init__(
        self,
        name: str,
        nodes: list[GraphNode] | None = None,
        edges: list[GraphEdge] | None = None,
        *,
        start: str | None = None,
        max_steps: int = 100,
        max_concurrency: int = 8,
        version: str = "1",
        checkpoint_store: CheckpointStore | None = None,
    ) -> None:
        if not name.strip():
            raise ValueError("Graph name cannot be empty")
        if max_steps < 1 or max_concurrency < 1:
            raise ValueError("max_steps and max_concurrency must be positive")
        if not version.strip():
            raise ValueError("Graph version cannot be empty")
        self.name, self.version = name, version
        self.max_steps, self.max_concurrency = max_steps, max_concurrency
        self.nodes: dict[str, GraphNode] = {}
        self.edges = list(edges or [])
        self.start = start
        self.checkpoint_store = checkpoint_store or InMemoryCheckpointStore()
        for node in nodes or []:
            self.add_node(node)

    def add_node(self, node: GraphNode) -> "AsyncGraph":
        if node.name in self.nodes:
            raise GraphError(f"Duplicate graph node: {node.name}")
        self.nodes[node.name] = node
        if self.start is None:
            self.start = node.name
        return self

    def add_edge(self, source: str, target: str, condition=None, label: str = "") -> "AsyncGraph":
        self.edges.append(GraphEdge(source, target, condition, label))
        return self

    def validate(self) -> None:
        if not self.nodes:
            raise GraphError("Graph must contain at least one node")
        if self.start not in self.nodes:
            raise GraphError(f"Start node does not exist: {self.start!r}")
        outgoing: dict[str, list[GraphEdge]] = {}
        incoming: dict[str, list[GraphEdge]] = {}
        for edge in self.edges:
            if edge.source not in self.nodes:
                raise GraphError(f"Edge source does not exist: {edge.source}")
            if edge.target not in self.nodes:
                raise GraphError(f"Edge target does not exist: {edge.target}")
            outgoing.setdefault(edge.source, []).append(edge)
            incoming.setdefault(edge.target, []).append(edge)
        for source, edges in outgoing.items():
            if any(edge.condition is not None for edge in edges):
                if sum(edge.condition is None for edge in edges) > 1:
                    raise GraphError(
                        f"Node {source!r} has multiple fallback edges; use one fallback"
                    )
        # Kahn's algorithm: parallel graph mode is intentionally DAG-only.
        indegree = {name: len(incoming.get(name, [])) for name in self.nodes}
        queue = [name for name, degree in indegree.items() if degree == 0]
        visited = 0
        while queue:
            current = queue.pop()
            visited += 1
            for edge in outgoing.get(current, []):
                indegree[edge.target] -= 1
                if indegree[edge.target] == 0:
                    queue.append(edge.target)
        if visited != len(self.nodes):
            raise GraphError("AsyncGraph requires a directed acyclic graph (cycles are not supported)")
        if incoming.get(self.start):
            raise GraphError("The start node cannot have incoming edges")

    def _unpack(self, checkpoint: GraphCheckpoint):
        wrapped = checkpoint.state
        state = deepcopy(wrapped.get(_STATE_KEY, {}))
        meta = deepcopy(wrapped.get(_META_KEY, {}))
        return state, meta

    def _checkpoint(
        self, state: dict[str, Any], meta: dict[str, Any], *,
        current_node: str | None, completed: list[str], steps: int,
        status: str, error: str | None = None, pending_approval: str | None = None,
    ) -> GraphCheckpoint:
        return GraphCheckpoint(
            graph_name=self.name,
            graph_version=self.version,
            current_node=current_node,
            state={_STATE_KEY: deepcopy(state), _META_KEY: deepcopy(meta)},
            completed_nodes=list(completed),
            steps=steps,
            status=status,
            error=error,
            pending_approval=pending_approval,
        )

    def _result(self, checkpoint: GraphCheckpoint, run_id: str | None) -> AsyncGraphResult:
        state, meta = self._unpack(checkpoint)
        return AsyncGraphResult(
            graph=self.name,
            status=checkpoint.status,
            state=state,
            executed_nodes=list(checkpoint.completed_nodes),
            skipped_nodes=list(meta.get("skipped", [])),
            error=checkpoint.error,
            run_id=run_id,
            steps=checkpoint.steps,
            pending_approval=checkpoint.pending_approval,
        )

    async def _call(self, node: GraphNode, state: dict[str, Any]) -> Any:
        async def invoke():
            if inspect.iscoroutinefunction(node.action):
                return await node.action(state)
            value = await asyncio.to_thread(node.action, state)
            if inspect.isawaitable(value):
                return await value
            return value

        attempts = 0
        while True:
            try:
                if node.timeout_seconds is not None:
                    return await asyncio.wait_for(invoke(), timeout=node.timeout_seconds)
                return await invoke()
            except Exception:
                if attempts >= node.retries or not node.retry_safe:
                    raise
                attempts += 1

    def _route_from(self, source: str, state: dict[str, Any], active_edges: set[str]) -> None:
        outgoing = [edge for edge in self.edges if edge.source == source]
        if not outgoing:
            return
        conditional = [edge for edge in outgoing if edge.condition is not None]
        fallback = next((edge for edge in outgoing if edge.condition is None), None)
        matched = []
        for edge in conditional:
            if edge.condition(state):
                matched.append(edge)
        if conditional:
            chosen = matched or ([fallback] if fallback is not None else [])
        else:
            chosen = outgoing
        for edge in chosen:
            active_edges.add(f"{edge.source}\u0000{edge.target}\u0000{edge.label}")

    @staticmethod
    def _edge_id(edge: GraphEdge) -> str:
        # Labels and node names are expected to be ordinary strings. A NUL
        # separator avoids ambiguity for typical identifiers.
        return f"{edge.source}\u0000{edge.target}\u0000{edge.label}"

    async def run_async(
        self,
        inputs: Mapping[str, Any] | None = None,
        *,
        run_id: str | None = None,
        resume: bool = False,
        approvals: Mapping[str, bool] | None = None,
    ) -> AsyncGraphResult:
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
            state, meta = self._unpack(checkpoint)
            if checkpoint.status == "waiting_for_approval":
                pending = checkpoint.pending_approval
                if pending is None or pending not in decisions:
                    return self._result(checkpoint, run_id)
            completed = list(checkpoint.completed_nodes)
            steps = checkpoint.steps
            checkpoint.status = "running"
            checkpoint.error = None
        else:
            state = dict(inputs or {})
            meta = {"resolved": [], "active_edges": [], "skipped": []}
            completed, steps = [], []

        resolved = set(meta.get("resolved", completed))
        active_edges = set(meta.get("active_edges", []))
        skipped = set(meta.get("skipped", []))
        incoming = {name: [e for e in self.edges if e.target == name] for name in self.nodes}
        outgoing = {name: [e for e in self.edges if e.source == name] for name in self.nodes}
        semaphore = asyncio.Semaphore(self.max_concurrency)

        def save(status: str, error: str | None = None, pending: str | None = None,
                 current: str | None = None):
            cp = self._checkpoint(
                state, {"resolved": sorted(resolved), "active_edges": sorted(active_edges),
                        "skipped": sorted(skipped)},
                current_node=current, completed=completed, steps=steps,
                status=status, error=error, pending_approval=pending,
            )
            if run_id:
                self.checkpoint_store.save(run_id, cp)
            return self._result(cp, run_id)

        # On resume, apply the supplied decision for the previously paused node.
        if resume and checkpoint.status == "running" and checkpoint.pending_approval:
            node_name = checkpoint.pending_approval
            if node_name in decisions:
                approved = decisions.pop(node_name)
                node = self.nodes[node_name]
                state[node.approval_key or f"{node_name}_approved"] = approved
                resolved.add(node_name)
                if not approved:
                    skipped.add(node_name)
                    if node_name not in completed:
                        completed.append(node_name)
                    self._route_from(node_name, state, active_edges)
                else:
                    # Re-enter this node in the ready set so its action executes.
                    resolved.discard(node_name)
                    meta["approved_nodes"] = list(set(meta.get("approved_nodes", [])) | {node_name})

        approved_nodes = set(meta.get("approved_nodes", []))
        while len(resolved) < len(self.nodes):
            # A node becomes ready when all parents have been resolved. Nodes
            # with no selected incoming edge are marked skipped without running.
            ready = []
            for name in self.nodes:
                if name in resolved:
                    continue
                parents = incoming[name]
                if not parents:
                    ready.append(name)
                elif all(edge.source in resolved for edge in parents):
                    if any(self._edge_id(edge) in active_edges for edge in parents):
                        ready.append(name)
                    else:
                        resolved.add(name)
                        skipped.add(name)
            if not ready:
                if len(resolved) == len(self.nodes):
                    break
                return save("failed", "Graph reached a deadlock; check routing and dependencies")

            ready.sort()
            gated = next((n for n in ready if self.nodes[n].approval_required and n not in approved_nodes
                          and n not in decisions), None)
            if gated is not None:
                return save("waiting_for_approval", pending=gated, current=gated)

            approved_this_wave: dict[str, bool] = {}
            runnable = []
            for name in ready:
                node = self.nodes[name]
                if node.approval_required and name not in approved_nodes:
                    decision = decisions.pop(name)
                    state[node.approval_key or f"{name}_approved"] = decision
                    if not decision:
                        resolved.add(name)
                        skipped.add(name)
                        if name not in completed:
                            completed.append(name)
                        self._route_from(name, state, active_edges)
                        steps += 1
                        continue
                    approved_nodes.add(name)
                    approved_this_wave[name] = True
                runnable.append(name)

            if steps + len(runnable) > self.max_steps:
                return save("failed", f"Graph exceeded max_steps={self.max_steps}")

            snapshot = deepcopy(state)

            async def execute(name: str):
                async with semaphore:
                    node = self.nodes[name]
                    return await self._call(node, deepcopy(snapshot))

            outcomes = await asyncio.gather(*(execute(name) for name in runnable), return_exceptions=True)
            failures = [(name, value) for name, value in zip(runnable, outcomes)
                        if isinstance(value, BaseException)]
            successes = [(name, value) for name, value in zip(runnable, outcomes)
                         if not isinstance(value, BaseException)]

            # Detect concurrent writes before changing shared state.
            writes: dict[str, str] = {}
            for name, value in successes:
                node = self.nodes[name]
                mapping = {node.output_key: value} if node.output_key else (
                    dict(value) if isinstance(value, Mapping) else {}
                )
                for key in mapping:
                    if key in writes:
                        return save("failed", f"Parallel output conflict for key {key!r} from nodes {writes[key]!r} and {name!r}")
                    writes[key] = name

            for name, value in sorted(successes, key=lambda item: item[0]):
                node = self.nodes[name]
                if node.output_key:
                    state[node.output_key] = value
                elif isinstance(value, Mapping):
                    state.update(value)
                if node.approval_required:
                    state[node.approval_key or f"{name}_approved"] = True
                if name not in completed:
                    completed.append(name)
                resolved.add(name)
                steps += 1

            for name, _ in sorted(successes, key=lambda item: item[0]):
                try:
                    self._route_from(name, state, active_edges)
                except Exception as exc:
                    return save("failed", f"Routing after node {name!r} failed: {exc}", current=name)

            if failures:
                name, error = failures[0]
                # Successful siblings are checkpointed; only failed nodes remain
                # unresolved and can be resumed without rerunning successful siblings.
                return save("failed", f"Node {name!r} failed: {error}", current=name)

            if run_id:
                save("running")

        return save("completed")

    def run(self, *args, **kwargs) -> AsyncGraphResult:
        """Synchronous convenience wrapper; do not call inside a running event loop."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.run_async(*args, **kwargs))
        raise RuntimeError("AsyncGraph.run() cannot run inside an active event loop; await run_async()")
