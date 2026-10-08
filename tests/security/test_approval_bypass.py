"""Security tests: approval bypass attempts (A-to-Z spec section 91).

Nothing may escalate permissions: high-risk goals need explicit approval,
and deny/allow-once never grant broader rights than requested.
"""
from litert_agent.self.goals import GoalManager, GoalState
from litert_agent.security.approvals import ApprovalManager


def test_high_risk_goal_cannot_become_ready_without_approval(tmp_path):
    gm = GoalManager(tmp_path / "sec.db")
    goal = gm.create_goal("Wipe production database", risk="critical")
    assert goal.status == GoalState.WAITING_APPROVAL.value
    # dependency resolution must not promote an unapproved goal
    ready_ids = [g.id for g in gm.find_ready_goals()]
    assert goal.id not in ready_ids
    assert gm.execute_next_goal() is None
    # only the explicit human approval unlocks it
    gm.approve_goal(goal.id)
    assert gm.get_goal(goal.id).status == GoalState.PENDING.value
    gm.close()


def test_medium_risk_also_requires_approval(tmp_path):
    gm = GoalManager(tmp_path / "sec.db")
    assert gm.create_goal("Modify config", risk="medium").status == GoalState.WAITING_APPROVAL.value
    gm.close()


def test_denied_approval_grants_nothing():
    import asyncio

    mgr = ApprovalManager()

    async def _request():
        await mgr.request_approval("terminal", "execute", {"command": "sudo reboot"}, "dangerous")

    asyncio.run(_request())
    approval = mgr.pending[0]
    mgr.decide(approval["id"], "deny")
    assert approval["status"] == "DENY"
    assert mgr.session_approvals == set()  # deny must not leak into session rights


def test_allow_once_does_not_grant_session_rights():
    import asyncio

    mgr = ApprovalManager()

    async def _request():
        await mgr.request_approval("terminal", "execute", {"command": "rm /tmp/x"}, "cleanup")

    asyncio.run(_request())
    approval = mgr.pending[0]
    mgr.decide(approval["id"], "allow_once")
    assert mgr.session_approvals == set()  # one-shot only

    async def _second():
        # a second identical request must queue again, not auto-approve
        return await mgr.request_approval("terminal", "execute", {"command": "rm /tmp/y"}, "cleanup")

    assert asyncio.run(_second()) is False
    assert len(mgr.pending) == 1
