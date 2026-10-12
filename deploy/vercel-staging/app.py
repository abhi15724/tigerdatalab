"""Vercel staging entrypoint using the published TigerDataLab package.

Configure GROQ_API_KEY and TIGERDATALAB_API_KEY in Vercel Project Settings.
Never commit credentials. GROQ_MODEL is optional and falls back to a known
configured default when unset or blank.
"""
from __future__ import annotations

import logging
import os

from fastapi import Request
from fastapi.responses import JSONResponse
from tigerdatalab.ai import CompanyAgent, get_provider

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


def _diagnose_provider_error(exc: Exception) -> tuple[str, int, str]:
    """Map provider failures to safe, actionable diagnostics.

    Only the category is returned or logged; exception text may contain
    provider response details and must never be exposed to the caller.
    """
    detail = str(exc).lower()
    exception_type = type(exc).__name__.lower()

    if "not configured" in detail or "api key" in detail and "configur" in detail:
        return (
            "provider_not_configured",
            503,
            "The model provider is not configured. Check the provider environment variables.",
        )
    if "http 401" in detail or "http 403" in detail or "unauthorized" in detail:
        return (
            "provider_auth_rejected",
            502,
            "The model provider rejected its credentials. Verify the provider API key.",
        )
    if "http 429" in detail or "rate limit" in detail or "quota" in detail:
        return (
            "provider_rate_limited",
            503,
            "The model provider rate limit or quota was reached. Check provider usage and limits.",
        )
    if (
        "timeout" in exception_type
        or "timed out" in detail
        or "urlerror" in exception_type
        or "connection" in detail
        or "network" in detail
    ):
        return (
            "provider_unavailable",
            503,
            "The model provider could not be reached. Check connectivity and retry.",
        )
    if "http 400" in detail or "http 404" in detail or "model" in detail and (
        "not found" in detail or "unsupported" in detail
    ):
        return (
            "provider_request_rejected",
            502,
            "The model provider rejected the request. Verify the configured model name and request compatibility.",
        )
    return (
        "inference_internal_error",
        500,
        "Inference failed unexpectedly. Check sanitized server diagnostics.",
    )


@app.exception_handler(Exception)
async def staging_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a safe diagnostic code without leaking secrets/provider payloads."""
    code, status_code, message = _diagnose_provider_error(exc)
    # Do not log str(exc), request headers, payloads, or stack traces here:
    # provider exceptions can contain response bodies or credential material.
    logger.error(
        "staging_request_failed path=%s diagnostic_code=%s exception_type=%s",
        request.url.path,
        code,
        type(exc).__name__,
    )
    return JSONResponse(
        status_code=status_code,
        content={
            "error": "model_inference_failed",
            "diagnostic_code": code,
            "message": message,
        },
    )
