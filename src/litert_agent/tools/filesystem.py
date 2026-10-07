"""Filesystem tool."""

import shutil
from pathlib import Path
from litert_agent.tools.base import BaseTool, ToolResult
from litert_agent.security.permissions import PermissionLevel

class FilesystemTool(BaseTool):
    name = "filesystem"
    description = "Read, write, list, search, copy, move, and delete files"
    permission_level = PermissionLevel.ALLOW

    async def execute(self, action: str, path: str, content: str = "", destination: str = "", **kwargs) -> ToolResult:
        p = Path(path)
        try:
            if action == "read":
                if not p.exists():
                    return ToolResult(success=False, output="", error="File does not exist")
                text = p.read_text(encoding="utf-8")
                return ToolResult(success=True, output=text)

            elif action == "write":
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
                return ToolResult(success=True, output=f"Successfully wrote to {path}")

            elif action == "list":
                if not p.exists():
                    return ToolResult(success=False, output="", error="Directory does not exist")
                items = [f.name + ("/" if f.is_dir() else "") for f in p.iterdir()]
                return ToolResult(success=True, output="\n".join(items))

            elif action == "delete":
                if not p.exists():
                    return ToolResult(success=False, output="", error="Path does not exist")
                if p.is_dir():
                    shutil.rmtree(p)
                else:
                    p.unlink()
                return ToolResult(success=True, output=f"Successfully deleted {path}")

            elif action == "copy":
                dest = Path(destination)
                dest.parent.mkdir(parents=True, exist_ok=True)
                if p.is_dir():
                    shutil.copytree(p, dest)
                else:
                    shutil.copy2(p, dest)
                return ToolResult(success=True, output=f"Copied {path} to {destination}")

            return ToolResult(success=False, output="", error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
