import asyncio
import json

import pytest

from tigerdatalab.ai.distributed import SQLiteTaskQueue
from tigerdatalab.ai.graph import Graph, GraphNode, SQLiteCheckpointStore
from tigerdatalab.ai.async_graph import AsyncGraph
from tigerdatalab.ai.graph_scheduler import DistributedGraphScheduler, GraphSchedulerError
from tigerdatalab.ai.graph_debugger import render_graph_debugger


def test_distributed_scheduler_runs_graph_and_persists_result(tmp_path):
    checkpoints = SQLiteCheckpointStore(tmp_path / "checkpoints.sqlite3")
    queue = SQLiteTaskQueue(tmp_path / "tasks.sqlite3")
    graph = Graph("report", [GraphNode("build", lambda state: {"report": state["topic"] + " done"})],
                  checkpoint_store=checkpoints)
    scheduler = DistributedGraphScheduler(queue, {"report": graph}, worker_id="worker-1")
    submitted = scheduler.submit("report", {"topic": "market"}, tenant_id="tenant-a")
    assert scheduler.status(submitted["task_id"], tenant_id="tenant-b") is None
    assert scheduler.process_once()
    task = scheduler.status(submitted["task_id"], tenant_id="tenant-a")
    assert task["status"] == "completed"
    assert task["result"]["status"] == "completed"
    assert task["result"]["state"]["report"] == "market done"
    checkpoints.close()
    queue.close()


def test_distributed_scheduler_supports_async_graph(tmp_path):
    async def make_output(state):
        await asyncio.sleep(0)
        return {"answer": 42}
    graph = AsyncGraph("async-report", [GraphNode("build", make_output)])
    with SQLiteTaskQueue(tmp_path / "tasks.sqlite3") as queue:
        scheduler = DistributedGraphScheduler(queue, {"async-report": graph}, worker_id="worker-async")
        submitted = scheduler.submit("async-report", tenant_id="tenant-a")
        assert asyncio.run(scheduler.process_once_async())
        task = scheduler.status(submitted["task_id"], tenant_id="tenant-a")
        assert task["result"]["state"]["answer"] == 42


def test_distributed_scheduler_resume_waiting_approval(tmp_path):
    store = SQLiteCheckpointStore(tmp_path / "checkpoints.sqlite3")
    graph = Graph("approval", [
        GraphNode("approve", lambda state: {"action": "ready"}, approval_required=True),
        GraphNode("finish", lambda state: {"finished": state["approve_approved"]}),
    ], checkpoint_store=store)
    graph.add_edge("approve", "finish")
    with SQLiteTaskQueue(tmp_path / "tasks.sqlite3") as queue:
        scheduler = DistributedGraphScheduler(queue, {"approval": graph}, worker_id="worker")
        submitted = scheduler.submit("approval", tenant_id="t")
        scheduler.process_once()
        task = scheduler.status(submitted["task_id"], tenant_id="t")
        assert task["result"]["status"] == "waiting_for_approval"
        resumed = scheduler.resume("approval", submitted["run_id"], tenant_id="t", approvals={"approve": True})
        scheduler.process_once()
        task2 = scheduler.status(resumed["task_id"], tenant_id="t")
        assert task2["result"]["status"] == "completed"
        assert task2["result"]["state"]["finished"] is True
    store.close()


def test_graph_debugger_is_standalone_read_only_html(tmp_path):
    store = SQLiteCheckpointStore(tmp_path / "checkpoints.sqlite3")
    graph = Graph("inspect", [GraphNode("a", lambda state: {"x": 1}, description="Produce x")],
                  checkpoint_store=store)
    page = render_graph_debugger(graph)
    assert "<!doctype html>" in page.lower()
    assert "Produce x" in page
    assert "graph-data" in page
    assert "never executes graph actions" in page
    assert json.loads(page.split('<script type="application/json" id="graph-data">')[1].split("</script>")[0])["graph"] == "inspect"
    store.close()


def test_scheduler_rejects_unknown_graph(tmp_path):
    with SQLiteTaskQueue(tmp_path / "tasks.sqlite3") as queue:
        scheduler = DistributedGraphScheduler(queue, {"known": Graph("known", [GraphNode("a", lambda state: {})])},
                                              worker_id="worker")
        with pytest.raises(GraphSchedulerError, match="not registered"):
            scheduler.submit("unknown", tenant_id="t")
