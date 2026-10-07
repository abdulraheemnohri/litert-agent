"""Integration test for orchestrator and autonomous loop."""

import pytest
from pathlib import Path
from litert_agent.config import Config
from litert_agent.runtime.orchestrator import Orchestrator

@pytest.mark.asyncio
async def test_orchestrator_loop_flow(tmp_path):
    cfg = Config()
    cfg.agent.home_dir = tmp_path
    orchestrator = Orchestrator(cfg)
    await orchestrator.initialize()

    result = await orchestrator.run_task("Create hello.txt file with world")
    assert result is not None
