"""Python tool."""

import sys
import asyncio
import tempfile
from pathlib import Path
from litert_agent.tools.base import BaseTool, ToolResult

class PythonTool(BaseTool):
    name = "python"
    description = "Execute Python scripts or snippet"

    async def execute(self, action: str = "run", code: str = "", script_path: str = "", **kwargs) -> ToolResult:
        if action == "run" and code:
            with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
                tf.write(code)
                tf_path = tf.name

            try:
                proc = await asyncio.create_subprocess_exec(
                    sys.executable, tf_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
                out = stdout.decode("utf-8")
                err = stderr.decode("utf-8")
                Path(tf_path).unlink(missing_ok=True)
                return ToolResult(success=proc.returncode == 0, output=out if proc.returncode == 0 else out + "\n" + err)
            except Exception as e:
                Path(tf_path).unlink(missing_ok=True)
                return ToolResult(success=False, output="", error=str(e))

        return ToolResult(success=False, output="", error="No python code or valid action provided")
