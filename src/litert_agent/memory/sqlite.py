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
