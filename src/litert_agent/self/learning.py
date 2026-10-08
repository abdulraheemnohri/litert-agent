"""Self-learning engine (A-to-Z spec sections 13-14).

Learning here means experience -> evaluation -> lesson -> memory, never
model-weight modification. Skill proposals generated from repeated patterns
follow the spec lifecycle and default to inactive (no auto-activation).
Tables use a `self_x_` prefix to avoid collisions with the canonical
memory/sqlite.py schema in the same shared database.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path.home() / ".litert-agent" / "agent.db"

SKILL_LIFECYCLE = (
    "PROPOSED", "VALIDATING", "TESTING", "WAITING_APPROVAL",
    "ACTIVE", "FAILED", "REJECTED", "ROLLED_BACK",
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS self_x_experiences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task TEXT NOT NULL,
    outcome TEXT NOT NULL,
    tools TEXT DEFAULT '',
    errors TEXT DEFAULT '',
    lesson TEXT DEFAULT '',
    confidence REAL DEFAULT 0.5,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS self_x_lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experience_id INTEGER,
    lesson TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS self_x_skill_proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    reason TEXT DEFAULT '',
    evidence TEXT DEFAULT '',
    status TEXT DEFAULT 'PROPOSED',
    created_at TEXT NOT NULL
);
"""

_PATTERN_THRESHOLD = 3  # repeated (tool, error) pairs before a skill proposal


@dataclass
class Experience:
    id: int
    task: str
    outcome: str
    tools: str
    errors: str
    lesson: str
    confidence: float
    created_at: str

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class LearningEngine:
    def __init__(self, db_path: str | Path = DEFAULT_DB) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # -- Experience ---------------------------------------------------------
    def record_experience(
        self,
        task: str,
        outcome: str,
        *,
        tools: list[str] | None = None,
        errors: list[str] | None = None,
    ) -> Experience:
        """Record what happened and evaluate it (spec section 14)."""
        success = outcome.lower() in {"success", "completed", "pass"}
        errors_joined = "; ".join(errors or [])
        confidence = self.calculate_confidence(success, len(errors or []))
        lesson = self.extract_lesson(task, outcome, errors_joined)
        cur = self._conn.execute(
            "INSERT INTO self_x_experiences (task, outcome, tools, errors, lesson,"
            " confidence, created_at) VALUES (?,?,?,?,?,?,?)",
            (task, outcome, ",".join(tools or []), errors_joined, lesson,
             confidence, _now()),
        )
        self._conn.commit()
        if lesson:
            self.store_lesson(cur.lastrowid, lesson, confidence)
        return self.get_experience(cur.lastrowid)

    def get_experience(self, experience_id: int) -> Experience:
        row = self._conn.execute(
            "SELECT * FROM self_x_experiences WHERE id = ?", (experience_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"experience not found: {experience_id}")
        return Experience(
            id=row["id"], task=row["task"], outcome=row["outcome"],
            tools=row["tools"], errors=row["errors"], lesson=row["lesson"],
            confidence=row["confidence"], created_at=row["created_at"],
        )

    def list_experiences(self, limit: int = 50) -> list[Experience]:
        rows = self._conn.execute(
            "SELECT id FROM self_x_experiences ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [self.get_experience(r["id"]) for r in rows]

    @staticmethod
    def calculate_confidence(success: bool, error_count: int) -> float:
        """Higher confidence for clean successes; failures lower it."""
        base = 0.8 if success else 0.4
        return max(0.0, min(1.0, base - 0.05 * error_count))

    @staticmethod
    def extract_lesson(task: str, outcome: str, errors: str) -> str:
        if outcome.lower() in {"success", "completed", "pass"}:
            return f"Approach used for '{task}' worked."
        if errors:
            return f"'{task}' failed: {errors.split(';')[0].strip()}. Try a different approach."
        return f"'{task}' did not reach completion; review the plan."

    def store_lesson(self, experience_id: int, lesson: str, confidence: float) -> int:
        cur = self._conn.execute(
            "INSERT INTO self_x_lessons (experience_id, lesson, confidence, created_at)"
            " VALUES (?,?,?,?)",
            (experience_id, lesson, confidence, _now()),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def list_lessons(self, min_confidence: float = 0.0) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM self_x_lessons WHERE confidence >= ? ORDER BY id DESC",
            (min_confidence,),
        ).fetchall()
        return [dict(r) for r in rows]

    # -- Pattern detection / skill proposals ---------------------------------
    def derive_pattern(self) -> dict | None:
        """Detect a repeated (tool, first-error) pattern across failures."""
        rows = self._conn.execute(
            "SELECT tools, errors FROM self_x_experiences WHERE outcome NOT IN"
            " ('success','completed','pass')"
        ).fetchall()
        counts: dict[tuple[str, str], int] = {}
        for row in rows:
            tool = (row["tools"] or "unknown").split(",")[0]
            error = (row["errors"] or "unknown").split(";")[0].strip()
            counts[(tool, error)] = counts.get((tool, error), 0) + 1
        if not counts:
            return None
        (tool, error), n = max(counts.items(), key=lambda kv: kv[1])
        return {"tool": tool, "error": error, "count": n}

    def propose_skill_from_pattern(self) -> dict | None:
        """Propose a skill when a failure pattern repeats enough times.

        Proposals stay PROPOSED — activation requires human approval
        (skill_auto_activation defaults to false).
        """
        pattern = self.derive_pattern()
        if not pattern or pattern["count"] < _PATTERN_THRESHOLD:
            return None
        name = f"{pattern['tool']}-diagnostic"
        existing = self._conn.execute(
            "SELECT id FROM self_x_skill_proposals WHERE name = ?", (name,)
        ).fetchone()
        if existing:
            return None
        reason = f"Repeated failure ({pattern['count']}x) with tool '{pattern['tool']}': {pattern['error']}"
        self._conn.execute(
            "INSERT INTO self_x_skill_proposals (name, reason, evidence, status, created_at)"
            " VALUES (?,?,?,?,?)",
            (name, reason, pattern["error"], "PROPOSED", _now()),
        )
        self._conn.commit()
        return {"name": name, "reason": reason, "status": "PROPOSED"}

    def list_skill_proposals(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM self_x_skill_proposals ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def decide_skill_proposal(self, proposal_id: int, approve: bool) -> dict:
        """Human decision on a skill proposal (spec section 17)."""
        status = "ACTIVE" if approve else "REJECTED"
        row = self._conn.execute(
            "SELECT id FROM self_x_skill_proposals WHERE id = ?", (proposal_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"proposal not found: {proposal_id}")
        self._conn.execute(
            "UPDATE self_x_skill_proposals SET status = ? WHERE id = ?", (status, proposal_id)
        )
        self._conn.commit()
        return {"id": proposal_id, "status": status}
