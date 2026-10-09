"""Safe, dependency-free tool registration and execution primitives."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping


class ToolError(RuntimeError):
    """Raised for invalid or unsafe tool operations."""


def _validate_schema_value(value: Any, schema: Mapping[str, Any], path: str = "arguments") -> None:
    """Validate the JSON Schema subset commonly used for function tools.

    Supports types, enum, required/properties, additionalProperties, string
    lengths, numeric bounds, and array lengths/items. Unknown JSON Schema
    keywords are ignored; applications needing full JSON Schema semantics
    should validate at their API boundary with a dedicated validator.
    """
    import math

    if not isinstance(schema, Mapping):
        raise ToolError(f"Invalid schema at {path}: expected an object")
    expected = schema.get("type")
    types = expected if isinstance(expected, list) else [expected] if expected else []
    type_checks = {
        "object": lambda v: isinstance(v, Mapping),
        "array": lambda v: isinstance(v, list),
        "string": lambda v: isinstance(v, str),
        "boolean": lambda v: isinstance(v, bool),
        "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
        "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v),
        "null": lambda v: v is None,
    }
    if types and not any(t in type_checks and type_checks[t](value) for t in types):
        raise ToolError(f"Invalid {path}: expected type {' or '.join(map(str, types))}")
    if "enum" in schema and value not in schema["enum"]:
        raise ToolError(f"Invalid {path}: value is not an allowed enum member")
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            raise ToolError(f"Invalid {path}: string is shorter than minLength")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            raise ToolError(f"Invalid {path}: string exceeds maxLength")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if not math.isfinite(value):
            raise ToolError(f"Invalid {path}: number must be finite")
        if "minimum" in schema and value < schema["minimum"]:
            raise ToolError(f"Invalid {path}: number is below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            raise ToolError(f"Invalid {path}: number exceeds maximum")
    if isinstance(value, Mapping):
        required = schema.get("required", [])
        if not isinstance(required, list):
            raise ToolError(f"Invalid schema at {path}: required must be a list")
        missing = [key for key in required if key not in value]
        if missing:
            raise ToolError(f"Invalid {path}: missing required properties {missing!r}")
        properties = schema.get("properties", {})
        if not isinstance(properties, Mapping):
            raise ToolError(f"Invalid schema at {path}: properties must be an object")
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(properties))
            if extra:
                raise ToolError(f"Invalid {path}: unexpected properties {extra!r}")
        for key, item in value.items():
            if key in properties:
                _validate_schema_value(item, properties[key], f"{path}.{key}")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise ToolError(f"Invalid {path}: array is shorter than minItems")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise ToolError(f"Invalid {path}: array exceeds maxItems")
        item_schema = schema.get("items")
        if isinstance(item_schema, Mapping):
            for index, item in enumerate(value):
                _validate_schema_value(item, item_schema, f"{path}[{index}]")

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
        if arguments is not None and not isinstance(arguments, Mapping):
            raise ToolError(f"Arguments for tool '{self.name}' must be an object")
        args = dict(arguments or {})
        _validate_schema_value(args, self.parameters, "arguments")
        try:
            return self.function(**args)
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
