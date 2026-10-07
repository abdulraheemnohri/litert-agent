"""Task store."""

import uuid
from litert_agent.memory.sqlite import DatabaseManager

class TaskMemory:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def create_task(self, title: str, description: str) -> str:
        t_id = str(uuid.uuid4())
        self.db_manager.execute_write(
            "INSERT INTO tasks (id, title, description, status) VALUES (?, ?, ?, ?)",
            (t_id, title, description, "PENDING")
        )
        return t_id

    async def update_task_status(self, task_id: str, status: str, result: str = ""):
        self.db_manager.execute_write(
            "UPDATE tasks SET status = ?, result = ? WHERE id = ?",
            (status, result, task_id)
        )

    async def get_task(self, task_id: str) -> dict | None:
        rows = self.db_manager.execute_read(
            "SELECT id, title, description, status, result FROM tasks WHERE id = ?",
            (task_id,)
        )
        if rows:
            r = rows[0]
            return {"id": r[0], "title": r[1], "description": r[2], "status": r[3], "result": r[4]}
        return None
