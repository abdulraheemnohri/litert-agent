"""Scheduler tool interface."""

from litert_agent.tools.base import BaseTool, ToolResult

class SchedulerTool(BaseTool):
    name = "scheduler"
    description = "Job scheduler tool interface"

    async def execute(self, action: str, job_name: str = "", cron: str = "", **kwargs) -> ToolResult:
        return ToolResult(success=True, output=f"Scheduled job {job_name} with action {action}")
