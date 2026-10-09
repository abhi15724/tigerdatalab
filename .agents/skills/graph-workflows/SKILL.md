# Graph Workflows

## Design target
Use `tigerdatalab.ai.Graph` for branching or resumable workflows; use the existing `Workflow` for simple linear sequences.

## Required semantics
- Explicit named nodes and declared edges; validate missing nodes and ambiguous fallback edges.
- Bound node executions and return clear failure results.
- Retries require explicit `retry_safe=True`; do not retry side effects blindly.
- Checkpoint after each successful node and validate graph name/version before resuming.
- Treat the default in-memory checkpoint store as process-local, not durable persistence.
- Add tests for cycles, dead ends, branch selection, exceptions, retries, resume and incompatible checkpoints.
- Do not claim distributed durability, exactly-once effects, parallel execution, async nodes, timeouts or approval gates unless implemented and tested.
