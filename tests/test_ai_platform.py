"""Tests for the provider-independent AI platform layer."""
from tigerdatalab.ai import Document, Evaluator, KnowledgeBase, chunk_text


def test_chunk_text_and_retrieval():
    assert chunk_text("one two three", chunk_size=100, overlap=0) == ["one two three"]
    kb = KnowledgeBase()
    kb.add(Document("sla", "Customers receive a refund when the SLA is breached."))
    hits = kb.search("SLA refund", top_k=1)
    assert len(hits) == 1
    assert hits[0][0].document_id == "sla"
    assert "refund" in kb.context("refund")


def test_evaluator_scores_callable():
    result = Evaluator().evaluate(lambda prompt: "yes", [{"prompt": "q", "expected": "yes"}, {"prompt": "q2", "expected": "no"}])
    assert result.total == 2
    assert result.passed == 1
    assert result.failed == 1
    assert result.score == 0.5
    assert result.average_latency_ms >= 0
