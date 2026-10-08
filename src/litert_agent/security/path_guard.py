"""Workspace path guard used as defense-in-depth for filesystem operations.

The policy layer decides whether an operation is allowed, but filesystem paths
are independently constrained here so a future caller cannot accidentally
bypass workspace boundaries.
"""

from pathlib import Path


class PathGuard:
    def __init__(
        self,
        workspace_root: str | Path,
        blocked_names: tuple[str, ...] = (".env", "id_rsa", "shadow", "passwd"),
        max_file_size: int = 10 * 1024 * 1024,
    ):
        self.workspace_root = Path(workspace_root).expanduser().resolve()
        self.blocked_names = {name.lower() for name in blocked_names}
        self.max_file_size = max_file_size

    def resolve(self, path: str | Path) -> Path:
        return Path(path).expanduser().resolve()

    def is_within_workspace(self, path: str | Path) -> bool:
        try:
            resolved = self.resolve(path)
            return resolved == self.workspace_root or self.workspace_root in resolved.parents
        except (OSError, RuntimeError, ValueError):
            return False

    def is_sensitive(self, path: str | Path) -> bool:
        try:
            resolved = self.resolve(path)
            parts = {part.lower() for part in resolved.parts}
            return bool(parts & self.blocked_names)
        except (OSError, RuntimeError, ValueError):
            return True

    def check(self, path: str | Path, *, write: bool = False) -> tuple[bool, str]:
        if not self.is_within_workspace(path):
            return False, "Path is outside the configured workspace"
        if self.is_sensitive(path):
            return False, "Path targets a protected/sensitive resource"
        if write:
            try:
                target = self.resolve(path)
                if target.exists() and target.is_file() and target.stat().st_size > self.max_file_size:
                    return False, f"File exceeds maximum configured size of {self.max_file_size} bytes"
            except (OSError, RuntimeError, ValueError) as exc:
                return False, f"Unable to inspect path: {exc}"
        return True, ""
