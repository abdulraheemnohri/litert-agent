"""Unit tests for the shared runtime service."""

import pytest
from litert_agent.config import Config
from litert_agent.runtime.service import AgentRuntime


def test_runtime_singleton():
    r1 = AgentRuntime.get(Config())
    r2 = AgentRuntime.get()
    assert r1 is r2


def test_runtime_status_shape():
    runtime = AgentRuntime(Config())
    status = runtime.status()
    assert status["model_provider"] == "litert-cli"
    assert "queue_size" in status


def test_runtime_health():
    runtime = AgentRuntime(Config())
    health = runtime.health()
    assert health["status"] in ("HEALTHY", "DEGRADED")
