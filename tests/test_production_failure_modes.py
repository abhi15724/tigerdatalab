"""Failure-injection and security regression tests for production readiness."""
import time

import pytest

from tigerdatalab.ai.agent_runtime import AgentRuntime, AgentTurn
from tigerdatalab.ai.distributed import QueueError, SQLiteTaskQueue, TaskWorker
from tigerdatalab.ai.deployment import DeploymentError, create_app


class ReadyAgent:
    name = "staging-test-agent"
    ready = True

    def ask(self, prompt, **kwargs):
        class Result:
            output = "synthetic response"
            model = "test-model"
            context = None
            tool_results = None
        return Result()


def test_deployment_fails_closed_without_credentials(monkeypatch):
    pytest.importorskip("fastapi")
    monkeypatch.delenv("TIGERDATALAB_API_KEY", raising=False)
    with pytest.raises(DeploymentError, match="Authentication is enabled by default"):
        create_app(ReadyAgent())


def test_deployment_rejects_bad_credentials_and_accepts_valid_bearer():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    client = TestClient(create_app(ReadyAgent(), api_key="staging-test-secret"))
    assert client.post("/v1/ask", json={"prompt": "synthetic test"}).status_code == 401
    assert client.post("/v1/ask", json={"prompt": "synthetic test"},
                       headers={"Authorization": "Bearer wrong"}).status_code == 401
    response = client.post("/v1/ask", json={"prompt": "synthetic test"},
                           headers={"Authorization": "Bearer staging-test-secret"})
    assert response.status_code == 200


def test_spoofed_forwarded_for_does_not_bypass_rate_limit():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    client = TestClient(create_app(ReadyAgent(), require_auth=False, rate_limit=1, rate_window_seconds=60))
    first = client.post("/v1/ask", json={"prompt": "synthetic"},
                        headers={"X-Forwarded-For": "198.51.100.10"})
    second = client.post("/v1/ask", json={"prompt": "synthetic"},
                         headers={"X-Forwarded-For": "203.0.113.99"})
    assert first.status_code == 200
    assert second.status_code == 429


def test_worker_retries_transient_failure_then_marks_terminal_failure(tmp_path):
    with SQLiteTaskQueue(tmp_path / "retry.sqlite3") as queue:
        task_id = queue.enqueue("flaky", {"safe": True}, tenant_id="tenant-a", max_attempts=2)
        worker = TaskWorker(queue, "worker-a", {"flaky": lambda payload: (_ for _ in ()).throw(RuntimeError("injected failure"))})
        assert worker.process_once()
        after_first = queue.get(task_id, tenant_id="tenant-a")
        assert after_first["status"] == "queued"
        assert after_first["attempts"] == 1
        assert worker.process_once()
        after_second = queue.get(task_id, tenant_id="tenant-a")
        assert after_second["status"] == "failed"
        assert after_second["attempts"] == 2
        assert "injected failure" in after_second["error"]


def test_expired_worker_lease_cannot_overwrite_new_owner(tmp_path):
    with SQLiteTaskQueue(tmp_path / "lease.sqlite3") as queue:
        task_id = queue.enqueue("work", {}, tenant_id="tenant-a", max_attempts=3)
        first = queue.claim("worker-a", lease_seconds=0.02)
        assert first is not None and first.id == task_id
        time.sleep(0.04)
        second = queue.claim("worker-b", lease_seconds=1)
        assert second is not None and second.id == task_id
        with pytest.raises(QueueError, match="lease"):
            queue.complete(task_id, "worker-a", {"stale": True})
        queue.complete(task_id, "worker-b", {"owner": "worker-b"})
        assert queue.get(task_id, tenant_id="tenant-a")["result"] == {"owner": "worker-b"}


def test_runtime_model_timeout_returns_failure_without_hanging():
    import time as _time

    def slow_model(messages, schemas):
        _time.sleep(0.2)
        return AgentTurn(text="late")

    result = AgentRuntime(slow_model, model_timeout_seconds=0.01).run("synthetic timeout probe")
    assert result.status == "failed"
    assert "timed out" in (result.error or "").lower()
    assert "secret" not in (result.error or "").lower()

def test_audit_endpoint_requires_separate_reader_credential():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    hidden = TestClient(create_app(ReadyAgent(), api_key="service-key"))
    assert hidden.get("/v1/audit", headers={"Authorization": "Bearer service-key"}).status_code == 404

    protected = TestClient(create_app(
        ReadyAgent(), api_key="service-key", audit_reader_key="audit-reader-secret"
    ))
    service_only = protected.get("/v1/audit", headers={"Authorization": "Bearer service-key"})
    assert service_only.status_code == 403
    reader = protected.get("/v1/audit", headers={
        "Authorization": "Bearer service-key",
        "X-Audit-Reader-Key": "audit-reader-secret",
    })
    assert reader.status_code == 200

def test_public_inference_rejects_unbounded_router_and_provider_options():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    client = TestClient(create_app(ReadyAgent(), api_key="service-key"))
    headers = {"Authorization": "Bearer service-key"}
    for options in ({"strategy": "cost"}, {"max_tokens": 10}, {"top_k": True}, {"top_k": 1000}):
        response = client.post("/v1/ask", headers=headers,
                               json={"prompt": "synthetic", "options": options})
        assert response.status_code == 400, (options, response.text)

    allowed = client.post("/v1/ask", headers=headers,
                          json={"prompt": "synthetic", "options": {"top_k": 3}})
    assert allowed.status_code == 200
