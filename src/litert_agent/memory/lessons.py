"""Lessons learned memory store."""

import uuid
from litert_agent.memory.sqlite import DatabaseManager

class LessonsMemory:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def add_lesson(self, context: str, lesson: str):
        l_id = str(uuid.uuid4())
        self.db_manager.execute_write(
            "INSERT INTO lessons (id, context, lesson) VALUES (?, ?, ?)",
            (l_id, context, lesson)
        )

    async def get_lessons(self, context: str = "") -> list[dict]:
        query = "SELECT context, lesson FROM lessons WHERE context LIKE ?" if context else "SELECT context, lesson FROM lessons"
        params = (f"%{context}%",) if context else ()
        rows = self.db_manager.execute_read(query, params)
        return [{"context": r[0], "lesson": r[1]} for r in rows]
