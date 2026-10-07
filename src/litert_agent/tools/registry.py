"""Tool Registry."""

from litert_agent.tools.base import BaseTool, ToolResult

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[dict[str, str]]:
        return [
            {"name": t.name, "description": t.description, "permission_level": t.permission_level.value}
            for t in self._tools.values()
        ]

    async def execute_tool(self, name: str, action: str, kwargs: dict) -> ToolResult:
        tool = self.get(name)
        if not tool:
            return ToolResult(success=False, output="", error=f"Tool '{name}' not found")
        if not tool.validate_args(action, kwargs):
            return ToolResult(success=False, output="", error=f"Invalid arguments for action '{action}' on tool '{name}'")
        return await tool.execute(action, **kwargs)
