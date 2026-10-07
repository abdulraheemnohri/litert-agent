"""Executor: validates actions against policy, asks approval, runs tools."""

from litert_agent.security.permissions import PermissionLevel
from litert_agent.security.policy import SecurityPolicy
from litert_agent.tools.base import ToolResult
from litert_agent.tools.registry import ToolRegistry


class Executor:
    """Executes validated, policy-checked and (when required) approved tool actions."""

    def __init__(self, tool_registry: ToolRegistry, policy: SecurityPolicy, approval_manager=None):
        self.tool_registry = tool_registry
        self.policy = policy
        self.approval_manager = approval_manager

    def check_policy(self, tool_name: str, action: str, args: dict) -> PermissionLevel:
        return self.policy.evaluate_tool_call(tool_name, action, args)

    def validate_action(self, tool_name: str, action: str, args: dict) -> bool:
        tool = self.tool_registry.get(tool_name)
        if tool is None:
            return False
        if not args:
            args = {}
        return tool.validate_args(action, args)

    async def _request_approval(self, tool_name: str, action: str, args: dict) -> bool:
        if self.approval_manager is None:
            return False
        return await self.approval_manager.request_approval(
            tool_name, action, args, risk_reason=f"{tool_name}.{action} requires approval",
        )

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

        if permission == PermissionLevel.ASK and self.approval_manager is not None:
            approved = await self._request_approval(tool_name, action, args or {})
            if not approved:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Denied: approval not granted for {tool_name}.{action}",
                )

        return await self.tool_registry.execute_tool(tool_name, action, args or {})
