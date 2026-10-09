"""Lightweight runtime security controls.

These controls are defense-in-depth, not a process/OS sandbox. Never execute
untrusted model-generated code in the main process. Use a hardened container,
VM or isolated worker for untrusted code execution.
"""
from __future__ import annotations

import sqlite3
import json
import time
from collections import deque
from pathlib import Path
from threading import RLock
from typing import Any, Mapping, Protocol


class SecurityPolicyError(RuntimeError):
    """Raised when a runtime security policy denies an operation."""


class ToolRateLimiter(Protocol):
    def check(self, role: str, tool_name: str) -> None: ...


class InMemoryToolRateLimiter:
    """Thread-safe per-role/per-tool sliding-window limiter for one process."""

    def __init__(self, max_calls: int = 30, window_seconds: float = 60.0) -> None:
        if max_calls < 1 or window_seconds <= 0:
            raise ValueError("max_calls and window_seconds must be positive")
        self.max_calls, self.window_seconds = max_calls, window_seconds
        self._events: dict[tuple[str, str], deque[float]] = {}
        self._lock = RLock()

    def check(self, role: str, tool_name: str) -> None:
        now = time.monotonic()
        key = (role, tool_name)
        with self._lock:
            bucket = self._events.setdefault(key, deque())
            cutoff = now - self.window_seconds
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= self.max_calls:
                raise SecurityPolicyError(f"Rate limit exceeded for tool {tool_name!r}")
            bucket.append(now)


class AuditSink(Protocol):
    def record(self, event: Mapping[str, Any]) -> None: ...


class SQLiteAuditLog:
    """Append-only SQLite audit events; avoid passing prompts, secrets or raw PII."""

    def __init__(self, database: str | Path = "tigerdatalab_audit.sqlite3") -> None:
        self.database = str(database)
        if self.database != ":memory:":
            Path(self.database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._db = sqlite3.connect(self.database, timeout=30, check_same_thread=False)
        self._db.execute("PRAGMA busy_timeout = 30000")
        if self.database != ":memory:":
            self._db.execute("PRAGMA journal_mode = WAL")
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                event TEXT NOT NULL,
                tenant_id TEXT,
                run_id TEXT,
                details_json TEXT NOT NULL
            )
        """)
        self._db.commit()

    def record(self, event: Mapping[str, Any]) -> None:
        event_name = str(event.get("event", "unknown"))[:128]
        tenant_id = str(event["tenant_id"])[:256] if event.get("tenant_id") is not None else None
        run_id = str(event["run_id"])[:256] if event.get("run_id") is not None else None
        details = {str(k): v for k, v in event.items()
                   if k not in {"event", "timestamp", "tenant_id", "run_id"}}
        encoded = json.dumps(details, ensure_ascii=False, default=str)
        with self._lock:
            self._db.execute(
                "INSERT INTO audit_events(timestamp,event,tenant_id,run_id,details_json) VALUES(?,?,?,?,?)",
                (float(event.get("timestamp", time.time())), event_name, tenant_id, run_id, encoded),
            )
            self._db.commit()

    def query(self, *, tenant_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        if limit < 1 or limit > 10000:
            raise ValueError("limit must be between 1 and 10000")
        with self._lock:
            if tenant_id is None:
                rows = self._db.execute(
                    "SELECT timestamp,event,tenant_id,run_id,details_json FROM audit_events ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            else:
                rows = self._db.execute(
                    "SELECT timestamp,event,tenant_id,run_id,details_json FROM audit_events WHERE tenant_id=? ORDER BY id DESC LIMIT ?",
                    (tenant_id, limit),
                ).fetchall()
        return [{"timestamp": r[0], "event": r[1], "tenant_id": r[2],
                 "run_id": r[3], "details": json.loads(r[4])} for r in rows]

    def close(self) -> None:
        with self._lock:
            self._db.close()

    def __enter__(self) -> "SQLiteAuditLog":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
