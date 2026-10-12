"""Vercel staging entrypoint using the published TigerDataLab package.

Configure GROQ_API_KEY and TIGERDATALAB_API_KEY in Vercel Project Settings.
Never commit credentials. GROQ_MODEL is optional and falls back to a known
configured default when unset or blank.
"""
from __future__ import annotations

import os

from tigerdatalab.ai import CompanyAgent, get_provider

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
