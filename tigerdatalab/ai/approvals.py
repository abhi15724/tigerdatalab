"""Human-in-the-loop approval primitives for sensitive agent actions."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

@dataclass(frozen=True)
class ApprovalRequest:
    action: str
    arguments: dict[str, Any]
    requester: str | None = None
    id: str | None = None

@dataclass
class ApprovalStore:
    """In-memory approval store; replace with a durable store in production."""
    _items: dict[str, ApprovalRequest] = field(default_factory=dict)
    _decisions: dict[str, bool] = field(default_factory=dict)

    def request(self, action: str, arguments: dict[str, Any], requester: str | None = None) -> ApprovalRequest:
        rid = f"approval-{int(datetime.now(timezone.utc).timestamp() * 1000000)}"
        item = ApprovalRequest(action, dict(arguments), requester, rid)
        self._items[rid] = item
        return item

    def decide(self, request_id: str, approved: bool) -> None:
        if request_id not in self._items:
            raise KeyError(f"Unknown approval request: {request_id}")
        self._decisions[request_id] = bool(approved)

    def approved(self, request_id: str) -> bool:
        return self._decisions.get(request_id, False)
