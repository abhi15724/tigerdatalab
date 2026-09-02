"""In-memory registry for versioned AI assets and lineage metadata."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Asset:
    kind: str
    name: str
    version: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Registry:
    """Explicit registry for datasets, knowledge bases, models, tools and workflows."""

    VALID_KINDS = {"dataset", "knowledge_base", "model", "tool", "workflow", "evaluation", "system"}

    def __init__(self) -> None:
        self._assets: dict[tuple[str, str, str], Asset] = {}

    def register(self, asset: Asset) -> Asset:
        if asset.kind not in self.VALID_KINDS:
            raise ValueError(f"Unsupported asset kind: {asset.kind}")
        key = (asset.kind, asset.name, asset.version)
        if key in self._assets:
            raise ValueError(f"Asset already registered: {key}")
        self._assets[key] = asset
        return asset

    def get(self, kind: str, name: str, version: str | None = None) -> Asset:
        if version is not None:
            return self._assets[(kind, name, version)]
        matches = [a for (k, n, _), a in self._assets.items() if k == kind and n == name]
        if not matches:
            raise KeyError((kind, name))
        return sorted(matches, key=lambda a: a.created_at)[-1]

    def list(self, kind: str | None = None) -> list[Asset]:
        assets = list(self._assets.values())
        if kind is not None:
            assets = [a for a in assets if a.kind == kind]
        return sorted(assets, key=lambda a: (a.kind, a.name, a.version))

    def snapshot(self) -> list[dict[str, Any]]:
        return [asdict(asset) for asset in self.list()]
