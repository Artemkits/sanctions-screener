"""Audit log: who checked what and when, plus analyst decisions."""
import json
from datetime import datetime, timezone

from .db import dumps, session


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log(action: str, actor: str, query: dict, summary: dict, payload: dict | None = None) -> int:
    with session() as conn:
        cur = conn.execute(
            "INSERT INTO audit_log (ts, actor, action, query, summary, payload) VALUES (?,?,?,?,?,?)",
            (now(), (actor or "anonim")[:80], action, dumps(query), dumps(summary),
             dumps(payload) if payload is not None else None))
        return cur.lastrowid


def get(log_id: int) -> dict | None:
    with session() as conn:
        r = conn.execute("SELECT * FROM audit_log WHERE id = ?", (log_id,)).fetchone()
    if not r:
        return None
    d = dict(r)
    for k in ("query", "summary", "payload"):
        d[k] = json.loads(d[k]) if d[k] else None
    return d


def recent(limit: int = 100) -> list[dict]:
    with session() as conn:
        rows = conn.execute(
            "SELECT id, ts, actor, action, query, summary FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [{**dict(r), "query": json.loads(r["query"]), "summary": json.loads(r["summary"])} for r in rows]


def decisions_for(search_id: int) -> list[dict]:
    with session() as conn:
        rows = conn.execute(
            "SELECT id, ts, actor, query, summary FROM audit_log WHERE action = 'decision' "
            "AND json_extract(query, '$.search_id') = ? ORDER BY id", (search_id,)).fetchall()
    return [{**dict(r), "query": json.loads(r["query"]), "summary": json.loads(r["summary"])} for r in rows]
