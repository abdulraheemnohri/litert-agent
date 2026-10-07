"""Self-learning engine: turns verified outcomes into reusable lessons and skill candidates.

Learning changes persistent knowledge and skill metadata, not model weights or security policy.
"""
from dataclasses import dataclass, asdict
import time

@dataclass
class LearningEvent:
    task_id: str
    success: bool
    observation: str
    lesson: str
    skill_hint: str | None = None
    confidence: float = 0.0
    created_at: float = 0.0

class LearningEngine:
    def __init__(self, memory, skills, evolution):
        self.memory, self.skills, self.evolution = memory, skills, evolution

    async def learn_from_outcome(self, task_id: str, success: bool, observation: str, lesson: str = "") -> LearningEvent:
        text = lesson.strip() or observation.strip()
        event = LearningEvent(task_id, success, observation[:4000], text[:4000], None, 0.8 if success else 0.5, time.time())
        if text:
            await self.memory.lessons.add_lesson(f"task:{task_id}", text)
        return event

    async def retrieve_lessons(self, query: str, limit: int = 10) -> list[dict]:
        rows = await self.memory.lessons.get_lessons(query)
        return rows[-limit:]

    def propose_skill(self, name: str, description: str, tools: list[str], reason: str):
        skill = {"name": name, "description": description, "tools": tools, "source": "self-learning", "version": "0.1.0"}
        ok, msg = self.skills.validator.validate(skill)
        if not ok:
            raise ValueError(msg)
        return self.evolution.propose("skill", reason, [f"register skill {name}"])

    def should_promote(self, successes: int, attempts: int, min_attempts: int = 3) -> bool:
        return attempts >= min_attempts and successes / max(1, attempts) >= 0.75
