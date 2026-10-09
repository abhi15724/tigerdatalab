"""Queue-backed graph scheduling with durable checkpoints and resumable workers.

Execution is at-least-once: handlers and graph node side effects must be idempotent.
Use a shared transactional database/queue and a CheckpointStore implementation
visible to every worker. The included SQLite implementations are single-host /
shared-volume building blocks, not a multi-region broker.
"""
from __future__ import annotations

import asyncio
import hashlib
import inspect
import uuid
from typing import Any, Mapping

from .async_graph import AsyncGraph
from .distributed import TaskWorker
from .graph import Graph, GraphError


class GraphSchedulerError(RuntimeError):
    """Invalid graph scheduling request or worker execution."""


class DistributedGraphScheduler:
    """Submit and resume Graph/AsyncGraph runs through a durable task queue.

    Args:
        queue: A TaskQueue-compatible implementation.
        graphs: Registered graph objects, keyed by their public graph name.
        worker_id: Unique identity for this worker process.
        lease_seconds: Must exceed the longest execution, unless your queue
            adapter implements lease renewal.
        max_attempts: Queue retries for recoverable worker/process failures.
    """

    TASK_TYPE = "tigerdatalab.graph.run"

    @staticmethod
    def _checkpoint_key(tenant_id: str, run_id: str) -> str:
        """Derive an opaque checkpoint key scoped to one tenant and public run ID."""
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not isinstance(run_id, str) or not run_id.strip():
            raise ValueError("run_id is required")
        digest = hashlib.sha256((tenant_id + chr(0) + run_id).encode("utf-8")).hexdigest()
        return "tenant-run-" + digest

    def __init__(
        self,
        queue,
        graphs: Mapping[str, Graph | AsyncGraph],
        *,
        worker_id: str,
        lease_seconds: float = 300,
        max_attempts: int = 3,
    ) -> None:
        if not worker_id.strip():
            raise ValueError("worker_id is required")
        if lease_seconds <= 0 or max_attempts < 1:
            raise ValueError("lease_seconds and max_attempts must be positive")
        self.queue = queue
        self.graphs = dict(graphs)
        self.worker_id = worker_id
        self.lease_seconds = lease_seconds
        self.max_attempts = max_attempts
        if not self.graphs:
            raise ValueError("at least one graph must be registered")
        for name, graph in self.graphs.items():
            if name != graph.name:
                raise ValueError(f"Graph registry key {name!r} does not match graph.name {graph.name!r}")
            graph.validate()
        self._worker = TaskWorker(queue, worker_id, {self.TASK_TYPE: self._execute_task_sync})
        self._async_worker = TaskWorker(queue, worker_id, {self.TASK_TYPE: self._execute_task})

    def submit(
        self,
        graph_name: str,
        inputs: Mapping[str, Any] | None = None,
        *,
        tenant_id: str,
        run_id: str | None = None,
    ) -> dict[str, str]:
        """Enqueue a fresh graph run; return queue task ID and graph run ID."""
        graph = self._get_graph(graph_name)
        run_id = run_id or uuid.uuid4().hex
        if not tenant_id or not tenant_id.strip():
            raise ValueError("tenant_id is required")
        checkpoint_run_id = self._checkpoint_key(tenant_id, run_id)
        if graph.checkpoint_store.load(checkpoint_run_id) is not None:
            raise GraphSchedulerError(f"Graph run_id {run_id!r} already exists for this tenant")
        payload = {
            "graph_name": graph_name,
            "graph_version": graph.version,
            "graph_run_id": run_id,
            "checkpoint_run_id": checkpoint_run_id,
            "tenant_id": tenant_id,
            "inputs": dict(inputs or {}),
            "resume": False,
            "approvals": {},
        }
        task_id = self.queue.enqueue(
            self.TASK_TYPE, payload, tenant_id=tenant_id, max_attempts=self.max_attempts
        )
        return {"task_id": task_id, "run_id": run_id}

    def resume(
        self,
        graph_name: str,
        run_id: str,
        *,
        tenant_id: str,
        approvals: Mapping[str, bool] | None = None,
    ) -> dict[str, str]:
        """Queue a checkpoint resume or supply a pending human approval."""
        graph = self._get_graph(graph_name)
        checkpoint_run_id = self._checkpoint_key(tenant_id, run_id)
        checkpoint = graph.checkpoint_store.load(checkpoint_run_id)
        if checkpoint is None:
            raise GraphSchedulerError(f"No checkpoint found for run_id {run_id!r} in this tenant")
        if checkpoint.graph_name != graph.name or checkpoint.graph_version != graph.version:
            raise GraphSchedulerError("Checkpoint graph name/version does not match registered graph")
        if checkpoint.status == "completed":
            raise GraphSchedulerError("Completed graph runs cannot be resumed")
        decisions = dict(approvals or {})
        if any(not isinstance(value, bool) for value in decisions.values()):
            raise ValueError("approval decisions must be booleans")
        if checkpoint.status == "waiting_for_approval":
            pending = checkpoint.pending_approval
            if pending and pending not in decisions:
                raise ValueError(f"Approval decision for pending node {pending!r} is required")
        payload = {
            "graph_name": graph_name,
            "graph_version": graph.version,
            "graph_run_id": run_id,
            "checkpoint_run_id": checkpoint_run_id,
            "tenant_id": tenant_id,
            "inputs": {},
            "resume": True,
            "approvals": decisions,
        }
        task_id = self.queue.enqueue(
            self.TASK_TYPE, payload, tenant_id=tenant_id, max_attempts=self.max_attempts
        )
        return {"task_id": task_id, "run_id": run_id}

    def status(self, task_id: str, *, tenant_id: str) -> dict[str, Any] | None:
        """Return tenant-scoped queue state; never disclose another tenant's task."""
        return self.queue.get(task_id, tenant_id=tenant_id)

    def _get_graph(self, graph_name: str) -> Graph | AsyncGraph:
        try:
            return self.graphs[graph_name]
        except KeyError as exc:
            raise GraphSchedulerError(f"Graph {graph_name!r} is not registered") from exc

    def _execute_task_sync(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        """Synchronous queue handler; run async graphs in a dedicated event loop."""
        graph = self._get_graph(str(payload.get("graph_name", "")))
        if isinstance(graph, AsyncGraph):
            return asyncio.run(self._execute_task(payload))
        if payload.get("graph_version") != graph.version:
            raise GraphSchedulerError("Queued graph version does not match registered graph")
        run_id = str(payload["graph_run_id"])
        checkpoint_run_id = str(payload.get("checkpoint_run_id") or self._checkpoint_key(
            str(payload.get("tenant_id", "")), run_id
        ))
        result = graph.run(
            inputs=payload.get("inputs") or None,
            run_id=checkpoint_run_id,
            resume=bool(payload.get("resume")),
            approvals=payload.get("approvals") or None,
        )
        summary = {
            "graph_name": result.graph, "run_id": run_id, "status": result.status,
            "steps": result.steps, "executed_nodes": list(result.executed_nodes),
            "pending_approval": result.pending_approval, "error": result.error, "state": result.state,
        }
        if result.status == "failed":
            raise GraphSchedulerError(result.error or f"Graph {graph.name!r} failed")
        return summary

    async def _execute_task(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        graph = self._get_graph(str(payload.get("graph_name", "")))
        if payload.get("graph_version") != graph.version:
            raise GraphSchedulerError("Queued graph version does not match registered graph")
        run_id = str(payload["graph_run_id"])
        checkpoint_run_id = str(payload.get("checkpoint_run_id") or self._checkpoint_key(
            str(payload.get("tenant_id", "")), run_id
        ))
        kwargs = {
            "inputs": payload.get("inputs") or None,
            "run_id": checkpoint_run_id,
            "resume": bool(payload.get("resume")),
            "approvals": payload.get("approvals") or None,
        }
        if isinstance(graph, AsyncGraph):
            result = await graph.run_async(**kwargs)
        else:
            result = await asyncio.to_thread(graph.run, **kwargs)
        summary = {
            "graph_name": result.graph,
            "run_id": run_id,
            "status": result.status,
            "steps": result.steps,
            "executed_nodes": list(result.executed_nodes),
            "pending_approval": result.pending_approval,
            "error": result.error,
            "state": result.state,
        }
        if result.status == "failed":
            # Raising makes the durable task queue retry/recover the graph checkpoint.
            raise GraphSchedulerError(result.error or f"Graph {graph.name!r} failed")
        return summary

    async def process_once_async(self, *, retry_delay: float = 0) -> bool:
        """Claim and process one queued graph task asynchronously."""
        return await self._async_worker.process_once_async(
            lease_seconds=self.lease_seconds, retry_delay=retry_delay
        )

    def process_once(self, *, retry_delay: float = 0) -> bool:
        """Claim and process one queued graph task synchronously."""
        return self._worker.process_once(
            lease_seconds=self.lease_seconds, retry_delay=retry_delay
        )
