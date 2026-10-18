"""SQLite storage: one unified schema for all sanctions sources plus the audit log."""
import json
import sqlite3
from contextlib import contextmanager

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id            INTEGER PRIMARY KEY,
    source        TEXT NOT NULL,          -- EU | UN | OFAC
    source_id     TEXT NOT NULL,          -- id of the record in the source file
    entity_type   TEXT NOT NULL,          -- person | entity | vessel | aircraft
    primary_name  TEXT NOT NULL,
    birth_dates   TEXT NOT NULL DEFAULT '[]',   -- JSON list of {date, year, circa, from_year, to_year}
    nationalities TEXT NOT NULL DEFAULT '[]',   -- JSON list of {iso2, name}
    programs      TEXT NOT NULL DEFAULT '[]',   -- JSON list of program codes
    listed_on     TEXT,
    url           TEXT,
    remarks       TEXT,
    extra         TEXT NOT NULL DEFAULT '{}',   -- JSON: place of birth, gender, reference no., ...
    UNIQUE(source, source_id)
);
CREATE TABLE IF NOT EXISTS aliases (
    id        INTEGER PRIMARY KEY,
    entry_id  INTEGER NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
    name      TEXT NOT NULL,
    script    TEXT NOT NULL,              -- latin | cyrillic | arabic | greek | other
    lang      TEXT,
    quality   TEXT                        -- primary | strong | weak
);
CREATE INDEX IF NOT EXISTS idx_aliases_entry ON aliases(entry_id);
CREATE TABLE IF NOT EXISTS source_meta (
    source        TEXT PRIMARY KEY,
    fetched_at    TEXT,
    list_date     TEXT,
    record_count  INTEGER,
    alias_count   INTEGER,
    url           TEXT,
    status        TEXT,
    note          TEXT
);
CREATE TABLE IF NOT EXISTS audit_log (
    id         INTEGER PRIMARY KEY,
    ts         TEXT NOT NULL,
    actor      TEXT NOT NULL,
    action     TEXT NOT NULL,             -- search | batch | decision | telegram
    query      TEXT NOT NULL,             -- JSON
    summary    TEXT NOT NULL,             -- JSON
    payload    TEXT                       -- JSON (full results, used to rebuild reports)
);
"""


def connect(path=None) -> sqlite3.Connection:
    p = path or DB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.executescript(SCHEMA)
    return conn


@contextmanager
def session(path=None):
    conn = connect(path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)
