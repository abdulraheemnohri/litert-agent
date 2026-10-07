"""Verifier: checks tool results against expectations."""

import re

from litert_agent.tools.base import ToolResult


class Verifier:
    """Verifies execution results."""

    def verify_action(self, tool_result: ToolResult) -> bool:
        return bool(tool_result.success)

    def verify_output(self, tool_result: ToolResult, expected: str | None = None) -> bool:
        if not tool_result.success:
            return False
        if expected is None:
            return True
        return bool(re.search(re.escape(expected), tool_result.output))

    def verify_file_content(self, content: str, expected: str) -> bool:
        return expected in content
