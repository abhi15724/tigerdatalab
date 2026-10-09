"""Secret resolution contracts; credentials are not persisted by this module."""
from __future__ import annotations

import os
import re
from typing import Protocol


class SecretResolutionError(RuntimeError):
    """Raised when a requested secret is unavailable or invalid."""


class SecretProvider(Protocol):
    def get(self, name: str) -> str: ...


class EnvironmentSecretProvider:
    """Resolve secrets from environment variables only.

    Use a platform secret manager in hosted deployments by implementing the
    same interface. Never print or include returned secret values in traces.
    """

    _NAME = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$")

    def __init__(self, environ=None) -> None:
        self._environ = os.environ if environ is None else environ

    def get(self, name: str) -> str:
        if not isinstance(name, str) or not self._NAME.fullmatch(name):
            raise SecretResolutionError("Secret names must be uppercase environment-variable identifiers")
        value = self._environ.get(name)
        if not value:
            raise SecretResolutionError(f"Required secret {name} is not configured")
        return str(value)
