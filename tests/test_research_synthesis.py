import pytest

from litert_agent.self.research_synthesis import ResearchSynthesizer


class FakeDB:
    def __init__(self):
        self.writes = []

    def execute_read(self, query, params=()):
        if "SELECT topic,goal" in query:
            return [("python", "verify claims")]
        if "research_mission_urls" in query:
            return [("s1", "https://example.org", "Example", 0.75, "evidence text")]
        return []

    def execute_write(self, query, params=()):
        self.writes.append((query, params))


class FakeResponse:
    type = "final"
    content = '{"summary":"verified","claims":[{"claim":"A","evidence":"E","confidence":0.9,"source_index":1}],"open_questions":[],"contradictions":[]}'


class FakeProvider:
    discovery_info = {"executable": "litert-lm"}

    async def generate(self, prompt, system_prompt=None):
        return FakeResponse()


class FakeResearch:
    async def ingest_claim(self, *args):
        return {"status": "NEW"}


@pytest.mark.asyncio
async def test_synthesize_uses_litert_provider():
    db = FakeDB()
    engine = ResearchSynthesizer(db, FakeProvider(), FakeResearch())
    result = await engine.synthesize("m1")
    assert result["summary"] == "verified"
    assert result["claims"][0]["status"] == "NEW"
    assert db.writes


def test_parse_json():
    value = ResearchSynthesizer.parse_json('{"summary":"ok"}')
    assert value["summary"] == "ok"
