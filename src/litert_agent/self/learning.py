"""Bounded experience-based learning for LiteRT Agent.

Learning changes retrievable knowledge and validated skill metadata, never model
weights or security policy. Every learned item has evidence, confidence and
validation state so the agent cannot silently turn guesses into permanent rules.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from time import time
from typing import Any

@dataclass
class Experience:
    task_id: str
    goal: str
    outcome: str
    success: bool
    evidence: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time)

@dataclass
class Lesson:
    key: str
    lesson: str
    evidence: list[str]
    confidence: float = 0.5
    uses: int = 0
    validated: bool = False
    created_at: float = field(default_factory=time)
    updated_at: float = field(default_factory=time)

class LearningEngine:
    """Turns verified task experience into bounded, auditable lessons."""
    def __init__(self, memory=None):
        self.memory = memory
        self.experiences: list[Experience] = []
        self.lessons: dict[str, Lesson] = {}

    def record(self, experience: Experience) -> Experience:
        self.experiences.append(experience)
        return experience

    def extract_lesson(self, experience: Experience, lesson: str, key: str, evidence: list[str] | None = None) -> Lesson:
        if not lesson.strip() or not key.strip():
            raise ValueError("lesson and key are required")
        item = self.lessons.get(key)
        ev = evidence or experience.evidence
        if item:
            item.uses += 1
            item.evidence = list(dict.fromkeys(item.evidence + ev))[-20:]
            item.confidence = min(0.99, item.confidence + (0.08 if experience.success else -0.05))
            item.updated_at = time()
        else:
            item = Lesson(key=key, lesson=lesson[:2000], evidence=ev[-20:], confidence=0.65 if experience.success else 0.35)
            self.lessons[key] = item
        return item

    def validate(self, key: str, success: bool, evidence: str = "") -> Lesson:
        item = self.lessons[key]
        item.uses += 1
        item.confidence = max(0.0, min(0.99, item.confidence + (0.1 if success else -0.1)))
        if evidence:
            item.evidence = list(dict.fromkeys(item.evidence + [evidence]))[-20:]
        item.validated = success and item.confidence >= 0.75
        item.updated_at = time()
        return item

    def recall(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
        q = query.lower()
        scored=[]
        for item in self.lessons.values():
            score=(2 if item.validated else 0)+(item.confidence*2)+(1 if any(w in item.lesson.lower() for w in q.split() if len(w)>2) else 0)
            scored.append((score,item))
        return [asdict(x[1]) for x in sorted(scored,key=lambda x:x[0],reverse=True)[:limit]]

    def forget(self, key: str) -> bool:
        return self.lessons.pop(key, None) is not None

    def export(self) -> dict[str, Any]:
        return {"experiences":[asdict(x) for x in self.experiences[-1000:]],"lessons":[asdict(x) for x in self.lessons.values()]}
