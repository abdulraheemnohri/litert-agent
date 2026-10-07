"""Semantic facts store."""

import uuid

from litert_agent.memory.sqlite import DatabaseManager


class SemanticMemory:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def add_fact(self, subject: str, predicate: str, obj: str):
        fact_id = str(uuid.uuid4())
        self.db_manager.execute_write(
            "INSERT INTO facts (id, subject, predicate, object) VALUES (?, ?, ?, ?)",
            (fact_id, subject, predicate, obj)
        )

    async def get_facts(self, subject: str) -> list[dict]:
        rows = self.db_manager.execute_read(
            "SELECT subject, predicate, object FROM facts WHERE subject LIKE ?",
            (f"%{subject}%",)
        )
        return [{"subject": r[0], "predicate": r[1], "object": r[2]} for r in rows]
