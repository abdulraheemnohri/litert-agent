"""Execution verification contracts for bounded autonomous actions."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from litert_agent.tools.base import ToolResult


@dataclass(frozen=True)
class VerificationContract:
    """A small, deterministic contract derived from model metadata."""

    checks: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_requests(cls, requests: list[str] | None) -> "VerificationContract":
        cleaned = tuple(
            item.strip()[:500]
            for item in (requests or [])
            if isinstance(item, str) and item.strip()
        )
        return cls(cleaned[:16])


class Verifier:
    """Verifies tool results against explicit, bounded expectations."""

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

    def verify_contract(
        self, tool_result: ToolResult, contract: VerificationContract
    ) -> tuple[bool, list[str]]:
        if not tool_result.success:
            return False, [tool_result.error or "tool execution failed"]
        failures: list[str] = []
        output = tool_result.output or ""
        for check in contract.checks:
            # Deterministic checks only; model text never becomes executable code.
            if check.lower().startswith("contains:"):
                expected = check.split(":", 1)[1].strip()
                if expected and expected not in output:
                    failures.append(f"missing expected output: {expected[:200]}")
            elif check.lower().startswith("not_contains:"):
                forbidden = check.split(":", 1)[1].strip()
                if forbidden and forbidden in output:
                    failures.append(f"forbidden output present: {forbidden[:200]}")
            elif check.lower().startswith("regex:"):
                pattern = check.split(":", 1)[1].strip()
                try:
                    if not re.search(pattern, output):
                        failures.append("regex verification failed")
                except re.error:
                    failures.append("invalid regex verification request")
            else:
                # Unknown verification requests are evidence gaps, not commands.
                failures.append(f"unsupported verification check: {check[:200]}")
        return not failures, failures
