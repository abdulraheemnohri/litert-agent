"""SQLite Database schema and manager."""

import sqlite3
from pathlib import Path

from litert_agent.constants import DEFAULT_DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    category TEXT,
    content TEXT,
    importance REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS facts (
    id TEXT PRIMARY KEY,
    subject TEXT,
    predicate TEXT,
    object TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lessons (
    id TEXT PRIMARY KEY,
    context TEXT,
    lesson TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT,
    description TEXT,
    status TEXT,
    result TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS plans (
    id TEXT PRIMARY KEY,
    task_id TEXT,
    goal TEXT,
    steps TEXT,
    status TEXT
);

CREATE TABLE IF NOT EXISTS executions (
    id TEXT PRIMARY KEY,
    task_id TEXT,
    tool TEXT,
    args TEXT,
    result TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tool_calls (
    id TEXT PRIMARY KEY,
    tool_name TEXT,
    arguments TEXT,
    status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    event_type TEXT,
    payload TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS errors (
    id TEXT PRIMARY KEY,
    error_type TEXT,
    message TEXT,
    stacktrace TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE,
    description TEXT,
    code TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS checkpoints (
    id TEXT PRIMARY KEY,
    task_id TEXT,
    description TEXT,
    state_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS research_sources (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    title TEXT,
    trust TEXT NOT NULL,
    credibility REAL NOT NULL DEFAULT 0.5,
    fetched_at REAL NOT NULL,
    content TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS research_missions (
    id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    goal TEXT NOT NULL,
    status TEXT NOT NULL,
    source_count INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL,
    updated_at REAL
);

CREATE TABLE IF NOT EXISTS research_mission_urls (
    mission_id TEXT NOT NULL,
    url TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    source_id TEXT,
    error TEXT,
    PRIMARY KEY (mission_id, url)
);

CREATE TABLE IF NOT EXISTS research_findings (
    id TEXT PRIMARY KEY,
    mission_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    claim TEXT NOT NULL,
    evidence TEXT NOT NULL,
    normalized_claim TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 0.5,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS research_summaries (
    id TEXT PRIMARY KEY,
    mission_id TEXT NOT NULL,
    summary TEXT NOT NULL,
    claims_json TEXT NOT NULL,
    source_ids_json TEXT NOT NULL,
    model TEXT NOT NULL,
    created_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_research_findings_normalized
    ON research_findings(normalized_claim);

CREATE INDEX IF NOT EXISTS idx_research_findings_topic
    ON research_findings(topic);

CREATE INDEX IF NOT EXISTS idx_research_summaries_mission
    ON research_summaries(mission_id, created_at);

CREATE TABLE IF NOT EXISTS self_goals (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL,
    parent_id TEXT,
    goal_type TEXT NOT NULL,
    progress REAL NOT NULL DEFAULT 0.0,
    created_at REAL NOT NULL,
    updated_at REAL
);

CREATE TABLE IF NOT EXISTS goal_dependencies (
    goal_id TEXT NOT NULL,
    depends_on_goal_id TEXT NOT NULL,
    PRIMARY KEY (goal_id, depends_on_goal_id)
);

CREATE TABLE IF NOT EXISTS curiosity_queue (
    id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    reason TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at REAL NOT NULL,
    claimed_at REAL,
    completed_at REAL
);

CREATE INDEX IF NOT EXISTS idx_curiosity_pending
    ON curiosity_queue(status, priority, created_at);

CREATE TABLE IF NOT EXISTS knowledge_expiry (
    id TEXT PRIMARY KEY,
    memory_type TEXT NOT NULL,
    memory_key TEXT NOT NULL,
    last_verified REAL NOT NULL,
    expires_after_seconds REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'FRESH',
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS self_skill_versions (
    id TEXT PRIMARY KEY,
    skill_name TEXT NOT NULL,
    version TEXT NOT NULL,
    skill_json TEXT NOT NULL,
    created_at REAL NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS self_skill_quarantine (
    skill_name TEXT PRIMARY KEY,
    reason TEXT NOT NULL,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS research (
    id TEXT PRIMARY KEY,
    topic TEXT,
    findings TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

class DatabaseManager:
    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def init_db(self):
        with sqlite3.connect(self.db_path) as db:
            db.executescript(SCHEMA)
            columns = {row[1] for row in db.execute("PRAGMA table_info(research_sources)")}
            if "content" not in columns:
                db.execute("ALTER TABLE research_sources ADD COLUMN content TEXT NOT NULL DEFAULT ''")
            db.commit()

    def execute_write(self, query: str, params: tuple = ()):
        with sqlite3.connect(self.db_path) as db:
            cursor = db.cursor()
            cursor.execute(query, params)
            db.commit()
            return cursor.lastrowid

    def execute_read(self, query: str, params: tuple = ()):
        with sqlite3.connect(self.db_path) as db:
            cursor = db.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
