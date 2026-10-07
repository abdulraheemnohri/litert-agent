"""Scheduler queue."""

import asyncio
from litert_agent.scheduler.jobs import Job


class JobQueue:
    """In-memory job queue with a registry of all known jobs."""

    def __init__(self):
        self.queue: asyncio.Queue[Job] = asyncio.Queue()
        self._all: list[Job] = []

    async def enqueue(self, job: Job):
        self._all.append(job)
        await self.queue.put(job)

    async def dequeue(self) -> Job:
        return await self.queue.get()

    def size(self) -> int:
        return self.queue.qsize()

    def list_jobs(self) -> list[Job]:
        """All jobs ever enqueued (pending, running, completed)."""
        return list(self._all)

    def get_job(self, job_id: str) -> Job | None:
        for job in self._all:
            if job.id == job_id:
                return job
        return None
