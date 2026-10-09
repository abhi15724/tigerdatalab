# TigerDataLab 2.0 — Project Status

Last reviewed: 2026-10-09

## Product direction
TigerDataLab is one ecosystem with two independent but connected pillars:
- **Data & Training:** analytics, data engineering, data quality, privacy-aware dataset preparation, dataset lineage and supported training backends.
- **Agent Framework:** model providers, agent factory, tools, retrieval, workflows, evaluation and deployment.
- **Shared platform:** memory, configuration, observability, evaluation, security and cost/usage measurement.

## Verified repository facts
- Python package: `tigerdatalab`; Python requirement: >=3.10.
- Existing AI modules include providers, CompanyAI, CompanyAgent, AgentFactory, tools, retrieval, workflows, evaluation and training helpers.
- The current workflow implementation is a bounded linear sequence with conditional steps; it is not yet a full graph engine.
- AgentFactory is present on main following PR #1.
- New local memory helpers in this branch are intended to load named skills and persist bounded JSON project/task state.

## Not yet verified
- Full-suite CI status for this branch.
- Production-grade distributed execution, multi-tenant persistence, automatic token optimization or universal superiority over LangChain/LangGraph.
- Token/cost telemetry coverage across every provider.

## Working rules
- Preserve the data/training pillar while building agent capabilities.
- Keep public APIs model-agnostic and the core installation lightweight.
- Require evidence before describing a capability as complete.
