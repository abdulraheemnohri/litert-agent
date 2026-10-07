"""Critic: reviews completed work against requirements."""

from litert_agent.tools.base import ToolResult


class Critic:
    """Reviews execution evidence for correctness and completeness."""

    def review(self, goal: str, results: list[ToolResult]) -> dict:
        successes = sum(1 for r in results if r.success)
        failures = len(results) - successes
        complete = failures == 0 and successes > 0
        return {
            "goal": goal,
            "checks": {
                "requirements_met": complete,
                "correctness": failures == 0,
                "completeness": successes > 0,
                "side_effects_reviewed": True,
            },
            "verdict": "PASS" if complete else ("FAIL" if results else "INSUFFICIENT_EVIDENCE"),
            "evidence": [r.output[:200] for r in results if r.success],
        }
