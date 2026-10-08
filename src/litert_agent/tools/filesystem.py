"""Filesystem tool with defense-in-depth workspace boundaries."""

import shutil
from pathlib import Path

from litert_agent.security.path_guard import PathGuard
from litert_agent.security.permissions import PermissionLevel
from litert_agent.tools.base import BaseTool, ToolResult


class FilesystemTool(BaseTool):
    name = "filesystem"
    description = "Read, write, list, search, copy, move, and delete files"
    permission_level = PermissionLevel.ALLOW

    def __init__(self, workspace_root: str | Path | None = None, max_file_size: int = 10 * 1024 * 1024):
        self.path_guard = PathGuard(workspace_root or Path.cwd(), max_file_size=max_file_size)

    def _check(self, path: str, *, write: bool = False) -> tuple[bool, str]:
        return self.path_guard.check(path, write=write)

    async def execute(
        self,
        action: str,
        path: str,
        content: str = "",
        destination: str = "",
        **kwargs,
    ) -> ToolResult:
        try:
            write_action = action in {"write", "append", "delete", "copy", "move"}
            allowed, reason = self._check(path, write=write_action)
            if not allowed:
                return ToolResult(success=False, output="", error=f"Path blocked: {reason}")

            p = self.path_guard.resolve(path)

            if action == "read":
                if not p.exists():
                    return ToolResult(success=False, output="", error="File does not exist")
                if p.is_file() and p.stat().st_size > self.path_guard.max_file_size:
                    return ToolResult(success=False, output="", error="File exceeds configured size limit")
                return ToolResult(success=True, output=p.read_text(encoding="utf-8"))

            if action == "write":
                if len(content.encode("utf-8")) > self.path_guard.max_file_size:
                    return ToolResult(success=False, output="", error="Content exceeds configured size limit")
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
                return ToolResult(success=True, output=f"Successfully wrote to {path}")

            if action == "append":
                if len(content.encode("utf-8")) > self.path_guard.max_file_size:
                    return ToolResult(success=False, output="", error="Content exceeds configured size limit")
                p.parent.mkdir(parents=True, exist_ok=True)
                p.open("a", encoding="utf-8").write(content)
                return ToolResult(success=True, output=f"Successfully appended to {path}")

            if action == "list":
                if not p.exists():
                    return ToolResult(success=False, output="", error="Directory does not exist")
                items = [f.name + ("/" if f.is_dir() else "") for f in p.iterdir()]
                return ToolResult(success=True, output="\n".join(items))

            if action == "delete":
                if not p.exists():
                    return ToolResult(success=False, output="", error="Path does not exist")
                if p.is_dir():
                    shutil.rmtree(p)
                else:
                    p.unlink()
                return ToolResult(success=True, output=f"Successfully deleted {path}")

            if action == "copy":
                if not destination:
                    return ToolResult(success=False, output="", error="Destination is required")
                dest_allowed, dest_reason = self._check(destination, write=True)
                if not dest_allowed:
                    return ToolResult(success=False, output="", error=f"Destination blocked: {dest_reason}")
                dest = self.path_guard.resolve(destination)
                dest.parent.mkdir(parents=True, exist_ok=True)
                if p.is_dir():
                    shutil.copytree(p, dest)
                else:
                    shutil.copy2(p, dest)
                return ToolResult(success=True, output=f"Copied {path} to {destination}")

            return ToolResult(success=False, output="", error=f"Unknown action: {action}")
        except Exception as exc:
            return ToolResult(success=False, output="", error=str(exc))
