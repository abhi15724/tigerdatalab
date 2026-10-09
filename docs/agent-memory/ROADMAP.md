# TigerDataLab 2.0 Roadmap

## Phase 1 — Foundation
- [x] Add selective skill loading and bounded local project/task memory (this branch).
- [x] Add skill-driven development and token-efficiency operating guidance.
- [ ] Verify the focused tests and repository CI.
- [ ] Define stable task/run and evidence schemas.

## Phase 2 — Reliable graph runtime
- Typed state and named nodes.
- Declarative edges and validated conditional routing.
- Bounded loops, safe retries, node-level timeout policies and checkpoint hooks.
- Resume from validated checkpoints; version graph definitions.
- Human approval gates enforced by action handlers.

## Phase 3 — Quality and cost controls
- Standard usage/cost telemetry across providers where available.
- Explicit budgets, stop conditions and graceful budget-exhausted states.
- Evaluation suites and task-level quality thresholds.
- Safe caching and context compaction with provenance.
- Targeted repair loops rather than restarting whole tasks.

## Phase 4 — Unified data-to-agent workflows
- Reusable data-quality-to-RAG pipelines.
- Dataset lineage and retrieval-source provenance in agent outputs.
- Reproducible evaluation datasets and regression tests.
- Optional deployment/observability integrations.

## Phase 5 — Public benchmark
Compare against relevant LangChain/LangGraph patterns on identical tasks, models, data and quality thresholds. Report task success, tokens and cost per successful task, latency, recovery rate and developer effort. Publish results before making comparative performance claims.
