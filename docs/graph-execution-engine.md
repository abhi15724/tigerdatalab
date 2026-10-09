# Graph Execution Engine

TigerDataLab's graph engine adds directed execution, conditional routing, bounded loops, explicit retry policy and checkpoints while retaining the existing `Workflow` API for simple linear tasks.

## Quick start

```python
from tigerdatalab.ai import Graph, GraphNode

graph = Graph("research-report", start="research", max_steps=12)
graph.add_node(GraphNode("research", lambda state: {
    "sources": ["source-a", "source-b"]
}))
graph.add_node(GraphNode("verify", lambda state: {
    "verified": len(state["sources"]) >= 2
}))
graph.add_node(GraphNode("draft", lambda state: {
    "report": "Draft based on verified research"
}))
graph.add_node(GraphNode("review", lambda state: {
    "approved": state["verified"]
}))

graph.add_edge("research", "verify")
graph.add_edge("verify", "draft", condition=lambda state: state["verified"])
graph.add_edge("verify", "review")
graph.add_edge("draft", "review")

result = graph.run({"topic": "AI training data"}, run_id="report-001")
if result.status != "completed":
    raise RuntimeError(result.error)
print(result.state["report"])
```

## Execution semantics

- Each node receives a mutable state dictionary.
- Return a mapping to merge fields into state; use `output_key` to store a return value under a named key.
- Conditional edges are checked in declaration order; the first true condition wins. A single unconditional edge can act as the fallback.
- Retries require both `retries > 0` and `retry_safe=True`. Only opt into retries for operations that are safe to repeat.
- `max_steps` bounds node executions and prevents unbounded loops.
- Supply `run_id` to save checkpoints through the configured `CheckpointStore`. Resume using `graph.run(run_id="report-001", resume=True)`.
- Checkpoints contain graph name/version; increment the version when changing graph semantics so incompatible runs cannot resume silently.

## Limitations

The default `InMemoryCheckpointStore` is process-local and is lost when the process exits. Implement `CheckpointStore` with a durable database/object store for restart survival. Checkpoints are saved after successful nodes; a crash after an external side effect but before checkpoint persistence can repeat that side effect on resume. This is not exactly-once execution.

The runtime is currently synchronous and does not provide parallel scheduling, async nodes, distributed workers, node timeouts, or human approval gates. These need separate implementations and tests.
