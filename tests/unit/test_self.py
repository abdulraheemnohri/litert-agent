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
