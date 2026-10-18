"""Download the official lists and (re)load them into SQLite.

Usage:  python -m app.update            # all sources
        python -m app.update EU OFAC    # selected sources
        python -m app.update --offline  # re-parse files already in data/raw
"""
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

from .config import DATA_DIR, SOURCES
from .db import dumps, session
from .sources import eu, ofac, un
from .text import detect_script

PARSERS = {"EU": eu.parse, "UN": un.parse, "OFAC": ofac.parse}
RAW_DIR = DATA_DIR / "raw"


def download(source: str) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    target = RAW_DIR / f"{source.lower()}.xml"
    tmp = target.with_suffix(".part")
    headers = {"User-Agent": "sanctions-screener-demo/1.0 (+https://github.com)"}
    with httpx.stream("GET", SOURCES[source]["url"], headers=headers, timeout=180, follow_redirects=True) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_bytes(1 << 16):
                f.write(chunk)
    tmp.replace(target)
    return target


def _dedupe_births(births: list) -> list:
    seen, out = set(), []
    for b in births:
        key = (b.get("date"), b.get("year"), b.get("from_year"), b.get("to_year"))
        if key not in seen:
            seen.add(key)
            out.append(b)
    return out


def load(source: str, path) -> tuple[int, int, str]:
    result = PARSERS[source](path)
    if not result.entries:
        raise RuntimeError(f"{source}: parser returned 0 entries")
    n_alias = 0
    with session() as conn:
        conn.execute("DELETE FROM entries WHERE source = ?", (source,))
        for e in result.entries:
            e.birth_dates = _dedupe_births(e.birth_dates)
            cur = conn.execute(
                """INSERT OR IGNORE INTO entries (source, source_id, entity_type, primary_name, birth_dates,
                   nationalities, programs, listed_on, url, remarks, extra)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (e.source, e.source_id, e.entity_type, e.primary_name, dumps(e.birth_dates),
                 dumps(e.nationalities), dumps(e.programs), e.listed_on, e.url, e.remarks, dumps(e.extra)),
            )
            if not cur.rowcount:
                continue
            rows = [(cur.lastrowid, a.name, detect_script(a.name), a.lang, a.quality) for a in e.aliases]
            conn.executemany("INSERT INTO aliases (entry_id, name, script, lang, quality) VALUES (?,?,?,?,?)", rows)
            n_alias += len(rows)
    return len(result.entries), n_alias, result.list_date


def set_meta(source, **kw):
    with session() as conn:
        conn.execute("INSERT OR IGNORE INTO source_meta (source) VALUES (?)", (source,))
        sets = ", ".join(f"{k} = ?" for k in kw)
        conn.execute(f"UPDATE source_meta SET {sets} WHERE source = ?", (*kw.values(), source))


def update(sources=None, offline=False) -> dict:
    report = {}
    for src in sources or list(SOURCES):
        t0 = time.time()
        try:
            path = RAW_DIR / f"{src.lower()}.xml" if offline else download(src)
            n, na, list_date = load(src, path)
            set_meta(src, fetched_at=datetime.now(UTC).isoformat(timespec="seconds"),
                     list_date=list_date, record_count=n, alias_count=na,
                     url=SOURCES[src]["url"], status="ok", note="")
            report[src] = f"ok: {n} records, {na} aliases, list date {list_date} ({time.time() - t0:.1f}s)"
        except Exception as exc:  # keep the previous data if a source fails
            set_meta(src, status="error", note=str(exc)[:500])
            report[src] = f"ERROR: {exc}"
    return report


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    for k, v in update([a.upper() for a in args] or None, offline="--offline" in sys.argv).items():
        print(f"{k:5} {v}")
