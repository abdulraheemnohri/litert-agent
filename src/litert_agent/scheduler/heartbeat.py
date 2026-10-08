"""Runtime heartbeat and health-gate helpers.

The heartbeat is observational by default. It never changes policy, model
provider, credentials, or system configuration.
"""
from dataclasses import dataclass, field
import time


@dataclass
class HeartbeatReport:
    timestamp: float
    healthy: bool
    checks: dict[str, bool] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


class Heartbeat:
    def __init__(self, runtime=None):
        self.runtime = runtime
        self.last_report: HeartbeatReport | None = None

    def check(self) -> HeartbeatReport:
        checks = {}
        warnings = []
        if self.runtime is None:
            checks["runtime"] = False
            warnings.append("runtime_unavailable")
        else:
            checks["runtime"] = True
            try:
                health = self.runtime.health()
                checks["model"] = bool(health)
                if health.get("status") == "DEGRADED":
                    warnings.append("runtime_degraded")
            except Exception as exc:
                checks["model"] = False
                warnings.append(f"health_error:{type(exc).__name__}")
        report = HeartbeatReport(time.time(), all(checks.values()) if checks else False, checks, warnings)
        self.last_report = report
        return report

    def is_healthy(self) -> bool:
        return self.check().healthy
