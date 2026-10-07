"""Tests for the bounded self-management subsystem."""

from litert_agent.config import Config
from litert_agent.self.evolution import EvolutionManager
from litert_agent.self.manager import SelfManager


def test_self_manager_identity_is_litert_only(tmp_path):
    cfg = Config()
    cfg.agent.home_dir = tmp_path / "home"
    cfg.agent.workspace_dir = tmp_path
    manager = SelfManager(cfg)
    identity = manager.identity()
    assert identity["provider"] == "litert-cli"
    assert "LiteRT-LM" in identity["mission"]


def test_self_manager_diagnostics_is_bounded(tmp_path):
    cfg = Config()
    cfg.agent.home_dir = tmp_path / "home"
    cfg.agent.workspace_dir = tmp_path
    cfg.agent.home_dir.mkdir()
    report = SelfManager(cfg).diagnose()
    assert isinstance(report["checks"], dict)
    assert isinstance(report["warnings"], list)


def test_evolution_blocks_forbidden_areas():
    manager = EvolutionManager()
    try:
        manager.propose("model_weights", "test", ["change"])
    except ValueError:
        return
    raise AssertionError("forbidden evolution must be rejected")


def test_self_skill_lifecycle():
    from litert_agent.self.skills import SelfSkillManager
    from litert_agent.skills.validator import SkillValidator
    from litert_agent.self.evolution import EvolutionManager
    class R:
        def __init__(self): self.items = []
        def recommend(self, task): return []
        def register(self, skill): self.items.append(skill)
    r = R()
    m = SelfSkillManager(r, SkillValidator, EvolutionManager())
    m.propose("test-skill", "safe test skill", ["python"], "repeated testing workflow")
    assert m.validate("test-skill")[0]
    m.approve("test-skill")
    m.register("test-skill")
    assert r.items[0]["name"] == "test-skill"


def test_web_learning_url_validation():
    from litert_agent.self.web_learning import WebLearningEngine
    class H: pass
    class M: pass
    e = WebLearningEngine(H(), M())
    assert e.validate_url("https://example.com")
    assert not e.validate_url("file:///tmp/x")
