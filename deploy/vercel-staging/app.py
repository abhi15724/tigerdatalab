"""Vercel staging entrypoint using the published TigerDataLab package.

Configure GROQ_API_KEY and TIGERDATALAB_API_KEY in Vercel Project Settings.
Never commit credentials. GROQ_MODEL is optional and falls back to a known
configured default when unset or blank.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from tigerdatalab.ai import CompanyAgent, get_provider
from tigerdatalab.ai.providers import ProviderError

logger = logging.getLogger("tigerdatalab.staging")

# Empty environment variables must not disable the fallback. This avoids an
# import-time failure when Vercel has a blank optional GROQ_MODEL setting.
MODEL = os.getenv("GROQ_MODEL", "").strip() or "openai/gpt-oss-20b"

try:
    timeout_seconds = float(os.getenv("GROQ_TIMEOUT_SECONDS", "35"))
except ValueError as exc:
    raise RuntimeError("GROQ_TIMEOUT_SECONDS must be a number") from exc
if not 1 <= timeout_seconds <= 120:
    raise RuntimeError("GROQ_TIMEOUT_SECONDS must be between 1 and 120")

agent = CompanyAgent(name="TigerDataLab Staging Agent").connect(
    provider=get_provider("groq", timeout=timeout_seconds),
    model=MODEL,
    system=(
        "You are the TigerDataLab staging inference assistant. "
        "Answer clearly and concisely. Do not claim staging checks prove "
        "production readiness or certification."
    ),
)

# Authentication is enabled by default. TIGERDATALAB_API_KEY must be set
# in Vercel before this app is used.
app = agent.app(version="4.1.1-staging")


def _provider_failure(message: str) -> tuple[str, int, str]:
    """Map provider errors to safe, stable diagnostics without exposing details."""
    lowered = message.lower()
    status_match = re.search(r"\bhttp\s+(\d{3})\b", lowered)
    status = int(status_match.group(1)) if status_match else None

    if "not configured" in lowered or "not set" in lowered:
        return "provider_not_configured", 503, "The model provider is not configured."
    if status in (401, 403):
        return "provider_auth_rejected", 502, "The model provider rejected its credentials."
    if status == 429:
        return "provider_rate_limited", 503, "The model provider rate limit was reached."
    if status is not None and status >= 500:
        return "provider_upstream_error", 502, "The model provider returned a server error."
    if "request failed" in lowered or "timed out" in lowered or "timeout" in lowered:
        return "provider_unavailable", 503, "The model provider could not be reached."
    if "unexpected response" in lowered:
        return "provider_invalid_response", 502, "The model provider returned an invalid response."
    if status is not None:
        return "provider_request_rejected", 502, "The model provider rejected the request."
    return "provider_request_failed", 502, "The model provider request failed."


@app.add_exception_handler(ProviderError)
async def provider_error_handler(request: Request, exc: ProviderError) -> JSONResponse:
    # Do not log or return str(exc): provider errors may contain upstream bodies.
    code, status_code, safe_message = _provider_failure(str(exc))
    logger.warning(
        "staging_inference_failure category=%s exception_type=%s path=%s",
        code,
        type(exc).__name__,
        request.url.path,
    )
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": safe_message}},
    )


@app.add_exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # Keep unexpected failures diagnosable without logging messages, prompts,
    # provider response bodies, authorization headers, or environment values.
    logger.error(
        "staging_inference_failure category=unexpected_runtime_error exception_type=%s path=%s",
        type(exc).__name__,
        request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "unexpected_runtime_error",
                "message": "An unexpected inference error occurred. Check sanitized server diagnostics.",
            }
        },
    )
