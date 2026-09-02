"""AI dataset formatters and deterministic splits."""
from __future__ import annotations
from typing import Any

def _key(row: dict[str, Any], names: tuple[str, ...]) -> str | None:
    keys = {str(k).strip().lower(): k for k in row}
    for name in names:
        if name in keys:
            return keys[name]
    return None

def to_sft(row: dict[str, Any]) -> dict[str, Any] | None:
    user_key = _key(row, ("user", "prompt", "question", "customer_message", "input", "instruction"))
    assistant_key = _key(row, ("assistant", "response", "answer", "agent_response", "output", "completion"))
    if not user_key or not assistant_key:
        return None
    user = str(row.get(user_key) or "").strip()
    assistant = str(row.get(assistant_key) or "").strip()
    if not user or not assistant:
        return None
    return {"messages": [{"role": "user", "content": user}, {"role": "assistant", "content": assistant}]}

def split_records(records: list[dict[str, Any]], train_ratio: float = .8, validation_ratio: float = .1) -> dict[str, list[dict[str, Any]]]:
    if train_ratio <= 0 or validation_ratio < 0 or train_ratio + validation_ratio >= 1:
        raise ValueError("train_ratio must be > 0, validation_ratio >= 0, and their sum < 1")
    n = len(records)
    train_end = int(n * train_ratio)
    validation_end = train_end + int(n * validation_ratio)
    return {"train": records[:train_end], "validation": records[train_end:validation_end], "test": records[validation_end:]}
