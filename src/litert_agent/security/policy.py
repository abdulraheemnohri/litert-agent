"""Security policy configuration and check logic."""

from pathlib import Path

from litert_agent.security.command_guard import CommandGuard
from litert_agent.security.path_guard import PathGuard
from litert_agent.security.permissions import PermissionLevel


class SecurityPolicy:
    def __init__(self, safe_mode: bool = False, workspace_root: str | Path | None = None):
        self.safe_mode = safe_mode
        self.path_guard = PathGuard(workspace_root or Path.cwd())

    def evaluate_tool_call(self, tool_name: str, action: str, args: dict) -> PermissionLevel:
        args = args or {}

        if self.safe_mode:
            if tool_name in ("filesystem", "terminal") and action in ("write", "delete", "execute"):
                return PermissionLevel.BLOCK

        if tool_name == "terminal":
            classification = CommandGuard.classify(str(args.get("command", "")))
            if classification == "BLOCK":
                return PermissionLevel.BLOCK
            if classification == "ASK":
                return PermissionLevel.ASK

        if tool_name == "filesystem":
            path = str(args.get("path", ""))
            write_actions = {"write", "append", "delete", "copy", "move"}
            allowed, _reason = self.path_guard.check(
                path,
                write=action in write_actions,
            )
            if not allowed:
                return PermissionLevel.BLOCK

            if action in write_actions and self.path_guard.is_sensitive(path):
                return PermissionLevel.ASK

        return PermissionLevel.ALLOW
