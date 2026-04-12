import asyncio

import pytest

from app.core.task_manager import TaskManager, TaskStep


@pytest.mark.asyncio
async def test_create_and_progress():
    tm = TaskManager()
    tid = tm.create_task("video.mp4")
    assert tid in tm.tasks
    assert tm.tasks[tid].status == TaskStep.QUEUED

    await tm.update_progress(tid, TaskStep.DETECTING, 0.3, "x")
    t = tm.get(tid)
    assert t.status == TaskStep.DETECTING
    assert t.progress == 0.3
    assert t.message == "x"


@pytest.mark.asyncio
async def test_subscriber_receives_message():
    tm = TaskManager()
    tid = tm.create_task("v.mp4")

    received: list[dict] = []

    class FakeWS:
        async def send_json(self, msg):
            received.append(msg)

    ws = FakeWS()
    await tm.subscribe(tid, ws)
    await tm.update_progress(tid, TaskStep.DETECTING, 0.5, "halfway")
    assert len(received) == 1
    assert received[0]["step"] == "detecting"
    assert received[0]["progress"] == 0.5


@pytest.mark.asyncio
async def test_dead_subscriber_is_removed():
    tm = TaskManager()
    tid = tm.create_task("v.mp4")

    class DeadWS:
        async def send_json(self, msg):
            raise RuntimeError("dead")

    ws = DeadWS()
    await tm.subscribe(tid, ws)
    await tm.update_progress(tid, TaskStep.DETECTING, 0.1, "")
    assert ws not in tm.subscribers[tid]


@pytest.mark.asyncio
async def test_enqueue_and_dequeue():
    tm = TaskManager()
    tid = tm.create_task("v.mp4")
    await tm.enqueue(tid)
    got = await asyncio.wait_for(tm.queue.get(), timeout=0.1)
    assert got == tid
