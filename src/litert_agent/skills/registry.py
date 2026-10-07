"""Skill registry with enable/disable and usage tracking."""

from litert_agent.skills.loader import SkillLoader


class SkillRegistry:
    """Registers, finds and tracks skills."""

    def __init__(self, db=None):
        self.loader = SkillLoader(db)
        self.skills: dict[str, dict] = {}
        self.disabled: set[str] = set()
        self.usage: dict[str, int] = {}
        self.success: dict[str, int] = {}
        for skill in self.loader.load_all():
            self.register(skill)

    def register(self, skill: dict):
        self.skills[skill["name"]] = skill

    def unregister(self, name: str) -> bool:
        return self.skills.pop(name, None) is not None

    def find(self, name: str) -> dict | None:
        return self.skills.get(name)

    def list_skills(self) -> list[dict]:
        out = []
        for name, skill in self.skills.items():
            uses = self.usage.get(name, 0)
            wins = self.success.get(name, 0)
            out.append({
                **skill,
                "enabled": name not in self.disabled,
                "usage_count": uses,
                "success_rate": (wins / uses) if uses else 1.0,
            })
        return out

    def enable(self, name: str):
        self.disabled.discard(name)

    def disable(self, name: str):
        self.disabled.add(name)

    def record_use(self, name: str, success: bool):
        self.usage[name] = self.usage.get(name, 0) + 1
        if success:
            self.success[name] = self.success.get(name, 0) + 1

    def recommend(self, task_description: str) -> list[dict]:
        lowered = task_description.lower()
        scored = []
        for name, skill in self.skills.items():
            if name in self.disabled:
                continue
            keywords = name.replace("-", " ").split()
            score = sum(1 for k in keywords if k in lowered)
            if score:
                scored.append((score, skill))
        scored.sort(key=lambda x: -x[0])
        return [s for _, s in scored[:3]]
