# PostgreSQL distributed runtime

TigerDataLab provides optional PostgreSQL adapters for a shared task queue and graph checkpoints. SQLite remains the zero-configuration option for local development and single-host deployments.

## Install and configure

```bash
pip install 'tigerdatalab[postgres]'
export TIGERDATALAB_DATABASE_URL='postgresql://user:password@host:5432/database?sslmode=require'
```

Keep the connection URL in a secret manager or environment injection, not source control. Use TLS, least-privilege credentials, managed backups, and an appropriate connection pooler for production. The adapter opens a short-lived connection per operation; tune the deployment and database connection limits accordingly.

## Use shared storage

```python
import os
from tigerdatalab.ai import (
    AsyncGraph, DistributedGraphScheduler, Graph,
    PostgreSQLCheckpointStore, PostgreSQLTaskQueue,
)

dsn = os.environ["TIGERDATALAB_DATABASE_URL"]
checkpoints = PostgreSQLCheckpointStore(dsn)
queue = PostgreSQLTaskQueue(dsn)
graph = Graph("research", nodes, checkpoint_store=checkpoints)
scheduler = DistributedGraphScheduler(
    queue, {"research": graph}, worker_id="worker-1",
    lease_seconds=90,
)
submitted = scheduler.submit("research", {"query": "data engineering"}, tenant_id="org-1")
# Worker loop: scheduler.process_once() or await scheduler.process_once_async()
```

Every worker must register the same graph name and version, and use the same PostgreSQL database. Queue claiming uses transactional row locks and `FOR UPDATE SKIP LOCKED` so concurrent workers can claim different tasks. Checkpoints are shared and atomically upserted.

## Lease renewal

The queue exposes `renew_lease(task_id, worker_id, lease_seconds=...)`. The built-in sync and async task workers now run a best-effort heartbeat for queue adapters that implement this capability, including the PostgreSQL adapter. SQLite does not currently expose lease renewal, so its workers retain the configured lease-duration constraint. If renewal fails, workers must still treat lease ownership checks as authoritative; a task handler may be retried by another worker. Do not rely on this adapter for exactly-once effects: use idempotency keys, outbox patterns, or external deduplication for side effects.

## Operations and limitations

- PostgreSQL availability, backup/restore, TLS, database role grants, monitoring, and connection limits are deployment responsibilities.
- This adapter is optional and must be tested against a real PostgreSQL service before production.
- Queue and checkpoint writes are separate transactions; a task and its checkpoint are not one atomic unit. Recovery relies on idempotent node actions and graph checkpoints.
- Tenant IDs scope queue status lookups, but application authorization must still verify that a caller is allowed to submit, resume, or inspect a graph.
- Heartbeats are best-effort; database/network interruptions can still cause lease loss. Use idempotent handlers and monitor worker/database errors.
- SQLite remains appropriate for local development and single-host persistent-volume deployments.
