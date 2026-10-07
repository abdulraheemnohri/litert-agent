"""Git tool."""

import asyncio
from litert_agent.tools.base import BaseTool, ToolResult

class GitTool(BaseTool):
    name = "git"
    description = "Git operations: status, diff, log, commit, add, etc."

    async def execute(self, action: str, **kwargs) -> ToolResult:
        cmd_map = {
            "status": "git status",
            "diff": "git diff",
            "log": "git log -n 5 --oneline",
            "add": f"git add {kwargs.get('path', '.')}",
            "commit": f"git commit -m \"{kwargs.get('message', 'Update')}\"",
        }
        cmd = cmd_map.get(action)
        if not cmd:
            return ToolResult(success=False, output="", error=f"Unsupported git action: {action}")

        try:
            proc = await asyncio.create_subprocess_shell(
                cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            out = stdout.decode("utf-8") + stderr.decode("utf-8")
            return ToolResult(success=proc.returncode == 0, output=out)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
