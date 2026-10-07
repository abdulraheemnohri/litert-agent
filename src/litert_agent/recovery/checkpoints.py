"""Checkpoint manager backed by the SQLite 'checkpoints' table."""

import json
import uuid
from datetime import datetime

from litert_agent.memory.sqlite import DatabaseManager


class CheckpointManager:
    """Creates, lists, inspects, restores and deletes checkpoints."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_checkpoint(self, task_id: str, description: str, state: dict) -> str:
        checkpoint_id = str(uuid.uuid4())
        self.db.execute_write(
            "INSERT INTO checkpoints (id, task_id, description, state_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (checkpoint_id, task_id, description, json.dumps(state), datetime.utcnow().isoformat()),
        )
        return checkpoint_id

    def list_checkpoints(self, task_id: str | None = None) -> list[dict]:
        if task_id:
            rows = self.db.execute_read(
                "SELECT id, task_id, description, created_at FROM checkpoints WHERE task_id = ? ORDER BY created_at DESC",
                (task_id,),
            )
        else:
            rows = self.db.execute_read(
                "SELECT id, task_id, description, created_at FROM checkpoints ORDER BY created_at DESC"
            )
        return [
            {"id": r[0], "task_id": r[1], "description": r[2], "created_at": r[3]}
            for r in rows
        ]

    def inspect_checkpoint(self, checkpoint_id: str) -> dict | None:
        rows = self.db.execute_read(
            "SELECT id, task_id, description, state_json, created_at FROM checkpoints WHERE id = ?",
            (checkpoint_id,),
        )
        if not rows:
            return None
        r = rows[0]
        try:
            state = json.loads(r[3])
        except Exception:
            state = {}
        return {"id": r[0], "task_id": r[1], "description": r[2], "state": state, "created_at": r[4]}

    def restore_checkpoint(self, checkpoint_id: str) -> dict | None:
        return self.inspect_checkpoint(checkpoint_id)

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        self.db.execute_write("DELETE FROM checkpoints WHERE id = ?", (checkpoint_id,))
        return True
