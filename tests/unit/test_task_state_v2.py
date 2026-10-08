from litert_agent.runtime.state import AgentState


def test_agent_state_tracks_step_lifecycle():
    state = AgentState(status="RUNNING")
    step = state.step("build")
    step.status = "ACTIVE"
    step.attempts = 2
    step.status = "VERIFYING"
    assert state.step("build").attempts == 2
    assert state.snapshot()["steps"][0]["status"] == "VERIFYING"


def test_agent_state_snapshot_is_json_safe():
    state = AgentState(current_task_id="t1", status="WAITING_APPROVAL", waiting_reason="approval")
    snapshot = state.snapshot()
    assert snapshot["current_task_id"] == "t1"
    assert snapshot["status"] == "WAITING_APPROVAL"
