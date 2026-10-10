import pytest

from tigerdatalab.ai import DeploymentError, create_app


class FakeAgent:
    name = "secure-agent"
    ready = True

    def ask(self, prompt, **kwargs):
        class Result:
            output = "ok"
            model = "fake"
            context = ""
            tool_results = None
        return Result()

    def run(self, inputs):
        return {"status": "completed"}


def test_auth_rejects_invalid_key():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    client = TestClient(create_app(FakeAgent(), api_key="secret"))
    assert client.get("/v1/audit").status_code == 401
    assert client.post("/v1/ask", json={"prompt": "hi"}).status_code == 401
    assert client.post("/v1/ask", json={"prompt": "hi"}, headers={"Authorization": "Bearer wrong"}).status_code == 401


def test_auth_accepts_valid_key_and_audits_request():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    client = TestClient(create_app(FakeAgent(), api_key="secret", audit_reader_key="audit-secret"))
    headers = {"Authorization": "Bearer secret"}
    response = client.post("/v1/ask", json={"prompt": "hi"}, headers=headers)
    assert response.status_code == 200
    events = client.get("/v1/audit", headers={**headers, "X-Audit-Reader-Key": "audit-secret"})
    assert events.status_code == 200
    assert any(event["event"] == "agent_ask" for event in events.json())


def test_rate_limit_returns_429():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    client = TestClient(create_app(FakeAgent(), require_auth=False, rate_limit=1, rate_window_seconds=60))
    assert client.post("/v1/ask", json={"prompt": "one"}).status_code == 200
    assert client.post("/v1/ask", json={"prompt": "two"}).status_code == 429


def test_auth_required_without_key_is_configuration_error():
    pytest.importorskip("fastapi")
    with pytest.raises(DeploymentError):
        create_app(FakeAgent(), require_auth=True)

def test_auth_is_required_by_default_without_key(monkeypatch):
    pytest.importorskip("fastapi")
    monkeypatch.delenv("TIGERDATALAB_API_KEY", raising=False)
    with pytest.raises(DeploymentError, match="Authentication is enabled by default"):
        create_app(FakeAgent())


def test_whitespace_api_key_is_rejected():
    pytest.importorskip("fastapi")
    with pytest.raises(DeploymentError, match="must not be empty"):
        create_app(FakeAgent(), api_key="   ")


def test_prompt_must_be_non_empty_string_and_bad_options_are_rejected():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    client = TestClient(create_app(FakeAgent(), api_key="secret"))
    headers = {"Authorization": "Bearer secret"}
    assert client.post("/v1/ask", json={"prompt": "  "}, headers=headers).status_code == 400
    assert client.post("/v1/ask", json={"prompt": "hi", "options": []}, headers=headers).status_code == 400


def test_forwarded_for_header_does_not_override_rate_limit_identity():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    client = TestClient(create_app(FakeAgent(), require_auth=False, rate_limit=1, rate_window_seconds=60))
    assert client.post("/v1/ask", json={"prompt": "one"}, headers={"X-Forwarded-For": "198.51.100.1"}).status_code == 200
    assert client.post("/v1/ask", json={"prompt": "two"}, headers={"X-Forwarded-For": "203.0.113.7"}).status_code == 429
