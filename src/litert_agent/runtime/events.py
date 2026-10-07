"""Events and event bus."""

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel


class AgentEvent(BaseModel):
    event_type: str
    payload: dict[str, Any] = {}

class EventBus:
    def __init__(self):
        self.listeners: dict[str, list[Callable[[AgentEvent], None]]] = {}

    def subscribe(self, event_type: str, callback: Callable[[AgentEvent], None]):
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)

    def publish(self, event: AgentEvent):
        for callback in self.listeners.get(event.event_type, []):
            try:
                callback(event)
            except Exception:
                pass
