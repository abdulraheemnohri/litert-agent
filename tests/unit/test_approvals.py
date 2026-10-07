"""Tests for the approval manager decision lifecycle."""

import pytest

from litert_agent.security.approvals import ApprovalManager


@pytest.mark.asyncio
async def test_request_approval_queues_pending():
    mgr = ApprovalManager()
    approved = await mgr.request_approval("terminal", "execute", {"command": "rm x"}, "destructive")
    assert approved is False
    assert len(mgr.pending) == 1
    a = mgr.pending[0]
    assert a["tool"] == "terminal"
    assert a["action"] == "execute"
    assert a["risk"] == "HIGH"
    assert a["status"] == "WAITING"


@pytest.mark.asyncio
async def test_auto_approve_skips_pending():
    mgr = ApprovalManager(auto_approve=True)
    approved = await mgr.request_approval("filesystem", "write", {}, "test")
    assert approved is True
    assert mgr.pending == []


def test_decide_allow_once_records_allow():
    mgr = ApprovalManager()

    async def _request():
        await mgr.request_approval("filesystem", "write", {"path": "/tmp/x"}, "write op")

    import asyncio
    asyncio.run(_request())
    approval = mgr.pending[0]
    result = mgr.decide(approval["id"], "allow_once")
    assert result is approval
    assert approval["status"] == "ALLOW"
    assert mgr.pending == []
    assert mgr.history == [approval]
    # allow_once must not grant session approval
    assert mgr.session_approvals == set()


def test_decide_allow_grants_session_approval():
    mgr = ApprovalManager()

    async def _request():
        await mgr.request_approval("terminal", "execute", {"command": "ls"}, "list dir")

    import asyncio
    asyncio.run(_request())
    approval = mgr.pending[0]
    mgr.decide(approval["id"], "allow")
    assert mgr.session_approvals == {"terminal:execute"}


@pytest.mark.asyncio
async def test_session_approval_short_circuits():
    mgr = ApprovalManager()
    await mgr.request_approval("http", "get", {"url": "x"}, "network")
    approval = mgr.pending[0]
    mgr.decide(approval["id"], "allow")
    approved = await mgr.request_approval("http", "get", {"url": "y"}, "network")
    assert approved is True
    assert mgr.pending == []


def test_decide_deny():
    mgr = ApprovalManager()

    async def _request():
        await mgr.request_approval("terminal", "execute", {"command": "sudo reboot"}, "dangerous")

    import asyncio
    asyncio.run(_request())
    approval = mgr.pending[0]
    result = mgr.decide(approval["id"], "deny")
    assert result is approval
    assert approval["status"] == "DENY"
    assert mgr.session_approvals == set()


def test_decide_unknown_id_returns_none():
    mgr = ApprovalManager()
    assert mgr.decide("nope", "allow") is None


def test_lists_are_copies():
    mgr = ApprovalManager()
    pending = mgr.list_pending()
    history = mgr.list_history()
    pending.append({"fake": True})
    assert mgr.list_pending() == []
