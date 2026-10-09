"""SQLite-backed, tenant-scoped conversation memory.

SQLite is useful for a single host or shared persistent volume. For high-write
multi-region deployments, implement ConversationMemory against a managed
database with appropriate transactions, encryption and retention controls.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import Any


class DurableMemoryError(RuntimeError):
    """Raised when durable conversation memory cannot be read or written."""


class SQLiteConversationMemory:
    """Durable conversation memory namespaced by tenant and conversation.

    The conversation_id alone is never used as a global key: tenant_id is
    required by every operation. Messages must be JSON serializable.
    """

    def __init__(self, database: str | Path = "tigerdatalab_memory.sqlite3") -> None:
        self.database = str(database)
        if self.database != ":memory:":
            Path(self.database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._db = sqlite3.connect(self.database, timeout=30, check_same_thread=False)
        self._db.execute("PRAGMA busy_timeout = 30000")
        if self.database != ":memory:":
            self._db.execute("PRAGMA journal_mode = WAL")
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                tenant_id TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                messages_json TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (tenant_id, conversation_id)
            )
        """)
        self._db.commit()

    @staticmethod
    def _scope(tenant_id: str, conversation_id: str) -> tuple[str, str]:
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not isinstance(conversation_id, str) or not conversation_id.strip():
            raise ValueError("conversation_id is required")
        return tenant_id, conversation_id

    def load(self, conversation_id: str, *, tenant_id: str = "default") -> list[dict[str, Any]]:
        tenant_id, conversation_id = self._scope(tenant_id, conversation_id)
        with self._lock:
            row = self._db.execute(
                "SELECT messages_json FROM conversations WHERE tenant_id=? AND conversation_id=?",
                (tenant_id, conversation_id),
            ).fetchone()
        if row is None:
            return []
        value = json.loads(row[0])
        if not isinstance(value, list) or any(not isinstance(m, dict) for m in value):
            raise DurableMemoryError("Stored conversation has an invalid message shape")
        return value

    def save(self, conversation_id: str, messages: list[dict[str, Any]], *, tenant_id: str = "default") -> None:
        tenant_id, conversation_id = self._scope(tenant_id, conversation_id)
        if not isinstance(messages, list) or any(not isinstance(m, dict) for m in messages):
            raise ValueError("messages must be a list of dictionaries")
        encoded = json.dumps(messages, ensure_ascii=False, allow_nan=False)
        with self._lock:
            self._db.execute("""
                INSERT INTO conversations(tenant_id, conversation_id, messages_json, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(tenant_id, conversation_id) DO UPDATE SET
                    messages_json=excluded.messages_json, updated_at=CURRENT_TIMESTAMP
            """, (tenant_id, conversation_id, encoded))
            self._db.commit()

    def delete(self, conversation_id: str, *, tenant_id: str = "default") -> bool:
        tenant_id, conversation_id = self._scope(tenant_id, conversation_id)
        with self._lock:
            cursor = self._db.execute(
                "DELETE FROM conversations WHERE tenant_id=? AND conversation_id=?",
                (tenant_id, conversation_id),
            )
            self._db.commit()
            return cursor.rowcount > 0

    def close(self) -> None:
        with self._lock:
            self._db.close()

    def __enter__(self) -> "SQLiteConversationMemory":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
