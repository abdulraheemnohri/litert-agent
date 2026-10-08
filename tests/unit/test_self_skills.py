import sqlite3

from litert_agent.memory.sqlite import SCHEMA, DatabaseManager
from litert_agent.self.evolution import EvolutionManager
from litert_agent.self.skills import SelfSkillManager
from litert_agent.skills.registry import SkillRegistry
from litert_agent.skills.validator import SkillValidator


def test_self_skill_persistence_and_quarantine(tmp_path):
    db = DatabaseManager(tmp_path / "agent.db")
    with sqlite3.connect(db.db_path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()
    registry = SkillRegistry(db)
    manager = SelfSkillManager(registry, SkillValidator(), EvolutionManager(), db)
    proposed = manager.propose("audit-demo", "audit files", ["filesystem"], "repeated audit task")
    manager.approve("audit-demo")
    manager.register("audit-demo")
    assert manager.version("audit-demo")
    state = manager.quarantine("audit-demo", "test quarantine")
    assert state["status"] == "QUARANTINED"
    restored = manager.restore("audit-demo")
    assert restored is True
