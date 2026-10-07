"""Skill validation before registration or execution."""


class SkillValidator:
    """Validates skill definitions."""

    REQUIRED_FIELDS = ("name", "description", "tools")
    VALID_TOOLS = {
        "terminal", "filesystem", "git", "python", "browser", "http",
        "search", "archive", "scheduler",
    }

    @classmethod
    def validate(cls, skill: dict) -> tuple[bool, str]:
        for field in cls.REQUIRED_FIELDS:
            if not skill.get(field):
                return False, f"Missing required field: {field}"
        name = skill["name"]
        if not isinstance(name, str) or not name.replace("-", "").replace("_", "").isalnum():
            return False, f"Invalid skill name: {name}"
        tools = skill.get("tools", [])
        if not isinstance(tools, list):
            return False, "tools must be a list"
        for tool in tools:
            if tool not in cls.VALID_TOOLS:
                return False, f"Unknown tool in skill '{name}': {tool}"
        return True, "ok"
