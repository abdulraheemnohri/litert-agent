from litert_agent.security.command_guard import CommandGuard
from litert_agent.security.path_guard import PathGuard


def test_path_guard_workspace_and_sensitive(tmp_path):
    guard = PathGuard(tmp_path)
    assert guard.check(tmp_path / "safe.txt")[0] is True
    assert guard.check(tmp_path.parent / "outside.txt")[0] is False
    assert guard.check(tmp_path / ".env")[0] is False


def test_command_guard_blocks_dangerous_commands():
    assert CommandGuard.classify("sudo rm -rf /") == "BLOCK"
    assert CommandGuard.classify("mkfs /dev/sda") == "BLOCK"


def test_command_guard_asks_for_mutating_commands():
    assert CommandGuard.classify("pip install requests") == "ASK"
    assert CommandGuard.classify("git push origin main") == "ASK"


def test_command_guard_allows_read_only_commands():
    assert CommandGuard.classify("git status") == "ALLOW"
    assert CommandGuard.classify("python --version") == "ALLOW"
