"""Composable, validated business workflow execution."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping


class WorkflowError(RuntimeError):
    """Raised when a workflow is invalid or cannot complete."""


@dataclass(frozen=True)
class WorkflowStep:
    name: str
    action: Callable[[dict[str, Any]], Any]
    description: str = ""
    condition: Callable[[dict[str, Any]], bool] | None = None
    output_key: str | None = None

    def run(self, state: dict[str, Any]) -> Any:
        if self.condition is not None and not self.condition(state):
            return None
        return self.action(state)


@dataclass
class WorkflowResult:
    workflow: str
    status: str
    state: dict[str, Any]
    executed_steps: list[str] = field(default_factory=list)
    skipped_steps: list[str] = field(default_factory=list)
    error: str | None = None


class Workflow:
    """Small orchestration engine with explicit steps and bounded execution."""

    def __init__(self, name: str, steps: list[WorkflowStep] | None = None, max_steps: int = 100):
        if not name.strip():
            raise ValueError("Workflow name cannot be empty")
        if max_steps < 1:
            raise ValueError("max_steps must be positive")
        self.name = name
        self.steps = list(steps or [])
        self.max_steps = max_steps

    def add_step(self, step: WorkflowStep) -> "Workflow":
        if any(existing.name == step.name for existing in self.steps):
            raise WorkflowError(f"Duplicate workflow step: {step.name}")
        self.steps.append(step)
        return self

    def validate(self) -> None:
        if not self.steps:
            raise WorkflowError("Workflow must contain at least one step")
        if len(self.steps) > self.max_steps:
            raise WorkflowError("Workflow exceeds max_steps")
        names = [step.name for step in self.steps]
        if any(not name.strip() for name in names):
            raise WorkflowError("Workflow step names cannot be empty")
        if len(names) != len(set(names)):
            raise WorkflowError("Workflow step names must be unique")

    def run(self, inputs: Mapping[str, Any] | None = None) -> WorkflowResult:
        self.validate()
        state = dict(inputs or {})
        executed: list[str] = []
        skipped: list[str] = []
        try:
            for step in self.steps:
                if step.condition is not None and not step.condition(state):
                    skipped.append(step.name)
                    continue
                value = step.action(state)
                if step.output_key:
                    state[step.output_key] = value
                elif isinstance(value, Mapping):
                    state.update(value)
                executed.append(step.name)
            return WorkflowResult(self.name, "completed", state, executed, skipped)
        except Exception as exc:
            return WorkflowResult(self.name, "failed", state, executed, skipped, str(exc))


def step(name: str, description: str = "", output_key: str | None = None, condition=None):
    """Decorator for building WorkflowStep instances."""
    def decorate(function: Callable[[dict[str, Any]], Any]) -> WorkflowStep:
        return WorkflowStep(name, function, description, condition, output_key)
    return decorate
