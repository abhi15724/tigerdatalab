"""Provider-agnostic interfaces for calling existing AI models.

API keys are accepted explicitly or read from environment variables. Keys are
never included in datasets, lineage, reports, or provider response metadata.
The adapters use only the Python standard library so the core package stays
lightweight.
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


class OpenAICompatibleProvider(Provider):
    """Adapter for providers exposing an OpenAI-compatible chat endpoint."""

    name = "openai-compatible"
    endpoint = ""
    api_key_env = ""

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 60.0,
        endpoint: str | None = None,
    ) -> None:
        self.api_key = api_key or (os.getenv(self.api_key_env) if self.api_key_env else None)
        self.timeout = timeout
        if endpoint:
            self.endpoint = endpoint.rstrip("/")

    def chat(self, messages: list[dict[str, str]], model: str, **kwargs: Any) -> AIResponse:
        if not self.api_key:
            raise ProviderError(f"{self.api_key_env or 'API key'} is not configured")
        if not self.endpoint:
            raise ProviderError("Provider endpoint is not configured")
        payload = {"model": model, "messages": messages, **kwargs}
        req = request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
        )
        req.add_header("Authorization", f"Bearer {self.api_key}")
        req.add_header("Content-Type", "application/json")
        return _http_chat(req, model, self.timeout)


class OpenAIProvider(OpenAICompatibleProvider):
    name = "openai"
    endpoint = "https://api.openai.com/v1/chat/completions"
    api_key_env = "OPENAI_API_KEY"


class GroqProvider(OpenAICompatibleProvider):
    name = "groq"
    endpoint = "https://api.groq.com/openai/v1/chat/completions"
    api_key_env = "GROQ_API_KEY"


class OpenRouterProvider(OpenAICompatibleProvider):
    name = "openrouter"
    endpoint = "https://openrouter.ai/api/v1/chat/completions"
    api_key_env = "OPENROUTER_API_KEY"


class MistralProvider(OpenAICompatibleProvider):
    name = "mistral"
    endpoint = "https://api.mistral.ai/v1/chat/completions"
    api_key_env = "MISTRAL_API_KEY"


class TogetherProvider(OpenAICompatibleProvider):
    name = "together"
    endpoint = "https://api.together.xyz/v1/chat/completions"
    api_key_env = "TOGETHER_API_KEY"


class AnthropicProvider(Provider):
    """Adapter for the Anthropic Messages API."""

    name = "anthropic"
    endpoint = "https://api.anthropic.com/v1/messages"
    api_key_env = "ANTHROPIC_API_KEY"

    def __init__(self, api_key: str | None = None, timeout: float = 60.0) -> None:
        self.api_key = api_key or os.getenv(self.api_key_env)
        self.timeout = timeout

    def chat(self, messages: list[dict[str, str]], model: str, **kwargs: Any) -> AIResponse:
        if not self.api_key:
            raise ProviderError(f"{self.api_key_env} is not configured")
        system = kwargs.pop("system", None)
        user_messages = messages
        if system is None:
            system_parts = [m["content"] for m in messages if m.get("role") == "system"]
            system = "\n\n".join(system_parts) or None
            user_messages = [m for m in messages if m.get("role") != "system"]
        payload: dict[str, Any] = {"model": model, "messages": user_messages, **kwargs}
        payload.setdefault("max_tokens", 1024)
        if system:
            payload["system"] = system
        req = request.Request(self.endpoint, data=json.dumps(payload).encode("utf-8"), method="POST")
        req.add_header("x-api-key", self.api_key)
        req.add_header("anthropic-version", "2023-06-01")
        req.add_header("Content-Type", "application/json")
        return _http_anthropic(req, model, self.timeout)


class GeminiProvider(Provider):
    """Adapter for Google's Gemini generateContent REST API."""

    name = "gemini"
    endpoint_template = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    api_key_env = "GOOGLE_API_KEY"

    def __init__(self, api_key: str | None = None, timeout: float = 60.0) -> None:
        self.api_key = api_key or os.getenv(self.api_key_env)
        self.timeout = timeout

    def chat(self, messages: list[dict[str, str]], model: str, **kwargs: Any) -> AIResponse:
        if not self.api_key:
            raise ProviderError(f"{self.api_key_env} is not configured")
        contents: list[dict[str, Any]] = []
        system_parts: list[str] = []
        for message in messages:
            role = message.get("role", "user")
            text = message.get("content", "")
            if role == "system":
                system_parts.append(text)
                continue
            contents.append({"role": "model" if role == "assistant" else "user", "parts": [{"text": text}]})
        payload: dict[str, Any] = {"contents": contents}
        if system_parts:
            payload["systemInstruction"] = {"parts": [{"text": "\n\n".join(system_parts)}]}
        for key in ("generationConfig", "safetySettings", "tools", "toolConfig"):
            if key in kwargs:
                payload[key] = kwargs[key]
        url = self.endpoint_template.format(model=model) + "?key=" + self.api_key
        req = request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST")
        req.add_header("Content-Type", "application/json")
        return _http_gemini(req, model, self.timeout)


def _http_json(req: request.Request, timeout: float) -> Mapping[str, Any]:
    try:
        with request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise ProviderError(f"AI provider HTTP {exc.code}: {detail}") from exc
    except (error.URLError, TimeoutError) as exc:
        raise ProviderError(f"AI provider request failed: {exc}") from exc
    if not isinstance(data, Mapping):
        raise ProviderError("AI provider returned an unexpected response")
    return data


def _http_chat(req: request.Request, model: str, timeout: float) -> AIResponse:
    raw = _http_json(req, timeout)
    try:
        text = raw["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderError("AI provider returned an unexpected chat response") from exc
    return AIResponse(text=text, model=str(raw.get("model", model)), usage=raw.get("usage") or {}, raw=raw)


def _http_anthropic(req: request.Request, model: str, timeout: float) -> AIResponse:
    raw = _http_json(req, timeout)
    try:
        blocks = raw["content"]
        text = "\n".join(block.get("text", "") for block in blocks if block.get("type") == "text")
    except (KeyError, TypeError) as exc:
        raise ProviderError("Anthropic returned an unexpected response") from exc
    return AIResponse(text=text, model=str(raw.get("model", model)), usage=raw.get("usage") or {}, raw=raw)


def _http_gemini(req: request.Request, model: str, timeout: float) -> AIResponse:
    raw = _http_json(req, timeout)
    try:
        parts = raw["candidates"][0]["content"]["parts"]
        text = "\n".join(part.get("text", "") for part in parts if "text" in part)
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderError("Gemini returned an unexpected response") from exc
    usage = raw.get("usageMetadata") or {}
    return AIResponse(text=text, model=model, usage=usage, raw=raw)


def get_provider(name: str, **kwargs: Any) -> Provider:
    """Return a supported provider adapter by name."""
    key = name.strip().lower().replace("_", "-")
    providers: dict[str, type[Provider]] = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "claude": AnthropicProvider,
        "gemini": GeminiProvider,
        "google": GeminiProvider,
        "groq": GroqProvider,
        "openrouter": OpenRouterProvider,
        "mistral": MistralProvider,
        "together": TogetherProvider,
    }
    provider_class = providers.get(key)
    if provider_class is None:
        raise ProviderError(f"Unsupported provider: {name!r}. Add an adapter explicitly.")
    return provider_class(**kwargs)
