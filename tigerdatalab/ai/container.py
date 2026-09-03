"""Container entrypoint for a user-supplied CompanyAgent factory.

Set TIGER_AGENT_FACTORY to ``module:callable``. The callable must return a ready
CompanyAgent. The module is intentionally supplied by the deploying company so
no customer credentials or application code are baked into the package image.
"""
from __future__ import annotations

import importlib
import os

from .deployment import serve


def main() -> None:
    target = os.getenv("TIGER_AGENT_FACTORY")
    if not target or ":" not in target:
        raise SystemExit("Set TIGER_AGENT_FACTORY=module:callable before starting the container")
    module_name, factory_name = target.split(":", 1)
    factory = getattr(importlib.import_module(module_name), factory_name)
    agent = factory()
    serve(
        agent,
        host=os.getenv("TIGER_HOST", "0.0.0.0"),
        port=int(os.getenv("TIGER_PORT", "8000")),
    )


if __name__ == "__main__":
    main()
