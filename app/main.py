"""FastAPI application: JSON API + single-page UI + printable escalation report."""
import os
import threading
import time
from contextlib import asynccontextmanager

import pycountry
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import audit, batch, report
from .config import BASE_DIR, MATCH_THRESHOLD, REVIEW_THRESHOLD, SOURCES, WEAK_THRESHOLD
from .db import connect
from .matcher import get_index, index_ready, rebuild_index
from .methodology import letter_table
from .translit import SYSTEM_LABELS

STATIC = BASE_DIR / "app" / "static"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
MAX_JOBS = 20


REFRESH_HOURS = float(os.getenv("AUTO_REFRESH_HOURS", "0") or 0)


def _refresh_loop():
    """Keep a long-running instance current: re-download the lists every AUTO_REFRESH_HOURS."""
    from .update import update
    while True:
        time.sleep(REFRESH_HOURS * 3600)
        try:
            update()
            rebuild_index()
        except Exception as exc:  # never kill the server because a source is down
            print("list refresh failed:", exc)


@asynccontextmanager
async def lifespan(_app):
    threading.Thread(target=get_index, daemon=True).start()   # build the index in the background
    if REFRESH_HOURS > 0:
        threading.Thread(target=_refresh_loop, daemon=True).start()
    yield


app = FastAPI(title="Sanctions Screener", version="1.1", lifespan=lifespan,
              description="Transliteration-aware screening against EU, UN and OFAC sanctions lists (demo).")
app.mount("/static", StaticFiles(directory=STATIC), name="static")

_jobs: dict[int, dict] = {}
_jobs_lock = threading.Lock()


class SearchIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    birth: str = Field("", max_length=20)
    nationality: str = Field("", max_length=2)
    entity_type: str = Field("person", pattern="^(person|entity|any)$")
    gender: str = Field("", pattern="^(|M|F)$")
    document: str = Field("", max_length=40)
    show_weak: bool = True
    sources: list[str] = Field(default_factory=list, max_length=10)
    min_score: float | None = Field(None, ge=0, le=100)
    limit: int = Field(50, ge=1, le=200)
    analyst: str = Field("", max_length=80)


class DecisionIn(BaseModel):
    search_id: int
    decision: str = Field(..., pattern="^(false_positive|escalation|freeze)$")
    comment: str = Field("", max_length=2000)
    analyst: str = Field("", max_length=80)
    entry_ids: list[int] = []


@app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
def index_page():
    return FileResponse(STATIC / "index.html")


def _meta_from_db() -> dict:
    conn = connect()
    rows = {r["source"]: dict(r) for r in conn.execute("SELECT * FROM source_meta") if r["source"] in SOURCES}
    conn.close()
    return {s: {k: rows.get(s, {}).get(k) for k in ("list_date", "fetched_at", "record_count", "alias_count", "status")}
            for s in SOURCES}


@app.get("/api/status")
def status():
    """List versions; answers immediately even while the index is still being built."""
    if not index_ready():
        return {"ready": False, "lists": _meta_from_db()}
    ix = get_index()
    return {"ready": True, "lists": ix.list_versions(),
            "index": {"built_at": ix.built_at, "seconds": ix.build_seconds, "forms": len(ix.forms),
                      "tokens": len(ix.vocab)},
            "thresholds": {"match": MATCH_THRESHOLD, "review": REVIEW_THRESHOLD, "weak": WEAK_THRESHOLD}}


@app.get("/api/lists")
def lists():
    ix = get_index()
    return {s: {**ix.list_versions()[s], **ix.stats.get(s, {}), "name": SOURCES[s]["name"],
                "label": SOURCES[s]["label"], "url": SOURCES[s]["url"], "info_url": SOURCES[s]["info_url"],
                "provider": SOURCES[s].get("provider", "official")}
            for s in SOURCES}


@app.get("/api/methodology")
def methodology():
    return {**letter_table(), "systems": SYSTEM_LABELS,
            "thresholds": {"match": MATCH_THRESHOLD, "review": REVIEW_THRESHOLD, "weak": WEAK_THRESHOLD}}


@app.get("/api/countries")
def countries():
    return sorted(({"code": c.alpha_2, "name": c.name} for c in pycountry.countries), key=lambda c: c["name"])


@app.post("/api/search")
def search(body: SearchIn):
    ix = get_index()
    min_score = body.min_score if body.min_score is not None else (WEAK_THRESHOLD if body.show_weak else REVIEW_THRESHOLD)
    res = ix.search(body.name, birth=body.birth, nationality=body.nationality.upper(), entity_type=body.entity_type,
                    min_score=min_score, limit=body.limit, gender=body.gender, document=body.document,
                    sources=[x for x in body.sources if x in SOURCES] or None)
    counts = {s: sum(1 for r in res["results"] if r["status"] == s) for s in ("match", "review", "weak")}
    res["search_id"] = audit.log(
        "search", body.analyst,
        {"name": body.name, "birth": body.birth, "nationality": body.nationality, "entity_type": body.entity_type,
         "gender": body.gender, "document": body.document, "sources": body.sources},
        {"top_score": res["results"][0]["score"] if res["results"] else None, **counts,
         "elapsed_ms": res["elapsed_ms"]},
        payload=res)
    return res


@app.get("/api/entry/{entry_id}")
def entry(entry_id: int):
    d = get_index().entry_detail(entry_id)
    if not d:
        raise HTTPException(404, "entry not found")
    return d


@app.post("/api/decision")
def decision(body: DecisionIn):
    rec = audit.get(body.search_id)
    if not rec or rec["action"] != "search":
        raise HTTPException(404, "search not found")
    log_id = audit.log("decision", body.analyst,
                       {"search_id": body.search_id, "entry_ids": body.entry_ids, "name": rec["query"].get("name")},
                       {"decision": body.decision, "comment": body.comment})
    return {"ok": True, "id": log_id}


@app.get("/report/{search_id}", response_class=HTMLResponse)
def report_page(search_id: int, lang: str = "pl"):
    rec = audit.get(search_id)
    if not rec or rec["action"] != "search":
        raise HTTPException(404, "search not found")
    return report.render(rec, audit.decisions_for(search_id), lang=lang if lang in ("pl", "en") else "pl")


# ---------------------------------------------------------------- batch (background job with progress)

def _run_batch(job_id: int):
    job = _jobs[job_id]
    ix = get_index()
    for i, row in enumerate(job["rows"]):
        job["results"].append(batch.screen_row(ix, row, job["entity_type"]))
        job["done"] = i + 1
    summary = batch.summarize(job["results"])
    job["summary"] = summary
    job["batch_id"] = audit.log("batch", job["analyst"], {"file": job["file"], "rows": len(job["rows"])}, summary)
    job["status"] = "done"
    job["elapsed_ms"] = round((time.time() - job["started"]) * 1000)


@app.post("/api/batch")
async def batch_upload(file: UploadFile = File(...), entity_type: str = Form("person"), analyst: str = Form("")):
    raw = await file.read()
    if len(raw) > 2_000_000:
        raise HTTPException(413, "file too large (max 2 MB)")
    rows, truncated = batch.read_rows(raw)
    if not rows:
        raise HTTPException(400, "no names found in the CSV")
    with _jobs_lock:
        job_id = max(_jobs, default=0) + 1
        _jobs[job_id] = {"id": job_id, "status": "running", "file": file.filename, "rows": rows, "done": 0,
                         "results": [], "entity_type": entity_type if entity_type in ("person", "entity", "any") else "person",
                         "analyst": analyst, "truncated": truncated, "started": time.time()}
        for old in sorted(_jobs)[:-MAX_JOBS]:
            _jobs.pop(old, None)
    threading.Thread(target=_run_batch, args=(job_id,), daemon=True).start()
    return {"job_id": job_id, "total": len(rows), "truncated": truncated}


@app.get("/api/batch/{job_id}.csv")
def batch_csv(job_id: int):
    job = _jobs.get(job_id)
    if not job or job["status"] != "done":
        raise HTTPException(404, "batch not ready or expired — run it again")
    return PlainTextResponse("﻿" + batch.to_csv(job["results"]), media_type="text/csv; charset=utf-8",
                             headers={"Content-Disposition": f'attachment; filename="screening_batch_{job_id}.csv"'})


@app.get("/api/batch/{job_id}")
def batch_status(job_id: int):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "batch expired — run it again")
    out = {k: job.get(k) for k in ("id", "status", "file", "done", "truncated", "summary", "elapsed_ms")}
    out["total"] = len(job["rows"])
    if job["status"] == "done":
        out["results"] = job["results"]
    return out


# ---------------------------------------------------------------- audit + admin

@app.get("/api/audit")
def audit_log(limit: int = 100):
    return audit.recent(min(max(limit, 1), 500))


@app.post("/api/admin/update")
def admin_update(request: Request):
    """Re-download the lists. Disabled unless ADMIN_TOKEN is configured."""
    if not ADMIN_TOKEN or request.headers.get("x-admin-token") != ADMIN_TOKEN:
        raise HTTPException(403, "updates are disabled on this instance")
    from .update import update
    result = update()
    rebuild_index()
    return result


@app.api_route("/healthz", methods=["GET", "HEAD"], include_in_schema=False)
def healthz():
    return JSONResponse({"ok": True, "ready": index_ready()})
