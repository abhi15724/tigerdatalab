"""Optional integration tests; set TIGERDATALAB_TEST_POSTGRES_DSN to enable."""
import os
import uuid

import pytest

from tigerdatalab.ai.graph import GraphCheckpoint
from tigerdatalab.ai.postgres_runtime import PostgreSQLCheckpointStore, PostgreSQLTaskQueue

DSN = os.getenv("TIGERDATALAB_TEST_POSTGRES_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="PostgreSQL integration DSN not configured")


def test_postgres_queue_claim_renew_complete_and_tenant_scope():
    queue = PostgreSQLTaskQueue(DSN)
    tenant = "integration-" + uuid.uuid4().hex
    task_id = queue.enqueue("integration", {"ok": True}, tenant_id=tenant)
    task = queue.claim("worker-integration", lease_seconds=30)
    assert task is not None and task.id == task_id
    queue.renew_lease(task_id, "worker-integration", lease_seconds=30)
    queue.complete(task_id, "worker-integration", {"done": True})
    assert queue.get(task_id, tenant_id=tenant)["result"] == {"done": True}
    assert queue.get(task_id, tenant_id="another-tenant") is None


def test_postgres_checkpoint_roundtrip():
    store = PostgreSQLCheckpointStore(DSN)
    run_id = "integration-" + uuid.uuid4().hex
    checkpoint = GraphCheckpoint("integration-graph", "v1", "node-a",
                                  {"query": "ping"}, ["node-start"], 1, "running")
    store.save(run_id, checkpoint)
    loaded = store.load(run_id)
    assert loaded is not None
    assert loaded.graph_name == checkpoint.graph_name
    assert loaded.state == checkpoint.state
    assert loaded.completed_nodes == checkpoint.completed_nodes
