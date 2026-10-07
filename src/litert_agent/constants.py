"""Constants and defaults for litert-agent."""

from pathlib import Path

DEFAULT_HOME_DIR = Path.home() / ".litert-agent"
DEFAULT_DB_PATH = DEFAULT_HOME_DIR / "agent.db"
DEFAULT_LOG_DIR = DEFAULT_HOME_DIR / "logs"
DEFAULT_CHECKPOINT_DIR = DEFAULT_HOME_DIR / "checkpoints"

DEFAULT_AUTONOMY_LEVEL = 3
DEFAULT_LITERT_CLI = "litert-lm"
