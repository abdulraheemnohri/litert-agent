from litert_agent.recovery.crash_recovery import CrashRecovery
from litert_agent.memory.sqlite import SCHEMA, DatabaseManager


def test_crash_recovery_persists_runtime_state(tmp_path):
    db = DatabaseManager(tmp_path / "agent.db")
    with __import__("sqlite3").connect(db.db_path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()
    recovery = CrashRecovery(db)
    recovery.persist_state(
        "task-1", "step-2", ["a", "b"], 4,
        runtime_state={"status": "WAITING_APPROVAL", "active_step_id": "b"},
        status="WAITING_APPROVAL",
    )
    state = recovery.load_state("task-1")
    assert state["iteration"] == 4
    assert state["status"] == "WAITING_APPROVAL"
    assert state["runtime_state"]["active_step_id"] == "b"


def test_crash_recovery_corrupt_state_is_safe(tmp_path):
    db = DatabaseManager(tmp_path / "agent.db")
    with __import__("sqlite3").connect(db.db_path) as conn:
        conn.executescript(SCHEMA)
        conn.execute(
            "INSERT INTO checkpoints (id, task_id, description, state_json) VALUES (?, ?, ?, ?)",
            ("crash-x", "x", "crash-recovery-snapshot", "{bad"),
        )
        conn.commit()
    assert CrashRecovery(db).load_state("x") is None
