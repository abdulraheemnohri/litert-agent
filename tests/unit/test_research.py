"""Tests for the research store: credibility, contradictions, synthesis."""
from litert_agent.research.missions import ResearchStore


def test_source_credibility(tmp_path):
    rs = ResearchStore(tmp_path / "a.db")
    assert rs.score_source("https://example.edu/x") > rs.score_source("https://blog.example.com/x")
    rs.close()


def test_contradiction_detection(tmp_path):
    rs = ResearchStore(tmp_path / "a.db")
    m = rs.create_research("Is X supported?")
    s1 = rs.add_source(m.id, "https://a.example.org/p1")
    s2 = rs.add_source(m.id, "https://b.example.edu/p2")
    rs.add_claim(m.id, s1.id, "X is supported")
    rs.add_claim(m.id, s2.id, "X is not supported")
    contradictions = rs.detect_contradictions(m.id)
    assert contradictions and contradictions[0]["negative_claims"] == 1
    rs.close()


def test_synthesis_saves_corroborated_knowledge(tmp_path):
    rs = ResearchStore(tmp_path / "a.db")
    m = rs.create_research("Best test runner?")
    s1 = rs.add_source(m.id, "https://a.example.org/p1")
    s2 = rs.add_source(m.id, "https://b.example.edu/p2")
    rs.add_claim(m.id, s1.id, "pytest is widely used")
    rs.add_claim(m.id, s2.id, "pytest is widely used")
    synthesis = rs.synthesize(m.id)
    assert "Corroborated" in synthesis
    knowledge = rs.list_knowledge("CORROBORATED")
    assert knowledge and knowledge[0]["claim"] == "pytest is widely used"
    rs.close()
