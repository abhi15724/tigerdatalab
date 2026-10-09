# Production Runtime Guide

This guide describes the infrastructure components currently included in TigerDataLab. They are production-oriented building blocks, not a certification that an application is secure under every deployment model.

## Durable, tenant-scoped conversation memory

```python
from tigerdatalab.ai import AgentRuntime, SQLiteConversationMemory

memory = SQLiteConversationMemory("./data/agent-memory.sqlite3")
runtime = AgentRuntime(model=my_model_adapter, memory=memory)

result = runtime.run(
    "Summarize my project",
    tenant_id="org-123",
    conversation_id="session-456",
)
```

The SQLite primary key is the pair `(tenant_id, conversation_id)`. The runtime passes the tenant scope to memory implementations that accept it. Use opaque tenant/session IDs and authorize the tenant before invoking the runtime. SQLite is appropriate for one host or a shared persistent volume; use a managed transactional database for high-write multi-region services. Configure disk encryption, backup, retention and deletion policies in the hosting environment.

## Native provider tool calling

```python
from tigerdatalab.ai import (
    AgentRuntime, PermissionPolicy, Tool, ToolRegistry,
    anthropic_agent_model, gemini_agent_model,
)
from tigerdatalab.ai.providers import AnthropicProvider, GeminiProvider

tools = ToolRegistry()
tools.register(Tool("lookup", "Look up a SKU", lookup_function,
                    parameters={"type": "object", "properties": {"sku": {"type": "string"}}, "required": ["sku"]}))

# Select one adapter:
model = anthropic_agent_model(AnthropicProvider(), "YOUR_ANTHROPIC_MODEL")
# Or:
# model = gemini_agent_model(GeminiProvider(), "YOUR_GEMINI_MODEL")

runtime = AgentRuntime(
    model, tools,
    permissions=PermissionPolicy().allow("default", "lookup"),
    max_steps=8, max_tool_calls=12, max_tokens=4000,
    tool_timeout_seconds=20,
)
```

Set `ANTHROPIC_API_KEY` or `GOOGLE_API_KEY` in the environment. Check the selected model's support for tool calling and schema constraints. Provider capabilities and model names change; validate against your provider account.

## Observability, estimated cost and audit

```python
from tigerdatalab.ai import RuntimeTelemetry, SQLiteAuditLog, LoggingObserver, AgentRuntime

telemetry = RuntimeTelemetry(prices={
    "example-model": {"input": 0.15, "output": 0.60},  # USD / million tokens
})
audit = SQLiteAuditLog("./data/agent-audit.sqlite3")
runtime = AgentRuntime(model, observer=telemetry, audit_sink=audit)
# ... execute work ...
print(telemetry.snapshot())
print(audit.query(tenant_id="org-123", limit=100))
```

Telemetry is process-local; cost is an estimate based on configured prices and reported token usage, not provider billing. Logs and audit events intentionally should not contain raw prompts, credentials, or tool arguments. Apply a retention policy and restrict access to audit records.

## Rate limiting and secret resolution

Use `InMemoryToolRateLimiter` to limit per-role/per-tool calls in a single process. For multiple replicas, implement `ToolRateLimiter` with a shared store. Use `EnvironmentSecretProvider` to resolve named environment secrets or implement `SecretProvider` with a cloud secret manager. Never put secret values into graph state, conversation memory, telemetry or source control.

## Distributed task queue and workers

```python
from tigerdatalab.ai import SQLiteTaskQueue, TaskWorker

queue = SQLiteTaskQueue("./data/agent-tasks.sqlite3")
task_id = queue.enqueue("summarize", {"document_id": "doc-9"}, tenant_id="org-123")
worker = TaskWorker(queue, "worker-a", {"summarize": summarize_handler})
worker.process_once(lease_seconds=60)
print(queue.get(task_id, tenant_id="org-123"))
```

Multiple worker processes may compete for tasks through a shared durable SQLite database, using transactional claims and expiring leases. For horizontally scaled production services, prefer a managed queue or Postgres-backed implementation, worker heartbeats, dead-letter handling, metrics and operational alerting. Task handlers must be idempotent: a worker can lose its lease after an external side effect and a retry may execute the handler again. Queue leases do not provide exactly-once external side effects.

## Graph visualization

```python
from tigerdatalab.ai import to_mermaid

print(to_mermaid(graph))
```

The renderer inspects the graph definition only. It never executes graph actions or condition callbacks. Use the output in Mermaid-compatible documentation or preview tools. Interactive breakpoints, step-through execution and a visual graph editor are not part of this implementation yet.

## Security checklist before internet-facing deployment

- Require authentication; authenticate and authorize tenant access on every request.
- Store credentials in environment variables or a managed secret store, rotate them, and never commit them.
- Use tool allow-lists, least-privilege credentials, approval gates for consequential operations and rate limits.
- Apply request-size limits, input validation, output limits, network egress policy and dependency scanning.
- Use a hardened container/VM or isolated worker for untrusted code. These library controls do **not** sandbox arbitrary Python or model-generated shell commands.
- Configure database encryption, backups, access controls, audit retention and deletion.
- Use idempotency keys for external side effects; checkpoints and queue leases do not guarantee exactly-once behavior.
- Use shared persistence and rate-limiting implementations when deploying multiple replicas.
- Test failure recovery, tenant isolation, expired leases, provider timeouts and abuse cases before release.

## Current scope boundaries

The queue implementation is SQLite-based and uses cooperative leased workers. It does not provide a remote broker, distributed graph scheduler, lease renewal, exactly-once effects or a web UI debugger. The graph visualization helper emits Mermaid source, not an interactive editor. Native Anthropic/Gemini adapters map common function-calling payloads; provider-specific model limitations may require adjustments.
