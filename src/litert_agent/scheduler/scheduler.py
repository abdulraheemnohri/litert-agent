"""Background worker and task scheduler."""

import asyncio
from litert_agent.scheduler.queue import JobQueue
from litert_agent.scheduler.jobs import Job

class BackgroundWorker:
    def __init__(self, queue: JobQueue):
        self.queue = queue
        self.running = False

    async def start(self):
        self.running = True
        while self.running:
            try:
                job = await asyncio.wait_for(self.queue.dequeue(), timeout=0.1)
                job.status = "RUNNING"
                job.status = "COMPLETED"
            except asyncio.TimeoutError:
                pass
            await asyncio.sleep(0.01)

    def stop(self):
        self.running = False

class Scheduler:
    def __init__(self):
        self.queue = JobQueue()
        self.worker = BackgroundWorker(self.queue)

    async def add_job(self, name: str, task_description: str) -> Job:
        job = Job(name=name, task_description=task_description)
        await self.queue.enqueue(job)
        return job
