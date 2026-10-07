"""Executor: validates actions against policy and runs tools."""

from litert_agent.tools.base import ToolResult
from litert_agent.tools.registry import ToolRegistry
from litert_agent.security.policy import SecurityPolicy
from litert_agent.security.permissions import PermissionLevel


class Executor:
    """Executes validated, policy-checked tool actions."""

    def __init__(self, tool_registry: ToolRegistry, policy: SecurityPolicy):
        self.tool_registry = tool_registry
        self.policy = policy

    def check_policy(self, tool_name: str, action: str, args: dict) -> PermissionLevel:
        return self.policy.evaluate_tool_call(tool_name, action, args)

    def validate_action(self, tool_name: str, action: str, args: dict) -> bool:
        tool = self.tool_registry.get(tool_name)
        if tool is None:
            return False
        if not args:
            args = {}
        return tool.validate_args(action, args)

    async def execute_action(self, tool_name: str, action: str, args: dict) -> ToolResult:
        if not self.validate_action(tool_name, action, args or {}):
            return ToolResult(
                success=False,
                output="",
                error=f"Invalid action '{action}' for tool '{tool_name}'",
            )

        permission = self.check_policy(tool_name, action, args or {})
        if permission == PermissionLevel.BLOCK:
            return ToolResult(
                success=False,
                output="",
                error=f"Blocked by security policy: {tool_name}.{action}",
            )

        return await self.tool_registry.execute_tool(tool_name, action, args or {})
