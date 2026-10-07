"""Unit tests for configuration loading and profiles."""


from litert_agent.config import Config


def test_defaults():
    cfg = Config()
    assert cfg.agent.profile == "normal"
    assert cfg.model.cli_path == "litert-lm"


def test_overrides():
    cfg = Config().apply_overrides(safe_mode=True, offline_mode=True, profile="low-memory")
    assert cfg.agent.safe_mode is True
    assert cfg.agent.offline_mode is True
    assert cfg.agent.profile == "low-memory"


def test_profiles():
    low = Config().apply_overrides(profile="low-memory").apply_profile()
    perf = Config().apply_overrides(profile="performance").apply_profile()
    assert low.scheduler.workers == 1
    assert low.memory.working_max_items == 20
    assert perf.scheduler.workers == 4
    assert perf.memory.working_max_items == 100


def test_toml_load(tmp_path):
    toml = tmp_path / "config.toml"
    toml.write_text("""
[agent]
name = "my-agent"
autonomy_level = 2
safe_mode = true

[model]
timeout_seconds = 60.0
""", encoding="utf-8")
    cfg = Config.load(toml)
    assert cfg.agent.name == "my-agent"
    assert cfg.agent.safe_mode is True
    assert cfg.model.timeout_seconds == 60.0


def test_corrupt_toml_falls_back(tmp_path):
    toml = tmp_path / "config.toml"
    toml.write_text("not [ valid toml !!", encoding="utf-8")
    cfg = Config.load(toml)
    assert cfg.agent.name == "litert-agent"
