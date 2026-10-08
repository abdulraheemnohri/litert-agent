"""Research missions with credibility scoring and synthesis.

Pipeline (spec section 15):
question -> sources -> claims -> credibility -> contradiction check ->
synthesis -> knowledge record.

Internet content is stored as data only; it is never executed or treated
as instructions.
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_DB = Path.home() / ".litert-agent" / "agent.db"

# Knowledge verification states (spec section 16)
KNOWLEDGE_STATES = (
    "UNVERIFIED", "SUPPORTED", "CORROBORATED", "CONTRADICTED", "STALE", "ARCHIVED",
)

_NEGATIVE = re.compile(r"\b(not|never|cannot|no)\b", re.IGNORECASE)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS research (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    status TEXT DEFAULT 'OPEN',
    synthesis TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS research_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    research_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    credibility REAL DEFAULT 0.5,
    fetched_at TEXT
);
CREATE TABLE IF NOT EXISTS research_claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    research_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    claim TEXT NOT NULL,
    polarity INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim TEXT NOT NULL,
    source TEXT DEFAULT '',
    confidence REAL DEFAULT 0.5,
    provenance TEXT DEFAULT '',
    domain TEXT DEFAULT '',
    verification_state TEXT DEFAULT 'UNVERIFIED',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

# Rough domain-credibility heuristics (evidence quality, not authority).
_DOMAIN_CREDIBILITY = {
    ".edu": 0.9, ".gov": 0.9, ".org": 0.6, ".com": 0.4, ".net": 0.4,
}


@dataclass
class Source:
    id: int
    url: str
    credibility: float

@dataclass
class Claim:
    id: int
    source_id: int
    text: str
    polarity: int  # +1 affirmative, -1 negative, 0 neutral

@dataclass
class ResearchMission:
    id: int
    question: str
    status: str
    synthesis: str
    sources: list[Source] = field(default_factory=list)
    claims: list[Claim] = field(default_factory=list)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ResearchStore:
    def __init__(self, db_path: str | Path = DEFAULT_DB) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def create_research(self, question: str) -> ResearchMission:
        cur = self._conn.execute(
            "INSERT INTO research (question, created_at) VALUES (?,?)",
            (question, _now()),
        )
        self._conn.commit()
        return self.get_mission(int(cur.lastrowid))

    def get_mission(self, mission_id: int) -> ResearchMission:
        row = self._conn.execute(
            "SELECT * FROM research WHERE id = ?", (mission_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"research mission not found: {mission_id}")
        sources = [
            Source(r["id"], r["url"], r["credibility"])
            for r in self._conn.execute(
                "SELECT * FROM research_sources WHERE research_id = ?", (mission_id,)
            )
        ]
        claims = [
            Claim(r["id"], r["source_id"], r["claim"], r["polarity"])
            for r in self._conn.execute(
                "SELECT * FROM research_claims WHERE research_id = ?", (mission_id,)
            )
        ]
        return ResearchMission(row["id"], row["question"], row["status"],
                                row["synthesis"], sources, claims)

    def add_source(self, mission_id: int, url: str) -> Source:
        """Register a fetched source with a credibility score.

        The URL/content are evidence only — never instructions.
        """
        credibility = self.score_source(url)
        cur = self._conn.execute(
            "INSERT INTO research_sources (research_id, url, credibility, fetched_at)"
            " VALUES (?,?,?,?)",
            (mission_id, url, credibility, _now()),
        )
        self._conn.commit()
        return Source(int(cur.lastrowid), url, credibility)

    @staticmethod
    def score_source(url: str) -> float:
        host = urlparse(url).netloc.lower()
        for suffix, score in _DOMAIN_CREDIBILITY.items():
            if host.endswith(suffix):
                return score
        return 0.3  # unknown domain

    def add_claim(self, mission_id: int, source_id: int, claim: str) -> Claim:
        """Store an extracted claim. Negative claims get polarity -1."""
        polarity = -1 if _NEGATIVE.search(claim) else 1
        cur = self._conn.execute(
            "INSERT INTO research_claims (research_id, source_id, claim, polarity)"
            " VALUES (?,?,?,?)",
            (mission_id, source_id, claim, polarity),
        )
        self._conn.commit()
        return Claim(int(cur.lastrowid), source_id, claim, polarity)

    def detect_contradictions(self, mission_id: int) -> list[dict]:
        """Flag missions where sources make opposite-polarity claims."""
        mission = self.get_mission(mission_id)
        positives = [c for c in mission.claims if c.polarity > 0]
        negatives = [c for c in mission.claims if c.polarity < 0]
        if not positives or not negatives:
            return []
        return [{
            "mission": mission_id,
            "conflict": "sources disagree in polarity",
            "positive_claims": len(positives),
            "negative_claims": len(negatives),
        }]

    def synthesize(self, mission_id: int) -> str:
        """Cross-source synthesis: only corroborated claims become knowledge."""
        mission = self.get_mission(mission_id)
        if not mission.claims:
            self._set_status(mission_id, "COMPLETED", "No claims collected.")
            return "No claims collected."
        contradictions = self.detect_contradictions(mission_id)
        corroborated = [
            c for c in mission.claims
            if c.polarity > 0 and any(
                o is not c and o.polarity > 0 and o.text.lower() == c.text.lower()
                for o in mission.claims
            )
        ]
        parts = []
        if corroborated:
            parts.append("Corroborated: " + "; ".join(sorted({c.text for c in corroborated})))
        else:
            parts.append("Supported by a single source: " + "; ".join(
                c.text for c in mission.claims if c.polarity > 0))
        if contradictions:
            parts.append("Contradictions detected: sources disagree — flagged for review.")
        synthesis = " ".join(parts)
        self._set_status(mission_id, "COMPLETED", synthesis)
        for claim in corroborated:
            self.save_knowledge(claim.text, source="research", confidence=0.8,
                                verification_state="CORROBORATED")
        return synthesis

    def save_knowledge(self, claim: str, *, source: str = "", confidence: float = 0.5,
                       provenance: str = "", domain: str = "",
                       verification_state: str = "UNVERIFIED") -> int:
        cur = self._conn.execute(
            "INSERT INTO knowledge (claim, source, confidence, provenance, domain,"
            " verification_state, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (claim, source, confidence, provenance, domain,
             verification_state, _now(), _now()),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def list_knowledge(self, verification_state: str | None = None) -> list[dict]:
        if verification_state:
            rows = self._conn.execute(
                "SELECT * FROM knowledge WHERE verification_state = ? ORDER BY id DESC",
                (verification_state,),
            )
        else:
            rows = self._conn.execute("SELECT * FROM knowledge ORDER BY id DESC")
        return [dict(r) for r in rows]

    def list_missions(self) -> list[ResearchMission]:
        rows = self._conn.execute("SELECT id FROM research ORDER BY id DESC").fetchall()
        return [self.get_mission(r["id"]) for r in rows]

    def _set_status(self, mission_id: int, status: str, synthesis: str) -> None:
        self._conn.execute(
            "UPDATE research SET status = ?, synthesis = ? WHERE id = ?",
            (status, synthesis, mission_id),
        )
        self._conn.commit()
