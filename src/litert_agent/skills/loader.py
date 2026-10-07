"""Skill loading from built-in definitions and the skills table."""

from litert_agent.skills.builtin.builtin_skills import BUILTIN_SKILLS


class SkillLoader:
    """Loads skill definitions from built-ins and the database."""

    def __init__(self, db=None):
        self.db = db

    def load_builtin(self) -> list[dict]:
        return list(BUILTIN_SKILLS)

    def load_from_db(self) -> list[dict]:
        if self.db is None:
            return []
        rows = self.db.execute_read("SELECT id, name, description, code FROM skills")
        return [{"id": r[0], "name": r[1], "description": r[2], "code": r[3]} for r in rows]

    def load_all(self) -> list[dict]:
        return self.load_builtin() + self.load_from_db()
