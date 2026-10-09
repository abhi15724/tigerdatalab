import asyncio
import time

from tigerdatalab.ai.distributed import TaskWorker


class MemoryLeaseQueue:
    def __init__(self):
        self.task = {"id": "t1", "task_type": "work", "payload": {"value": 7},
                     "tenant_id": "tenant", "attempts": 1, "max_attempts": 3,
                     "lease_owner": None, "lease_until": None}
        self.renewals = 0
        self.completed = None
        self.failed = None

    def claim(self, worker_id, *, lease_seconds=60):
        if self.task is None:
            return None
        from tigerdatalab.ai.distributed import Task
        row, self.task = self.task, None
        return Task(row["id"], row["task_type"], row["payload"], row["tenant_id"],
                    row["attempts"], row["max_attempts"], worker_id, time.time()+lease_seconds)

    def renew_lease(self, task_id, worker_id, *, lease_seconds=60):
        self.renewals += 1

    def complete(self, task_id, worker_id, result):
        self.completed = dict(result)

    def fail(self, task_id, worker_id, error, *, retry_delay=0):
        self.failed = error


def test_sync_worker_renews_lease_during_long_handler():
    import time
    queue = MemoryLeaseQueue()
    worker = TaskWorker(queue, "worker-1", {"work": lambda payload: (time.sleep(0.18) or {"answer": payload["value"]})})
    assert worker.process_once(lease_seconds=0.12)
    assert queue.renewals >= 1
    assert queue.completed == {"answer": 7}


def test_async_worker_renews_lease_during_long_handler():
    async def scenario():
        queue = MemoryLeaseQueue()
        async def handler(payload):
            await asyncio.sleep(0.18)
            return {"answer": payload["value"]}
        worker = TaskWorker(queue, "worker-async", {"work": handler})
        assert await worker.process_once_async(lease_seconds=0.12)
        assert queue.renewals >= 1
        assert queue.completed == {"answer": 7}
    asyncio.run(scenario())
