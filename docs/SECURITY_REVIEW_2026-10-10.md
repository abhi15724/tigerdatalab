# Security Review — TigerDataLab

**Review date:** 2026-10-10  
**Scope:** repository-level static review of deployment API, runtime, tool execution, queue/checkpoint adapters and existing tests.  
**Not in scope:** live infrastructure, cloud IAM/secrets, container image, network policy, external penetration test, compliance audit, or customer-specific threat model.  
**Status:** initial engineering review; independent reviewer and staging evidence still required.

## Finding SEC-001 — Audit events shared with ordinary API callers

- **Severity:** High when the service API key is shared among tenants or customers; otherwise Medium.
- **Component:** `tigerdatalab/ai/deployment.py`, `GET /v1/audit`.
- **Evidence:** the route previously used only the general service bearer key and returned `audit.events()` without tenant filtering. A client holding an inference key could therefore read the process audit history.
- **Remediation in this branch:** audit reads require a separate `TIGERDATALAB_AUDIT_READER_KEY` (or explicit `audit_reader_key`) in addition to the normal service credential. Without an audit-reader key, the endpoint returns 404; with a service key but no/invalid reader key, it returns 403. A regression test covers this boundary.
- **Residual risk:** this remains a process-wide audit reader, not tenant-filtered RBAC. Only grant the separate key to trusted operators. For multi-tenant products, implement authenticated operator roles and tenant-scoped audit queries before exposing this endpoint.

## Finding SEC-002 — Application authentication is a shared service key, not end-user identity

- **Severity:** High if used as a multi-tenant public SaaS without an authorization layer.
- **Evidence:** `create_app` accepts one bearer key and does not derive a verified tenant/user identity from an identity provider. Rate limiting uses the network peer address. The queue/runtime have tenant IDs, but an HTTP caller cannot safely self-assert a tenant merely by sending a field.
- **Required action:** integrate OIDC/JWT or a trusted gateway, validate issuer/audience/signature/expiry, derive tenant/user identity from verified claims, authorize each resource, and pass that trusted identity downstream. Keep shared-key mode for controlled service-to-service/single-tenant deployments only.

## Finding SEC-003 — Audit and rate-limit state is process-local by default

- **Severity:** Medium for horizontally scaled or restart-sensitive deployments.
- **Evidence:** the deployment helper uses an in-memory audit sink and in-process sliding-window buckets by default. Multiple replicas do not share the same limit/audit history; restart loses those records.
- **Required action:** use a durable audit sink with access control and retention, and a shared rate limiter/gateway for multi-replica deployments. Document and test retention, redaction and failure behavior.

## Finding SEC-004 — Distributed side effects are at-least-once

- **Severity:** High for payments, external writes, email dispatch, financial actions, or other non-idempotent tools.
- **Evidence:** queue leases can expire while a handler has already produced an external side effect. A second worker may retry. Lease ownership prevents stale queue completion but cannot undo an external side effect.
- **Required action:** application idempotency keys, transactional outbox/inbox where applicable, deduplication, reconciliation, and human approval for high-impact tools. Test process termination after side effect but before task completion.

## Finding SEC-005 — JSON Schema validation is intentionally partial

- **Severity:** Medium, dependent on tool schema and data.
- **Evidence:** the built-in validator implements a subset of JSON Schema and is not a complete standards validator. Tool schemas also cannot replace business-rule validation or authorization.
- **Required action:** use a full JSON Schema validator where complex schemas require it, keep server-side authorization independent of model arguments, and test every tool's boundary cases.

## Security controls observed

- Deployment authentication is enabled by default and missing credentials fail closed.
- Caller-supplied `X-Forwarded-For` is not used as rate-limit identity by the helper.
- Tool calls are allow-listed by role and validated against the supported schema subset before invocation.
- Model/tool calls have configurable timeouts/budgets; queue task claims use leases and stale owners cannot complete an expired lease.
- PostgreSQL adapter tests run against a real PostgreSQL service in CI; dependency audit is a separate CI gate.

## Required before a production approval

1. Run the focused CI gate on the candidate commit and review dependency audit output.
2. Run `scripts/staging_smoke.py` against the actual staging URL.
3. Run workload-specific load, provider/DB outage, worker restart, and backup/restore tests.
4. Have an independent security reviewer validate the deployment and threat model.
5. Close or explicitly accept all findings with owners and expiry dates.
6. Approve a workload-specific release record; do not issue blanket certification.

## Finding SEC-006 — Untrusted callers could override router/provider options

- **Severity:** Medium; potentially High where provider options affect spending, model selection, or shared routing state.
- **Component:** `tigerdatalab/ai/deployment.py`, `POST /v1/ask`.
- **Evidence:** arbitrary JSON `options` were forwarded to `agent.ask`, which passes options to the model router/provider. This could expose router controls such as per-request strategy selection and provider parameters not intended for client control.
- **Remediation in this branch:** the HTTP API accepts only `top_k` and bounds it to an integer from 1 through 20; arbitrary options are rejected with HTTP 400. Configure model/provider settings on the server side.
- **Residual risk:** direct in-process calls to `CompanyAgent.ask` remain an application API and must be protected by the embedding application. Add narrowly scoped options only with explicit validation and concurrency tests.
