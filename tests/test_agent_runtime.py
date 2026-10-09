import asyncio
import json

from tigerdatalab.ai.agent_runtime import AgentRuntime, AgentToolCall, AgentTurn, InMemoryConversationMemory, openai_compatible_agent_model
from tigerdatalab.ai.durable_memory import SQLiteConversationMemory
from tigerdatalab.ai.providers import AIResponse, Provider
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
    calls = {"n": 0}
    def model(messages, schemas):
        calls["n"] += 1
        if calls["n"] == 1:
            return AgentTurn(tool_calls=(AgentToolCall("x", "danger", {}),))
        return AgentTurn(text="I did not run the action because approval was denied.")
    runtime = AgentRuntime(model, tools, permissions=PermissionPolicy().allow("default", "danger"),
                           approval=lambda name, args, role: False)
    result = runtime.run("run dangerous action")
    assert result.status == "completed" and ran["value"] is False
    assert "approval was denied" in result.output
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



def test_openai_compatible_provider_helper_wires_tools():
    class FakeProvider(Provider):
        name = "fake"
        def __init__(self):
            self.calls = 0
        def chat(self, messages, model, **kwargs):
            self.calls += 1
            assert kwargs["tools"][0]["function"]["name"] == "add"
            if self.calls == 1:
                raw = {"choices": [{"message": {
                    "role": "assistant", "content": None,
                    "tool_calls": [{"id": "c1", "type": "function", "function": {
                        "name": "add", "arguments": "{\"a\": 3, \"b\": 4}"
                    }}]
                }}]}
                return AIResponse(text="", model=model, raw=raw)
            return AIResponse(text="7", model=model, raw={"choices": [{"message": {"role": "assistant", "content": "7"}}]})

    provider = FakeProvider()
    model = openai_compatible_agent_model(provider, "fake-model")
    runtime = AgentRuntime(model, make_tools(), permissions=PermissionPolicy().allow("default", "add"))
    result = runtime.run("add 3 and 4")
    assert result.status == "completed"
    assert result.output == "7"
    assert result.tool_results["c1"] == 7


def test_in_memory_memory_isolated_by_tenant():
    memory = InMemoryConversationMemory()
    memory.save("shared-id", [{"role": "user", "content": "tenant A"}], tenant_id="tenant-a")
    memory.save("shared-id", [{"role": "user", "content": "tenant B"}], tenant_id="tenant-b")
    assert memory.load("shared-id", tenant_id="tenant-a")[0]["content"] == "tenant A"
    assert memory.load("shared-id", tenant_id="tenant-b")[0]["content"] == "tenant B"
    assert memory.load("shared-id") == []


def test_agent_runtime_model_timeout_is_bounded():
    async def slow_model(messages, schemas):
        await asyncio.sleep(0.05)
        return AgentTurn(text="too late")

    runtime = AgentRuntime(slow_model, model_timeout_seconds=0.001)
    result = asyncio.run(runtime.run_async("hello"))
    assert result.status == "failed"
    assert "Model call timed out after" in result.error


def test_agent_runtime_rejects_non_positive_model_timeout():
    import pytest
    with pytest.raises(ValueError, match="model_timeout_seconds"):
        AgentRuntime(lambda messages, schemas: AgentTurn(text="ok"), model_timeout_seconds=0)


def test_sqlite_conversation_memory_persists_and_isolates_tenants(tmp_path):
    database = tmp_path / "memory.sqlite3"
    with SQLiteConversationMemory(database) as memory:
        memory.save("shared", [{"role": "user", "content": "A"}], tenant_id="tenant-a")
        memory.save("shared", [{"role": "user", "content": "B"}], tenant_id="tenant-b")
        assert memory.load("shared", tenant_id="tenant-a")[0]["content"] == "A"
        assert memory.load("shared", tenant_id="tenant-b")[0]["content"] == "B"

    with SQLiteConversationMemory(database) as reopened:
        assert reopened.load("shared", tenant_id="tenant-a")[0]["content"] == "A"
        assert reopened.load("shared", tenant_id="tenant-b")[0]["content"] == "B"


def test_sqlite_conversation_memory_requires_tenant_and_conversation(tmp_path):
    import pytest
    with SQLiteConversationMemory(tmp_path / "memory.sqlite3") as memory:
        with pytest.raises(ValueError, match="tenant_id"):
            memory.load("c1", tenant_id="")
        with pytest.raises(ValueError, match="conversation_id"):
            memory.save("", [], tenant_id="tenant-a")


