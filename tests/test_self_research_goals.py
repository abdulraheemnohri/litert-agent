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
async def test_research_provenance_and_duplicate(db):
    engine = ResearchEngine(db, HTTP())
    mission = engine.create_mission("test", "verify evidence", ["https://example.com"])
    source = await engine.fetch_source("https://example.com")
    first = await engine.ingest_claim(mission["id"], source, "test", "The system works", "evidence")
    second = await engine.ingest_claim(mission["id"], source, "test", "The system works", "evidence")
    assert first["status"] == "NEW"
    assert second["status"] == "DUPLICATE"
    assert source.trust == "UNTRUSTED"


def test_goals_and_curiosity(db):
    goals = GoalManager(db)
    goal = goals.create("Learn", "Research a topic", "HIGH")
    assert goal["status"] == "PENDING"
    goals.update(goal["id"], status="ACTIVE", progress=0.5)
    assert goals.get(goal["id"])["progress"] == 0.5
    goals.enqueue_curiosity("SQLite", "Improve memory design")
    assert goals.pop_curiosity()["topic"] == "SQLite"


def test_research_url_validation():
    assert ResearchEngine.validate_url("https://example.com")
    assert not ResearchEngine.validate_url("file:///tmp/x")
