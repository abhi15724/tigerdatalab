"""Deterministic, local-first PII detection and masking."""
from __future__ import annotations
from dataclasses import dataclass, field
import re
from typing import Any

_PATTERNS = {
    "email": re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+(?![\w.-])"),
    "phone": re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)"),
    "ipv4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "credit_card": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
}

@dataclass
class PIIFinding:
    kind: str
    count: int

@dataclass
class PIIScanner:
    findings: list[PIIFinding] = field(default_factory=list)

    def scan(self, value: Any) -> list[PIIFinding]:
        text = "" if value is None else str(value)
        result = [PIIFinding(kind, len(pattern.findall(text))) for kind, pattern in _PATTERNS.items()]
        self.findings = [item for item in result if item.count]
        return self.findings

    def mask(self, value: Any) -> tuple[str, dict[str, int]]:
        text = "" if value is None else str(value)
        counts: dict[str, int] = {}
        for kind, pattern in _PATTERNS.items():
            count = len(pattern.findall(text))
            if count:
                text = pattern.sub(f"[{kind.upper()}]", text)
                counts[kind] = count
        return text, counts

def mask_record(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, int]]:
    """Recursively mask PII in nested training records."""
    counts: dict[str, int] = {}
    scanner = PIIScanner()

    def transform(value: Any) -> Any:
        if isinstance(value, str):
            new_value, found = scanner.mask(value)
            for kind, count in found.items():
                counts[kind] = counts.get(kind, 0) + count
            return new_value
        if isinstance(value, dict):
            return {key: transform(item) for key, item in value.items()}
        if isinstance(value, list):
            return [transform(item) for item in value]
        if isinstance(value, tuple):
            return tuple(transform(item) for item in value)
        return value

    return transform(record), counts
