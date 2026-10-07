"""Prioritizer: task priority engine."""

from enum import Enum


class Priority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"
    BACKGROUND = "BACKGROUND"


class Prioritizer:
    """Computes and orders task priorities."""

    def calculate_priority(self, description: str) -> Priority:
        lowered = description.lower()
        if any(k in lowered for k in ("critical", "urgent", "security", "crash", "data loss")):
            return Priority.CRITICAL
        if any(k in lowered for k in ("fix", "failing", "broken", "error")):
            return Priority.HIGH
        if any(k in lowered for k in ("document", "cleanup", "refactor", "later")):
            return Priority.LOW
        if any(k in lowered for k in ("background", "idle", "when free")):
            return Priority.BACKGROUND
        return Priority.NORMAL

    def sort_tasks(self, tasks: list[dict]) -> list[dict]:
        order = {p.value: i for i, p in enumerate(
            [Priority.CRITICAL, Priority.HIGH, Priority.NORMAL, Priority.LOW, Priority.BACKGROUND])}
        return sorted(tasks, key=lambda t: order.get(t.get("priority", "NORMAL"), 2))
