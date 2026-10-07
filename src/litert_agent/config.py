"""Configuration settings model with TOML file loading and runtime profiles."""

import tomllib
from pathlib import Path

from pydantic import BaseModel, Field

from litert_agent.constants import (
    DEFAULT_AUTONOMY_LEVEL,
    DEFAULT_HOME_DIR,
    DEFAULT_LITERT_CLI,
)


class AgentConfig(BaseModel):
    name: str = "litert-agent"
    autonomy_level: int = DEFAULT_AUTONOMY_LEVEL
    home_dir: Path = DEFAULT_HOME_DIR
    workspace_dir: Path = Field(default_factory=Path.cwd)
    safe_mode: bool = False
    offline_mode: bool = False
    profile: str = "normal"  # low-memory | normal | performance


class ModelConfig(BaseModel):
    cli_path: str = DEFAULT_LITERT_CLI
    model_path: str = ""
    timeout_seconds: float = 120.0
    temperature: float = 0.7
    max_tokens: int = 4096


class LoopConfig(BaseModel):
    max_iterations: int = 50
    max_retries: int = 3
    max_tool_calls: int = 100


class MemoryConfig(BaseModel):
    enabled: bool = True
    working_max_items: int = 50


class SchedulerConfig(BaseModel):
    enabled: bool = True
    heartbeat_seconds: float = 30.0
    workers: int = 1


class WebConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8765


class Config(BaseModel):
    agent: AgentConfig = Field(default_factory=AgentConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    loop: LoopConfig = Field(default_factory=LoopConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    web: WebConfig = Field(default_factory=WebConfig)

    @classmethod
    def load(cls, config_path: Path | None = None, overrides: dict | None = None) -> "Config":
        """Load config from TOML file (default ~/.litert-agent/config.toml), then apply overrides."""
        cfg = cls()
        path = config_path or (DEFAULT_HOME_DIR / "config.toml")
        if path.exists():
            try:
                with open(path, "rb") as f:
                    data = tomllib.load(f)
                cfg = cls.model_validate(data)
            except Exception:
                # Corrupt config: fall back to defaults rather than crash startup
                cfg = cls()
        if overrides:
            cfg = cfg.apply_overrides(**overrides)
        return cfg.apply_profile()

    def apply_overrides(self, safe_mode: bool | None = None, offline_mode: bool | None = None,
                        profile: str | None = None, autonomy_level: int | None = None,
                        workspace: str | None = None) -> "Config":
        if safe_mode is not None:
            self.agent.safe_mode = safe_mode
        if offline_mode is not None:
            self.agent.offline_mode = offline_mode
        if profile is not None:
            self.agent.profile = profile
        if autonomy_level is not None:
            self.agent.autonomy_level = autonomy_level
        if workspace is not None:
            self.agent.workspace_dir = Path(workspace)
        return self

    def apply_profile(self) -> "Config":
        p = self.agent.profile
        if p == "low-memory":
            self.scheduler.workers = 1
            self.scheduler.heartbeat_seconds = 60.0
            self.memory.working_max_items = 20
            self.loop.max_iterations = min(self.loop.max_iterations, 25)
        elif p == "performance":
            self.scheduler.workers = 4
            self.scheduler.heartbeat_seconds = 15.0
            self.memory.working_max_items = 100
        # normal: keep defaults
        return self
