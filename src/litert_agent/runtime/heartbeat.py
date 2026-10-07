"""Heartbeat and Supervisor."""

import asyncio

from litert_agent.runtime.events import AgentEvent, EventBus


class Heartbeat:
    """Periodically emits health events on the shared event bus."""

    def __init__(self, interval_seconds: float = 30.0, event_bus: EventBus | None = None):
        self.interval = interval_seconds
        self.event_bus = event_bus or EventBus()
        self.running = False

    async def start(self):
        self.running = True
        while self.running:
            await asyncio.sleep(self.interval)
            self.event_bus.publish(AgentEvent(event_type="health", payload=Supervisor().check_health()))

    def stop(self):
        self.running = False


class Supervisor:
    """Checks agent, model, worker and queue health."""

    def __init__(self, model_provider=None, queue=None):
        self.model_provider = model_provider
        self.queue = queue

    def check_health(self) -> dict:
        report = {"status": "HEALTHY", "checks": {}}
        if self.model_provider is not None:
            info = getattr(self.model_provider, "discovery_info", None) or {}
            available = bool(info.get("available", False))
            report["checks"]["model"] = "READY" if available else "UNAVAILABLE"
            if not available:
                report["status"] = "DEGRADED"
        if self.queue is not None:
            report["checks"]["queue_size"] = self.queue.size()
        return report
