import sqlite3

import pytest

from litert_agent.memory.sqlite import SCHEMA, DatabaseManager
from litert_agent.self.goals import GoalManager
from litert_agent.self.research import ResearchEngine


class Result:
    success = True
    output = "<title>Example</title> Evidence says the system works."
    error = None


class HTTP:
    async def execute(self, **kwargs):
        return Result()


@pytest.fixture
def db(tmp_path):
    manager = DatabaseManager(tmp_path / "agent.db")
    with sqlite3.connect(manager.db_path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()
    return manager


@pytest.mark.asyncio
async def test_research_provenance_duplicate_and_collection(db):
    engine = ResearchEngine(db, HTTP())
    mission = engine.create_mission(
        "test", "verify evidence",
        ["https://example.com", "https://example.org"],
    )
    result = await engine.collect_mission_sources(mission["id"])
    assert result["collected"] == 2
    assert all(item["status"] == "FETCHED" for item in result["urls"])

    source = await engine.fetch_source("https://example.com")
    first = await engine.ingest_claim(
        mission["id"], source, "test", "The system works", "evidence"
    )
    second = await engine.ingest_claim(
        mission["id"], source, "test", "The system works", "evidence"
    )
    assert first["status"] == "NEW"
    assert second["status"] == "DUPLICATE"
    assert source.trust == "UNTRUSTED"


def test_goals_dependencies_and_curiosity(db):
    goals = GoalManager(db)
    parent = goals.create("Parent", "Base work", "HIGH")
    child = goals.create("Child", "Dependent work", "NORMAL")
    goals.add_dependency(child["id"], parent["id"])
    assert goals.is_ready(child["id"]) is False

    goals.update(parent["id"], status="COMPLETED", progress=1.0)
    assert goals.is_ready(child["id"]) is True

    goals.enqueue_curiosity("SQLite", "Improve memory design")
    item = goals.pop_curiosity()
    assert item["topic"] == "SQLite"
    assert item["status"] == "CLAIMED"
    goals.complete_curiosity(item["id"])


def test_required_self_schema(db):
    names = {r[0] for r in db.execute_read(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}
    required = {
        "research_sources", "research_missions", "research_mission_urls",
        "research_findings", "self_goals", "goal_dependencies",
        "curiosity_queue", "knowledge_expiry", "self_skill_versions",
        "self_skill_quarantine",
    }
    assert required.issubset(names)


def test_research_url_validation():
    assert ResearchEngine.validate_url("https://example.com")
    assert not ResearchEngine.validate_url("file:///tmp/x")
