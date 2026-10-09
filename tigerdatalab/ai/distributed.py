"""Persistent SQLite task queue for cooperative multi-worker execution.

Use a shared durable volume and unique worker IDs. For horizontally scaled
cloud deployments, implement the same TaskQueue protocol with Postgres or a
managed queue; SQLite is not a substitute for a distributed broker.
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any, Mapping, Protocol


class QueueError(RuntimeError):
    """Invalid task queue operation."""


@dataclass(frozen=True)
class Task:
    id: str
    task_type: str
    payload: Mapping[str, Any]
    tenant_id: str
    attempts: int
    max_attempts: int
    lease_owner: str | None
    lease_until: float | None


class TaskQueue(Protocol):
    def enqueue(self, task_type: str, payload: Mapping[str, Any], *, tenant_id: str, max_attempts: int = 3) -> str: ...
    def claim(self, worker_id: str, *, lease_seconds: float = 60) -> Task | None: ...
    def complete(self, task_id: str, worker_id: str, result: Mapping[str, Any]) -> None: ...
    def fail(self, task_id: str, worker_id: str, error: str, *, retry_delay: float = 0) -> None: ...


class SQLiteTaskQueue:
    """Transactional leased queue supporting competing workers on one SQLite DB."""

    def __init__(self, database: str | Path = "tigerdatalab_tasks.sqlite3") -> None:
        self.database = str(database)
        if self.database != ":memory:":
            Path(self.database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._db = sqlite3.connect(self.database, timeout=30, check_same_thread=False, isolation_level=None)
        self._db.execute("PRAGMA busy_timeout = 30000")
        if self.database != ":memory:":
            self._db.execute("PRAGMA journal_mode = WAL")
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY, task_type TEXT NOT NULL, payload_json TEXT NOT NULL,
                tenant_id TEXT NOT NULL, status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL, available_at REAL NOT NULL, lease_owner TEXT,
                lease_until REAL, result_json TEXT, error TEXT, created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        self._db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_ready ON tasks(status, available_at, created_at)")
        self._db.commit()

    def enqueue(self, task_type: str, payload: Mapping[str, Any], *, tenant_id: str, max_attempts: int = 3) -> str:
        if not task_type.strip() or not tenant_id.strip():
            raise ValueError("task_type and tenant_id are required")
        if max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        encoded = json.dumps(dict(payload), ensure_ascii=False, allow_nan=False)
        task_id, now = uuid.uuid4().hex, time.time()
        with self._lock:
            self._db.execute(
                "INSERT INTO tasks(id,task_type,payload_json,tenant_id,status,max_attempts,available_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (task_id, task_type, encoded, tenant_id, "queued", max_attempts, now, now, now),
            )
        return task_id

    def claim(self, worker_id: str, *, lease_seconds: float = 60) -> Task | None:
        if not worker_id.strip() or lease_seconds <= 0:
            raise ValueError("worker_id and positive lease_seconds are required")
        now = time.time()
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                self._db.execute(
                    "UPDATE tasks SET status='failed',error='lease expired after max attempts',lease_owner=NULL,lease_until=NULL,updated_at=? "
                    "WHERE status='leased' AND lease_until <= ? AND attempts >= max_attempts",
                    (now, now),
                )
                row = self._db.execute("""
                    SELECT id,task_type,payload_json,tenant_id,attempts,max_attempts,lease_owner,lease_until
                    FROM tasks
                    WHERE attempts < max_attempts AND available_at <= ?
                      AND (status='queued' OR (status='leased' AND lease_until <= ?))
                    ORDER BY created_at, id LIMIT 1
                """, (now, now)).fetchone()
                if row is None:
                    self._db.commit()
                    return None
                task_id = row[0]
                self._db.execute("""
                    UPDATE tasks SET status='leased', attempts=attempts+1, lease_owner=?,
                    lease_until=?, updated_at=? WHERE id=?
                """, (worker_id, now + lease_seconds, now, task_id))
                self._db.commit()
                return Task(task_id, row[1], json.loads(row[2]), row[3], row[4] + 1,
                            row[5], worker_id, now + lease_seconds)
            except Exception:
                self._db.rollback()
                raise

    def _assert_owner(self, task_id: str, worker_id: str) -> None:
        row = self._db.execute("SELECT status,lease_owner,lease_until FROM tasks WHERE id=?", (task_id,)).fetchone()
        if row is None or row[0] != "leased" or row[1] != worker_id or (row[2] or 0) <= time.time():
            raise QueueError("Task lease is missing, expired, or owned by another worker")

    def complete(self, task_id: str, worker_id: str, result: Mapping[str, Any]) -> None:
        encoded, now = json.dumps(dict(result), ensure_ascii=False, allow_nan=False), time.time()
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                self._assert_owner(task_id, worker_id)
                self._db.execute(
                    "UPDATE tasks SET status='completed',result_json=?,lease_owner=NULL,lease_until=NULL,updated_at=? WHERE id=? AND status='leased' AND lease_owner=?",
                    (encoded, now, task_id, worker_id),
                )
                self._db.commit()
            except Exception:
                self._db.rollback()
                raise

    def fail(self, task_id: str, worker_id: str, error: str, *, retry_delay: float = 0) -> None:
        if retry_delay < 0:
            raise ValueError("retry_delay cannot be negative")
        now = time.time()
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                self._assert_owner(task_id, worker_id)
                row = self._db.execute("SELECT attempts,max_attempts FROM tasks WHERE id=?", (task_id,)).fetchone()
                status = "queued" if row[0] < row[1] else "failed"
                self._db.execute(
                    "UPDATE tasks SET status=?,error=?,available_at=?,lease_owner=NULL,lease_until=NULL,updated_at=? WHERE id=? AND status='leased' AND lease_owner=?",
                    (status, str(error)[:4000], now + retry_delay, now, task_id, worker_id),
                )
                self._db.commit()
            except Exception:
                self._db.rollback()
                raise

    def get(self, task_id: str, *, tenant_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._db.execute(
                "SELECT id,task_type,payload_json,tenant_id,status,attempts,max_attempts,result_json,error,lease_owner,lease_until FROM tasks WHERE id=? AND tenant_id=?",
                (task_id, tenant_id),
            ).fetchone()
        if row is None:
            return None
        return {"id": row[0], "task_type": row[1], "payload": json.loads(row[2]), "tenant_id": row[3],
                "status": row[4], "attempts": row[5], "max_attempts": row[6],
                "result": json.loads(row[7]) if row[7] else None, "error": row[8],
                "lease_owner": row[9], "lease_until": row[10]}

    def close(self) -> None:
        with self._lock:
            self._db.close()

    def __enter__(self) -> "SQLiteTaskQueue":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()



class TaskWorker:
    """Execute registered task handlers with lease ownership and bounded retries.

    A handler receives the task payload and must return a JSON-serializable
    mapping. Handlers should be idempotent: a worker can lose its lease after
    an external side effect and another worker may retry the task.
    """

    def __init__(self, queue: TaskQueue, worker_id: str, handlers: Mapping[str, Any]) -> None:
        if not worker_id.strip():
            raise ValueError("worker_id is required")
        self.queue, self.worker_id = queue, worker_id
        self.handlers = dict(handlers)

    def process_once(self, *, lease_seconds: float = 60, retry_delay: float = 0) -> bool:
        task = self.queue.claim(self.worker_id, lease_seconds=lease_seconds)
        if task is None:
            return False
        handler = self.handlers.get(task.task_type)
        if handler is None:
            self.queue.fail(task.id, self.worker_id, f"No handler for task type {task.task_type!r}")
            return True
        try:
            result = handler(dict(task.payload))
            if hasattr(result, "__await__"):
                raise QueueError("Async handler used in sync worker; use process_once_async()")
            if not isinstance(result, Mapping):
                raise QueueError("Task handler must return a mapping")
            self.queue.complete(task.id, self.worker_id, result)
        except Exception as exc:
            try:
                self.queue.fail(task.id, self.worker_id, f"{type(exc).__name__}: {exc}", retry_delay=retry_delay)
            except QueueError:
                # The lease may have expired while the handler ran; never overwrite
                # a newer worker's ownership or result.
                raise
        return True

    async def process_once_async(self, *, lease_seconds: float = 60, retry_delay: float = 0) -> bool:
        import asyncio
        task = await asyncio.to_thread(self.queue.claim, self.worker_id, lease_seconds=lease_seconds)
        if task is None:
            return False
        handler = self.handlers.get(task.task_type)
        if handler is None:
            await asyncio.to_thread(self.queue.fail, task.id, self.worker_id,
                                    f"No handler for task type {task.task_type!r}")
            return True
        try:
            result = handler(dict(task.payload))
            if hasattr(result, "__await__"):
                result = await result
            if not isinstance(result, Mapping):
                raise QueueError("Task handler must return a mapping")
            await asyncio.to_thread(self.queue.complete, task.id, self.worker_id, result)
        except Exception as exc:
            await asyncio.to_thread(self.queue.fail, task.id, self.worker_id,
                                    f"{type(exc).__name__}: {exc}", retry_delay=retry_delay)
        return True
