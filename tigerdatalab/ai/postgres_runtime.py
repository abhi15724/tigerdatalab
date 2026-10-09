"""PostgreSQL-backed queue and checkpoint adapters for multi-worker deployments.

Install with `pip install 'tigerdatalab[postgres]'`. Use a managed PostgreSQL
service with TLS, backups, and least-privilege credentials in production.
Handlers remain at-least-once: use idempotency keys for external side effects.
"""
from __future__ import annotations

import json
import time
import uuid
from typing import Any, Mapping

from .distributed import QueueError, Task
from .graph import GraphCheckpoint, GraphError


class PostgreSQLTaskQueue:
    """Shared transactional task queue using row locks and SKIP LOCKED.

    A new connection is opened per operation so the instance can be shared by
    worker threads. The driver is imported lazily; PostgreSQL is optional.
    """

    def __init__(self, dsn: str, *, connect_timeout: int = 10) -> None:
        if not dsn or not dsn.strip():
            raise ValueError("PostgreSQL DSN is required")
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError("Install PostgreSQL support with pip install 'tigerdatalab[postgres]'") from exc
        self._psycopg, self._dict_row = psycopg, dict_row
        self.dsn, self.connect_timeout = dsn, connect_timeout
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tigerdatalab_tasks (
                    id TEXT PRIMARY KEY, task_type TEXT NOT NULL, payload_json JSONB NOT NULL,
                    tenant_id TEXT NOT NULL, status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL, available_at DOUBLE PRECISION NOT NULL,
                    lease_owner TEXT, lease_until DOUBLE PRECISION, result_json JSONB, error TEXT,
                    created_at DOUBLE PRECISION NOT NULL, updated_at DOUBLE PRECISION NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tdl_tasks_ready ON tigerdatalab_tasks(status, available_at, created_at)")
            conn.commit()

    def _connect(self):
        return self._psycopg.connect(self.dsn, connect_timeout=self.connect_timeout, row_factory=self._dict_row)

    def enqueue(self, task_type: str, payload: Mapping[str, Any], *, tenant_id: str, max_attempts: int = 3) -> str:
        if not task_type.strip() or not tenant_id.strip():
            raise ValueError("task_type and tenant_id are required")
        if max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        json.dumps(dict(payload), allow_nan=False)
        task_id, now = uuid.uuid4().hex, time.time()
        with self._connect() as conn:
            conn.execute("""INSERT INTO tigerdatalab_tasks
                (id,task_type,payload_json,tenant_id,status,attempts,max_attempts,available_at,created_at,updated_at)
                VALUES (%s,%s,%s::jsonb,%s,'queued',0,%s,%s,%s,%s)""",
                (task_id, task_type, json.dumps(dict(payload), allow_nan=False), tenant_id, max_attempts, now, now, now))
            conn.commit()
        return task_id

    def claim(self, worker_id: str, *, lease_seconds: float = 60) -> Task | None:
        if not worker_id.strip() or lease_seconds <= 0:
            raise ValueError("worker_id and positive lease_seconds are required")
        now = time.time()
        with self._connect() as conn:
            with conn.transaction():
                conn.execute("""UPDATE tigerdatalab_tasks SET status='failed', error='lease expired after max attempts',
                    lease_owner=NULL, lease_until=NULL, updated_at=%s
                    WHERE status='leased' AND lease_until <= %s AND attempts >= max_attempts""", (now, now))
                row = conn.execute("""SELECT * FROM tigerdatalab_tasks
                    WHERE attempts < max_attempts AND available_at <= %s
                    AND (status='queued' OR (status='leased' AND lease_until <= %s))
                    ORDER BY created_at,id FOR UPDATE SKIP LOCKED LIMIT 1""", (now, now)).fetchone()
                if row is None:
                    return None
                until = now + lease_seconds
                conn.execute("""UPDATE tigerdatalab_tasks SET status='leased',attempts=attempts+1,
                    lease_owner=%s,lease_until=%s,updated_at=%s WHERE id=%s""", (worker_id, until, now, row["id"]))
                return Task(row["id"], row["task_type"], row["payload_json"], row["tenant_id"],
                            row["attempts"] + 1, row["max_attempts"], worker_id, until)

    def _owned(self, conn, task_id: str, worker_id: str):
        row = conn.execute("SELECT status,lease_owner,lease_until FROM tigerdatalab_tasks WHERE id=%s FOR UPDATE", (task_id,)).fetchone()
        if not row or row["status"] != "leased" or row["lease_owner"] != worker_id or (row["lease_until"] or 0) <= time.time():
            raise QueueError("Task lease is missing, expired, or owned by another worker")
        return row

    def renew_lease(self, task_id: str, worker_id: str, *, lease_seconds: float = 60) -> None:
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive")
        with self._connect() as conn:
            with conn.transaction():
                self._owned(conn, task_id, worker_id)
                conn.execute("UPDATE tigerdatalab_tasks SET lease_until=%s,updated_at=%s WHERE id=%s",
                             (time.time() + lease_seconds, time.time(), task_id))

    def complete(self, task_id: str, worker_id: str, result: Mapping[str, Any]) -> None:
        encoded, now = json.dumps(dict(result), ensure_ascii=False, allow_nan=False), time.time()
        with self._connect() as conn:
            with conn.transaction():
                self._owned(conn, task_id, worker_id)
                conn.execute("""UPDATE tigerdatalab_tasks SET status='completed',result_json=%s::jsonb,
                    lease_owner=NULL,lease_until=NULL,updated_at=%s WHERE id=%s""", (encoded, now, task_id))

    def fail(self, task_id: str, worker_id: str, error: str, *, retry_delay: float = 0) -> None:
        if retry_delay < 0:
            raise ValueError("retry_delay cannot be negative")
        now = time.time()
        with self._connect() as conn:
            with conn.transaction():
                self._owned(conn, task_id, worker_id)
                row = conn.execute("SELECT attempts,max_attempts FROM tigerdatalab_tasks WHERE id=%s", (task_id,)).fetchone()
                status = "queued" if row["attempts"] < row["max_attempts"] else "failed"
                conn.execute("""UPDATE tigerdatalab_tasks SET status=%s,error=%s,available_at=%s,
                    lease_owner=NULL,lease_until=NULL,updated_at=%s WHERE id=%s""",
                    (status, str(error)[:4000], now + retry_delay, now, task_id))

    def get(self, task_id: str, *, tenant_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("""SELECT * FROM tigerdatalab_tasks WHERE id=%s AND tenant_id=%s""",
                               (task_id, tenant_id)).fetchone()
        if row is None:
            return None
        return {"id": row["id"], "task_type": row["task_type"], "payload": row["payload_json"],
                "tenant_id": row["tenant_id"], "status": row["status"], "attempts": row["attempts"],
                "max_attempts": row["max_attempts"], "result": row["result_json"], "error": row["error"],
                "lease_owner": row["lease_owner"], "lease_until": row["lease_until"]}


class PostgreSQLCheckpointStore:
    """Shared checkpoint store. Each save is an atomic upsert visible to all workers."""

    def __init__(self, dsn: str, *, connect_timeout: int = 10) -> None:
        if not dsn or not dsn.strip():
            raise ValueError("PostgreSQL DSN is required")
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError("Install PostgreSQL support with pip install 'tigerdatalab[postgres]'") from exc
        self._psycopg, self._dict_row = psycopg, dict_row
        self.dsn, self.connect_timeout = dsn, connect_timeout
        with self._connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS tigerdatalab_graph_checkpoints (
                run_id TEXT PRIMARY KEY, graph_name TEXT NOT NULL, graph_version TEXT NOT NULL,
                current_node TEXT, state_json JSONB NOT NULL, completed_nodes_json JSONB NOT NULL,
                steps INTEGER NOT NULL, status TEXT NOT NULL, error TEXT, pending_approval TEXT,
                updated_at DOUBLE PRECISION NOT NULL)""")
            conn.commit()

    def _connect(self):
        return self._psycopg.connect(self.dsn, connect_timeout=self.connect_timeout, row_factory=self._dict_row)

    def save(self, run_id: str, checkpoint: GraphCheckpoint) -> None:
        try:
            state = json.dumps(checkpoint.state, ensure_ascii=False, allow_nan=False)
            completed = json.dumps(checkpoint.completed_nodes, ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise GraphError("PostgreSQL checkpoint state must contain only JSON-serializable values") from exc
        with self._connect() as conn:
            conn.execute("""INSERT INTO tigerdatalab_graph_checkpoints
                (run_id,graph_name,graph_version,current_node,state_json,completed_nodes_json,steps,status,error,pending_approval,updated_at)
                VALUES (%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s,%s,%s)
                ON CONFLICT(run_id) DO UPDATE SET graph_name=EXCLUDED.graph_name,graph_version=EXCLUDED.graph_version,
                current_node=EXCLUDED.current_node,state_json=EXCLUDED.state_json,
                completed_nodes_json=EXCLUDED.completed_nodes_json,steps=EXCLUDED.steps,status=EXCLUDED.status,
                error=EXCLUDED.error,pending_approval=EXCLUDED.pending_approval,updated_at=EXCLUDED.updated_at""",
                (run_id, checkpoint.graph_name, checkpoint.graph_version, checkpoint.current_node,
                 state, completed, checkpoint.steps, checkpoint.status, checkpoint.error,
                 checkpoint.pending_approval, time.time()))
            conn.commit()

    def load(self, run_id: str) -> GraphCheckpoint | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM tigerdatalab_graph_checkpoints WHERE run_id=%s", (run_id,)).fetchone()
        if row is None:
            return None
        return GraphCheckpoint(graph_name=row["graph_name"], graph_version=row["graph_version"],
            current_node=row["current_node"], state=row["state_json"],
            completed_nodes=row["completed_nodes_json"], steps=row["steps"], status=row["status"],
            error=row["error"], pending_approval=row["pending_approval"])
