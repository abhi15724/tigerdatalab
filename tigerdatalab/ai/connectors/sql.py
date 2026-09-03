"""Read-only SQL connector. Requires an installed DB-API driver."""
from __future__ import annotations
from typing import Any
from .base import Connector, ConnectorError

class SQLConnector(Connector):
    def __init__(self, connection: Any, *, allow_write: bool = False):
        self.connection = connection
        self.allow_write = allow_write

    def request(self, operation: str, *, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        statement = query.lstrip().lower()
        if not self.allow_write and not statement.startswith(("select", "with", "pragma", "explain")):
            raise ConnectorError("SQLConnector is read-only; enable allow_write explicitly for mutations")
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            if cursor.description is None:
                self.connection.commit()
                return []
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as exc:
            raise ConnectorError(f"SQL operation '{operation}' failed: {exc}") from exc
