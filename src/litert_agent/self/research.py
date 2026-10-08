"""Bounded self-research, provenance, contradiction and knowledge-quality engine.

Research is evidence collection only: web content is untrusted data and is never
executed. Knowledge changes remain auditable and do not alter model weights,
security policy, or provider identity.
"""
from __future__ import annotations

import hashlib
import re
import time
import uuid
from dataclasses import asdict, dataclass
from urllib.parse import urlparse


@dataclass
class SourceRecord:
    id: str
    url: str
    source_hash: str
    title: str
    trust: str
    credibility: float
    fetched_at: float


@dataclass
class ResearchFinding:
    id: str
    mission_id: str
    source_id: str
    topic: str
    claim: str
    evidence: str
    confidence: float
    created_at: float


class ResearchEngine:
    """Local SQLite-backed research coordinator using the existing HTTP tool."""

    def __init__(self, db, http_tool, memory=None):
        self.db = db
        self.http = http_tool
        self.memory = memory

    @staticmethod
    def validate_url(url: str) -> bool:
        p = urlparse(url)
        return p.scheme in {"http", "https"} and bool(p.netloc)

    @staticmethod
    def credibility(url: str) -> float:
        host = urlparse(url).hostname or ""
        host = host.lower()
        if host.endswith(".gov") or host.endswith(".edu"):
            return 0.90
        if host.endswith(".org"):
            return 0.75
        if host.endswith(".com"):
            return 0.65
        return 0.50

    @staticmethod
    def normalize_claim(text: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip().lower()[:2000]

    async def fetch_source(self, url: str) -> SourceRecord:
        if not self.validate_url(url):
            raise ValueError("Only valid HTTP(S) URLs may be researched")
        result = await self.http.execute(action="get", url=url)
        if not result.success:
            raise RuntimeError(result.error or "research fetch failed")
        content = result.output[:200000]
        digest = hashlib.sha256(content.encode("utf-8", "replace")).hexdigest()
        title = re.sub(r"<[^>]+>", " ", content[:500]).strip()[:200]
        sid = str(uuid.uuid4())
        rec = SourceRecord(sid, url, digest, title, "UNTRUSTED", self.credibility(url), time.time())
        self.db.execute_write(
            "INSERT OR IGNORE INTO research_sources "
            "(id,url,source_hash,title,trust,credibility,fetched_at) VALUES (?,?,?,?,?,?,?)",
            (rec.id, rec.url, rec.source_hash, rec.title, rec.trust, rec.credibility, rec.fetched_at),
        )
        return rec

    async def ingest_claim(self, mission_id: str, source: SourceRecord, topic: str,
                           claim: str, evidence: str, confidence: float = 0.5) -> dict:
        claim = claim.strip()[:4000]
        evidence = evidence.strip()[:8000]
        if not claim:
            raise ValueError("claim is required")
        finding_id = str(uuid.uuid4())
        normalized = self.normalize_claim(claim)
        duplicate = self.db.execute_read(
            "SELECT id FROM research_findings WHERE normalized_claim = ? LIMIT 1", (normalized,)
        )
        status = "DUPLICATE" if duplicate else "NEW"
        self.db.execute_write(
            "INSERT INTO research_findings "
            "(id,mission_id,source_id,topic,claim,evidence,normalized_claim,confidence,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (finding_id, mission_id, source.id, topic[:500], claim, evidence,
             normalized, max(0.0, min(1.0, confidence)), time.time()),
        )
        self.db.execute_write(
            "UPDATE research_missions SET source_count = source_count + 1, updated_at=? WHERE id = ?",
            (time.time(), mission_id),
        )
        if self.memory and status == "NEW":
            await self.memory.lessons.add_lesson(
                f"research:{topic}:{source.source_hash[:16]}",
                f"{claim} | evidence: {evidence[:3000]}",
            )
        return {"id": finding_id, "status": status, "source": asdict(source)}

    def compare_claims(self, topic: str = "", limit: int = 100) -> list[dict]:
        rows = self.db.execute_read(
            "SELECT id,claim,evidence,confidence,source_id FROM research_findings "
            "WHERE topic LIKE ? ORDER BY created_at DESC LIMIT ?",
            (f"%{topic}%", limit),
        )
        findings = [{"id": r[0], "claim": r[1], "evidence": r[2], "confidence": r[3], "source_id": r[4]}
                    for r in rows]
        groups = {}
        for item in findings:
            key = self.normalize_claim(item["claim"])
            groups.setdefault(key, []).append(item)
        results = []
        for key, items in groups.items():
            contradictions = []
            for i, left in enumerate(items):
                for right in items[i + 1:]:
                    l = left["claim"].lower()
                    r = right["claim"].lower()
                    left_negative = " not " in (" " + l + " ")
                    right_negative = " not " in (" " + r + " ")
                    if left_negative != right_negative:
                        contradictions.append({"left": left["id"], "right": right["id"], "reason": "negation polarity"})
            results.append({"claim": key, "support": items, "contradiction_candidates": contradictions})
        return results

    def list_sources(self, limit: int = 50) -> list[dict]:
        rows = self.db.execute_read(
            "SELECT id,url,title,trust,credibility,fetched_at FROM research_sources "
            "ORDER BY fetched_at DESC LIMIT ?", (limit,))
        return [{"id":r[0],"url":r[1],"title":r[2],"trust":r[3],
                 "credibility":r[4],"fetched_at":r[5]} for r in rows]

    def list_findings(self, topic: str = "", limit: int = 100) -> list[dict]:
        rows = self.db.execute_read(
            "SELECT id,mission_id,source_id,topic,claim,evidence,confidence,created_at "
            "FROM research_findings WHERE topic LIKE ? ORDER BY created_at DESC LIMIT ?",
            (f"%{topic}%", limit),
        )
        return [{"id":r[0],"mission_id":r[1],"source_id":r[2],"topic":r[3],
                 "claim":r[4],"evidence":r[5],"confidence":r[6],"created_at":r[7]} for r in rows]

    def create_mission(self, topic: str, goal: str, urls: list[str] | None = None) -> dict:
        mid = str(uuid.uuid4())
        urls = urls or []
        for url in urls:
            if not self.validate_url(url):
                raise ValueError(f"Invalid research URL: {url}")
        now = time.time()
        self.db.execute_write(
            "INSERT INTO research_missions (id,topic,goal,status,source_count,created_at,updated_at) "
            "VALUES (?,?,?,?,?,?,?)", (mid, topic[:500], goal[:4000], "PENDING", 0, now, now)
        )
        for url in urls:
            self.db.execute_write(
                "INSERT OR IGNORE INTO research_mission_urls (mission_id,url,status) VALUES (?,?,?)",
                (mid, url, "PENDING"),
            )
        return {"id": mid, "topic": topic, "goal": goal, "status": "PENDING", "urls": urls}

    def finish_mission(self, mission_id: str, status: str = "COMPLETED") -> bool:
        allowed = {"PENDING","RUNNING","COMPLETED","FAILED","PAUSED","CANCELLED"}
        if status not in allowed:
            raise ValueError("invalid mission status")
        self.db.execute_write(
            "UPDATE research_missions SET status=?, updated_at=? WHERE id=?",
            (status, time.time(), mission_id),
        )
        return True

    def mission_urls(self, mission_id: str) -> list[dict]:
        rows = self.db.execute_read(
            "SELECT url,status,source_id,error FROM research_mission_urls "
            "WHERE mission_id=? ORDER BY url", (mission_id,)
        )
        return [{"url": r[0], "status": r[1], "source_id": r[2], "error": r[3]} for r in rows]

    async def collect_mission_sources(self, mission_id: str) -> dict:
        if not self.db.execute_read("SELECT id FROM research_missions WHERE id=?", (mission_id,)):
            raise KeyError(mission_id)
        self.finish_mission(mission_id, "RUNNING")
        collected, failed = 0, 0
        rows = self.db.execute_read(
            "SELECT url FROM research_mission_urls WHERE mission_id=? AND status IN ('PENDING','FAILED')",
            (mission_id,),
        )
        for (url,) in rows:
            try:
                source = await self.fetch_source(url)
                self.db.execute_write(
                    "UPDATE research_mission_urls SET status='FETCHED',source_id=?,error=NULL WHERE mission_id=? AND url=?",
                    (source.id, mission_id, url),
                )
                collected += 1
            except Exception as exc:
                self.db.execute_write(
                    "UPDATE research_mission_urls SET status='FAILED',error=? WHERE mission_id=? AND url=?",
                    (str(exc)[:2000], mission_id, url),
                )
                failed += 1
        self.finish_mission(mission_id, "COMPLETED" if failed == 0 else "PAUSED")
        return {"mission_id": mission_id, "collected": collected, "failed": failed, "urls": self.mission_urls(mission_id)}

    def list_missions(self, limit: int = 50) -> list[dict]:
        rows = self.db.execute_read(
            "SELECT id,topic,goal,status,source_count,created_at,updated_at FROM research_missions "
            "ORDER BY created_at DESC LIMIT ?", (limit,))
        return [{"id":r[0],"topic":r[1],"goal":r[2],"status":r[3],
                 "source_count":r[4],"created_at":r[5],"updated_at":r[6],
                 "urls": self.mission_urls(r[0])} for r in rows]
