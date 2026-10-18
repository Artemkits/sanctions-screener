"""FastAPI application: JSON API + single-page UI + printable escalation report."""
import os
import threading

import pycountry
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import audit, batch, report
from .config import BASE_DIR, REVIEW_THRESHOLD, WEAK_THRESHOLD
from .matcher import get_index, rebuild_index

STATIC = BASE_DIR / "app" / "static"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

app = FastAPI(title="Sanctions Screener", version="1.0",
              description="Transliteration-aware screening against EU, UN and OFAC sanctions lists (demo).")
app.mount("/static", StaticFiles(directory=STATIC), name="static")

_batches: dict[int, list] = {}


@app.on_event("startup")
def _warm_up():
    threading.Thread(target=get_index, daemon=True).start()


class SearchIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    birth: str = Field("", max_length=20)
    nationality: str = Field("", max_length=2)
    entity_type: str = Field("person", pattern="^(person|entity|any)$")
    show_weak: bool = True
    analyst: str = Field("", max_length=80)


class DecisionIn(BaseModel):
    search_id: int
    decision: str = Field(..., pattern="^(false_positive|escalation|freeze)$")
    comment: str = Field("", max_length=2000)
    analyst: str = Field("", max_length=80)
    entry_ids: list[int] = []


@app.get("/", include_in_schema=False)
def index_page():
    return FileResponse(STATIC / "index.html")


@app.get("/api/status")
def status():
    ix = get_index()
    return {"lists": ix.list_versions(), "index": {"built_at": ix.built_at, "seconds": ix.build_seconds,
                                                  "forms": len(ix.forms), "tokens": len(ix.vocab)}}


@app.get("/api/countries")
def countries():
    return sorted(({"code": c.alpha_2, "name": c.name} for c in pycountry.countries), key=lambda c: c["name"])


@app.post("/api/search")
def search(body: SearchIn):
    ix = get_index()
    res = ix.search(body.name, birth=body.birth, nationality=body.nationality.upper(),
                    entity_type=body.entity_type, min_score=WEAK_THRESHOLD if body.show_weak else REVIEW_THRESHOLD)
    counts = {s: sum(1 for r in res["results"] if r["status"] == s) for s in ("match", "review", "weak")}
    res["search_id"] = audit.log(
        "search", body.analyst,
        {"name": body.name, "birth": body.birth, "nationality": body.nationality, "entity_type": body.entity_type},
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
    if not audit.get(body.search_id):
        raise HTTPException(404, "search not found")
    log_id = audit.log("decision", body.analyst,
                       {"search_id": body.search_id, "entry_ids": body.entry_ids},
                       {"decision": body.decision, "comment": body.comment})
    return {"ok": True, "id": log_id}


@app.get("/report/{search_id}", response_class=HTMLResponse)
def report_page(search_id: int, lang: str = "pl"):
    rec = audit.get(search_id)
    if not rec or rec["action"] != "search":
        raise HTTPException(404, "search not found")
    return report.render(rec, audit.decisions_for(search_id), lang=lang if lang in ("pl", "en") else "pl")


@app.post("/api/batch")
async def batch_upload(file: UploadFile = File(...), entity_type: str = Form("person"), analyst: str = Form("")):
    raw = await file.read()
    if len(raw) > 2_000_000:
        raise HTTPException(413, "file too large (max 2 MB)")
    rows = batch.read_rows(raw)
    if not rows:
        raise HTTPException(400, "no names found in the CSV")
    results = batch.screen(get_index(), rows, entity_type=entity_type)
    summary = {s: sum(1 for r in results if r["status"] == s) for s in ("match", "review", "clear")}
    batch_id = audit.log("batch", analyst, {"file": file.filename, "rows": len(rows)}, summary)
    _batches[batch_id] = results
    return {"batch_id": batch_id, "rows": len(rows), "summary": summary, "results": results,
            "truncated": len(rows) >= batch.MAX_ROWS}


@app.get("/api/batch/{batch_id}.csv")
def batch_csv(batch_id: int):
    results = _batches.get(batch_id)
    if results is None:
        raise HTTPException(404, "batch expired — run it again")
    return PlainTextResponse(batch.to_csv(results), media_type="text/csv; charset=utf-8",
                             headers={"Content-Disposition": f'attachment; filename="screening_batch_{batch_id}.csv"'})


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


@app.get("/healthz", include_in_schema=False)
def healthz():
    return JSONResponse({"ok": True})
