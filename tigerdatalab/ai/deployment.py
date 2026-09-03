"""Production-oriented deployment helpers for TigerDataLab company agents.

The deployment layer deliberately stays lightweight: it creates an ASGI app with
health/readiness endpoints and a JSON inference endpoint. FastAPI/Uvicorn are
optional dependencies so the core package remains dependency-light.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


class DeploymentError(RuntimeError):
    """Raised when an agent cannot be deployed."""


@dataclass(frozen=True)
class DeploymentConfig:
    """Configuration used by a deployed company agent."""
    name: str
    version: str = "1.0.0"
    api_prefix: str = "/v1"


def create_app(agent: Any, *, name: str | None = None, version: str = "1.0.0") -> Any:
    """Create a FastAPI application around a ready CompanyAgent.

    Endpoints:
      GET  /health       process health
      GET  /ready        readiness (requires a connected runtime)
      POST /v1/ask      synchronous agent inference
      POST /v1/run      controlled workflow execution
    """
    try:
        from fastapi import FastAPI, HTTPException
    except ImportError as exc:
        raise DeploymentError(
            "FastAPI is required for deployment. Install with: "
            "pip install 'tigerdatalab[deployment]'"
        ) from exc

    if not getattr(agent, "ready", False):
        raise DeploymentError("Connect or attach the agent runtime before deployment")

    app = FastAPI(
        title=name or getattr(agent, "name", "TigerDataLab Agent"),
        version=version,
        description="TigerDataLab company AI agent runtime",
    )

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {"status": "ok", "agent": getattr(agent, "name", "agent"), "version": version}

    @app.get("/ready")
    def ready() -> dict[str, Any]:
        if not getattr(agent, "ready", False):
            raise HTTPException(status_code=503, detail="agent runtime is not ready")
        return {"status": "ready"}

    @app.post("/v1/ask")
    def ask(payload: Mapping[str, Any]) -> dict[str, Any]:
        prompt = payload.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise HTTPException(status_code=400, detail="prompt must be a non-empty string")
        result = agent.ask(prompt, **dict(payload.get("options") or {}))
        return {
            "output": result.output,
            "model": result.model,
            "context": result.context,
            "tool_results": result.tool_results,
        }

    @app.post("/v1/run")
    def run(payload: Mapping[str, Any] | None = None) -> Any:
        return agent.run(dict(payload or {}))

    return app


def serve(agent: Any, *, host: str = "0.0.0.0", port: int = 8000, **kwargs: Any) -> None:
    """Run the agent with Uvicorn. Intended for local/container deployment."""
    try:
        import uvicorn
    except ImportError as exc:
        raise DeploymentError(
            "Uvicorn is required to serve an agent. Install with: "
            "pip install 'tigerdatalab[deployment]'"
        ) from exc
    app = create_app(agent, **kwargs)
    uvicorn.run(app, host=host, port=port)
