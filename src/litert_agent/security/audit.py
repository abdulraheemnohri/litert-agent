"""Audit logger for security events."""

import json
from datetime import datetime
from pathlib import Path

from litert_agent.constants import DEFAULT_LOG_DIR
from litert_agent.security.secrets import SecretSanitizer


class AuditLogger:
    def __init__(self, log_dir: Path = DEFAULT_LOG_DIR):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "audit.log"

    def log(self, event_type: str, tool_name: str, args: dict, result: str, permission: str):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "tool": tool_name,
            "args": SecretSanitizer.sanitize(str(args)),
            "result": SecretSanitizer.sanitize(str(result)[:500]),
            "permission": permission,
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
