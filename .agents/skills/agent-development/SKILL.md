# Agent Development

1. Inspect `tigerdatalab/ai/agent.py`, `agent_factory.py`, `providers.py`, `tools.py`, `rag.py` and their tests before designing an agent feature.
2. Reuse `CompanyAgent`, `AgentFactory`, `Provider`, `Tool`, `KnowledgeBase` and `Evaluator` where appropriate.
3. Keep templates declarative. Register callable tools explicitly; never instantiate arbitrary Python code from model output or configuration.
4. Separate model responses from tool execution. Validate tool name, arguments, permissions, timeout and result size before executing a tool.
5. Keep provider credentials in environment variables or a dedicated secret manager.
6. Include deterministic fake-provider tests; normal unit tests must not require paid model APIs or network access.
7. Document the limits of the current implementation rather than implying unsupported autonomous behavior.
