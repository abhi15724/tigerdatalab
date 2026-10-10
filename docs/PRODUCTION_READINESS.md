# Production Readiness Pass

**Project:** TigerDataLab  
**Baseline reviewed:** 2026-10-09  
**Scope:** Python package, AI agent runtime, distributed execution, data safety, release process.

This document is an engineering gate, not a claim that every item is already implemented or independently verified. A production deployment is ready only when the relevant checks below have evidence in CI and in the target environment.

## Current baseline

The repository already includes a bounded agent runtime, tool allow-lists and permission policies, optional approval hooks, tracing/audit interfaces, in-memory conversation memory, graph checkpointing, a task scheduler, and optional PostgreSQL adapters. These are useful primitives; they do not by themselves guarantee production safety or distributed correctness.

Known constraints that must remain explicit:
- `InMemoryConversationMemory` is process-local (tenant-scoped in the runtime hardening branch) and is not durable across process restarts; use `SQLiteConversationMemory` for local/single-host persistence.
- Provider tool calling is adapter-specific; the OpenAI-compatible adapter is not a universal native adapter for every provider.
- Distributed task execution may be at-least-once. Side-effecting tasks must be idempotent or protected by application-level deduplication.
- SQLite is appropriate for local/single-host use; PostgreSQL-backed multi-worker behavior must be tested against a real PostgreSQL service.
- The host application remains responsible for authentication, authorization, secret management, network controls, backups, retention, and operational monitoring.

## Release gates

### P0 — Correctness and safe failure
- [ ] Every public runtime validates budgets and configuration at construction time.
- [ ] Model/provider failures, invalid tool-call JSON, unknown tools, permission denials, approval denials, timeouts, and cancellation have deterministic outcomes.
- [x] Tool execution has a bounded timeout and bounded number of calls/steps.
- [x] Model calls have a configurable timeout; timeout regression tests are included in PR #11.
- [ ] Token/usage accounting handles missing, malformed, negative, and cumulative usage values safely.
- [ ] Errors returned to callers do not expose credentials, raw secrets, or sensitive prompt/context contents.
- [ ] Repeated run IDs, task retries, worker restarts, and checkpoint corruption have defined behavior.

### P0 — Security boundaries
- [ ] Tool schemas and arguments are validated before invocation. A dependency-free JSON Schema subset validator is implemented for common object/array/type/enum/bounds constraints; validate required schemas and edge cases before marking this gate complete.
- [ ] Tool permissions are deny-by-default and checked at execution time, not only when tools are advertised to a model.
- [ ] Approval is required for destructive, external, financial, or otherwise high-impact tools.
- [x] Conversation-memory adapters namespace records by tenant and conversation; verify tenant scoping separately for checkpoint, task, audit, and retrieval stores before enabling multi-tenancy across those components.
- [ ] No API keys or production credentials are committed; secrets are injected through the deployment environment/secret manager.
- [ ] Logs and traces redact sensitive data by default and have a documented retention policy.
- [ ] Untrusted tool/model output is treated as data, never as executable instructions.

### P1 — Persistence and distributed execution
- [ ] Persistent adapters have schema/version handling, transactions, and documented migration behavior.
- [ ] Concurrent workers claim tasks atomically and recover expired leases safely.
- [ ] Retry policies include bounded attempts and backoff; permanent failures reach a terminal/dead-letter state.
- [ ] Checkpoint writes are atomic and versioned; resume behavior is tested after process termination.
- [ ] Side effects use idempotency keys or explicitly document at-least-once semantics.
- [ ] PostgreSQL integration tests run against a real service in CI (`.github/workflows/production-gates.yml` added; mark complete only after a successful run).

### P1 — Observability and operations
- [ ] Each run/task has a correlation ID and structured lifecycle events.
- [ ] Record latency, retry counts, provider/model, tool duration, failures, and token usage where available.
- [ ] Metrics avoid high-cardinality labels and never contain secrets or raw user prompts by default.
- [ ] Define health/readiness checks for deployed services and dependency failure behavior.
- [ ] Document timeouts, concurrency limits, queue capacity, shutdown behavior, backup/restore, and incident response.

### P1 — Package and compatibility
- [ ] Test supported Python versions and optional dependency combinations.
- [ ] Build source distribution and wheel from a clean checkout.
- [ ] Validate distributions with Twine and smoke-test installation from built artifacts.
- [ ] Verify the CLI entry point and core imports after installation.
- [ ] Pin dependencies in deployable applications and periodically review dependency vulnerabilities (`.github/workflows/production-gates.yml` adds `pip-audit`; review any findings before release).
- [ ] Keep the documented Python support range, CI matrix, and package classifiers consistent.

### P2 — Data and AI quality
- [ ] Dataset transformations are reproducible and lineage manifests record input/output identity and configuration.
- [ ] Train/validation/test splits prevent leakage for the relevant data domain.
- [ ] PII masking is documented as best-effort unless backed by measured detection guarantees.
- [ ] RAG access controls are applied before retrieval and checked again before returning context.
- [ ] Evaluate model/provider changes against a versioned representative dataset before rollout.
- [ ] Define acceptable quality, latency, cost, and failure-rate thresholds for each deployment.

## Required verification evidence

Attach links or artifacts for each release candidate:
1. CI matrix result for every supported Python version and all production-gate workflow jobs on the exact release commit.
2. Full test result plus targeted failure/recovery and security tests.
3. Wheel and source distribution validation, plus clean-install smoke test.
4. PostgreSQL integration result for distributed deployments.
5. Dependency/security scan result and reviewed exceptions.
6. Deployment-specific load test, backup/restore drill, and rollback procedure.
7. Known limitations and operator runbook (`docs/PRODUCTION_OPERATIONS.md`); deployment-specific sign-off remains mandatory.

## Suggested execution order

1. Audit the runtime, permissions, memory/checkpoint interfaces, scheduler, and PostgreSQL adapters; add failing tests before changing behavior.
2. Fix correctness/security defects and prove them with focused tests.
3. Harden CI and package verification so release artifacts are reproducible.
4. Add deployment observability, operations guidance, and load/recovery tests.
5. Mark a gate complete only when the test or operational evidence exists.

## Production status

**Status: repository CI gates passed; workload production sign-off is pending. No blanket production certification issued.** The current `main` commit has successful CI and production-gate workflow runs, including the security/failure test job, PostgreSQL integration job, and dependency audit job. A manual staging-verification workflow is available, but it has not been executed against a configured staging deployment in this review. Load/soak testing, backup/restore, rollback rehearsal, and independent security sign-off must be recorded against a declared workload before issuing a GO decision. See `docs/FINAL_PRODUCTION_READINESS_DOSSIER.md`, `docs/STAGING_FAILURE_TESTING.md`, and `docs/SECURITY_REVIEW_2026-10-10.md`. CI cannot replace deployment-specific testing.
