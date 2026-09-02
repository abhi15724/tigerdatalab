"""Provider/model routing with cost, latency, capability and health-aware selection."""
from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic
from typing import Any, Mapping

from .providers import AIResponse, Provider, get_provider


class RoutingError(RuntimeError):
    """Raised when no configured model can serve a request."""


@dataclass(frozen=True)
class ModelTarget:
    """A model endpoint plus optional routing metadata.

    The first four fields are backward compatible with the original router.
    """

    provider: Provider
    model: str
    cost_weight: float = 1.0
    latency_weight: float = 1.0
    capabilities: tuple[str, ...] = ()
    estimated_cost_per_1k_tokens: float | None = None
    estimated_latency_ms: float | None = None


@dataclass
class _TargetState:
    failures: int = 0
    successes: int = 0
    latency_ms: float | None = None
    last_error: str | None = None
    opened_until: float = 0.0


class ModelRouter:
    """Intelligent, provider-agnostic model router.

    Strategies:
    - ``ordered``: original deterministic first-success behavior (default).
    - ``cost``: prefer the lowest configured cost.
    - ``latency``: prefer the lowest configured latency.
    - ``balanced``: combine cost, latency and historical reliability.

    The router never assumes that a model belongs to a particular vendor.
    Any :class:`Provider` implementation can be registered.
    """

    def __init__(
        self,
        targets: list[ModelTarget] | None = None,
        *,
        strategy: str = "ordered",
        failure_threshold: int = 2,
        cooldown_seconds: float = 30.0,
    ) -> None:
        self.targets = list(targets or [])
        self.strategy = self._validate_strategy(strategy)
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be >= 0")
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._state: dict[int, _TargetState] = {i: _TargetState() for i in range(len(self.targets))}

    @staticmethod
    def _validate_strategy(strategy: str) -> str:
        value = strategy.strip().lower().replace("_", "-")
        aliases = {"first": "ordered", "fallback": "ordered", "fast": "latency", "cheap": "cost"}
        value = aliases.get(value, value)
        if value not in {"ordered", "cost", "latency", "balanced"}:
            raise ValueError("strategy must be one of: ordered, cost, latency, balanced")
        return value

    def add(
        self,
        provider: Provider,
        model: str,
        *,
        cost_weight: float = 1.0,
        latency_weight: float = 1.0,
        capabilities: tuple[str, ...] | list[str] = (),
        estimated_cost_per_1k_tokens: float | None = None,
        estimated_latency_ms: float | None = None,
    ) -> "ModelRouter":
        if not model.strip():
            raise ValueError("model cannot be empty")
        if cost_weight < 0 or latency_weight < 0:
            raise ValueError("routing weights cannot be negative")
        if estimated_cost_per_1k_tokens is not None and estimated_cost_per_1k_tokens < 0:
            raise ValueError("estimated_cost_per_1k_tokens cannot be negative")
        if estimated_latency_ms is not None and estimated_latency_ms < 0:
            raise ValueError("estimated_latency_ms cannot be negative")
        target = ModelTarget(
            provider,
            model,
            cost_weight,
            latency_weight,
            tuple(str(c).strip().lower() for c in capabilities if str(c).strip()),
            estimated_cost_per_1k_tokens,
            estimated_latency_ms,
        )
        index = len(self.targets)
        self.targets.append(target)
        self._state[index] = _TargetState()
        return self

    def set_strategy(self, strategy: str) -> "ModelRouter":
        """Change the selection strategy without changing registered targets."""
        self.strategy = self._validate_strategy(strategy)
        return self

    def _healthy(self, index: int) -> bool:
        state = self._state.setdefault(index, _TargetState())
        return monotonic() >= state.opened_until

    def _eligible(self, required_capabilities: set[str]) -> list[tuple[int, ModelTarget]]:
        eligible = []
        for index, target in enumerate(self.targets):
            if not self._healthy(index):
                continue
            capabilities = set(target.capabilities)
            if required_capabilities and not required_capabilities.issubset(capabilities):
                continue
            eligible.append((index, target))
        return eligible

    def _score(self, index: int, target: ModelTarget) -> float:
        state = self._state[index]
        reliability = (state.successes + 1) / (state.successes + state.failures + 2)
        cost = target.estimated_cost_per_1k_tokens
        latency = target.estimated_latency_ms
        observed_latency = state.latency_ms if state.latency_ms is not None else latency
        # Unknown pricing/latency is neutral rather than an automatic penalty.
        cost_term = (cost if cost is not None else 1.0) * target.cost_weight
        latency_term = (observed_latency if observed_latency is not None else 1.0) * target.latency_weight
        return cost_term + latency_term / 1000.0 + (1.0 - reliability) * 2.0

    def _ordered_candidates(self, eligible: list[tuple[int, ModelTarget]]) -> list[tuple[int, ModelTarget]]:
        if self.strategy == "ordered":
            return eligible
        if self.strategy == "cost":
            return sorted(eligible, key=lambda item: (
                item[1].estimated_cost_per_1k_tokens is None,
                item[1].estimated_cost_per_1k_tokens if item[1].estimated_cost_per_1k_tokens is not None else float("inf"),
                item[0],
            ))
        if self.strategy == "latency":
            return sorted(eligible, key=lambda item: (
                item[1].estimated_latency_ms is None,
                item[1].estimated_latency_ms if item[1].estimated_latency_ms is not None else float("inf"),
                item[0],
            ))
        return sorted(eligible, key=lambda item: (self._score(item[0], item[1]), item[0]))

    def chat(
        self,
        messages: list[Mapping[str, str]],
        *,
        strategy: str | None = None,
        required_capabilities: set[str] | list[str] | tuple[str, ...] = (),
        max_cost_per_1k_tokens: float | None = None,
        max_latency_ms: float | None = None,
        **kwargs: Any,
    ) -> AIResponse:
        """Route a request and safely fall back across eligible providers.

        Routing controls are consumed by the router and are never forwarded to
        vendor APIs. Provider-specific kwargs continue to pass through.
        """
        if not self.targets:
            raise RoutingError("No model targets configured")
        if strategy is not None:
            strategy = self._validate_strategy(strategy)
        original_strategy = self.strategy
        if strategy is not None:
            self.strategy = strategy
        try:
            required = {str(c).strip().lower() for c in required_capabilities if str(c).strip()}
            eligible = self._eligible(required)
            if max_cost_per_1k_tokens is not None:
                eligible = [x for x in eligible if x[1].estimated_cost_per_1k_tokens is None or x[1].estimated_cost_per_1k_tokens <= max_cost_per_1k_tokens]
            if max_latency_ms is not None:
                eligible = [x for x in eligible if x[1].estimated_latency_ms is None or x[1].estimated_latency_ms <= max_latency_ms]
            candidates = self._ordered_candidates(eligible)
            if not candidates:
                raise RoutingError("No eligible model targets match the routing constraints")

            errors: list[str] = []
            for index, target in candidates:
                state = self._state[index]
                started = monotonic()
                try:
                    response = target.provider.chat(messages, model=target.model, **kwargs)
                except Exception as exc:
                    state.failures += 1
                    state.last_error = str(exc)
                    if state.failures >= self.failure_threshold:
                        state.opened_until = monotonic() + self.cooldown_seconds
                    errors.append(f"{target.provider.name}/{target.model}: {exc}")
                    continue
                elapsed = (monotonic() - started) * 1000.0
                state.successes += 1
                state.failures = 0
                state.last_error = None
                state.latency_ms = elapsed
                state.opened_until = 0.0
                return response
            raise RoutingError("All eligible model targets failed: " + "; ".join(errors))
        finally:
            self.strategy = original_strategy

    def health(self) -> list[dict[str, Any]]:
        """Return non-secret routing/health telemetry for each target."""
        now = monotonic()
        result = []
        for index, target in enumerate(self.targets):
            state = self._state.setdefault(index, _TargetState())
            result.append({
                "provider": target.provider.name,
                "model": target.model,
                "healthy": now >= state.opened_until,
                "successes": state.successes,
                "failures": state.failures,
                "latency_ms": state.latency_ms,
                "last_error": state.last_error,
            })
        return result


def router_from_config(config: list[Mapping[str, Any]]) -> ModelRouter:
    """Build an intelligent router from non-secret configuration."""
    strategy = "ordered"
    failure_threshold = 2
    cooldown_seconds = 30.0
    if config and "strategy" in config[0]:
        strategy = str(config[0]["strategy"])
    router = ModelRouter(strategy=strategy, failure_threshold=failure_threshold, cooldown_seconds=cooldown_seconds)
    for item in config:
        provider_name = str(item.get("provider", ""))
        model = str(item.get("model", ""))
        provider = get_provider(provider_name, **dict(item.get("provider_options", {})))
        capabilities = item.get("capabilities", ())
        router.add(
            provider,
            model,
            cost_weight=float(item.get("cost_weight", 1.0)),
            latency_weight=float(item.get("latency_weight", 1.0)),
            capabilities=capabilities,
            estimated_cost_per_1k_tokens=item.get("estimated_cost_per_1k_tokens"),
            estimated_latency_ms=item.get("estimated_latency_ms"),
        )
    return router
