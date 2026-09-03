"""Allow-listed REST API connector with environment-backed credentials."""
from __future__ import annotations
import os
from typing import Any, Mapping
from urllib.parse import urljoin
from urllib.request import Request, urlopen
import json
from .base import Connector, ConnectorError

class APIConnector(Connector):
    def __init__(self, base_url: str, *, auth_env: str | None = None, headers: Mapping[str, str] | None = None, timeout: float = 15.0):
        if not base_url.startswith(("https://", "http://")):
            raise ValueError("base_url must use http:// or https://")
        self.base_url = base_url.rstrip("/") + "/"
        self.auth_env = auth_env
        self.headers = dict(headers or {})
        self.timeout = timeout

    def request(self, operation: str, *, method: str = "GET", path: str = "", params: Mapping[str, Any] | None = None, json_body: Any = None) -> Any:
        if not operation.strip():
            raise ValueError("operation cannot be empty")
        url = urljoin(self.base_url, path.lstrip("/"))
        if params:
            from urllib.parse import urlencode
            url += ("&" if "?" in url else "?") + urlencode({k: v for k, v in params.items() if v is not None})
        headers = {"Accept": "application/json", **self.headers}
        if self.auth_env:
            token = os.getenv(self.auth_env)
            if not token:
                raise ConnectorError(f"Missing credential environment variable: {self.auth_env}")
            headers["Authorization"] = f"Bearer {token}"
        body = None if json_body is None else json.dumps(json_body).encode("utf-8")
        if body is not None:
            headers["Content-Type"] = "application/json"
        try:
            with urlopen(Request(url, data=body, headers=headers, method=method.upper()), timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except Exception as exc:
            raise ConnectorError(f"REST operation '{operation}' failed: {exc}") from exc

    def get(self, path: str, **kwargs: Any) -> Any:
        return self.request("get", method="GET", path=path, **kwargs)
    def post(self, path: str, *, json_body: Any = None, **kwargs: Any) -> Any:
        return self.request("post", method="POST", path=path, json_body=json_body, **kwargs)
