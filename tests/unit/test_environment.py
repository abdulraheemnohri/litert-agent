"""Unit tests for environment detection."""

from litert_agent.environment.capabilities import Capabilities
from litert_agent.environment.detector import EnvironmentDetector

def test_environment_detection():
    env = EnvironmentDetector.detect_all()
    assert "os" in env
    assert "python_version" in env

    caps = Capabilities.discover()
    assert caps.python_version != ""
