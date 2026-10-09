# Graph Workflows

## Design target
Evolve the current linear `Workflow` into a resumable graph runtime only through small, tested increments. Preserve the simple linear path for ordinary tasks.

## Required semantics for graph features
- Explicit typed state and named nodes.
- Declared edges and conditional routing with validation for missing nodes.
- Bounded steps/iterations, per-node timeout policy, and clear failure state.
- Retry only where the operation is safe to repeat; avoid blind retries for side effects.
- Checkpoint state before/after expensive or side-effecting operations.
- Resume from validated checkpoints and record the graph version.
- Approval gates for sensitive actions; approvals must be enforced by the action handler.
- Test cycles, dead ends, exceptions, resume behavior and deterministic branch selection.

Do not claim durable execution, parallel scheduling or distributed workers until each capability exists and is tested.
