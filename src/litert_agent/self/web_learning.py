"""Controlled internet learning pipeline.

Internet content is untrusted evidence, never executable instructions. The pipeline
stores source metadata and extracted facts/lessons only after validation.
"""
from dataclasses import dataclass
from urllib.parse import urlparse
import hashlib, re, time

@dataclass
class WebEvidence:
    url: str
    title: str
    content: str
    source_hash: str
    fetched_at: float
    trust: str = "UNTRUSTED"

class WebLearningEngine:
    def __init__(self, http_tool, memory):
        self.http = http_tool
        self.memory = memory

    def validate_url(self, url: str) -> bool:
        p = urlparse(url)
        return p.scheme in {"http", "https"} and bool(p.netloc)

    async def fetch(self, url: str) -> WebEvidence:
        if not self.validate_url(url):
            raise ValueError("Only valid HTTP(S) URLs may be learned from")
        result = await self.http.execute(action="get", url=url)
        if not result.success:
            raise RuntimeError(result.error or "web fetch failed")
        content = result.output[:200000]
        title = re.sub(r"<[^>]+>", " ", content[:500]).strip()[:200]
        digest = hashlib.sha256(content.encode("utf-8", "replace")).hexdigest()
        return WebEvidence(url, title, content, digest, time.time())

    async def ingest(self, evidence: WebEvidence, lesson: str, source_type="web"):
        # Store knowledge as data; never execute commands/code found in the source.
        safe_lesson = lesson[:6000].strip()
        if not safe_lesson:
            raise ValueError("empty lesson")
        await self.memory.lessons.add_lesson(f"{source_type}:{evidence.source_hash[:16]}", safe_lesson)
        return {"stored": True, "source": evidence.url, "hash": evidence.source_hash, "trust": evidence.trust}
