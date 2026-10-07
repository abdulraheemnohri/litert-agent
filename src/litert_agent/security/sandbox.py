"""Sandbox isolation validator."""

from pathlib import Path

class SandboxValidator:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root.resolve()

    def is_path_safe(self, path: str | Path) -> bool:
        try:
            resolved = Path(path).resolve()
            return resolved == self.workspace_root or self.workspace_root in resolved.parents
        except Exception:
            return False
