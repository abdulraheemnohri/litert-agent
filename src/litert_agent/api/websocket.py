"""WebSocket event streaming for live UI updates."""

import asyncio
import json
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """Manages active websocket connections and broadcasts events."""

    def __init__(self):
        self.active: list[WebSocket] = []
        self.history: list[dict[str, Any]] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.append(websocket)
        for event in self.history[-50:]:
            await websocket.send_text(json.dumps(event))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active:
            self.active.remove(websocket)

    async def broadcast(self, event: dict):
        self.history.append(event)
        if len(self.history) > 500:
            self.history = self.history[-500:]
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(json.dumps(event))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


def bind_event_bus(event_bus) -> None:
    """Forward all runtime events to websocket clients."""
    def forward(event):
        payload = {"type": event.event_type, "payload": event.payload}
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(manager.broadcast(payload))
        except RuntimeError:
            pass
    event_bus.subscribe("task_started", forward)
    event_bus.subscribe("task_completed", forward)
    event_bus.subscribe("tool_started", forward)
    event_bus.subscribe("tool_completed", forward)
    event_bus.subscribe("approval_required", forward)
    event_bus.subscribe("health", forward)
    event_bus.subscribe("log", forward)
