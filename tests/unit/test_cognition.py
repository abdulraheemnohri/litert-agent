"""Unit tests for the cognition layer."""

from litert_agent.cognition.decision import DecisionEngine
from litert_agent.cognition.planner import Planner
from litert_agent.cognition.prioritizer import Prioritizer, Priority
from litert_agent.cognition.reflector import Reflector
from litert_agent.cognition.replanner import Replanner
from litert_agent.cognition.verifier import Verifier
from litert_agent.model.protocol import ProtocolMessage
from litert_agent.tools.base import ToolResult


def test_planner_create_plan():
    planner = Planner()
    steps = planner.create_plan("Create a file and run tests")
    assert any("filesystem" in s for s in steps)
    assert any("terminal" in s for s in steps)
    assert steps[-1].startswith("Verify")


def test_decision_engine():
    engine = DecisionEngine()
    assert engine.decide(ProtocolMessage(type="final", content="done")) == "COMPLETE_TASK"
    assert engine.decide(ProtocolMessage(type="tool_call", tool="terminal")) == "EXECUTE_TOOL"
    assert engine.decide(ProtocolMessage(type="error", content="bad")) == "HANDLE_ERROR"


def test_verifier():
    verifier = Verifier()
    assert verifier.verify_action(ToolResult(success=True, output="ok")) is True
    assert verifier.verify_action(ToolResult(success=False, output="", error="x")) is False
    assert verifier.verify_output(ToolResult(success=True, output="hello world"), "world") is True


def test_reflector():
    reflector = Reflector()
    lesson = reflector.reflect("build app", [{"success": True, "tool": "terminal", "output": "ok"}], True)
    assert "succeeded" in lesson


def test_replanner_retry_and_escalate():
    replanner = Replanner(max_retries=1)
    assert replanner.retry_or_escalate("step1", "timeout error") == "RETRY"
    assert replanner.retry_or_escalate("step1", "timeout error") == "ESCALATE"
    assert replanner.retry_or_escalate("step2", "blocked by security policy") == "ESCALATE"


def test_prioritizer():
    prioritizer = Prioritizer()
    assert prioritizer.calculate_priority("urgent security fix") == Priority.CRITICAL
    tasks = [
        {"priority": "LOW", "name": "docs"},
        {"priority": "CRITICAL", "name": "fix"},
    ]
    ordered = prioritizer.sort_tasks(tasks)
    assert ordered[0]["name"] == "fix"
