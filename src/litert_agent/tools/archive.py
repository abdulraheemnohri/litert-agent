"""Process and Archive tools."""

import zipfile
from pathlib import Path

from litert_agent.tools.base import BaseTool, ToolResult


class ProcessTool(BaseTool):
    name = "process"
    description = "Process manager stub"

    async def execute(self, action: str = "list", **kwargs) -> ToolResult:
        return ToolResult(success=True, output="Running processes enumerated.")

class ArchiveTool(BaseTool):
    name = "archive"
    description = "Zip/Unzip files"

    async def execute(self, action: str, archive_path: str, source_path: str = "", **kwargs) -> ToolResult:
        try:
            if action == "zip":
                with zipfile.ZipFile(archive_path, 'w') as zipf:
                    zipf.write(source_path, arcname=Path(source_path).name)
                return ToolResult(success=True, output=f"Created archive {archive_path}")
            elif action == "unzip":
                with zipfile.ZipFile(archive_path, 'r') as zipf:
                    zipf.extractall(source_path or ".")
                return ToolResult(success=True, output=f"Extracted archive {archive_path}")
            return ToolResult(success=False, output="", error=f"Unknown archive action: {action}")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
