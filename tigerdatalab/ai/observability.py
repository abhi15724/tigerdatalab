"""Framework-neutral runtime observability and token-cost estimation."""
from __future__ import annotations

import logging
import math
import time
from collections import Counter
from threading import RLock
from typing import Any, Mapping, Protocol


class EventObserver(Protocol):
    def record(self, event: Mapping[str, Any]) -> None: ...


class LoggingObserver:
    """Emit structured, JSON-friendly lifecycle events without prompt contents."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger("tigerdatalab.ai.runtime")

    def record(self, event: Mapping[str, Any]) -> None:
        safe = {k: v for k, v in event.items() if k not in {"prompt", "messages", "arguments", "result"}}
        self.logger.info("tigerdatalab_runtime_event", extra={"tigerdatalab_event": safe})


class RuntimeTelemetry:
    """Thread-safe in-process metrics and optional cost estimates.

    prices maps model names to USD per million tokens, e.g.
    {"model-id": {"input": 0.15, "output": 0.60}}. Estimates are informational;
    provider billing is authoritative.
    """

    def __init__(self, prices: Mapping[str, Mapping[str, float]] | None = None) -> None:
        self.prices = {k: dict(v) for k, v in (prices or {}).items()}
        self._lock = RLock()
        self._events = Counter()
        self._tokens = Counter()
        self._cost_usd = Counter()
        self._latencies_ms = []

    def record(self, event: Mapping[str, Any]) -> None:
        name = str(event.get("event", "unknown"))
        with self._lock:
            self._events[name] += 1
            details = event.get("details") or {}
            usage = details.get("usage") or {}
            for key, value in usage.items():
                if isinstance(value, (int, float)) and value >= 0:
                    self._tokens[key] += int(value)
            model = details.get("model")
            price = self.prices.get(str(model), {})
            input_tokens = int(usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0)
            output_tokens = int(usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0)
            self._cost_usd["estimated"] += (
                input_tokens * float(price.get("input", 0)) +
                output_tokens * float(price.get("output", 0))
            ) / 1_000_000
            elapsed = details.get("elapsed_ms")
            if isinstance(elapsed, (int, float)) and elapsed >= 0:
                self._latencies_ms.append(float(elapsed))

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            ordered = sorted(self._latencies_ms)
            p95 = ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)] if ordered else None
            return {
                "events": dict(self._events),
                "tokens": dict(self._tokens),
                "estimated_cost_usd": round(self._cost_usd["estimated"], 8),
                "runs_with_latency": len(ordered),
                "latency_p95_ms": p95,
            }
