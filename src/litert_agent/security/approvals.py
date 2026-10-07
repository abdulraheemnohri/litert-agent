"""Approval manager for tool calls requiring confirmation."""

import asyncio
from litert_agent.security.permissions import PermissionLevel

class ApprovalManager:
    def __init__(self, auto_approve: bool = False):
        self.auto_approve = auto_approve
        self.session_approvals: set[str] = set()

    async def request_approval(self, tool_name: str, action: str, args: dict, risk_reason: str) -> bool:
        if self.auto_approve:
            return True
        key = f"{tool_name}:{action}"
        if key in self.session_approvals:
            return True

        print(f"\n[APPROVAL REQUIRED] Tool: {tool_name} Action: {action} Reason: {risk_reason}")
        return False
