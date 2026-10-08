"""Tests for the self-learning engine."""
from litert_agent.self.learning import LearningEngine


def test_record_experience_extracts_lesson(tmp_path):
    le = LearningEngine(tmp_path / "a.db")
    exp = le.record_experience("run tests", "failed", tools=["terminal"],
                               errors=["ImportError: missing module"])
    assert exp.confidence < 0.6
    assert le.list_lessons()
    le.close()


def test_successful_experience_high_confidence(tmp_path):
    le = LearningEngine(tmp_path / "a.db")
    exp = le.record_experience("run tests", "success", tools=["terminal"])
    assert exp.confidence >= 0.75
    le.close()


def test_pattern_and_skill_proposal(tmp_path):
    le = LearningEngine(tmp_path / "a.db")
    for _ in range(3):
        le.record_experience("deploy", "failed", tools=["terminal"],
                             errors=["port already in use"])
    pattern = le.derive_pattern()
    assert pattern is not None and pattern["count"] == 3
    proposal = le.propose_skill_from_pattern()
    assert proposal is not None and proposal["status"] == "PROPOSED"
    # no auto-activation: rejection keeps it out
    pid = le.list_skill_proposals()[0]["id"]
    assert le.decide_skill_proposal(pid, approve=False)["status"] == "REJECTED"
    le.close()


def test_skill_proposal_needs_threshold(tmp_path):
    le = LearningEngine(tmp_path / "a.db")
    le.record_experience("deploy", "failed", tools=["terminal"], errors=["x"])
    assert le.propose_skill_from_pattern() is None
    le.close()
