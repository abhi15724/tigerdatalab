# Async and Parallel Graph Execution

TigerDataLab provides two orchestration styles:

- `Graph`: synchronous execution, conditional routing, loops bounded by `max_steps`, approval gates and checkpoints.
- `AsyncGraph`: asynchronous DAG execution, parallel fan-out, conditional branches, concurrency limits, per-node timeouts, safe retries, approvals and checkpoints.

## Parallel DAG example

```python
import asyncio
from tigerdatalab.ai import AsyncGraph, GraphNode

async def fetch_a(state):
    return {"a": "result A"}

async def fetch_b(state):
    return {"b": "result B"}

def combine(state):
    return {"summary": state["a"] + " + " + state["b"]}

graph = AsyncGraph("research", max_concurrency=4)
graph.add_node(GraphNode("fetch_a", fetch_a))
graph.add_node(GraphNode("fetch_b", fetch_b))
graph.add_node(GraphNode("combine", combine))
graph.add_edge("fetch_a", "combine")
graph.add_edge("fetch_b", "combine")

result = await graph.run_async({"topic": "agent frameworks"})
assert result.status == "completed"
print(result.state["summary"])
```

Independent nodes run concurrently up to `max_concurrency`. The join node waits until all its parents resolve. Node actions receive independent snapshots of state. Return mappings instead of mutating the supplied state. If parallel nodes return the same output key, the run fails with a conflict rather than silently overwriting data.

## Sync and async nodes

Both regular functions and `async def` functions are supported. Synchronous functions run in worker threads so they do not block the event loop. Set `timeout_seconds` on a `GraphNode` to bound an operation. Cancelling a timed-out thread does not forcibly terminate the underlying Python function; use cooperative cancellation or isolated workers for untrusted/blocking operations.

## Routing

- Multiple unconditional edges form parallel fan-out.
- Conditional edges are evaluated after the source node completes.
- If conditional edges exist, one unconditional edge may be used as fallback when no condition matches.
- AsyncGraph is DAG-only and rejects cycles. Use `Graph` for bounded loop-style workflows.

## Resume and approvals

Pass a stable `run_id` to checkpoint progress. Use `SQLiteCheckpointStore` on persistent storage to resume after process restarts. Approval-gated nodes pause before execution; the caller must authenticate and authorize reviewers before supplying decisions.

A failed parallel wave can have external side effects before a sibling fails. Successful sibling results are checkpointed, but external side effects are never guaranteed exactly once. Use idempotency keys for network operations and do not store credentials in graph state.

## Limits

The initial async runtime is single-process and synchronous Python actions use threads. It does not implement distributed workers, leases, remote queues, or forcibly cancellable CPU-bound tasks. Use `await graph.run_async(...)` inside an event loop; `graph.run(...)` is a convenience wrapper for scripts without a running loop.
