# Agent Runtime

TigerDataLab provides AgentRuntime for bounded model/tool loops with an explicit tool registry.

## Example

```python
from tigerdatalab.ai import AgentRuntime, AgentTurn, AgentToolCall, Tool, ToolRegistry, PermissionPolicy

tools = ToolRegistry()
tools.register(Tool("lookup", "Look up a product", lambda sku: {"sku": sku, "stock": 8}))

def model(messages, schemas):
    if not any(m.get("role") == "tool" for m in messages):
        return AgentTurn(tool_calls=(AgentToolCall("call-1", "lookup", {"sku": "SKU-1"}),))
    return AgentTurn(text="The product has 8 units in stock.")

runtime = AgentRuntime(model, tools, permissions=PermissionPolicy().allow("default", "lookup"))
result = runtime.run("Check SKU-1")
print(result.status, result.output)
```

## Connect an OpenAI-compatible provider

```python
from tigerdatalab.ai import (
    AgentRuntime, PermissionPolicy, Tool, ToolRegistry,
    openai_compatible_agent_model,
)
from tigerdatalab.ai.providers import OpenRouterProvider

tools = ToolRegistry()
tools.register(Tool("lookup", "Look up a product", lambda sku: {"sku": sku, "stock": 8}))
model = openai_compatible_agent_model(
    OpenRouterProvider(),
    model="YOUR_OPENROUTER_MODEL",
)
runtime = AgentRuntime(
    model, tools,
    permissions=PermissionPolicy().allow("default", "lookup"),
    max_steps=8, max_tool_calls=12, max_tokens=4000,
)
result = runtime.run("Check SKU-1")
```

This helper uses the OpenAI-compatible chat-completions tool schema. Native Anthropic and Gemini function calling need provider-specific adapters.

## Guardrails and limitations

- Only explicitly registered tools can run; role permissions deny tools by default.
- The runtime never evaluates model-generated source code.
- Set max steps, tool calls, token budget and tool timeout to bound execution.
- An optional approval callback gates tool calls; authenticate and authorize reviewers in your application.
- Trace events record model/tool lifecycle without storing API keys.
- InMemoryConversationMemory is process-local; use a durable tenant-scoped implementation for production.
- OpenAI-compatible AIResponse tool calls are normalized. Other provider-specific formats need an adapter that returns AgentTurn.
- This component is not a sandbox or a complete multi-tenant hosting platform. Add isolation, durable audit retention, secret management and rate limiting for deployment.
