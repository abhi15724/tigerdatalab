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

    client = TestClient(create_app(FakeAgent(), api_key="secret"))
    headers = {"Authorization": "Bearer secret"}
    response = client.post("/v1/ask", json={"prompt": "hi"}, headers=headers)
    assert response.status_code == 200
    events = client.get("/v1/audit", headers=headers)
    assert events.status_code == 200
    assert any(event["event"] == "agent_ask" for event in events.json())


def test_rate_limit_returns_429():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    client = TestClient(create_app(FakeAgent(), rate_limit=1, rate_window_seconds=60))
    assert client.post("/v1/ask", json={"prompt": "one"}).status_code == 200
    assert client.post("/v1/ask", json={"prompt": "two"}).status_code == 429


def test_auth_required_without_key_is_configuration_error():
    pytest.importorskip("fastapi")
    with pytest.raises(DeploymentError):
        create_app(FakeAgent(), require_auth=True)
