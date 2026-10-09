import json
from unittest.mock import Mock

import pytest

from tigerdatalab.ai.distributed import Task
from tigerdatalab.ai.graph import GraphCheckpoint, GraphError
from tigerdatalab.ai.postgres_runtime import PostgreSQLCheckpointStore, PostgreSQLTaskQueue


def test_postgres_backends_require_dsn():
    with pytest.raises(ValueError, match="DSN"):
        PostgreSQLTaskQueue("")
    with pytest.raises(ValueError, match="DSN"):
        PostgreSQLCheckpointStore("")


def test_postgres_backends_explain_optional_driver_when_missing(monkeypatch):
    import builtins
    original = builtins.__import__
    def blocked(name, *args, **kwargs):
        if name == "psycopg":
            raise ImportError("blocked in test")
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", blocked)
    with pytest.raises(RuntimeError, match="tigerdatalab\[postgres\]"):
        PostgreSQLTaskQueue("postgresql://example")
    with pytest.raises(RuntimeError, match="tigerdatalab\[postgres\]"):
        PostgreSQLCheckpointStore("postgresql://example")


def test_checkpoint_state_rejects_non_json_values_without_connection():
    store = object.__new__(PostgreSQLCheckpointStore)
    store.dsn = "unused"
    store.connect_timeout = 1
    store._psycopg = Mock()
    cp = GraphCheckpoint("g", "v1", "n", {"not_json": object()})
    with pytest.raises(GraphError, match="JSON-serializable"):
        store.save("run", cp)
    store._psycopg.connect.assert_not_called()
