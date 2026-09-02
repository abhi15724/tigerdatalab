"""Safe, dependency-free tool registration and execution primitives."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping


class ToolError(RuntimeError):
    """Raised for invalid or unsafe tool operations."""


@dataclass(frozen=True)
class Tool:
    """A callable exposed to an AI system with an explicit contract."""
    name: str
    description: str
    function: Callable[..., Any]
    parameters: Mapping[str, Any] = field(default_factory=dict)
    enabled: bool = True

    def schema(self) -> dict[str, Any]:
        return {"type": "function", "function": {"name": self.name, "description": self.description, "parameters": dict(self.parameters)}}

    def execute(self, arguments: Mapping[str, Any] | None = None) -> Any:
        if not self.enabled:
            raise ToolError(f"Tool '{self.name}' is disabled")
        try:
            return self.function(**dict(arguments or {}))
        except TypeError as exc:
            raise ToolError(f"Invalid arguments for tool '{self.name}': {exc}") from exc


class ToolRegistry:
    """Explicit allow-list of tools; never executes arbitrary code from model output."""
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> Tool:
        if not tool.name.strip():
            raise ValueError("Tool name cannot be empty")
        if not callable(tool.function):
            raise TypeError("Tool function must be callable")
        if tool.name in self._tools:
            raise ToolError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool
        return tool

    def decorator(self, name: str, description: str, parameters: Mapping[str, Any] | None = None):
        def wrap(function: Callable[..., Any]) -> Callable[..., Any]:
            self.register(Tool(name, description, function, parameters or {}))
            return function
        return wrap

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise ToolError(f"Unknown tool: {name}")
        return self._tools[name]

    def schemas(self) -> list[dict[str, Any]]:
        return [item.schema() for item in self._tools.values() if item.enabled]

    def execute(self, name: str, arguments: Mapping[str, Any] | None = None) -> Any:
        return self.get(name).execute(arguments)

    def __len__(self) -> int:
        return len(self._tools)


def tool(name: str, description: str, parameters: Mapping[str, Any] | None = None):
    """Convenience decorator backed by the module-level registry."""
    return _default_registry.decorator(name, description, parameters)


_default_registry = ToolRegistry()
