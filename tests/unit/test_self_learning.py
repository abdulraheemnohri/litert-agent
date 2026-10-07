from litert_agent.self.learning import Experience, LearningEngine
from litert_agent.self.skills import SelfSkillEngine
from litert_agent.self.goals import SelfGoalManager


def test_learning_requires_validation_for_promotion():
    e=LearningEngine()
    x=Experience("t1","goal","ok",True,["test passed"])
    item=e.extract_lesson(x,"Use tests after edits","testing",x.evidence)
    assert item.validated is False
    e.validate("testing",True,"second verified success")
    assert e.lessons["testing"].validated is True


def test_self_skill_blocks_dangerous_capability():
    s=SelfSkillEngine()
    try:
        s.propose("bad","x","x",["modify_security_policy"])
    except ValueError:
        return
    assert False


def test_goals_choose_highest_priority():
    g=SelfGoalManager()
    g.create("a","low","x",10)
    g.create("b","high","x",90)
    assert g.next_goal().id=="b"
