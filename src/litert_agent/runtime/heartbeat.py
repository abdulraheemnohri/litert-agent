"""Heartbeat and Supervisor."""

import asyncio

class Heartbeat:
    def __init__(self, interval_seconds: float = 30.0):
        self.interval = interval_seconds
        self.running = False

    async def start(self):
        self.running = True
        while self.running:
            await asyncio.sleep(self.interval)

    def stop(self):
        self.running = False

class Supervisor:
    def check_health(self) -> dict:
        return {"status": "HEALTHY"}
