"""Crash recovery: durable, bounded task state snapshots."""

import json
from datetime import datetime

from litert_agent.memory.sqlite import DatabaseManager


class CrashRecovery:
    """Persists runtime state and resumes safely after restarts."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def persist_state(
        self, task_id: str, current_step: str, plan: list[str], iteration: int,
        runtime_state: dict | None = None, status: str = "RUNNING",
    ) -> str:
        state = {
            "task_id": task_id,
            "current_step": current_step,
            "plan": list(plan)[:128],
            "iteration": max(0, int(iteration)),
            "status": status,
            "runtime_state": runtime_state or {},
        }
        self.db.execute_write(
            "INSERT OR REPLACE INTO checkpoints "
            "(id, task_id, description, state_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (f"crash-{task_id}", task_id, "crash-recovery-snapshot",
             json.dumps(state), datetime.utcnow().isoformat()),
        )
        return f"crash-{task_id}"

    def load_state(self, task_id: str) -> dict | None:
        rows = self.db.execute_read(
            "SELECT state_json FROM checkpoints WHERE id = ?", (f"crash-{task_id}",)
        )
        if not rows:
            return None
        try:
            state = json.loads(rows[0][0])
        except (TypeError, ValueError, json.JSONDecodeError):
            return None
        if not isinstance(state, dict):
            return None
        try:
            state["iteration"] = min(max(int(state.get("iteration", 0)), 0), 100000)
        except (TypeError, ValueError):
            state["iteration"] = 0
        state["plan"] = state.get("plan") if isinstance(state.get("plan"), list) else []
        return state

    def clear_state(self, task_id: str) -> None:
        self.db.execute_write("DELETE FROM checkpoints WHERE id = ?", (f"crash-{task_id}",))

    def resume_or_pause(self, task_id: str) -> str:
        return "RESUME" if self.load_state(task_id) else "PAUSE"
