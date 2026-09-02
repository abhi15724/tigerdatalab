"""Validation schemas for common LLM and ML training records."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ValidationIssue:
    index: int
    code: str
    message: str


@dataclass
class ValidationReport:
    total: int
    valid: int
    invalid: int
    issues: list[ValidationIssue]

    @property
    def validity_rate(self) -> float:
        return round((self.valid / self.total) * 100, 2) if self.total else 0.0


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_record(record: Mapping[str, Any], task: str) -> list[str]:
    task = task.lower()
    if task == "sft":
        messages = record.get("messages")
        if not isinstance(messages, list) or not messages:
            return ["missing_messages"]
        if any(not isinstance(m, Mapping) or m.get("role") not in {"system", "user", "assistant"} or not _nonempty(m.get("content")) for m in messages):
            return ["invalid_messages"]
        if not any(m.get("role") == "user" for m in messages) or not any(m.get("role") == "assistant" for m in messages):
            return ["missing_user_or_assistant"]
        return []
    if task == "instruction":
        return [] if _nonempty(record.get("instruction")) and _nonempty(record.get("output")) else ["missing_instruction_or_output"]
    if task == "dpo":
        if not all(_nonempty(record.get(k)) for k in ("prompt", "chosen", "rejected")):
            return ["missing_preference_fields"]
        return ["identical_preference"] if record["chosen"].strip() == record["rejected"].strip() else []
    if task == "classification":
        return [] if _nonempty(record.get("text")) and _nonempty(record.get("label")) else ["missing_text_or_label"]
    if task == "text":
        return [] if _nonempty(record.get("text")) else ["missing_text"]
    raise ValueError("Supported tasks: sft, instruction, dpo, classification, text")


def validate_records(records: list[dict[str, Any]], task: str) -> ValidationReport:
    issues: list[ValidationIssue] = []
    valid = 0
    for index, record in enumerate(records):
        errors = validate_record(record, task)
        if errors:
            for code in errors:
                issues.append(ValidationIssue(index, code, code.replace("_", " ")))
        else:
            valid += 1
    return ValidationReport(len(records), valid, len(records) - valid, issues)
