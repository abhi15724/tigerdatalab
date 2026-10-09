# Durable Graph Execution and Approval Gates

## SQLite checkpoint persistence

```python
from tigerdatalab.ai import Graph, GraphNode, SQLiteCheckpointStore

store = SQLiteCheckpointStore("./.tigerdatalab/checkpoints.sqlite3")
graph = Graph("pipeline", checkpoint_store=store, version="1")
graph.add_node(GraphNode("prepare", lambda state: {"prepared": True}))
result = graph.run({"dataset": "train.jsonl"}, run_id="dataset-run-01")
store.close()
```

SQLite state must be JSON-serializable. The store uses transactions and a primary key per run ID; reopening the store loads checkpoints from disk. Store the database on persistent storage. A local SQLite file on an ephemeral serverless filesystem is not durable across deployments.

## Human approval gates

```python
from tigerdatalab.ai import Graph, GraphNode, SQLiteCheckpointStore

store = SQLiteCheckpointStore("./checkpoints.sqlite3")
graph = Graph("publish", checkpoint_store=store)
graph.add_node(GraphNode("prepare", lambda state: {"draft": "ready"}))
graph.add_node(GraphNode(
    "publish",
    lambda state: {"published": True},
    approval_required=True,
))
graph.add_edge("prepare", "publish")

result = graph.run({"topic": "release"}, run_id="release-42")
if result.status == "waiting_for_approval":
    print("Approval needed for:", result.pending_approval)

# Call this only after an authenticated human reviewer makes the decision.
result = graph.run(
    run_id="release-42",
    resume=True,
    approvals={"publish": True},
)
```

The engine pauses before running an approval-gated node. A positive decision allows it to execute; a negative decision skips the node, sets `publish_approved=False` by default, and routes along the graph's conditions. Use `approval_key="approved"` to choose a custom state key. Approval decisions are caller-supplied; this library does not authenticate reviewers or provide an approval web UI. Your application must authorize the reviewer before passing a decision.

## Safety and reliability boundaries

- The SQLite store persists state and status, not Python callables. Recreate the same graph code and version before resuming.
- State must be JSON-serializable; do not put credentials or raw secrets in graph state.
- Use a persistent disk/volume and protect the database with appropriate OS permissions.
- External side effects are not exactly-once. A process crash after an action but before the checkpoint commit can cause the action to repeat on resume; use idempotency keys for external operations.
- SQLite is suitable for local/single-service use. For distributed workers, use a shared database-backed store and concurrency/lease controls before claiming multi-worker safety.
