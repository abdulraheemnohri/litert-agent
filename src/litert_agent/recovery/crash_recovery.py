"""Crash recovery: persist and resume agent state across restarts."""

import json

from litert_agent.memory.sqlite import DatabaseManager


class CrashRecovery:
    """Persists runtime state and resumes after a crash."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def persist_state(self, task_id: str, current_step: str, plan: list[str], iteration: int) -> str:
        state = {
            "task_id": task_id,
            "current_step": current_step,
            "plan": plan,
            "iteration": iteration,
        }
        self.db.execute_write(
            "INSERT INTO checkpoints (id, task_id, description, state_json) VALUES (?, ?, ?, ?)",
            (f"crash-{task_id}", task_id, "crash-recovery-snapshot", json.dumps(state)),
        )
        return f"crash-{task_id}"

    def load_state(self, task_id: str) -> dict | None:
        rows = self.db.execute_read(
            "SELECT state_json FROM checkpoints WHERE id = ?", (f"crash-{task_id}",)
        )
        if not rows:
            return None
        try:
            return json.loads(rows[0][0])
        except Exception:
            return None

    def clear_state(self, task_id: str) -> None:
        self.db.execute_write("DELETE FROM checkpoints WHERE id = ?", (f"crash-{task_id}",))

    def resume_or_pause(self, task_id: str) -> str:
        state = self.load_state(task_id)
        if state is None:
            return "PAUSE"
        return "RESUME"
