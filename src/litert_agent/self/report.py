"""Self-awareness report (A-to-Z spec section 9)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from litert_agent.self.curiosity import CuriosityEngine
from litert_agent.self.goals import GoalManager, GoalState
from litert_agent.self.learning import LearningEngine


def generate_self_report(db_path: str | Path | None = None) -> dict[str, Any]:
    """Operational self-report: goals, curiosity, learning.

    Deliberately excludes hidden chain-of-thought and any secrets —
    only concise operational status (spec: no fake self-awareness).
    """
    goals = GoalManager(db_path) if db_path else GoalManager()
    curiosity = CuriosityEngine(db_path) if db_path else CuriosityEngine()
    learning = LearningEngine(db_path) if db_path else LearningEngine()
    try:
        by_status: dict[str, int] = {}
        for goal in goals.list_goals():
            by_status[goal.status] = by_status.get(goal.status, 0) + 1
        return {
            "goals": {
                "total": sum(by_status.values()),
                "active": by_status.get(GoalState.ACTIVE.value, 0),
                "pending": by_status.get(GoalState.PENDING.value, 0)
                + by_status.get(GoalState.READY.value, 0),
                "waiting_approval": by_status.get(GoalState.WAITING_APPROVAL.value, 0),
                "completed": by_status.get(GoalState.COMPLETED.value, 0),
                "failed": by_status.get(GoalState.FAILED.value, 0),
                "by_status": by_status,
            },
            "curiosity": {
                "open": [c.as_dict() for c in curiosity.rank_curiosity()],
            },
            "learning": {
                "recent_experiences": [e.as_dict() for e in learning.list_experiences(5)],
                "lessons": learning.list_lessons(),
                "skill_proposals": learning.list_skill_proposals(),
                "pattern": learning.derive_pattern(),
            },
        }
    finally:
        goals.close()
        curiosity.close()
        learning.close()
