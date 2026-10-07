"""Unit tests for multi-agent and scheduler subsystems."""

import pytest
from litert_agent.agents.roles import AgentRole
from litert_agent.agents.delegation import DelegationManager
from litert_agent.model.litert_cli import LiteRTLMProvider
from litert_agent.tools.registry import ToolRegistry
from litert_agent.scheduler.scheduler import Scheduler

@pytest.mark.asyncio
async def test_multi_agent_delegation():
    provider = LiteRTLMProvider()
    registry = ToolRegistry()
    delegator = DelegationManager(provider, registry)

    res = await delegator.delegate(AgentRole.TESTER, "Run unit tests")
    assert res["role"] == "tester"
    assert res["status"] == "COMPLETED"

@pytest.mark.asyncio
async def test_scheduler():
    scheduler = Scheduler()
    job = await scheduler.add_job("test_job", "Clean temp files")
    assert job.name == "test_job"
    assert scheduler.queue.size() == 1
