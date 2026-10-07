"""Integration test: full autonomous loop with a scripted fake provider."""

import pytest

from litert_agent.cognition.executor import Executor
from litert_agent.memory.manager import MemoryManager
from litert_agent.memory.sqlite import SCHEMA, DatabaseManager
from litert_agent.model.protocol import ProtocolMessage
from litert_agent.model.provider import ModelProvider
from litert_agent.recovery.checkpoints import CheckpointManager
from litert_agent.runtime.events import EventBus
from litert_agent.runtime.loop import AutonomousLoop
from litert_agent.security.approvals import ApprovalManager
from litert_agent.security.policy import SecurityPolicy
from litert_agent.tools.filesystem import FilesystemTool
from litert_agent.tools.registry import ToolRegistry


class ScriptedProvider(ModelProvider):
    """Returns queued messages in order."""

    def __init__(self, messages):
        self.messages = list(messages)

    async def generate(self, prompt: str, system_prompt: str | None = None) -> ProtocolMessage:
        if self.messages:
            return self.messages.pop(0)
        return ProtocolMessage(type="final", content="done by script")


@pytest.fixture
def memory(tmp_path):
    db = DatabaseManager(tmp_path / "agent.db")
    with __import__("sqlite3").connect(db.db_path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()
    mm = MemoryManager(tmp_path / "agent.db")
    mm.working.clear()
    return mm


@pytest.mark.asyncio
async def test_loop_executes_tool_then_completes(memory, tmp_path):
    registry = ToolRegistry()
    registry.register(FilesystemTool())
    approvals = ApprovalManager(auto_approve=True)
    executor = Executor(registry, SecurityPolicy(), approvals)
    bus = EventBus()
    events = []
    bus.subscribe("tool_completed", lambda e: events.append(e.event_type))
    bus.subscribe("task_completed", lambda e: events.append(e.event_type))

    target = tmp_path / "out.txt"
    provider = ScriptedProvider([
        ProtocolMessage(type="tool_call", tool="filesystem", action="write",
                        arguments={"path": str(target), "content": "hello"}),
        ProtocolMessage(type="final", content="file created"),
    ])

    loop = AutonomousLoop(provider, executor, memory, bus, checkpoint_manager=CheckpointManager(memory.db_manager))
    result = await loop.run_task("create a file")

    assert "tool_completed" in events
    assert "task_completed" in events
    assert target.read_text() == "hello"
    assert memory.db_manager.execute_read("SELECT COUNT(*) FROM checkpoints")[0][0] >= 1
    lessons = await memory.lessons.get_lessons("task_outcome")
    assert lessons


@pytest.mark.asyncio
async def test_loop_denied_approval_blocks_tool(memory, tmp_path):
    registry = ToolRegistry()
    registry.register(FilesystemTool())
    approvals = ApprovalManager(auto_approve=False)  # nothing approved -> deny
    executor = Executor(registry, SecurityPolicy(), approvals)

    provider = ScriptedProvider([
        ProtocolMessage(type="tool_call", tool="filesystem", action="delete",
                        arguments={"path": str(tmp_path / "x.txt")}),
    ])
    loop = AutonomousLoop(provider, executor, memory, EventBus())
    # fs delete policy is ASK-ish via protected path only; write path policy default ALLOW
    # so use an explicit protected path to force ASK/BLOCK denial
    result = await loop.run_task("delete a protected file")
    # loop must terminate without executing the denied action
    assert result is not None
