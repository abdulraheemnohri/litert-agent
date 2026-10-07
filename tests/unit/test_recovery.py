"""Unit tests for recovery and scheduler worker subsystems."""

import pytest
from litert_agent.memory.sqlite import DatabaseManager
from litert_agent.recovery.checkpoints import CheckpointManager
from litert_agent.recovery.crash_recovery import CrashRecovery
from litert_agent.recovery.healer import Healer
from litert_agent.scheduler.worker import JobWorker
from litert_agent.scheduler.queue import JobQueue
from litert_agent.scheduler.jobs import Job


@pytest.fixture
def db(tmp_path):
    manager = DatabaseManager(tmp_path / "agent.db")
    import asyncio
    asyncio.get_event_loop().run_until_complete(manager.init_db())
    return manager


def test_checkpoint_lifecycle(db):
    mgr = CheckpointManager(db)
    cid = mgr.create_checkpoint("task-1", "before edit", {"files": ["a.py"]})
    assert mgr.list_checkpoints("task-1")[0]["id"] == cid
    state = mgr.inspect_checkpoint(cid)
    assert state["state"]["files"] == ["a.py"]
    assert mgr.delete_checkpoint(cid) is True
    assert mgr.list_checkpoints("task-1") == []


def test_crash_recovery(db):
    cr = CrashRecovery(db)
    assert cr.resume_or_pause("t9") == "PAUSE"
    cr.persist_state("t9", "step-2", ["s1", "s2"], 4)
    state = cr.load_state("t9")
    assert state["current_step"] == "step-2"
    assert cr.resume_or_pause("t9") == "RESUME"
    cr.clear_state("t9")
    assert cr.load_state("t9") is None


def test_healer():
    healer = Healer(max_retries=1)
    assert healer.diagnose("request timeout") == "transient"
    assert healer.heal("model", "request timeout") == "RETRY"
    assert healer.heal("model", "request timeout") == "ESCALATE"


@pytest.mark.asyncio
async def test_job_worker():
    queue = JobQueue()

    async def handler(job: Job) -> str:
        return "COMPLETED"

    worker = JobWorker(queue, handler)
    await queue.enqueue(Job(name="j1", task_description="do"))
    job = await worker.claim_task()
    result = await worker.execute_task(job)
    assert result == "COMPLETED"
