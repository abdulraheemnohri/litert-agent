"""Search tool stub/local search."""

from litert_agent.tools.base import BaseTool, ToolResult

class SearchTool(BaseTool):
    name = "search"
    description = "Local/web search"

    async def execute(self, action: str = "search", query: str = "", **kwargs) -> ToolResult:
        return ToolResult(
            success=True,
            output=f"Search results for '{query}':\n1. Example documentation\n2. Local codebase reference"
        )
