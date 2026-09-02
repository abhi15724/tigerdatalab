"""Model evaluation primitives for company AI workflows."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping


@dataclass(frozen=True)
class EvaluationResult:
    total: int
    passed: int
    failed: int
    score: float
    average_latency_ms: float
    failures: list[dict[str, Any]] = field(default_factory=list)


class Evaluator:
    """Evaluate a callable model against expected outputs or custom checks."""

    def __init__(self, *, scorer: Callable[[str, Mapping[str, Any]], bool] | None = None) -> None:
        self.scorer = scorer or self._default_scorer

    @staticmethod
    def _default_scorer(output: str, record: Mapping[str, Any]) -> bool:
        expected = record.get("expected")
        if expected is None:
            return bool(output.strip())
        return output.strip().casefold() == str(expected).strip().casefold()

    def evaluate(self, model: Callable[[str], str], records: Iterable[Mapping[str, Any]]) -> EvaluationResult:
        failures: list[dict[str, Any]] = []
        passed = 0
        total = 0
        latencies: list[float] = []
        for record in records:
            prompt = str(record.get("prompt", record.get("input", "")))
            started = time.perf_counter()
            try:
                output = str(model(prompt))
                ok = self.scorer(output, record)
                error_message = None
            except Exception as exc:  # evaluation must report failures, not abort the suite
                output = ""
                ok = False
                error_message = str(exc)
            latencies.append((time.perf_counter() - started) * 1000)
            total += 1
            if ok:
                passed += 1
            else:
                failures.append({"prompt": prompt, "output": output, "expected": record.get("expected"), "error": error_message})
        return EvaluationResult(
            total=total,
            passed=passed,
            failed=total - passed,
            score=(passed / total if total else 0.0),
            average_latency_ms=(sum(latencies) / len(latencies) if latencies else 0.0),
            failures=failures,
        )


def evaluate(model: Callable[[str], str], records: Iterable[Mapping[str, Any]], *, scorer: Callable[[str, Mapping[str, Any]], bool] | None = None) -> EvaluationResult:
    return Evaluator(scorer=scorer).evaluate(model, records)
