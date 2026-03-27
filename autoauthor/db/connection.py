"""autoauthor/db/connection.py — SQLite 연결 관리 (WAL 모드)"""
from typing import Optional, Union
import sqlite3
import os
from pathlib import Path

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -32768;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS contents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    normalized_title TEXT NOT NULL UNIQUE,
    content_type TEXT DEFAULT 'movie',
    tmdb_id INTEGER,
    watcha_id TEXT,
    metadata TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_contents_norm ON contents(normalized_title);

CREATE TABLE IF NOT EXISTS trend_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL,
    source TEXT NOT NULL,
    rank INTEGER,
    score REAL NOT NULL,
    metadata TEXT,
    collected_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (content_id) REFERENCES contents(id)
);
CREATE INDEX IF NOT EXISTS idx_trend_cs ON trend_snapshots(content_id, source, collected_at);

CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    normalized_keyword TEXT NOT NULL UNIQUE,
    content_id INTEGER,
    search_intent TEXT DEFAULT 'exploratory',
    first_seen_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (content_id) REFERENCES contents(id)
);

CREATE TABLE IF NOT EXISTS keyword_analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_id INTEGER NOT NULL,
    blog_competition INTEGER DEFAULT -1,
    view_competition INTEGER DEFAULT -1,
    opportunity_score REAL DEFAULT 0,
    saturation_grade TEXT,
    trend_grade TEXT,
    has_demand INTEGER DEFAULT 0,
    analyzed_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (keyword_id) REFERENCES keywords(id)
);
CREATE INDEX IF NOT EXISTS idx_ka_kd ON keyword_analyses(keyword_id, analyzed_at);

CREATE TABLE IF NOT EXISTS content_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER,
    plan_type TEXT DEFAULT 'blog',
    title TEXT NOT NULL,
    structure TEXT NOT NULL,
    target_keywords TEXT,
    ai_model TEXT,
    priority TEXT DEFAULT 'normal',
    status TEXT DEFAULT 'draft',
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (content_id) REFERENCES contents(id)
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mode TEXT NOT NULL,
    category TEXT DEFAULT 'movie',
    source_coverage TEXT,
    contents_found INTEGER DEFAULT 0,
    keywords_analyzed INTEGER DEFAULT 0,
    plans_generated INTEGER DEFAULT 0,
    duration_seconds REAL,
    status TEXT DEFAULT 'running',
    error_message TEXT,
    started_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT
);
"""

_db_path: str = "data/autoauthor.db"
_connection: Optional[sqlite3.Connection] = None


def init_db(db_path: Optional[str] = None) -> sqlite3.Connection:
    global _db_path, _connection
    if db_path:
        _db_path = db_path
    os.makedirs(os.path.dirname(_db_path) or ".", exist_ok=True)
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    _connection = conn
    return conn


def get_db() -> sqlite3.Connection:
    global _connection
    if _connection is None:
        _connection = init_db()
    return _connection
