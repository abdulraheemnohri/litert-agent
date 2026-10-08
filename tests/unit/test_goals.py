"""Tests for the autonomous goal manager."""
from litert_agent.self.goals import GoalManager, GoalState


def test_create_and_get_goal(tmp_path):
    gm = GoalManager(tmp_path / "a.db")
    goal = gm.create_goal("Write tests", "cover goal manager")
    assert goal.status == GoalState.PENDING.value
    assert gm.get_goal(goal.id).title == "Write tests"
    gm.close()


def test_high_risk_goal_requires_approval(tmp_path):
    gm = GoalManager(tmp_path / "a.db")
    goal = gm.create_goal("Deploy to production", risk="high")
    assert goal.status == GoalState.WAITING_APPROVAL.value
    assert gm.find_ready_goals() == []
    approved = gm.approve_goal(goal.id)
    assert approved.status == GoalState.PENDING.value


def test_dependency_resolution_and_execute_next(tmp_path):
    gm = GoalManager(tmp_path / "a.db")
    blocker = gm.create_goal("Setup database", priority="LOW")
    dependent = gm.create_goal("Build feature", priority="HIGH", dependencies=[blocker.id])
    # dependent is not ready while blocker is incomplete
    ready_ids = [g.id for g in gm.find_ready_goals()]
    assert dependent.id not in ready_ids
    gm.complete_goal(blocker.id)
    ready = gm.find_ready_goals()
    assert dependent.id in [g.id for g in ready]
    active = gm.execute_next_goal()
    assert active is not None and active.id == dependent.id
    assert active.status == GoalState.ACTIVE.value


def test_lifecycle_transitions(tmp_path):
    gm = GoalManager(tmp_path / "a.db")
    goal = gm.create_goal("Paused task")
    assert gm.pause_goal(goal.id).status == GoalState.PAUSED.value
    assert gm.resume_goal(goal.id).status == GoalState.PENDING.value
    assert gm.fail_goal(goal.id).status == GoalState.FAILED.value
    assert gm.retry_goal(goal.id).status == GoalState.PENDING.value
    assert gm.cancel_goal(goal.id).status == GoalState.CANCELLED.value
    gm.close()
