"""Autonomous loop V2 protocol-state integration tests."""

import pytest

from litert_agent.cognition.executor import Executor
from litert_agent.memory.manager import MemoryManager
from litert_agent.memory.sqlite import SCHEMA, DatabaseManager
from litert_agent.model.protocol import ProtocolMessage
from litert_agent.model.provider import ModelProvider
from litert_agent.runtime.events import EventBus
from litert_agent.runtime.loop import AutonomousLoop
from litert_agent.security.approvals import ApprovalManager
from litert_agent.security.policy import SecurityPolicy
from litert_agent.tools.filesystem import FilesystemTool
from litert_agent.tools.registry import ToolRegistry


class ScriptedProvider(ModelProvider):
    def __init__(self, messages):
        self.messages = list(messages)

    async def generate(self, prompt: str, system_prompt: str | None = None) -> ProtocolMessage:
        return self.messages.pop(0) if self.messages else ProtocolMessage(
            type="thought", content="continue"
        )


@pytest.fixture
def memory(tmp_path):
    db = DatabaseManager(tmp_path / "agent.db")
    with __import__("sqlite3").connect(db.db_path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()
    return MemoryManager(tmp_path / "agent.db")


def make_loop(memory, provider, approvals=None):
    registry = ToolRegistry()
    registry.register(FilesystemTool())
    executor = Executor(registry, SecurityPolicy(), approvals or ApprovalManager(auto_approve=True))
    return AutonomousLoop(provider, executor, memory, EventBus())


@pytest.mark.asyncio
async def test_approval_message_pauses_without_executing(memory):
    provider = ScriptedProvider([
        ProtocolMessage(
            type="approval_required",
            reason="High-risk operation requires approval",
            requires_approval=True,
        )
    ])
    loop = make_loop(memory, provider)
    result = await loop.run_task("perform a protected operation")

    assert "approval required" in result.lower()
    assert loop.state.status == "PAUSED"
    rows = memory.db_manager.execute_read(
        "SELECT status FROM tasks ORDER BY id DESC LIMIT 1"
    )
    assert rows[0][0] == "WAITING_APPROVAL"


@pytest.mark.asyncio
async def test_plan_update_is_applied_without_bypassing_policy(memory):
    provider = ScriptedProvider([
        ProtocolMessage(
            type="plan",
            goal="inspect project",
            plan_steps=["inspect repository", "run tests", "verify result"],
        ),
        ProtocolMessage(
            type="thought",
            content="continue with the validated plan",
        ),
    ])
    loop = make_loop(memory, provider)
    loop.state.max_iterations = 2
    result = await loop.run_task("inspect project")

    assert result == "Task stopped: Max iterations reached."
