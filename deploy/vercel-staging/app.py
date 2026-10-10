"""Vercel staging entrypoint using the published TigerDataLab package.

Configure GROQ_API_KEY and TIGERDATALAB_API_KEY in Vercel Project Settings.
Never commit credentials. The model can be overridden with GROQ_MODEL.
"""
from __future__ import annotations

import os

from tigerdatalab.ai import CompanyAgent, get_provider

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()
if not MODEL:
    raise RuntimeError("GROQ_MODEL must not be empty")

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
