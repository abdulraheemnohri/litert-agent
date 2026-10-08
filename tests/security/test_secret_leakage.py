"""Security tests: secret leakage (A-to-Z spec sections 35, 91).

Secrets must never survive into logs, ordinary memory, knowledge or UI text.
"""
from litert_agent.security.secrets import SecretSanitizer
from litert_agent.research.missions import ResearchStore
from litert_agent.self.learning import LearningEngine


def test_sanitizer_redacts_api_keys():
    text = "config: api_key = super-secret-value-123 and more text"
    sanitized = SecretSanitizer.sanitize(text)
    assert "super-secret-value-123" not in sanitized
    assert "[REDACTED_SECRET]" in sanitized


def test_sanitizer_idempotent_on_clean_text():
    assert SecretSanitizer.sanitize("hello world") == "hello world"


def test_research_knowledge_holds_no_secrets_after_sanitization(tmp_path):
    """Pipeline rule: sanitize BEFORE storing knowledge."""
    rs = ResearchStore(tmp_path / "sec.db")
    mission = rs.create_research("Where are credentials configured?")
    s1 = rs.add_source(mission.id, "https://a.example.org/p1")
    s2 = rs.add_source(mission.id, "https://b.example.edu/p2")
    raw = "api_key = hunter2-do-not-share"
    clean = SecretSanitizer.sanitize(raw)
    rs.add_claim(mission.id, s1.id, clean)
    rs.add_claim(mission.id, s2.id, clean)
    rs.synthesize(mission.id)
    for record in rs.list_knowledge():
        assert "hunter2" not in record["claim"]
        assert "[REDACTED_SECRET]" in record["claim"] or "api_key" not in record["claim"]
    rs.close()


def test_lessons_hold_no_secrets_after_sanitization(tmp_path):
    le = LearningEngine(tmp_path / "sec.db")
    le.record_experience("deploy", "failed", tools=["terminal"],
                         errors=[SecretSanitizer.sanitize("api_key = leak-me-now")])
    for lesson in le.list_lessons():
        assert "leak-me-now" not in lesson["lesson"]
    le.close()
