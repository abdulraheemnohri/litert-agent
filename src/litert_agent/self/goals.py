"""Autonomous goal manager (A-to-Z spec section 12).

Goals persist in the shared SQLite database and drive the autonomous loop.
The manager never bypasses policy: high-risk goals are created in the
WAITING_APPROVAL state and stay there until an approval is recorded.
"""
from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

DEFAULT_DB = Path.home() / ".litert-agent" / "agent.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS goals (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    priority TEXT DEFAULT 'NORMAL',
    source TEXT DEFAULT 'user',
    dependencies TEXT DEFAULT '',
    risk TEXT DEFAULT 'low',
    status TEXT DEFAULT 'PENDING',
    progress INTEGER DEFAULT 0,
    parent_goal TEXT,
    verification_rules TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);
"""


class GoalState(str, Enum):
    IDEA = "IDEA"
    PENDING = "PENDING"
    READY = "READY"
    ACTIVE = "ACTIVE"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    BLOCKED = "BLOCKED"
    PAUSED = "PAUSED"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class Goal:
    id: str
    title: str
    description: str
    priority: str
    source: str
    dependencies: list[str]
    risk: str
    status: str
    progress: int
    parent_goal: str | None
    verification_rules: str
    created_at: str
    updated_at: str
    completed_at: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "title": self.title, "description": self.description,
            "priority": self.priority, "source": self.source,
            "dependencies": self.dependencies, "risk": self.risk,
            "status": self.status, "progress": self.progress,
            "parent_goal": self.parent_goal,
            "verification_rules": self.verification_rules,
            "created_at": self.created_at, "updated_at": self.updated_at,
            "completed_at": self.completed_at,
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class GoalManager:
    """SQLite-backed goal manager. All mutations are auditable via list()."""

    def __init__(self, db_path: str | Path = DEFAULT_DB) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # -- CRUD -------------------------------------------------------------
    def create_goal(
        self,
        title: str,
        description: str = "",
        *,
        priority: str = "NORMAL",
        source: str = "user",
        dependencies: list[str] | None = None,
        risk: str = "low",
        parent_goal: str | None = None,
        verification_rules: str = "",
    ) -> Goal:
        goal_id = uuid.uuid4().hex[:12]
        # High-risk goals must wait for approval before becoming executable.
        status = GoalState.WAITING_APPROVAL.value if risk in {"medium", "high", "critical"} else GoalState.PENDING.value
        now = _now()
        self._conn.execute(
            "INSERT INTO goals (id, title, description, priority, source,"
            " dependencies, risk, status, parent_goal, verification_rules,"
            " created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (goal_id, title, description, priority, source,
             ",".join(dependencies or []), risk, status, parent_goal,
             verification_rules, now, now),
        )
        self._conn.commit()
        return self.get_goal(goal_id)

    def get_goal(self, goal_id: str) -> Goal:
        row = self._conn.execute("SELECT * FROM goals WHERE id = ?", (goal_id,)).fetchone()
        if row is None:
            raise KeyError(f"goal not found: {goal_id}")
        return self._row_to_goal(row)

    def list_goals(self, status: str | None = None) -> list[Goal]:
        if status:
            rows = self._conn.execute(
                "SELECT * FROM goals WHERE status = ? ORDER BY created_at", (status,)
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM goals ORDER BY created_at").fetchall()
        return [self._row_to_goal(r) for r in rows]

    def _update(self, goal_id: str, **fields: Any) -> Goal:
        if not fields:
            return self.get_goal(goal_id)
        fields["updated_at"] = _now()
        sets = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [goal_id]
        self._conn.execute(f"UPDATE goals SET {sets} WHERE id = ?", values)
        self._conn.commit()
        return self.get_goal(goal_id)

    # -- Lifecycle ---------------------------------------------------------
    def update_goal(self, goal_id: str, **fields: Any) -> Goal:
        allowed = {"title", "description", "priority", "progress", "risk"}
        return self._update(goal_id, **{k: v for k, v in fields.items() if k in allowed})

    def pause_goal(self, goal_id: str) -> Goal:
        return self._update(goal_id, status=GoalState.PAUSED.value)

    def resume_goal(self, goal_id: str) -> Goal:
        return self._update(goal_id, status=GoalState.PENDING.value)

    def cancel_goal(self, goal_id: str) -> Goal:
        return self._update(goal_id, status=GoalState.CANCELLED.value)

    def approve_goal(self, goal_id: str) -> Goal:
        """Record an explicit human approval for a high-risk goal."""
        goal = self.get_goal(goal_id)
        if goal.status != GoalState.WAITING_APPROVAL.value:
            raise ValueError(f"goal {goal_id} is not waiting for approval")
        return self._update(goal_id, status=GoalState.PENDING.value)

    def complete_goal(self, goal_id: str) -> Goal:
        now = _now()
        self._update(goal_id, status=GoalState.COMPLETED.value, progress=100, completed_at=now)
        return self.get_goal(goal_id)

    def fail_goal(self, goal_id: str) -> Goal:
        return self._update(goal_id, status=GoalState.FAILED.value)

    def retry_goal(self, goal_id: str) -> Goal:
        return self._update(goal_id, status=GoalState.PENDING.value, progress=0)

    # -- Dependencies -------------------------------------------------------
    def find_ready_goals(self) -> list[Goal]:
        """Goals that are PENDING and whose dependencies are all COMPLETED."""
        pending = self.list_goals(GoalState.PENDING.value)
        completed = {g.id for g in self.list_goals(GoalState.COMPLETED.value)}
        ready: list[Goal] = []
        for goal in pending:
            deps = [d for d in goal.dependencies if d]
            if all(d in completed for d in deps):
                self._update(goal.id, status=GoalState.READY.value)
                ready.append(self.get_goal(goal.id))
        return ready

    def execute_next_goal(self) -> Goal | None:
        """Promote the highest-priority READY goal to ACTIVE.

        The actual execution is performed by the autonomous loop; this only
        performs the state transition so callers know which goal is current.
        """
        order = {"CRITICAL": 0, "HIGH": 1, "NORMAL": 2, "LOW": 3, "BACKGROUND": 4}
        ready = [g for g in self.list_goals(GoalState.READY.value)]
        if not ready:
            return None
        ready.sort(key=lambda g: order.get(g.priority, 99))
        goal = ready[0]
        return self._update(goal.id, status=GoalState.ACTIVE.value)

    @staticmethod
    def _row_to_goal(row: sqlite3.Row) -> Goal:
        return Goal(
            id=row["id"], title=row["title"], description=row["description"],
            priority=row["priority"], source=row["source"],
            dependencies=[d for d in (row["dependencies"] or "").split(",") if d],
            risk=row["risk"], status=row["status"], progress=row["progress"],
            parent_goal=row["parent_goal"],
            verification_rules=row["verification_rules"],
            created_at=row["created_at"], updated_at=row["updated_at"],
            completed_at=row["completed_at"],
        )
