import pytest

from tigerdatalab.ai import DeploymentError, create_app


class FakeAgent:
    name = "support-agent"
    ready = True

    def ask(self, prompt, **kwargs):
        class Result:
            output = "company answer"
            model = "fake-model"
            context = "policy context"
            tool_results = None
        return Result()

    def run(self, inputs):
        return {"status": "completed", "inputs": inputs}


def test_create_app_exposes_health_and_readiness():
    fastapi = pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    app = create_app(FakeAgent())
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200


def test_create_app_ask_endpoint():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    app = create_app(FakeAgent())
    response = TestClient(app).post("/v1/ask", json={"prompt": "What is the policy?"})
    assert response.status_code == 200
    assert response.json()["output"] == "company answer"


def test_deployment_requires_ready_agent():
    class NotReady:
        ready = False

    with pytest.raises(DeploymentError):
        create_app(NotReady())
