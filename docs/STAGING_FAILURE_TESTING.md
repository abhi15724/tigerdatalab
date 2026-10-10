# Staging, Failure-Injection, and Workload Sign-off

**Status:** test harness added; target-environment execution and workload sign-off are still required.  
**Rule:** use synthetic data and a dedicated staging database/provider account. Never run failure injection against production.

## 1. Declare the workload before testing

Record these values in the deployment change/ticket before calling a workload production-ready:

- Workload owner and on-call contact
- Data classification (public/internal/confidential/regulated); PII and retention requirements
- Expected request rate, peak concurrency, queue arrival rate, longest task, payload sizes
- Model/provider IDs and versions, tool list and permission policy
- p50/p95/p99 latency targets, availability/error-rate target, max cost per request/run
- Recovery objectives (RTO/RPO), retention/deletion needs, database version and deployment topology
- Approved test window, test budget, rollback artifact and stop conditions

Do not invent a single global capacity number for a framework whose limits depend on the provider, model, tools, database, graph and hosting environment.

## 2. Staging smoke checks

Deploy the exact candidate artifact to a staging environment with HTTPS, a dedicated API key, a separate audit-reader key if audit access is enabled, a non-production database, and bounded provider spending.

On a trusted workstation or runner, set environment variables without committing them:

- `TIGERDATALAB_STAGING_URL=https://your-staging-host`
- `TIGERDATALAB_STAGING_API_KEY` to the staging service bearer key

Run:

```bash
python scripts/staging_smoke.py
```

The default run checks health/readiness and verifies missing/invalid API keys receive HTTP 401. To make one authenticated synthetic inference request (may incur provider cost), run:

```bash
python scripts/staging_smoke.py --exercise-model
```

The script refuses non-HTTPS URLs. Do not put credentials on command lines or in shell history; inject them through your secret manager/CI secrets.

## 3. Required failure-injection scenarios

The automated CI gate `.github/workflows/production-gates.yml` runs the repository's focused failure/security tests. It is a precondition, not a replacement for staging tests.

| Scenario | Injection | Required result |
|---|---|---|
| Auth | Missing and invalid bearer key | 401; no agent invocation |
| Audit access | Service key without separate audit-reader key | Audit endpoint hidden/denied |
| Rate limiting | Burst requests with spoofed forwarded headers | Limit cannot be bypassed by caller-controlled X-Forwarded-For |
| Model outage/timeout | Slow or failing fake provider | Bounded failure; no infinite request |
| Tool failure | Handler raises repeatedly | Retry limit reached; terminal failed state |
| Worker crash/lease expiry | Expire lease, then let a second worker claim | Old worker cannot overwrite new owner's result |
| Tenant isolation | Reuse public run ID in another tenant | No checkpoint read/resume across tenants |
| PostgreSQL interruption | Restart/deny staging DB connections during a controlled test | Bounded error, no false success, worker recovers after service returns |
| Provider rate limit | Simulate 429/5xx/timeouts | Bounded retries/backoff; spending and queue limits hold |
| Shutdown/redeploy | Terminate a worker during a long task | Lease recovery; side effects idempotent/reconciled |
| Backup restore | Restore into an isolated database | Data, checkpoints and queue state meet declared RPO/RTO |
| Resource exhaustion | Gradually raise concurrency and payload sizes | SLOs hold or load sheds predictably; no runaway costs |

Use a staging database clone with synthetic data. Confirm the owner has approved each disruptive test. Do not inject network failures, kill processes, or run load tests against production.

## 4. Load and soak test

Use a representative synthetic workload, ramp gradually, and capture p50/p95/p99 latency, throughput, 4xx/5xx rate, queue age/depth, retries/lease expirations, worker memory/CPU, DB connections, provider latency, token/cost usage, and saturation.

Set the request rate/concurrency from the workload declaration. Stop the run if error rate, latency, queue backlog, or spend exceeds the agreed guardrail. Test normal peak, short burst, and a soak long enough to expose resource leaks. Include tool-heavy and long-running graph paths where applicable.

Do not mark this section complete without an artifact or dashboard URL tied to the exact release commit and staging configuration.

## 5. Security review exit criteria

Before sign-off, a reviewer other than the author should inspect:

- Authentication, authorization, tenant identity provenance and audit-reader access
- Tool permissions, JSON argument validation, human approval and side-effect idempotency
- Prompt/context/tool-output injection and generated-code isolation
- Secret storage/rotation, TLS, dependency findings and container/OS permissions
- Tenant scoping for every persistence, checkpoint, task, audit and retrieval adapter
- Error/log/trace redaction, retention/deletion, backups and incident response
- Dependency and deployment configuration, open ports, database roles, egress controls
- Threat model, abuse cases, test evidence, residual risks and remediation owners

Record reviewer, date, commit SHA, findings (severity, affected component, reproduction, remediation/exception), and approval. No unresolved critical/high findings without a formally accepted risk decision.

## 6. Release decision template

- Candidate commit/artifact digest:
- Workload owner and staging environment:
- CI + dependency audit links:
- Failure-injection result:
- Load/soak results and SLOs:
- Backup/restore result:
- Security reviewer and findings:
- Residual risks and owners:
- Rollback artifact and tested procedure:
- Decision: **GO / NO-GO / CONDITIONAL**
- Approver and timestamp:

A GO applies only to the workload, topology, limits, data class and version documented above. It is not a blanket certification of TigerDataLab for all production workloads.
