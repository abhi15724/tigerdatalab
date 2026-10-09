import asyncio

from tigerdatalab.ai.agent_runtime import AgentRuntime, AgentToolCall, AgentTurn
from tigerdatalab.ai.agent_adapters import anthropic_agent_model, gemini_agent_model
from tigerdatalab.ai.durable_memory import SQLiteConversationMemory
from tigerdatalab.ai.distributed import SQLiteTaskQueue, TaskWorker
from tigerdatalab.ai.observability import RuntimeTelemetry
from tigerdatalab.ai.providers import AIResponse
from tigerdatalab.ai.security import InMemoryToolRateLimiter, SQLiteAuditLog, SecurityPolicyError
from tigerdatalab.ai.graph import Graph, GraphNode
from tigerdatalab.ai.graph_visualization import to_mermaid
from tigerdatalab.ai.permissions import PermissionPolicy
from tigerdatalab.ai.tools import Tool, ToolRegistry


def test_sqlite_memory_is_tenant_scoped_and_durable(tmp_path):
    path = tmp_path / "memory.sqlite3"
    with SQLiteConversationMemory(path) as memory:
        memory.save("chat", [{"role": "user", "content": "tenant A"}], tenant_id="A")
        memory.save("chat", [{"role": "user", "content": "tenant B"}], tenant_id="B")
        assert memory.load("chat", tenant_id="A")[0]["content"] == "tenant A"
        assert memory.load("chat", tenant_id="B")[0]["content"] == "tenant B"
        assert memory.load("chat", tenant_id="C") == []
    with SQLiteConversationMemory(path) as reopened:
        assert reopened.load("chat", tenant_id="A")[0]["content"] == "tenant A"


def test_runtime_wires_tenant_memory_observer_and_audit(tmp_path):
    memory = SQLiteConversationMemory(tmp_path / "mem.sqlite3")
    audit = SQLiteAuditLog(tmp_path / "audit.sqlite3")
    telemetry = RuntimeTelemetry()
    runtime = AgentRuntime(lambda messages, schemas: AgentTurn(text="ok", usage={"total_tokens": 4}),
                           memory=memory, observer=telemetry, audit_sink=audit)
    result = runtime.run("hello", tenant_id="team-a", conversation_id="same")
    assert result.status == "completed"
    assert memory.load("same", tenant_id="team-a")[-1]["content"] == "ok"
    assert memory.load("same", tenant_id="team-b") == []
    assert telemetry.snapshot()["events"]["completed"] == 1
    assert audit.query(tenant_id="team-a")[0]["event"] == "completed"
    memory.close()
    audit.close()


def test_rate_limiter_rejects_excess_calls():
    limiter = InMemoryToolRateLimiter(max_calls=1, window_seconds=30)
    limiter.check("role", "tool")
    try:
        limiter.check("role", "tool")
    except SecurityPolicyError:
        pass
    else:
        raise AssertionError("expected rate limit")


def test_sqlite_task_queue_and_worker(tmp_path):
    with SQLiteTaskQueue(tmp_path / "tasks.sqlite3") as queue:
        task_id = queue.enqueue("sum", {"a": 3, "b": 4}, tenant_id="tenant")
        worker = TaskWorker(queue, "worker-1", {"sum": lambda payload: {"value": payload["a"] + payload["b"]}})
        assert worker.process_once()
        result = queue.get(task_id, tenant_id="tenant")
        assert result["status"] == "completed"
        assert result["result"]["value"] == 7
        assert queue.get(task_id, tenant_id="other") is None


def test_graph_mermaid_visualization():
    graph = Graph("demo")
    graph.add_node(GraphNode("start", lambda state: {"x": 1}))
    graph.add_node(GraphNode("finish", lambda state: {"done": True}))
    graph.add_edge("start", "finish", label="continue")
    output = to_mermaid(graph)
    assert "flowchart TD" in output
    assert "start" in output and "finish" in output and "continue" in output


def test_anthropic_adapter_normalizes_tool_use_and_tool_result():
    class FakeAnthropic:
        calls = 0
        def chat(self, messages, model, **kwargs):
            self.calls += 1
            assert "tools" in kwargs
            if self.calls == 1:
                return AIResponse("", model, {"input_tokens": 3, "output_tokens": 1},
                    {"content": [{"type": "tool_use", "id": "tool-1", "name": "add", "input": {"a": 2, "b": 3}}]})
            assert any(block.get("type") == "tool_result" for m in messages for block in (m.get("content") if isinstance(m.get("content"), list) else []))
            return AIResponse("5", model, {"input_tokens": 3, "output_tokens": 2}, {"content": [{"type": "text", "text": "5"}]})
    tools = ToolRegistry()
    tools.register(Tool("add", "Add", lambda a, b: a + b))
    runtime = AgentRuntime(anthropic_agent_model(FakeAnthropic(), "fake"), tools,
                           permissions=PermissionPolicy().allow("default", "add"))
    result = runtime.run("2+3")
    assert result.status == "completed" and result.output == "5"
    assert result.tool_results["tool-1"] == 5


def test_gemini_adapter_normalizes_function_call():
    class FakeGemini:
        calls = 0
        def generate_content(self, contents, model, system_instruction=None, **kwargs):
            self.calls += 1
            assert "tools" in kwargs
            if self.calls == 1:
                raw = {"candidates": [{"content": {"parts": [{"functionCall": {"name": "add", "args": {"a": 4, "b": 6}}}]}}]}
                return AIResponse("", model, {"promptTokenCount": 2, "candidatesTokenCount": 1, "totalTokenCount": 3}, raw)
            assert any("functionResponse" in part for m in contents for part in m.get("parts", []))
            raw = {"candidates": [{"content": {"parts": [{"text": "10"}]}}]}
            return AIResponse("10", model, {"promptTokenCount": 3, "candidatesTokenCount": 1, "totalTokenCount": 4}, raw)
    tools = ToolRegistry()
    tools.register(Tool("add", "Add", lambda a, b: a + b))
    runtime = AgentRuntime(gemini_agent_model(FakeGemini(), "fake"), tools,
                           permissions=PermissionPolicy().allow("default", "add"))
    result = runtime.run("4+6")
    assert result.status == "completed" and result.output == "10"
    assert result.tool_results["gemini-0"] == 10
