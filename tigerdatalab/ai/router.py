"""Provider/model routing without forcing a vendor SDK into the core package."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .providers import AIResponse, Provider, get_provider


class RoutingError(RuntimeError):
    """Raised when no configured model can serve a request."""


@dataclass(frozen=True)
class ModelTarget:
    provider: Provider
    model: str
    cost_weight: float = 1.0
    latency_weight: float = 1.0


class ModelRouter:
    """Ordered model router with optional task preferences and safe fallbacks."""

    def __init__(self, targets: list[ModelTarget] | None = None):
        self.targets = list(targets or [])

    def add(self, provider: Provider, model: str, *, cost_weight: float = 1.0, latency_weight: float = 1.0) -> "ModelRouter":
        if not model.strip():
            raise ValueError("model cannot be empty")
        self.targets.append(ModelTarget(provider, model, cost_weight, latency_weight))
        return self

    def chat(self, messages: list[Mapping[str, str]], **kwargs: Any) -> AIResponse:
        if not self.targets:
            raise RoutingError("No model targets configured")
        errors: list[str] = []
        for target in self.targets:
            try:
                return target.provider.chat(messages, model=target.model, **kwargs)
            except Exception as exc:
                errors.append(f"{target.model}: {exc}")
        raise RoutingError("All model targets failed: " + "; ".join(errors))


def router_from_config(config: list[Mapping[str, Any]]) -> ModelRouter:
    """Build a router from non-secret configuration; provider reads credentials from its environment."""
    router = ModelRouter()
    for item in config:
        provider_name = str(item.get("provider", ""))
        model = str(item.get("model", ""))
        provider = get_provider(provider_name, **dict(item.get("provider_options", {})))
        router.add(provider, model, cost_weight=float(item.get("cost_weight", 1.0)), latency_weight=float(item.get("latency_weight", 1.0)))
    return router
