# Graph Workflows

## Design target
Use `tigerdatalab.ai.Graph` for branching or resumable workflows; use `Workflow` for simple linear sequences.

## Required semantics
- Validate named nodes/edges and ambiguous fallback routes.
- Bound execution with `max_steps`.
- Retries require explicit `retry_safe=True`; do not retry side effects blindly.
- Use `SQLiteCheckpointStore` for restart persistence on a durable filesystem; the default in-memory store is only process-local.
- Approval-gated nodes must pause before action execution. The calling application must authenticate/authorize the reviewer before supplying `approvals={node_name: True|False}`.
- Validate graph name/version before resume. State stored in SQLite must be JSON-serializable.
- Add tests for routing, cycles, failures, retry policy, persistence after reopening the database, approvals and rejection routing.
- Never claim exactly-once side effects, authenticated approval UI, async/parallel execution or distributed coordination unless separately implemented and tested.
