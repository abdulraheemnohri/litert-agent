"""Unit tests for memory manager and sqlite memory subsystem."""

import pytest

from litert_agent.memory.manager import MemoryManager


@pytest.mark.asyncio
async def test_memory_manager_integration(tmp_path):
    db_file = tmp_path / "test_agent.db"
    mem = MemoryManager(db_file)
    await mem.initialize()

    mem.working.add("user", "Hello world")
    assert len(mem.working.get_recent(5)) == 1

    await mem.episodic.record_episode("general", "User asked to check tests")
    episodes = await mem.episodic.search_episodes("tests")
    assert len(episodes) == 1
    assert "tests" in episodes[0]["content"]

    await mem.semantic.add_fact("project", "uses", "pytest")
    facts = await mem.semantic.get_facts("project")
    assert len(facts) == 1
    assert facts[0]["object"] == "pytest"

    t_id = await mem.tasks.create_task("Run pytest", "Run full test suite")
    task = await mem.tasks.get_task(t_id)
    assert task["status"] == "PENDING"

    await mem.tasks.update_task_status(t_id, "COMPLETED", "All passed")
    updated = await mem.tasks.get_task(t_id)
    assert updated["status"] == "COMPLETED"
