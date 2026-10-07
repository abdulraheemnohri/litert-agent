"""Scheduler queue."""

import asyncio
from litert_agent.scheduler.jobs import Job

class JobQueue:
    def __init__(self):
        self.queue: asyncio.Queue[Job] = asyncio.Queue()

    async def enqueue(self, job: Job):
        await self.queue.put(job)

    async def dequeue(self) -> Job:
        return await self.queue.get()

    def size(self) -> int:
        return self.queue.qsize()
