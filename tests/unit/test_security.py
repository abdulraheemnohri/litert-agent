"""Unit tests for security module."""

from litert_agent.security.policy import PermissionLevel, SecurityPolicy
from litert_agent.security.sandbox import SandboxValidator
from litert_agent.security.secrets import SecretSanitizer


def test_security_policy():
    policy = SecurityPolicy(safe_mode=False)
    assert policy.evaluate_tool_call("terminal", "execute", {"command": "ls"}) == PermissionLevel.ALLOW
    assert policy.evaluate_tool_call("terminal", "execute", {"command": "sudo rm -rf /"}) == PermissionLevel.BLOCK
    assert policy.evaluate_tool_call("terminal", "execute", {"command": "pip install foo"}) == PermissionLevel.ASK

def test_secret_sanitizer():
    raw = "api_key=secret12345 password='my_password_xyz'"
    clean = SecretSanitizer.sanitize(raw)
    assert "secret12345" not in clean
    assert "my_password_xyz" not in clean

def test_sandbox_validator(tmp_path):
    validator = SandboxValidator(tmp_path)
    safe_file = tmp_path / "test.txt"
    unsafe_file = tmp_path.parent / "outside.txt"
    assert validator.is_path_safe(safe_file) is True
    assert validator.is_path_safe(unsafe_file) is False
