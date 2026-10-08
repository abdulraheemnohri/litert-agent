"""Tests for the curiosity engine."""
from litert_agent.self.curiosity import CuriosityEngine
from litert_agent.self.goals import GoalManager


def test_generate_and_rank(tmp_path):
    ce = CuriosityEngine(tmp_path / "a.db")
    ce.generate_curiosity("Why does the browser tool time out?", "tool_limitation")
    ce.generate_curiosity("Which files are unused?", "task_pattern")
    ranked = ce.rank_curiosity()
    assert ranked[0].origin == "tool_limitation"
    assert ranked[0].score >= ranked[1].score
    ce.close()


def test_deduplicate(tmp_path):
    ce = CuriosityEngine(tmp_path / "a.db")
    ce.generate_curiosity("Same question")
    ce.generate_curiosity("same question ")
    assert ce.deduplicate_curiosity() == 1
    assert len(ce.list_curiosity()) == 1
    ce.close()


def test_promote_to_goal_requires_approval(tmp_path):
    ce = CuriosityEngine(tmp_path / "a.db")
    gm = GoalManager(tmp_path / "a.db")
    item = ce.generate_curiosity("Can we speed up inference?", "research_gap")
    goal_id = ce.promote_curiosity_to_goal(item.id, gm)
    goal = gm.get_goal(goal_id)
    assert goal.source == "curiosity"
    assert goal.status == "WAITING_APPROVAL"  # generated goals always need approval
    ce.close(); gm.close()
