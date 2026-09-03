"""Explicit tool permissions for company agents."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable
from .tools import ToolError, ToolRegistry

@dataclass
class PermissionPolicy:
    """Allow-list tools by role; unknown tools are denied by default."""
    roles: dict[str, set[str]] = field(default_factory=dict)

    def allow(self, role: str, *tool_names: str) -> "PermissionPolicy":
        self.roles.setdefault(role, set()).update(tool_names)
        return self

    def check(self, role: str, tool_name: str) -> None:
        if tool_name not in self.roles.get(role, set()):
            raise ToolError(f"Tool '{tool_name}' is not permitted for role '{role}'")

    def filter_registry(self, role: str, registry: ToolRegistry) -> list[dict]:
        allowed = self.roles.get(role, set())
        return [schema for schema in registry.schemas() if schema["function"]["name"] in allowed]
