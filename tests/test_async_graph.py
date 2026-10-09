import asyncio
import time

import pytest

from tigerdatalab.ai.graph import GraphError, GraphNode, SQLiteCheckpointStore
from tigerdatalab.ai.async_graph import AsyncGraph


def test_async_graph_runs_coroutine_nodes():
    async def first(state):
        await asyncio.sleep(0)
        return {"value": 4}
    graph = AsyncGraph("async", [GraphNode("first", first)])
    result = asyncio.run(graph.run_async())
    assert result.status == "completed"
    assert result.state["value"] == 4


def test_async_graph_runs_independent_nodes_in_parallel():
    def task(value):
        def run(state):
            time.sleep(0.12)
            return {value: value}
        return run
    graph = AsyncGraph("parallel", max_concurrency=2)
    graph.add_node(GraphNode("a", task("a")))
    graph.add_node(GraphNode("b", task("b")))
    graph.add_node(GraphNode("join", lambda state: {"joined": state["a"] + state["b"]}))
    graph.add_edge("a", "join")
    graph.add_edge("b", "join")
    started = time.perf_counter()
    result = asyncio.run(graph.run_async())
    elapsed = time.perf_counter() - started
    assert result.status == "completed"
    assert result.state["joined"] == "ab"
    assert elapsed < 0.22


def test_async_graph_fans_out_on_unconditional_edges():
    graph = AsyncGraph("fanout")
    graph.add_node(GraphNode("start", lambda state: {"start": True}))
    graph.add_node(GraphNode("left", lambda state: {"left": True}))
    graph.add_node(GraphNode("right", lambda state: {"right": True}))
    graph.add_edge("start", "left")
    graph.add_edge("start", "right")
    result = asyncio.run(graph.run_async())
    assert result.status == "completed"
    assert result.state["left"] and result.state["right"]


def test_async_graph_conditional_branch_and_fallback():
    graph = AsyncGraph("branch")
    graph.add_node(GraphNode("start", lambda state: {"premium": False}))
    graph.add_node(GraphNode("premium", lambda state: {"path": "premium"}))
    graph.add_node(GraphNode("standard", lambda state: {"path": "standard"}))
    graph.add_edge("start", "premium", condition=lambda state: state["premium"])
    graph.add_edge("start", "standard")
    result = asyncio.run(graph.run_async())
    assert result.status == "completed"
    assert result.state["path"] == "standard"
    assert "premium" in result.skipped_nodes


def test_async_graph_rejects_cycles():
    graph = AsyncGraph("cycle")
    graph.add_node(GraphNode("a", lambda state: None))
    graph.add_node(GraphNode("b", lambda state: None))
    graph.add_edge("a", "b")
    graph.add_edge("b", "a")
    with pytest.raises(GraphError, match="acyclic"):
        graph.validate()


def test_async_graph_detects_conflicting_parallel_outputs():
    graph = AsyncGraph("conflict")
    graph.add_node(GraphNode("a", lambda state: {"same": 1}))
    graph.add_node(GraphNode("b", lambda state: {"same": 2}))
    result = asyncio.run(graph.run_async())
    assert result.status == "failed"
    assert "conflict" in result.error


def test_async_graph_timeout_and_safe_retry():
    attempts = {"count": 0}
    async def flaky(state):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("temporary")
        return {"ok": True}
    graph = AsyncGraph("retry", [GraphNode(
        "work", flaky, retries=1, retry_safe=True, timeout_seconds=1
    )])
    result = asyncio.run(graph.run_async())
    assert result.status == "completed"
    assert attempts["count"] == 2


def test_async_graph_approval_pauses_and_resumes(tmp_path):
    store = SQLiteCheckpointStore(tmp_path / "async-graph.sqlite3")
    calls = {"count": 0}
    graph = AsyncGraph("approval", checkpoint_store=store)
    graph.add_node(GraphNode("prepare", lambda state: {"prepared": True}))
    graph.add_node(GraphNode(
        "publish", lambda state: calls.__setitem__("count", calls["count"] + 1) or {"published": True},
        approval_required=True,
    ))
    graph.add_edge("prepare", "publish")
    waiting = asyncio.run(graph.run_async({}, run_id="approval-1"))
    assert waiting.status == "waiting_for_approval"
    assert waiting.pending_approval == "publish"
    resumed = asyncio.run(graph.run_async(run_id="approval-1", resume=True, approvals={"publish": True}))
    assert resumed.status == "completed"
    assert resumed.state["published"] is True
    assert calls["count"] == 1
    store.close()


def test_async_graph_persists_successful_sibling_when_another_fails(tmp_path):
    store = SQLiteCheckpointStore(tmp_path / "resume.sqlite3")
    calls = {"ok": 0, "fail": 0}
    def ok(state):
        calls["ok"] += 1
        return {"ok": True}
    def flaky(state):
        calls["fail"] += 1
        if calls["fail"] == 1:
            raise RuntimeError("once")
        return {"fixed": True}
    graph = AsyncGraph("resume", checkpoint_store=store)
    graph.add_node(GraphNode("ok", ok))
    graph.add_node(GraphNode("flaky", flaky))
    failed = asyncio.run(graph.run_async(run_id="run-1"))
    assert failed.status == "failed"
    resumed = asyncio.run(graph.run_async(run_id="run-1", resume=True))
    assert resumed.status == "completed"
    assert resumed.state["ok"] is True and resumed.state["fixed"] is True
    assert calls["ok"] == 1
    store.close()
