"""Replanner: classifies failures and retries with limits."""

from litert_agent.model.protocol import ProtocolMessage


class Replanner:
    """Handles failure classification, retries and escalation."""

    RETRYABLE = {"timeout", "transient", "tool_failure", "network"}

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.retries: dict[str, int] = {}

    def classify_failure(self, error: str) -> str:
        lowered = (error or "").lower()
        if "timeout" in lowered:
            return "timeout"
        if "network" in lowered or "connection" in lowered:
            return "network"
        if "blocked by security policy" in lowered:
            return "policy_denied"
        return "tool_failure"

    def can_retry(self, step: str) -> bool:
        return self.retries.get(step, 0) < self.max_retries

    def record_retry(self, step: str) -> int:
        self.retries[step] = self.retries.get(step, 0) + 1
        return self.retries[step]

    def retry_or_escalate(self, step: str, error: str) -> str:
        failure_class = self.classify_failure(error)
        if failure_class not in self.RETRYABLE:
            return "ESCALATE"
        if self.can_retry(step):
            self.record_retry(step)
            return "RETRY"
        return "ESCALATE"

    def update_plan(self, plan_steps: list[str], failed_step: str) -> list[str]:
        return [s for s in plan_steps if s != failed_step] + [f"Re-attempt: {failed_step}"]

    def escalation_message(self, step: str, error: str) -> ProtocolMessage:
        return ProtocolMessage(
            type="error",
            content=f"Step '{step}' exhausted retries. Last error: {error}",
            reason="max_retries_exceeded",
        )
