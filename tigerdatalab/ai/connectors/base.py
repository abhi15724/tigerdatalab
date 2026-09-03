"""Base connector contract."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

class ConnectorError(RuntimeError):
    """Raised when a connector operation fails."""

class Connector(ABC):
    """Minimal interface implemented by external-system connectors."""
    @abstractmethod
    def request(self, operation: str, **kwargs: Any) -> Any:
        raise NotImplementedError
