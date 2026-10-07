"""Self-healing: diagnose errors and choose a recovery strategy."""

from litert_agent.recovery.replanner_compat import classify_error  # noqa: F401 (re-export convenience)


class ErrorCategory:
    TRANSIENT = "transient"
    TOOL = "tool"
    MODEL = "model"
    POLICY = "policy"
    FATAL = "fatal"


class Healer:
    """Diagnoses errors and applies bounded recovery actions."""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.attempts: dict[str, int] = {}

    def diagnose(self, error: str) -> str:
        lowered = (error or "").lower()
        if "timeout" in lowered or "temporarily" in lowered:
            return ErrorCategory.TRANSIENT
        if "policy" in lowered or "permission" in lowered:
            return ErrorCategory.POLICY
        if "litert" in lowered or "model" in lowered:
            return ErrorCategory.MODEL
        if "crash" in lowered or "corrupt" in lowered:
            return ErrorCategory.FATAL
        return ErrorCategory.TOOL

    def heal(self, component: str, error: str) -> str:
        category = self.diagnose(error)
        if category == ErrorCategory.FATAL:
            return "ESCALATE"
        if self.attempts.get(component, 0) >= self.max_retries:
            return "ESCALATE"
        self.attempts[component] = self.attempts.get(component, 0) + 1
        if category == ErrorCategory.TRANSIENT:
            return "RETRY"
        if category == ErrorCategory.MODEL:
            return "RESTART_COMPONENT"
        return "RETRY"
