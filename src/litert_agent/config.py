"""Configuration settings model."""

from pathlib import Path
from pydantic import BaseModel, Field
from litert_agent.constants import DEFAULT_HOME_DIR, DEFAULT_AUTONOMY_LEVEL, DEFAULT_LITERT_CLI

class AgentConfig(BaseModel):
    name: str = "litert-agent"
    autonomy_level: int = DEFAULT_AUTONOMY_LEVEL
    home_dir: Path = DEFAULT_HOME_DIR
    workspace_dir: Path = Field(default_factory=Path.cwd)
    safe_mode: bool = False
    offline_mode: bool = False

class ModelConfig(BaseModel):
    cli_path: str = DEFAULT_LITERT_CLI
    model_path: str = ""
    timeout_seconds: float = 120.0
    temperature: float = 0.7
    max_tokens: int = 4096

class Config(BaseModel):
    agent: AgentConfig = Field(default_factory=AgentConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
