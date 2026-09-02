"""Training-example adapters and deterministic dataset splitting.

The public helpers in this module intentionally remain dependency-free so the
AI layer can be used without a model provider or an LLM API.
"""
from __future__ import annotations

from hashlib import sha256
from typing import Any, Iterable, Mapping


def _key(row: Mapping[str, Any], names: tuple[str, ...]) -> str | None:
    keys = {str(k).strip().lower(): k for k in row}
    for name in names:
        if name in keys:
            return str(keys[name])
    return None


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def to_sft(row: Mapping[str, Any]) -> dict[str, Any] | None:
    """Convert common prompt/response columns to OpenAI-style chat SFT JSON."""
    user_key = _key(row, ("user", "prompt", "question", "customer_message", "input", "instruction"))
    assistant_key = _key(row, ("assistant", "response", "answer", "agent_response", "output", "completion"))
    if not user_key or not assistant_key:
        return None
    user, assistant = _text(row.get(user_key)), _text(row.get(assistant_key))
    if not user or not assistant:
        return None
    system_key = _key(row, ("system", "system_prompt", "context"))
    messages = []
    if system_key and _text(row.get(system_key)):
        messages.append({"role": "system", "content": _text(row.get(system_key))})
    messages.extend([
        {"role": "user", "content": user},
        {"role": "assistant", "content": assistant},
    ])
    return {"messages": messages}


def to_instruction(row: Mapping[str, Any]) -> dict[str, Any] | None:
    """Convert instruction/input/output columns to instruction-tuning format."""
    instruction_key = _key(row, ("instruction", "task", "prompt", "question", "user"))
    output_key = _key(row, ("output", "response", "answer", "assistant", "completion"))
    if not instruction_key or not output_key:
        return None
    instruction, output = _text(row.get(instruction_key)), _text(row.get(output_key))
    if not instruction or not output:
        return None
    input_key = _key(row, ("input", "context", "source", "context_text"))
    result: dict[str, Any] = {"instruction": instruction, "output": output}
    if input_key and _text(row.get(input_key)):
        result["input"] = _text(row.get(input_key))
    return result


def to_dpo(row: Mapping[str, Any]) -> dict[str, Any] | None:
    """Convert prompt/chosen/rejected preference records to DPO format."""
    prompt_key = _key(row, ("prompt", "instruction", "question", "user", "input"))
    chosen_key = _key(row, ("chosen", "preferred", "accepted", "positive", "good_response"))
    rejected_key = _key(row, ("rejected", "dispreferred", "declined", "negative", "bad_response"))
    if not prompt_key or not chosen_key or not rejected_key:
        return None
    prompt, chosen, rejected = map(_text, (row.get(prompt_key), row.get(chosen_key), row.get(rejected_key)))
    if not prompt or not chosen or not rejected or chosen == rejected:
        return None
    return {"prompt": prompt, "chosen": chosen, "rejected": rejected}


def to_classification(row: Mapping[str, Any]) -> dict[str, Any] | None:
    """Convert text/label columns to a simple supervised classification record."""
    text_key = _key(row, ("text", "input", "prompt", "question", "content"))
    label_key = _key(row, ("label", "target", "class", "category", "intent"))
    if not text_key or not label_key:
        return None
    text, label = _text(row.get(text_key)), _text(row.get(label_key))
    if not text or not label:
        return None
    return {"text": text, "label": label}


def to_text(row: Mapping[str, Any]) -> dict[str, str] | None:
    """Flatten non-empty fields into one training-text record."""
    values = [_text(value) for value in row.values() if _text(value)]
    return {"text": " ".join(values)} if values else None


def _stable_key(record: Mapping[str, Any]) -> int:
    import json
    payload = json.dumps(record, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))
    return int(sha256(payload.encode("utf-8")).hexdigest()[:16], 16)


def deterministic_split_records(
    records: Iterable[dict[str, Any]],
    train_ratio: float = .8,
    validation_ratio: float = .1,
) -> dict[str, list[dict[str, Any]]]:
    """Stable content-hash split; the same records always land in the same split."""
    if train_ratio <= 0 or validation_ratio < 0 or train_ratio + validation_ratio >= 1:
        raise ValueError("train_ratio must be > 0, validation_ratio >= 0, and their sum < 1")
    ordered = sorted(list(records), key=_stable_key)
    train_cut = train_ratio
    validation_cut = train_ratio + validation_ratio
    buckets = {"train": [], "validation": [], "test": []}
    for record in ordered:
        fraction = (_stable_key(record) % 10_000_000) / 10_000_000
        bucket = "train" if fraction < train_cut else "validation" if fraction < validation_cut else "test"
        buckets[bucket].append(record)
    return buckets


def split_records(records: list[dict[str, Any]], train_ratio: float = .8, validation_ratio: float = .1) -> dict[str, list[dict[str, Any]]]:
    """Backward-compatible positional split retained from the original API."""
    if train_ratio <= 0 or validation_ratio < 0 or train_ratio + validation_ratio >= 1:
        raise ValueError("train_ratio must be > 0, validation_ratio >= 0, and their sum < 1")
    n = len(records)
    train_end = int(n * train_ratio)
    validation_end = train_end + int(n * validation_ratio)
    return {"train": records[:train_end], "validation": records[train_end:validation_end], "test": records[validation_end:]}
