import asyncio
from litert_agent.security.approvals import ApprovalManager


def test_approval_lifecycle():
    manager = ApprovalManager()
    assert asyncio.run(manager.request_approval("terminal", "execute", {"command": "echo ok"}, "test")) is False
    pending = manager.list_pending()
    assert len(pending) == 1
    approval_id = pending[0]["id"]
    result = manager.decide(approval_id, "allow_once")
    assert result["status"] == "ALLOW"
    assert result["decision"] == "allow_once"
    assert manager.consume(approval_id) is True


def test_denial_and_invalid_decision():
    manager = ApprovalManager()
    asyncio.run(manager.request_approval("filesystem", "write", {"path": "x"}, "test"))
    approval_id = manager.list_pending()[0]["id"]
    assert manager.decide(approval_id, "invalid") is None
    result = manager.decide(approval_id, "deny")
    assert result["status"] == "DENY"
    assert manager.consume(approval_id) is False


def test_session_approval_allows_same_action():
    manager = ApprovalManager()
    asyncio.run(manager.request_approval("terminal", "execute", {}, "test"))
    approval_id = manager.list_pending()[0]["id"]
    manager.decide(approval_id, "allow")
    assert asyncio.run(manager.request_approval("terminal", "execute", {}, "test")) is True
