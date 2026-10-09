import asyncio
import json

from tigerdatalab.ai.agent_runtime import AgentRuntime, AgentToolCall, AgentTurn, InMemoryConversationMemory
from tigerdatalab.ai.permissions import PermissionPolicy
from tigerdatalab.ai.tools import Tool, ToolRegistry


def make_tools():
    tools = ToolRegistry()
    tools.register(Tool("add", "Add two numbers", lambda a, b: a + b))
    return tools


def test_agent_runtime_executes_registered_tool_then_returns_answer():
    calls = {"count": 0}
    def model(messages, schemas):
        calls["count"] += 1
        if calls["count"] == 1:
            assert schemas[0]["function"]["name"] == "add"
            return AgentTurn(tool_calls=(AgentToolCall("call-1", "add", {"a": 2, "b": 5}),))
        tool_message = next(m for m in messages if m.get("role") == "tool")
        assert json.loads(tool_message["content"]) == 7
        return AgentTurn(text="Seven", usage={"total_tokens": 12}, model="fake-model")
    policy = PermissionPolicy().allow("default", "add")
    result = AgentRuntime(model, make_tools(), permissions=policy).run("What is 2 + 5?")
    assert result.status == "completed" and result.output == "Seven"
    assert result.tool_results["call-1"] == 7 and result.usage["total_tokens"] == 12


def test_agent_runtime_blocks_tool_not_offered_to_role():
    def model(messages, schemas):
        return AgentTurn(tool_calls=(AgentToolCall("x", "add", {"a": 1, "b": 1}),))
    result = AgentRuntime(model, make_tools()).run("do it")
    assert result.status == "failed"
    assert "not permitted" in result.error


def test_agent_runtime_approval_gate_prevents_tool_execution():
    ran = {"value": False}
    tools = ToolRegistry()
    tools.register(Tool("danger", "Dangerous", lambda: ran.__setitem__("value", True)))
    def model(messages, schemas):
        return AgentTurn(tool_calls=(AgentToolCall("x", "danger", {}),))
    runtime = AgentRuntime(model, tools, permissions=PermissionPolicy().allow("default", "danger"),
                           approval=lambda name, args, role: False)
    result = runtime.run("run dangerous action")
    assert result.status == "completed" and ran["value"] is False
    assert any(e.event == "tool_denied" for e in result.trace)


def test_agent_runtime_persists_conversation_memory():
    memory = InMemoryConversationMemory()
    runtime = AgentRuntime(lambda messages, schemas: AgentTurn(text=f"messages={len(messages)}"), memory=memory)
    runtime.run("hello", conversation_id="c1")
    runtime.run("again", conversation_id="c1")
    assert len(memory.load("c1")) >= 4


def test_agent_runtime_token_budget():
    runtime = AgentRuntime(lambda messages, schemas: AgentTurn(text="done", usage={"total_tokens": 10}), max_tokens=5)
    result = runtime.run("hello")
    assert result.status == "failed" and "Token budget exceeded" in result.error


def test_agent_runtime_supports_async_model_and_tool():
    async def lookup(item):
        return {"item": item}
    tools = ToolRegistry()
    tools.register(Tool("lookup", "Look up an item", lookup))
    calls = {"n": 0}
    async def model(messages, schemas):
        calls["n"] += 1
        if calls["n"] == 1:
            return AgentTurn(tool_calls=(AgentToolCall("id", "lookup", {"item": "x"}),))
        return AgentTurn(text="found")
    runtime = AgentRuntime(model, tools, permissions=PermissionPolicy().allow("default", "lookup"))
    result = asyncio.run(runtime.run_async("lookup x"))
    assert result.status == "completed" and result.output == "found"
    assert result.tool_results["id"] == {"item": "x"}
