"""Background job worker with claim/execute/release lifecycle."""

import asyncio
from typing import Awaitable, Callable

from litert_agent.scheduler.jobs import Job
from litert_agent.scheduler.queue import JobQueue


class JobWorker:
    """Claims jobs from the queue and executes them via a handler callback."""

    def __init__(self, queue: JobQueue, handler: Callable[[Job], Awaitable[str]] | None = None):
        self.queue = queue
        self.handler = handler
        self.running = False
        self.completed: list[str] = []

    async def start(self):
        self.running = True
        while self.running:
            job = await self.claim_task()
            if job is None:
                await asyncio.sleep(0.05)
                continue
            try:
                result = await self.execute_task(job)
                self.completed.append(job.id)
                job.status = result
            except Exception as exc:  # recover, never crash the worker
                job.status = f"FAILED: {exc}"

    def stop(self):
        self.running = False

    async def claim_task(self) -> Job | None:
        if self.queue.size() == 0:
            return None
        return await self.queue.dequeue()

    async def execute_task(self, job: Job) -> str:
        if self.handler is None:
            job.status = "COMPLETED"
            return "COMPLETED"
        result = await self.handler(job)
        return result or "COMPLETED"

    def release_task(self, job: Job):
        job.status = "PENDING"
        self.queue.enqueue(job)
