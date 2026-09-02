"""Training-data quality metrics and audit helpers."""
from __future__ import annotations

from collections import Counter
from typing import Any


def _strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)


def quality_metrics(records: list[dict[str, Any]], validation_rate: float | None = None) -> dict[str, Any]:
    """Return deterministic, model-independent quality metrics."""
    texts = [text for record in records for text in _strings(record) if text.strip()]
    lengths = [len(text) for text in texts]
    return {
        "records": len(records),
        "text_fields": len(texts),
        "empty_text_fields": sum(1 for record in records for text in _strings(record) if not text.strip()),
        "characters": sum(lengths),
        "avg_characters": round(sum(lengths) / len(lengths), 2) if lengths else 0.0,
        "min_characters": min(lengths) if lengths else 0,
        "max_characters": max(lengths) if lengths else 0,
        "validation_rate": validation_rate if validation_rate is not None else 100.0,
    }


def label_distribution(records: list[dict[str, Any]], label_key: str = "label") -> dict[str, int]:
    """Count classification labels without imposing a vocabulary."""
    return dict(Counter(str(r[label_key]).strip() for r in records if str(r.get(label_key, "")).strip()))
