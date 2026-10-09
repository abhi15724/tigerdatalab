import pytest

from tigerdatalab.ai.graph import Graph, GraphError, GraphNode, InMemoryCheckpointStore


def test_graph_runs_linear_nodes_and_merges_mapping_outputs():
    graph = Graph("linear")
    graph.add_node(GraphNode("first", lambda state: {"value": 3}))
    graph.add_node(GraphNode("second", lambda state: {"total": state["value"] + 4}))
    graph.add_edge("first", "second")
    result = graph.run({"seed": 1})
    assert result.status == "completed"
    assert result.state == {"seed": 1, "value": 3, "total": 7}
    assert result.executed_nodes == ["first", "second"]
    assert result.steps == 2


def test_graph_routes_by_condition_and_uses_fallback():
    graph = Graph("route", start="classify")
    graph.add_node(GraphNode("classify", lambda state: {"kind": "premium"}))
    graph.add_node(GraphNode("premium", lambda state: {"chosen": "premium"}))
    graph.add_node(GraphNode("standard", lambda state: {"chosen": "standard"}))
    graph.add_edge("classify", "premium", lambda state: state["kind"] == "premium")
    graph.add_edge("classify", "standard")
    result = graph.run()
    assert result.status == "completed"
    assert result.state["chosen"] == "premium"
    assert result.executed_nodes == ["classify", "premium"]


def test_graph_rejects_invalid_edges_and_ambiguous_fallbacks():
    graph = Graph("bad", [GraphNode("a", lambda state: None)])
    graph.add_edge("a", "missing")
    with pytest.raises(GraphError, match="target does not exist"):
        graph.validate()
    graph = Graph("ambiguous", [GraphNode("a", lambda state: None), GraphNode("b", lambda state: None)])
    graph.add_edge("a", "b")
    graph.add_edge("a", "b")
    with pytest.raises(GraphError, match="multiple unconditional"):
        graph.validate()


def test_graph_requires_explicit_safe_retry_policy():
    with pytest.raises(ValueError, match="retry_safe=True"):
        GraphNode("unsafe", lambda state: None, retries=1)


def test_graph_retries_only_when_declared_safe():
    attempts = {"count": 0}
    def flaky(state):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("temporary")
        return {"ok": True}
    graph = Graph("retry", [GraphNode("work", flaky, retries=1, retry_safe=True)])
    result = graph.run()
    assert result.status == "completed"
    assert result.state["ok"] is True
    assert attempts["count"] == 2
    assert result.steps == 1


def test_graph_stops_cycles_at_max_steps():
    graph = Graph("cycle", max_steps=3)
    graph.add_node(GraphNode("loop", lambda state: {"count": state.get("count", 0) + 1}))
    graph.add_edge("loop", "loop")
    result = graph.run()
    assert result.status == "failed"
    assert result.steps == 3
    assert result.state["count"] == 3
    assert "max_steps=3" in result.error


def test_graph_resume_continues_after_last_successful_checkpoint():
    store = InMemoryCheckpointStore()
    calls = {"first": 0, "second": 0}
    def first(state):
        calls["first"] += 1
        return {"first_done": True}
    def second(state):
        calls["second"] += 1
        if calls["second"] == 1:
            raise RuntimeError("temporary failure")
        return {"second_done": True}
    graph = Graph("resume", checkpoint_store=store)
    graph.add_node(GraphNode("first", first))
    graph.add_node(GraphNode("second", second))
    graph.add_edge("first", "second")
    failed = graph.run(run_id="run-1")
    assert failed.status == "failed"
    assert failed.executed_nodes == ["first"]
    assert calls["first"] == 1
    resumed = graph.run(run_id="run-1", resume=True)
    assert resumed.status == "completed"
    assert resumed.state["first_done"] is True
    assert resumed.state["second_done"] is True
    assert calls["first"] == 1
    assert calls["second"] == 2


def test_graph_rejects_missing_or_incompatible_checkpoint():
    graph = Graph("g", [GraphNode("a", lambda state: None)])
    with pytest.raises(GraphError, match="No checkpoint"):
        graph.run(run_id="missing", resume=True)
    graph.run(run_id="run-2")
    other = Graph("g", [GraphNode("a", lambda state: None)], version="2",
                  checkpoint_store=graph.checkpoint_store)
    with pytest.raises(GraphError, match="version"):
        other.run(run_id="run-2", resume=True)


def test_graph_requires_run_id_for_resume():
    graph = Graph("g", [GraphNode("a", lambda state: None)])
    with pytest.raises(GraphError, match="requires a run_id"):
        graph.run(resume=True)
