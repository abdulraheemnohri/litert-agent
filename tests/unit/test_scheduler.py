"""Tests for the scheduler queue registry and job worker lifecycle."""

import asyncio

import pytest

from litert_agent.scheduler.jobs import Job
from litert_agent.scheduler.queue import JobQueue
from litert_agent.scheduler.worker import JobWorker


@pytest.mark.asyncio
async def test_enqueue_registers_job():
    queue = JobQueue()
    job = Job(name="test", task_description="do something")
    await queue.enqueue(job)
    assert queue.size() == 1
    assert queue.list_jobs() == [job]
    assert queue.get_job(job.id) is job


@pytest.mark.asyncio
async def test_get_job_unknown_id():
    queue = JobQueue()
    assert queue.get_job("missing") is None


@pytest.mark.asyncio
async def test_dequeue_removes_from_queue_but_keeps_registry():
    queue = JobQueue()
    job = Job(name="test", task_description="run tests")
    await queue.enqueue(job)
    popped = await queue.dequeue()
    assert popped is job
    assert queue.size() == 0
    assert queue.list_jobs() == [job]


@pytest.mark.asyncio
async def test_worker_executes_handler():
    queue = JobQueue()
    results = []

    async def handler(job):
        results.append(job.task_description)
        return "COMPLETED"

    worker = JobWorker(queue, handler=handler)
    job = Job(name="test", task_description="run tests")
    await queue.enqueue(job)

    claimed = await worker.claim_task()
    assert claimed is job
    status = await worker.execute_task(claimed)
    assert status == "COMPLETED"
    assert job.status == "COMPLETED"
    assert results == ["run tests"]


@pytest.mark.asyncio
async def test_worker_without_handler_completes():
    queue = JobQueue()
    worker = JobWorker(queue)
    job = Job(name="idle", task_description="noop")
    await queue.enqueue(job)
    claimed = await worker.claim_task()
    status = await worker.execute_task(claimed)
    assert status == "COMPLETED"


@pytest.mark.asyncio
async def test_worker_claim_empty_queue():
    queue = JobQueue()
    worker = JobWorker(queue)
    assert await worker.claim_task() is None


def test_release_task_requeues_without_await():
    queue = JobQueue()
    worker = JobWorker(queue)
    job = Job(name="retry", task_description="retry me")
    worker.release_task(job)
    assert job.status == "PENDING"
    assert queue.size() == 1


@pytest.mark.asyncio
async def test_worker_start_processes_jobs_and_survives_failures():
    queue = JobQueue()
    calls = []

    async def handler(job):
        calls.append(job.name)
        if job.name == "boom":
            raise RuntimeError("handler exploded")
        return "COMPLETED"

    worker = JobWorker(queue, handler=handler)
    ok_job = Job(name="fine", task_description="ok")
    bad_job = Job(name="boom", task_description="explode")
    await queue.enqueue(ok_job)
    await queue.enqueue(bad_job)

    async def stop_soon():
        await asyncio.sleep(0.3)
        worker.stop()

    await asyncio.gather(worker.start(), stop_soon())

    assert "fine" in calls and "boom" in calls
    assert ok_job.id in worker.completed
    assert bad_job.id in worker.failed
    assert bad_job.status.startswith("FAILED")
