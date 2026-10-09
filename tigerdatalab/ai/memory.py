"""Local project memory and selective skill loading for AI-agent workflows.

Memory is explicit, JSON-only, and intended for trusted local workspaces. Never
store API keys, passwords, private keys, or other credentials in project memory.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_SKILL_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
_TASK_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,99}$")
_SECRET_KEY_PARTS = ("api_key", "access_token", "password", "secret", "private_key", "credential")


class MemoryError(ValueError):
    """Raised when project memory or a skill file is invalid."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_json_value(value: Any, path: str = "$") -> None:
    """Reject non-JSON values and credential-shaped fields before persistence."""
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            normalized = key_text.lower().replace("-", "_")
            if any(part in normalized for part in _SECRET_KEY_PARTS):
                raise MemoryError(f"Refusing to persist sensitive field at {path}.{key_text}")
            _validate_json_value(item, f"{path}.{key_text}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _validate_json_value(item, f"{path}[{index}]")
    elif value is not None and not isinstance(value, (str, int, float, bool)):
        raise MemoryError(f"Unsupported JSON value at {path}: {type(value).__name__}")


def _write_json_atomic(path: Path, payload: Mapping[str, Any], max_bytes: int) -> None:
    _validate_json_value(payload)
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    if len(encoded) > max_bytes:
        raise MemoryError(f"Memory document exceeds {max_bytes} bytes")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_bytes(encoded)
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


class SkillLoader:
    """Load only explicitly requested .agents/skills/<name>/SKILL.md files."""

    def __init__(self, root: str | Path = ".agents/skills", *, max_skill_bytes: int = 64_000):
        self.root = Path(root).resolve()
        self.max_skill_bytes = max_skill_bytes

    def list_skills(self) -> list[str]:
        if not self.root.is_dir():
            return []
        return sorted(
            item.name for item in self.root.iterdir()
            if item.is_dir() and _SKILL_NAME.fullmatch(item.name)
            and (item / "SKILL.md").is_file()
        )

    def load(self, names: list[str] | tuple[str, ...]) -> dict[str, str]:
        """Load requested skills; fail clearly rather than silently loading everything."""
        loaded: dict[str, str] = {}
        for name in names:
            if not _SKILL_NAME.fullmatch(name):
                raise MemoryError(f"Invalid skill name: {name!r}")
            skill_path = (self.root / name / "SKILL.md").resolve()
            if not skill_path.is_relative_to(self.root):
                raise MemoryError("Skill path escapes the configured skills directory")
            if not skill_path.is_file():
                raise MemoryError(f"Skill not found: {name}")
            content = skill_path.read_bytes()
            if len(content) > self.max_skill_bytes:
                raise MemoryError(f"Skill '{name}' exceeds {self.max_skill_bytes} bytes")
            loaded[name] = content.decode("utf-8")
        return loaded

    def context(self, names: list[str] | tuple[str, ...]) -> str:
        """Build a compact context block from only the skills requested by the caller."""
        skills = self.load(names)
        return "\n\n---\n\n".join(f"# Skill: {name}\n{content}" for name, content in skills.items())


class ProjectMemory:
    """Persist project notes and task state as bounded, inspectable JSON documents."""

    def __init__(
        self,
        root: str | Path = ".tigerdatalab/agent-memory",
        *,
        max_document_bytes: int = 256_000,
    ):
        self.root = Path(root).resolve()
        self.max_document_bytes = max_document_bytes

    def _read(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        if not path.is_file() or path.stat().st_size > self.max_document_bytes:
            raise MemoryError(f"Invalid or oversized memory document: {path.name}")
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise MemoryError(f"Cannot read memory document: {path.name}") from exc
        if not isinstance(value, dict):
            raise MemoryError(f"Memory document must contain a JSON object: {path.name}")
        return value

    def read_project(self) -> dict[str, Any]:
        """Return project memory, or an empty mapping when it has not been created."""
        return self._read(self.root / "project.json")

    def write_project(self, data: Mapping[str, Any]) -> None:
        """Replace project memory atomically and stamp its update time."""
        payload = dict(data)
        payload["updated_at"] = _utc_now()
        _write_json_atomic(self.root / "project.json", payload, self.max_document_bytes)

    def load_task(self, task_id: str) -> dict[str, Any]:
        """Load task state by safe identifier; return an empty mapping if absent."""
        if not _TASK_ID.fullmatch(task_id):
            raise MemoryError("Invalid task id")
        return self._read(self.root / "tasks" / f"{task_id}.json")

    def save_task(self, task_id: str, state: Mapping[str, Any]) -> None:
        """Persist resumable task state atomically, with an update timestamp."""
        if not _TASK_ID.fullmatch(task_id):
            raise MemoryError("Invalid task id")
        payload = dict(state)
        payload["task_id"] = task_id
        payload["updated_at"] = _utc_now()
        _write_json_atomic(
            self.root / "tasks" / f"{task_id}.json",
            payload,
            self.max_document_bytes,
        )

    def record_evidence(self, task_id: str, evidence: Mapping[str, Any]) -> dict[str, Any]:
        """Append a compact evidence record; evidence must describe observed results."""
        state = self.load_task(task_id)
        records = state.setdefault("evidence", [])
        if not isinstance(records, list):
            raise MemoryError("Task evidence must be a list")
        item = dict(evidence)
        item.setdefault("recorded_at", _utc_now())
        records.append(item)
        self.save_task(task_id, state)
        return state
