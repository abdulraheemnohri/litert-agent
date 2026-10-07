"""Central Memory Manager."""

from pathlib import Path
from litert_agent.memory.sqlite import DatabaseManager
from litert_agent.memory.working import WorkingMemory
from litert_agent.memory.episodic import EpisodicMemory
from litert_agent.memory.semantic import SemanticMemory
from litert_agent.memory.lessons import LessonsMemory
from litert_agent.memory.tasks import TaskMemory

class MemoryManager:
    def __init__(self, db_path: Path):
        self.db_manager = DatabaseManager(db_path)
        self.working = WorkingMemory()
        self.episodic = EpisodicMemory(self.db_manager)
        self.semantic = SemanticMemory(self.db_manager)
        self.lessons = LessonsMemory(self.db_manager)
        self.tasks = TaskMemory(self.db_manager)

    async def initialize(self):
        await self.db_manager.init_db()
