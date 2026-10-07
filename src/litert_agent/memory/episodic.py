"""Episodic memory store."""

import uuid
from litert_agent.memory.sqlite import DatabaseManager

class EpisodicMemory:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def record_episode(self, category: str, content: str, importance: float = 1.0):
        m_id = str(uuid.uuid4())
        self.db_manager.execute_write(
            "INSERT INTO memories (id, category, content, importance) VALUES (?, ?, ?, ?)",
            (m_id, category, content, importance)
        )

    async def search_episodes(self, query: str, limit: int = 5) -> list[dict]:
        rows = self.db_manager.execute_read(
            "SELECT id, category, content, importance FROM memories WHERE content LIKE ? ORDER BY created_at DESC LIMIT ?",
            (f"%{query}%", limit)
        )
        return [{"id": r[0], "category": r[1], "content": r[2], "importance": r[3]} for r in rows]
