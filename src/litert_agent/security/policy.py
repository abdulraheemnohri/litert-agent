"""Security policy configuration and check logic."""

import re
from litert_agent.security.permissions import PermissionLevel

class SecurityPolicy:
    def __init__(self, safe_mode: bool = False):
        self.safe_mode = safe_mode

    def evaluate_tool_call(self, tool_name: str, action: str, args: dict) -> PermissionLevel:
        if self.safe_mode:
            if tool_name in ("filesystem", "terminal") and action in ("write", "delete", "execute"):
                return PermissionLevel.BLOCK

        if tool_name == "terminal":
            cmd = args.get("command", "")
            if re.search(r"\bsudo\b", cmd) or re.search(r"\brm\s+-rf\s+/", cmd):
                return PermissionLevel.BLOCK
            if re.search(r"\b(pip|apt|yum|pacman|brew)\s+install\b", cmd):
                return PermissionLevel.ASK

        if tool_name == "filesystem":
            path = str(args.get("path", ""))
            if any(p in path for p in [".git", ".env", "id_rsa", "shadow", "passwd"]):
                return PermissionLevel.ASK

        return PermissionLevel.ALLOW
