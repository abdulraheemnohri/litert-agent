"""Binds the shared AgentRuntime to the API and WebSocket stream."""

from litert_agent.runtime.service import AgentRuntime
from litert_agent.api.websocket import manager as ws_manager


async def get_runtime() -> "AgentRuntime":
    runtime = AgentRuntime.get()
    await runtime.start()
    # forward runtime events to websocket clients
    def forward(event):
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(ws_manager.broadcast({"type": event.event_type, "payload": event.payload}))
        except RuntimeError:
            pass
    for event_type in ("task_started", "task_completed", "task_failed", "plan_created",
                       "tool_started", "tool_completed", "health"):
        runtime.event_bus.subscribe(event_type, forward)
    return runtime
