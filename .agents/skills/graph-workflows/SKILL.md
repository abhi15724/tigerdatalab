# Async and Parallel Graph Workflows

- Use `AsyncGraph` for DAGs with independent nodes that can run concurrently; use `Graph` for synchronous routing and bounded cycles.
- Always set `max_concurrency` based on provider quotas and downstream limits.
- Return mapping outputs from nodes. Nodes receive isolated snapshots; do not mutate shared state.
- Parallel nodes must not write the same output key; conflicts intentionally fail the run.
- Retries require `retry_safe=True`. Use idempotency keys for external side effects.
- Set `timeout_seconds` for network/provider calls. A timeout does not forcibly stop a synchronous function already running in a worker thread.
- AsyncGraph is DAG-only. Validate graph structure before execution.
- Checkpoint state must be JSON-serializable when using SQLite. Never put credentials or raw secrets in state.
- The caller must authenticate/authorize approval decisions. This package does not provide reviewer identity or an approval UI.
- Add tests for fan-out, join, conditional routes, async actions, timeouts, retry behavior, output conflicts, approvals, persistence and resume.
