#!/usr/bin/env python3
"""Non-destructive smoke checks for a deployed TigerDataLab staging API.

By default this checks health/readiness and authentication boundaries only.
Pass --exercise-model to send one synthetic prompt (may incur provider cost).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def request(base: str, path: str, *, api_key: str | None = None, method: str = "GET", body=None):
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(base.rstrip("/") + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exercise-model", action="store_true", help="send one synthetic prompt; may incur provider cost")
    args = parser.parse_args()
    base = os.getenv("TIGERDATALAB_STAGING_URL", "").strip().rstrip("/")
    key = os.getenv("TIGERDATALAB_STAGING_API_KEY", "")
    if not base.startswith("https://"):
        print("FAIL: TIGERDATALAB_STAGING_URL must be an HTTPS URL", file=sys.stderr)
        return 2
    if not key.strip():
        print("FAIL: TIGERDATALAB_STAGING_API_KEY is required", file=sys.stderr)
        return 2

    checks = []
    for path in ("/health", "/ready"):
        status, body = request(base, path)
        checks.append((f"GET {path}", status == 200, f"HTTP {status}"))
    status, _ = request(base, "/v1/ask", method="POST", body={"prompt": "synthetic staging auth probe"})
    checks.append(("unauthenticated POST /v1/ask", status == 401, f"HTTP {status}"))
    status, _ = request(base, "/v1/ask", api_key="deliberately-wrong-key", method="POST",
                        body={"prompt": "synthetic staging auth probe"})
    checks.append(("invalid-key POST /v1/ask", status == 401, f"HTTP {status}"))

    if args.exercise_model:
        status, body = request(base, "/v1/ask", api_key=key, method="POST",
                               body={"prompt": "Reply with exactly: TIGERDATALAB_STAGING_OK"})
        ok = status == 200
        if ok:
            try:
                ok = "output" in json.loads(body)
            except (ValueError, TypeError):
                ok = False
        checks.append(("authenticated synthetic inference", ok, f"HTTP {status}"))

    for name, passed, detail in checks:
        print(f"{'PASS' if passed else 'FAIL'}  {name}: {detail}")
    failures = sum(not passed for _, passed, _ in checks)
    print(f"\n{len(checks) - failures}/{len(checks)} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
