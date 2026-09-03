"""Secure, production-oriented deployment helpers for TigerDataLab agents."""
from __future__ import annotations

import hashlib
import os
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Mapping

try:
    # FastAPI is an optional deployment dependency. Importing Request at module
    # scope is intentional: FastAPI resolves postponed endpoint annotations
    # from the function's global namespace, not the local scope of create_app().
    from fastapi import Request
except ImportError:  # pragma: no cover - exercised only without FastAPI installed
    Request = Any  # type: ignore[misc,assignment]


class DeploymentError(RuntimeError):
    """Raised when an agent cannot be deployed."""


@dataclass(frozen=True)
class DeploymentConfig:
    """Configuration for a deployed company agent."""
    name: str
    version: str = "1.0.0"
    api_prefix: str = "/v1"
    api_key_env: str = "TIGERDATALAB_API_KEY"
    rate_limit: int = 60
    rate_window_seconds: int = 60


class InMemoryAuditLog:
    """Small, thread-safe audit sink suitable for a single process."""

    def __init__(self, max_entries: int = 10000) -> None:
        self._events: deque[dict[str, Any]] = deque(maxlen=max_entries)
        self._lock = threading.Lock()

    def record(self, event: Mapping[str, Any]) -> None:
        with self._lock:
            self._events.append(dict(event))

    def events(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._events)


def _client_id(request: Any) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    return (
        forwarded.split(",", 1)[0].strip()
        if forwarded
        else request.client.host if request.client else "unknown"
    )


def create_app(
    agent: Any,
    *,
    name: str | None = None,
    version: str = "1.0.0",
    api_key: str | None = None,
    rate_limit: int = 60,
    rate_window_seconds: int = 60,
    audit_log: Any | None = None,
    require_auth: bool | None = None,
) -> Any:
    """Create a FastAPI app with auth, rate limiting and audit hooks.

    ``api_key`` can be supplied directly or via ``TIGERDATALAB_API_KEY``.
    If no key is configured, authentication remains disabled for backwards
    compatibility; internet-facing deployments should always configure one.
    """
    try:
        from fastapi import Body, FastAPI, HTTPException
    except ImportError as exc:
        raise DeploymentError(
            "FastAPI is required for deployment. Install with: "
            "pip install 'tigerdatalab[deployment]'"
        ) from exc

    if not getattr(agent, "ready", False):
        raise DeploymentError("Connect or attach the agent runtime before deployment")
    if rate_limit < 1 or rate_window_seconds < 1:
        raise DeploymentError("rate_limit and rate_window_seconds must be positive")

    configured_key = api_key or os.getenv("TIGERDATALAB_API_KEY")
    auth_required = bool(configured_key) if require_auth is None else require_auth
    if auth_required and not configured_key:
        raise DeploymentError("Authentication is required but no API key is configured")

    app = FastAPI(
        title=name or getattr(agent, "name", "TigerDataLab Agent"),
        version=version,
        description="TigerDataLab company AI agent runtime",
    )
    audit = audit_log or InMemoryAuditLog()
    buckets: dict[str, deque[float]] = {}
    lock = threading.Lock()

    def guard(request: Request) -> str:
        """Authenticate and rate-limit a request."""
        identity = _client_id(request)
        authorization = request.headers.get("authorization")
        if auth_required:
            expected = f"Bearer {configured_key}"
            if (
                not authorization
                or hashlib.sha256(authorization.encode()).digest()
                != hashlib.sha256(expected.encode()).digest()
            ):
                audit.record(
                    {
                        "event": "auth_failed",
                        "path": request.url.path,
                        "client": identity,
                        "timestamp": time.time(),
                    }
                )
                raise HTTPException(status_code=401, detail="invalid or missing API credentials")

        now = time.monotonic()
        with lock:
            bucket = buckets.setdefault(identity, deque())
            cutoff = now - rate_window_seconds
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= rate_limit:
                audit.record(
                    {
                        "event": "rate_limited",
                        "path": request.url.path,
                        "client": identity,
                        "timestamp": time.time(),
                    }
                )
                raise HTTPException(status_code=429, detail="rate limit exceeded")
            bucket.append(now)
        return identity

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {"status": "ok", "agent": getattr(agent, "name", "agent"), "version": version}

    @app.get("/ready")
    def ready() -> dict[str, Any]:
        if not getattr(agent, "ready", False):
            raise HTTPException(status_code=503, detail="agent runtime is not ready")
        return {"status": "ready"}

    @app.post("/v1/ask")
    def ask(
        request: Request,
        payload: Mapping[str, Any] = Body(...),
    ) -> dict[str, Any]:
        identity = guard(request)
        prompt = payload.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise HTTPException(status_code=400, detail="prompt must be a non-empty string")
        options = dict(payload.get("options") or {})
        result = agent.ask(prompt, **options)
        audit.record(
            {
                "event": "agent_ask",
                "path": "/v1/ask",
                "client": identity,
                "timestamp": time.time(),
                "model": result.model,
            }
        )
        return {
            "output": result.output,
            "model": result.model,
            "context": result.context,
            "tool_results": result.tool_results,
        }

    @app.post("/v1/run")
    def run(
        request: Request,
        payload: Mapping[str, Any] | None = Body(default=None),
    ) -> Any:
        identity = guard(request)
        result = agent.run(dict(payload or {}))
        audit.record(
            {
                "event": "workflow_run",
                "path": "/v1/run",
                "client": identity,
                "timestamp": time.time(),
            }
        )
        return result

    @app.get("/v1/audit")
    def audit_events(request: Request) -> list[dict[str, Any]]:
        guard(request)
        if not hasattr(audit, "events"):
            raise HTTPException(status_code=501, detail="audit sink does not support reading events")
        return audit.events()

    return app


def serve(agent: Any, *, host: str = "0.0.0.0", port: int = 8000, **kwargs: Any) -> None:
    """Run the agent with Uvicorn; TLS and other Uvicorn options may be passed through."""
    try:
        import uvicorn
    except ImportError as exc:
        raise DeploymentError(
            "Uvicorn is required to serve an agent. Install with: "
            "pip install 'tigerdatalab[deployment]'"
        ) from exc
    app = create_app(agent, **kwargs)
    uvicorn.run(app, host=host, port=port)
