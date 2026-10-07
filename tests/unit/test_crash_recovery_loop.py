"""Tests for crash-recovery integration in the autonomous loop."""

import pytest

from litert_agent.memory.manager import MemoryManager
from litert_agent.memory.sqlite import DatabaseManager, SCHEMA
from litert_agent.model.protocol import ProtocolMessage
from litert_agent.model.provider import ModelProvider
from litert_agent.cognition.executor import Executor
from litert_agent.tools.registry import ToolRegistry
from litert_agent.tools.filesystem import FilesystemTool
from litert_agent.security.policy import SecurityPolicy
from litert_agent.security.approvals import ApprovalManager
from litert_agent.runtime.loop import AutonomousLoop
from litert_agent.recovery.crash_recovery import CrashRecovery
from litert_agent.runtime.events import EventBus


class FinalProvider(ModelProvider):
    """Immediately reports completion."""

    async def generate(self, prompt: str, system_prompt: str | None = None) -> ProtocolMessage:
        return ProtocolMessage(type="final", content="done")


@pytest.fixture
def memory(tmp_path):
    db = DatabaseManager(tmp_path / "agent.db")
    with __import__("sqlite3").connect(db.db_path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()
    mm = MemoryManager(tmp_path / "agent.db")
    mm.working.clear()
    return mm


def _loop_with_recovery(memory, bus):
    registry = ToolRegistry()
    registry.register(FilesystemTool())
    executor = Executor(registry, SecurityPolicy(), ApprovalManager(auto_approve=True))
    recovery = CrashRecovery(memory.db_manager)
    return AutonomousLoop(FinalProvider(), executor, memory, bus, crash_recovery=recovery), recovery


@pytest.mark.asyncio
async def test_goal_key_is_stable(memory):
    loop, _ = _loop_with_recovery(memory, EventBus())
    assert AutonomousLoop.goal_key("same goal") == AutonomousLoop.goal_key("same goal")
    assert AutonomousLoop.goal_key("goal a") != AutonomousLoop.goal_key("goal b")


@pytest.mark.asyncio
async def test_completion_clears_snapshot(memory):
    bus = EventBus()
    events = []
    bus.subscribe("task_completed", lambda e: events.append(e.event_type))
    loop, recovery = _loop_with_recovery(memory, bus)

    result = await loop.run_task("finish quickly")
    assert "task_completed" in events
    assert recovery.load_state(AutonomousLoop.goal_key("finish quickly")) is None
    assert "done" in result


@pytest.mark.asyncio
async def test_resume_from_snapshot_publishes_event(memory):
    bus = EventBus()
    events = []
    bus.subscribe("task_resumed", lambda e: events.append(e.event_type))
    loop, recovery = _loop_with_recovery(memory, bus)
    goal = "resume me"
    key = AutonomousLoop.goal_key(goal)

    # simulate a crash snapshot left behind by a previous run
    recovery.persist_state(key, "halfway through the work", ["step one", "step two"], 4)

    result = await loop.run_task(goal)
    assert "task_resumed" in events
    assert "done" in result
    # snapshot cleared after successful completion
    assert recovery.load_state(key) is None


@pytest.mark.asyncio
async def test_snapshot_data_round_trips(memory):
    loop, recovery = _loop_with_recovery(memory, EventBus())
    key = AutonomousLoop.goal_key("round trip")
    recovery.persist_state(key, "current step", ["a", "b"], 7)
    state = recovery.load_state(key)
    assert state == {"task_id": key, "current_step": "current step", "plan": ["a", "b"], "iteration": 7}
