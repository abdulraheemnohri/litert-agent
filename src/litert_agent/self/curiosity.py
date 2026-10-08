"""Curiosity engine (A-to-Z spec section 11).

Generates candidate future goals from observed signals such as repeated
failures, missing knowledge and skill gaps. Curiosity items are proposals
only — they become goals (and then require approval for high risk) when
explicitly promoted.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path.home() / ".litert-agent" / "agent.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS curiosity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    origin TEXT DEFAULT '',
    score REAL DEFAULT 0.0,
    status TEXT DEFAULT 'NEW',
    created_at TEXT NOT NULL
);
"""

# Signals that raise the curiosity score.
_Signal = {
    "repeated_failure": 3.0,
    "missing_knowledge": 2.0,
    "skill_gap": 2.0,
    "task_pattern": 1.0,
    "tool_limitation": 2.5,
    "user_interest": 1.5,
    "research_gap": 2.0,
}


@dataclass
class CuriosityItem:
    id: int
    question: str
    origin: str
    score: float
    status: str
    created_at: str

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CuriosityEngine:
    def __init__(self, db_path: str | Path = DEFAULT_DB) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def generate_curiosity(self, question: str, origin: str = "observation") -> CuriosityItem:
        score = self.score_curiosity(origin)
        self._conn.execute(
            "INSERT INTO curiosity (question, origin, score, created_at) VALUES (?,?,?,?)",
            (question, origin, score, _now()),
        )
        self._conn.commit()
        return self.list_curiosity()[-1]

    @staticmethod
    def score_curiosity(origin: str) -> float:
        return _Signal.get(origin, 0.5)

    def deduplicate_curiosity(self) -> int:
        """Merge identical open questions, keeping the highest score."""
        rows = self._conn.execute(
            "SELECT id, question, score FROM curiosity WHERE status = 'NEW' ORDER BY id"
        ).fetchall()
        seen: dict[str, int] = {}
        removed = 0
        for row in rows:
            key = row["question"].strip().lower()
            if key in seen:
                keep = seen[key]
                if row["score"] > 0:
                    self._conn.execute(
                        "UPDATE curiosity SET score = MAX(score, ?) WHERE id = ?",
                        (row["score"], keep),
                    )
                self._conn.execute("DELETE FROM curiosity WHERE id = ?", (row["id"],))
                removed += 1
            else:
                seen[key] = row["id"]
        self._conn.commit()
        return removed

    def rank_curiosity(self) -> list[CuriosityItem]:
        rows = self._conn.execute(
            "SELECT * FROM curiosity WHERE status = 'NEW' ORDER BY score DESC, id"
        ).fetchall()
        return [self._row(r) for r in rows]

    def promote_curiosity_to_goal(self, item_id: int, goal_manager) -> str:
        """Promote a curiosity item into a real goal via the GoalManager."""
        row = self._conn.execute(
            "SELECT * FROM curiosity WHERE id = ?", (item_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"curiosity item not found: {item_id}")
        goal = goal_manager.create_goal(
            row["question"],
            description=f"Generated from curiosity (origin: {row['origin']}).",
            source="curiosity",
            risk="medium",  # generated goals always require approval
        )
        self._conn.execute(
            "UPDATE curiosity SET status = 'PROMOTED' WHERE id = ?", (item_id,)
        )
        self._conn.commit()
        return goal.id

    def expire_curiosity(self, max_age_days: int = 30) -> int:
        cutoff = datetime.now(timezone.utc).timestamp() - max_age_days * 86400
        rows = self._conn.execute(
            "DELETE FROM curiosity WHERE status = 'NEW' AND"
            " CAST(strftime('%s', created_at) AS INTEGER) < ?",
            (int(cutoff),),
        )
        self._conn.commit()
        return rows.rowcount

    def list_curiosity(self) -> list[CuriosityItem]:
        rows = self._conn.execute("SELECT * FROM curiosity ORDER BY id DESC").fetchall()
        return [self._row(r) for r in rows]

    @staticmethod
    def _row(row: sqlite3.Row) -> CuriosityItem:
        return CuriosityItem(
            id=row["id"], question=row["question"], origin=row["origin"],
            score=row["score"], status=row["status"], created_at=row["created_at"],
        )
