# Production Operations Runbook

Use this runbook as a minimum checklist for a TigerDataLab deployment. It is not a certification and must be adapted to the workload, hosting provider, data classification, and applicable legal requirements.

## 1. Before deployment

- Pin TigerDataLab and all application dependencies to reviewed versions; build and deploy an immutable wheel/container artifact.
- Configure `TIGERDATALAB_API_KEY` through the hosting platform's secret manager. `create_app()` requires authentication by default; `require_auth=False` is for isolated local development only.
- Use TLS at the ingress/load balancer. Never send bearer tokens over plain HTTP on an untrusted network.
- Use a dedicated database role with only the permissions needed by the application. Configure PostgreSQL TLS, backups, and connection limits for multi-worker workloads.
- Keep API keys, database DSNs, customer data, and prompts out of source control, issue reports, and logs.
- Configure request timeouts, concurrency limits, model/tool budgets, and provider spending limits for the expected workload.
- Review tool permissions. Require explicit human approval for destructive, financial, external-write, or other high-impact operations.
- Treat tool/model output as untrusted input. Do not run generated code in the application process; use an isolated sandbox/worker with OS-level restrictions.

## 2. Storage and tenancy

- In-memory conversation memory is volatile and process-local. SQLite adapters are for local/single-host use; protect database files with filesystem permissions and encrypted disks/backups as appropriate.
- For multi-worker execution, use PostgreSQL or a suitable managed queue/checkpoint backend and run the repository's real PostgreSQL integration tests against the target database version.
- A tenant-aware queue API does not automatically provide tenant isolation for every memory, checkpoint, audit, or retrieval backend. Test isolation for each adapter and authenticate/authorize tenant identity at the application boundary.
- Distributed tasks may execute more than once after worker crashes or expired leases. Make external side effects idempotent; use application-level idempotency keys and reconciliation.
- Define retention and deletion procedures for conversations, audit events, dataset artifacts, checkpoints, and model-training data. Test backup restoration before relying on backups.

## 3. Monitoring and incident response

- Monitor request rate, latency percentiles, model/provider errors, tool failures/timeouts, queue depth/age, retries, worker restarts, database connections, and estimated token/cost usage.
- Alert on sustained error-rate increases, queue backlog, repeated lease expiry, unusual authentication failures, provider budget limits, and database capacity.
- Do not put prompts, tool arguments, access tokens, or personal data in metric labels. Redact or omit sensitive values in logs and traces.
- On suspected credential exposure: revoke/rotate the credential, identify affected deployments, review audit/provider logs, and document remediation.
- On suspected cross-tenant data exposure: stop affected traffic, preserve relevant logs, revoke affected credentials if needed, investigate the access path, notify responsible security/privacy contacts, and follow applicable incident obligations.

## 4. Release and rollback

1. Open a pull request and require all CI jobs to pass on the exact head commit.
2. Review the diff, dependency-audit findings, security-sensitive changes, and migration/compatibility impact.
3. Deploy to staging using production-like configuration and synthetic/non-sensitive data.
4. Run smoke tests, workload-specific load tests, timeout/failure tests, and backup/restore validation.
5. Roll out gradually with a known-good previous artifact available for rollback.
6. After deployment, verify health/readiness, error rate, latency, queue progress, database health, and cost/usage.
7. Roll back if critical health or security indicators regress; preserve evidence and investigate before retrying.

## 5. Required workload-specific sign-off

Before calling a workload production-ready, record the owner, data classification, target throughput/concurrency, latency/error/cost SLOs, model/provider versions, tool permissions, retention policy, backup/restore evidence, load-test results, rollback artifact, and security review findings.

Do not interpret passing unit tests or CI as proof of security, availability, regulatory compliance, or capacity for a particular workload.
