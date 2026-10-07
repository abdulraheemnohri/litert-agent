"""Unit tests for the skills subsystem."""

from litert_agent.skills.loader import SkillLoader
from litert_agent.skills.registry import SkillRegistry
from litert_agent.skills.validator import SkillValidator


def test_loader_builtin():
    skills = SkillLoader().load_builtin()
    assert len(skills) == 10
    assert any(s["name"] == "coding" for s in skills)


def test_registry():
    registry = SkillRegistry()
    assert registry.find("coding") is not None
    registry.disable("coding")
    assert registry.find("coding")["name"] == "coding"
    assert not [s for s in registry.list_skills() if s["name"] == "coding" and s["enabled"]]
    registry.enable("coding")
    recs = registry.recommend("please debug and fix the failing code")
    assert any(s["name"] == "debugging" for s in recs)


def test_validator():
    ok, msg = SkillValidator.validate({"name": "my-skill", "description": "d", "tools": ["terminal"]})
    assert ok is True
    bad, _ = SkillValidator.validate({"name": "x", "tools": ["terminal"]})
    assert bad is False
    unknown, _ = SkillValidator.validate({"name": "x", "description": "d", "tools": ["magic"]})
    assert unknown is False
