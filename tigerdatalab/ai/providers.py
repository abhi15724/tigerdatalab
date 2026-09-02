"""Provider-agnostic interfaces for calling existing AI models.

The module intentionally uses stdlib-only HTTP so the core package remains
lightweight. Provider API keys are read from environment variables and are
never stored in datasets, lineage, or configuration objects.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Mapping
from urllib import error, request


class ProviderError(RuntimeError):
    """Raised when an AI provider request fails."""


@dataclass(frozen=True)
class AIResponse:
    """Normalized provider response."""
    text: str
    model: str
    usage: Mapping[str, int] = field(default_factory=dict)
    raw: Mapping[str, Any] = field(default_factory=dict)


class Provider:
    """Small interface implemented by model providers."""
    name = "provider"

    def chat(self, messages: list[dict[str, str]], model: str, **kwargs: Any) -> AIResponse:
        raise NotImplementedError


class OpenAIProvider(Provider):
    name = "openai"
    endpoint = "https://api.openai.com/v1/chat/completions"

    def __init__(self, api_key: str | None = None, timeout: float = 60.0) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.timeout = timeout

    def chat(self, messages: list[dict[str, str]], model: str, **kwargs: Any) -> AIResponse:
        if not self.api_key:
            raise ProviderError("OPENAI_API_KEY is not configured")
        payload = {"model": model, "messages": messages, **kwargs}
        req = request.Request(self.endpoint, data=json.dumps(payload).encode(), method="POST")
        req.add_header("Authorization", f"Bearer {self.api_key}")
        req.add_header("Content-Type", "application/json")
        return _http_chat(req, model, self.timeout)


def _http_chat(req: request.Request, model: str, timeout: float) -> AIResponse:
    try:
        with request.urlopen(req, timeout=timeout) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise ProviderError(f"AI provider HTTP {exc.code}: {detail}") from exc
    except (error.URLError, TimeoutError) as exc:
        raise ProviderError(f"AI provider request failed: {exc}") from exc
    try:
        text = raw["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderError("AI provider returned an unexpected response") from exc
    usage = raw.get("usage") or {}
    return AIResponse(text=text, model=raw.get("model", model), usage=usage, raw=raw)


def get_provider(name: str, **kwargs: Any) -> Provider:
    """Return a supported provider adapter."""
    key = name.strip().lower()
    if key == "openai":
        return OpenAIProvider(**kwargs)
    raise ProviderError(f"Unsupported provider: {name!r}. Add an adapter explicitly.")
