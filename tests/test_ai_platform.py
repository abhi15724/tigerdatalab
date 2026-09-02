"""Tests for the provider-independent AI platform layer."""
from tigerdatalab.ai import (
    AIResponse, Asset, CompanyAI, Document, Evaluator, KnowledgeBase, ModelRouter,
    Provider, Registry, Tool, ToolRegistry, Workflow, WorkflowStep, chunk_text,
)


class FakeProvider(Provider):
    name = "fake"
    def __init__(self, text="ok", fail=False):
        self.text, self.fail = text, fail

    def chat(self, messages, model, **kwargs):
        if self.fail:
            raise RuntimeError("failure")
        return AIResponse(text=self.text, model=model)


def test_chunk_text_and_retrieval():
    assert chunk_text("one two three", chunk_size=100, overlap=0) == ["one two three"]
    kb = KnowledgeBase()
    kb.add(Document("sla", "Customers receive a refund when the SLA is breached."))
    hits = kb.search("SLA refund", top_k=1)
    assert len(hits) == 1 and hits[0][0].document_id == "sla"
    assert "refund" in kb.context("refund")


def test_evaluator_scores_callable():
    result = Evaluator().evaluate(lambda prompt: "yes", [{"prompt": "q", "expected": "yes"}, {"prompt": "q2", "expected": "no"}])
    assert (result.total, result.passed, result.failed, result.score) == (2, 1, 1, 0.5)
    assert result.average_latency_ms >= 0


def test_tools_are_allow_listed():
    tools = ToolRegistry()
    tools.register(Tool("add", "Add values", lambda a, b: a + b, {"type": "object"}))
    assert tools.execute("add", {"a": 2, "b": 3}) == 5
    assert tools.schemas()[0]["type"] == "function"


def test_workflow_conditions_and_outputs():
    wf = Workflow("demo")
    wf.add_step(WorkflowStep("load", lambda s: {"value": 2}))
    wf.add_step(WorkflowStep("double", lambda s: s["value"] * 2, output_key="result"))
    result = wf.run()
    assert result.status == "completed" and result.state["result"] == 4


def test_router_fallback():
    router = ModelRouter()
    router.add(FakeProvider(fail=True), "bad")
    router.add(FakeProvider("good"), "good")
    assert router.chat([{"role": "user", "content": "hi"}]).text == "good"


def test_registry_versions():
    registry = Registry()
    registry.register(Asset("model", "support", "1.0"))
    registry.register(Asset("model", "support", "2.0"))
    assert registry.get("model", "support").version == "2.0"


def test_company_ai_uses_router():
    router = ModelRouter().add(FakeProvider("hello"), "fake-model")
    result = CompanyAI(router).ask("hello")
    assert result.output == "hello" and result.model == "fake-model"
