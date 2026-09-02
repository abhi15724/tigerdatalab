import pytest

from tigerdatalab.ai import AIResponse, ModelRouter, Provider, RoutingError, router_from_config


class FakeProvider(Provider):
    def __init__(self, name, *, fail=False):
        self.name = name
        self.fail = fail
        self.calls = 0

    def chat(self, messages, model, **kwargs):
        self.calls += 1
        if self.fail:
            raise RuntimeError("offline")
        return AIResponse(text=f"answer from {self.name}", model=model)


def test_router_supports_multiple_providers():
    first = FakeProvider("openai")
    second = FakeProvider("anthropic")
    router = ModelRouter()
    router.add(first, "gpt-test").add(second, "claude-test")
    result = router.chat([{"role": "user", "content": "hi"}])
    assert result.model == "gpt-test"
    assert first.calls == 1
    assert second.calls == 0


def test_router_falls_back_and_opens_unhealthy_target():
    primary = FakeProvider("primary", fail=True)
    fallback = FakeProvider("fallback")
    router = ModelRouter(failure_threshold=1, cooldown_seconds=60)
    router.add(primary, "primary-model").add(fallback, "fallback-model")

    result = router.chat([{"role": "user", "content": "hi"}])
    assert result.model == "fallback-model"
    assert router.health()[0]["healthy"] is False
    assert primary.calls == 1

    result = router.chat([{"role": "user", "content": "again"}])
    assert result.model == "fallback-model"
    assert primary.calls == 1


def test_cost_strategy_prefers_cheapest_configured_model():
    expensive = FakeProvider("expensive")
    cheap = FakeProvider("cheap")
    router = ModelRouter(strategy="cost")
    router.add(expensive, "expensive", estimated_cost_per_1k_tokens=2.0)
    router.add(cheap, "cheap", estimated_cost_per_1k_tokens=0.2)
    result = router.chat([{"role": "user", "content": "hi"}])
    assert result.model == "cheap"


def test_latency_strategy_prefers_fastest_configured_model():
    slow = FakeProvider("slow")
    fast = FakeProvider("fast")
    router = ModelRouter(strategy="latency")
    router.add(slow, "slow", estimated_latency_ms=900)
    router.add(fast, "fast", estimated_latency_ms=120)
    result = router.chat([{"role": "user", "content": "hi"}])
    assert result.model == "fast"


def test_capability_filtering():
    basic = FakeProvider("basic")
    vision = FakeProvider("vision")
    router = ModelRouter()
    router.add(basic, "basic", capabilities=("chat",))
    router.add(vision, "vision", capabilities=("chat", "vision"))
    result = router.chat([{"role": "user", "content": "describe image"}], required_capabilities={"vision"})
    assert result.model == "vision"


def test_router_constraints_fail_cleanly():
    provider = FakeProvider("provider")
    router = ModelRouter()
    router.add(provider, "model", estimated_cost_per_1k_tokens=1.0)
    with pytest.raises(RoutingError, match="No eligible"):
        router.chat([{"role": "user", "content": "hi"}], max_cost_per_1k_tokens=0.1)


def test_router_from_config_preserves_provider_agnostic_design(monkeypatch):
    monkeypatch.setattr("tigerdatalab.ai.router.get_provider", lambda name, **kwargs: FakeProvider(name))
    router = router_from_config([
        {"provider": "openai", "model": "gpt-test", "strategy": "balanced", "capabilities": ["chat"]},
        {"provider": "anthropic", "model": "claude-test", "capabilities": ["chat", "reasoning"]},
    ])
    assert router.strategy == "balanced"
    assert [target.provider.name for target in router.targets] == ["openai", "anthropic"]
