# Distributed Graph Scheduler and Debugger

## Queue a graph

```python
from tigerdatalab.ai import (
    DistributedGraphScheduler, Graph, GraphNode,
    SQLiteCheckpointStore, SQLiteTaskQueue,
)

checkpoints = SQLiteCheckpointStore("./data/checkpoints.sqlite3")
queue = SQLiteTaskQueue("./data/tasks.sqlite3")
graph = Graph(
    "research",
    [GraphNode("research", research_action), GraphNode("verify", verify_action)],
    checkpoint_store=checkpoints,
)
graph.add_edge("research", "verify")
scheduler = DistributedGraphScheduler(queue, {"research": graph}, worker_id="worker-1")
submitted = scheduler.submit("research", {"query": "AI data platforms"}, tenant_id="org-1")
# On a worker process:
scheduler.process_once()
status = scheduler.status(submitted["task_id"], tenant_id="org-1")
```

Register the same graph name/version and compatible checkpoint store on each worker. Use a shared durable database/queue visible to all workers. SQLite is best for a single host or shared persistent volume; use Postgres or a managed broker for production horizontal scaling. The worker lease must exceed the maximum graph execution time because lease renewal is not yet implemented.

## Async graphs

`DistributedGraphScheduler` supports both `Graph` and `AsyncGraph`. Call `await scheduler.process_once_async()` from an async worker loop. Async graph nodes can fan out concurrently according to their graph's `max_concurrency`.

## Recovery and retries

Graph checkpoints are persisted after node completion. If a worker crashes, the queue lease expires and another worker can claim the task. The graph checkpoint lets the new worker resume completed work rather than restarting the entire graph. A crash during a node can cause that node to execute again, so all external side effects should be idempotent. The queue uses bounded retries and records terminal failures. It does not guarantee exactly-once effects.

## Human approval

If a graph pauses with `waiting_for_approval`, submit a new resume task with the decision:

```python
scheduler.resume(
    "research", submitted["run_id"],
    tenant_id="org-1", approvals={"publish": True},
)
```

Authorize the tenant and the approver at the application/API layer before calling this method.

## Read-only visual debugger

```python
from tigerdatalab.ai import render_graph_debugger

html = render_graph_debugger(graph, submitted["run_id"])
with open("graph-debugger.html", "w", encoding="utf-8") as f:
    f.write(html)
```

Open the generated file locally to inspect node statuses, edges, node metadata, checkpoint state, error and approval status. The page is self-contained and read-only; it does not execute graph actions or connect to a running worker. Refresh/regenerate it to view newer checkpoints. State may contain sensitive data—authorize access and redact before sharing.

## Current limitations

- The included queue/checkpoint backends are SQLite; use shared managed backends for horizontally scaled deployments.
- Worker leases are not renewed during long graph runs; set lease duration appropriately.
- Recovery is at-least-once, not exactly-once. A node interrupted mid-side-effect may run again.
- This debugger is a static local inspector, not a hosted live dashboard or single-step execution controller.
- Each worker must register compatible graph definitions and versions before processing tasks.
