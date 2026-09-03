"""Outbound webhook connector for approved company automations."""
from __future__ import annotations
from typing import Any, Mapping
from .rest import APIConnector

class WebhookConnector(APIConnector):
    def send(self, path: str, payload: Mapping[str, Any]) -> Any:
        return self.post(path, json_body=dict(payload))
