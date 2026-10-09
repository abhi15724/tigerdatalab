# TigerDataLab Agent Factory

This module builds reusable agents from TigerDataLab's CompanyAgent runtime, model providers,
knowledge base, workflows and explicitly registered tools. It is an in-process factory, not
a hosted or distributed multi-tenant control plane.

## Quick start

```python
from tigerdatalab.ai import AgentFactory, AgentTemplate, OpenRouterProvider

factory = AgentFactory(project_name="support")
factory.register_template(AgentTemplate(
    name="support-assistant",
    provider="openrouter",
    model="YOUR_OPENROUTER_MODEL",
    system_prompt="Answer from approved support policies. If unsure, say so.",
    description="Customer support knowledge assistant",
))
agent = factory.create("support-assistant", provider=OpenRouterProvider())
print(agent.ask("How do I reset my password?").output)
```

Set `OPENROUTER_API_KEY` in the environment. Never store credentials in templates, config
files, source control, or prompts.

## Explicit tools

Register trusted Python callables with `factory.register_tool(Tool(...))`, then reference
their names in `AgentTemplate.tool_names`. Tool schemas should use JSON Schema and include
required fields and `additionalProperties: false` where appropriate. Do not expose arbitrary
shell, filesystem, database-write, or code-execution tools. Provider tool-call support varies;
the factory registers tools with the current TigerDataLab runtime but does not claim a complete
model-driven tool-execution loop for every provider.

## Configuration

`create_from_config()` accepts only `name`, `provider`, `model`, `system_prompt`,
`description`, and `tool_names`. Callable tools must be registered separately; arbitrary
code and credential fields are rejected.

## Lifecycle and production boundaries

- `register_template()`: validate reusable configuration.
- `register_tool()`: add an explicitly supplied callable.
- `create()`: connect provider and assemble agent, knowledge, workflow, and tools.
- `get()`, `list_templates()`, `list_agents()`: inspect in-memory registrations.
- `create_from_config()`: create from a restricted Python mapping.

The registry is in-memory and process-local. A public multi-user service still needs durable
storage, authentication, tenant isolation, secret management, audit retention, background
jobs, quotas, timeouts, retries and monitoring. Sensitive actions need enforcement inside the
action handler, not only an approval record.
