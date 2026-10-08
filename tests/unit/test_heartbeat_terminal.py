from litert_agent.environment.terminal import TerminalEnvironment
from litert_agent.scheduler.heartbeat import Heartbeat


def test_terminal_environment_detects_runtime():
    data = TerminalEnvironment.detect()
    assert data["platform"]
    assert data["family"]
    assert "cwd" in data


def test_heartbeat_without_runtime_is_unhealthy():
    report = Heartbeat().check()
    assert report.healthy is False
    assert "runtime" in report.checks
