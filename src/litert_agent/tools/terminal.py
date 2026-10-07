"""Terminal tool for command execution."""

import asyncio
from litert_agent.tools.base import BaseTool, ToolResult
from litert_agent.security.permissions import PermissionLevel
from litert_agent.environment.platform import PlatformInfo

class TerminalTool(BaseTool):
    name = "terminal"
    description = "Execute shell commands safely with timeouts and CWD options"
    permission_level = PermissionLevel.ASK

    async def execute(self, action: str = "execute", command: str = "", cwd: str | None = None, timeout: float = 60.0) -> ToolResult:
        if not command:
            return ToolResult(success=False, output="", error="No command provided")

        shell = PlatformInfo.default_shell()
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                executable=shell if not PlatformInfo.is_windows() else None
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            out_str = stdout.decode("utf-8", errors="replace")
            err_str = stderr.decode("utf-8", errors="replace")

            success = (proc.returncode == 0)
            return ToolResult(
                success=success,
                output=out_str if success else out_str + "\n" + err_str,
                error=None if success else f"Exit code: {proc.returncode}"
            )
        except asyncio.TimeoutError:
            return ToolResult(success=False, output="", error=f"Command timed out after {timeout} seconds")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
