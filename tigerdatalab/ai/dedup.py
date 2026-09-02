"""Deterministic exact and lightweight normalized deduplication."""
from __future__ import annotations
import hashlib
import json
import re
from typing import Any

def canonical_record(record: dict[str, Any]) -> str:
    value = {str(k): re.sub(r"\s+", " ", str(v).strip()).lower() if isinstance(v, str) else v for k, v in record.items()}
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def fingerprint(record: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_record(record).encode("utf-8")).hexdigest()

def deduplicate(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    removed = 0
    for record in records:
        key = fingerprint(record)
        if key in seen:
            removed += 1
            continue
        seen.add(key)
        result.append(record)
    return result, removed
