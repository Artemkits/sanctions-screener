"""End-to-end API tests on a temporary database."""
import time

import pytest
from fastapi.testclient import TestClient

import app.db
import app.matcher as matcher
from app.main import app as fastapi_app


@pytest.fixture(scope="module")
def client(db_conn, tmp_path_factory):
    path = db_conn.execute("PRAGMA database_list").fetchone()["file"]
    old = app.db.DB_PATH
    app.db.DB_PATH = type(old)(path)
    matcher._index = matcher.Index().build(db_conn)
    with TestClient(fastapi_app) as c:
        yield c
    app.db.DB_PATH = old
    matcher._index = None


def test_status_and_lists(client):
    s = client.get("/api/status").json()
    assert s["ready"] and s["lists"]["EU"]["list_date"] == "2026-10-15"
    lists = client.get("/api/lists").json()
    assert lists["OFAC"]["entries"] == 4 and "by_type" in lists["OFAC"]


def test_search_report_decision_flow(client):
    r = client.post("/api/search", json={"name": "Сергій Щербина", "birth": "1975", "analyst": "tester"}).json()
    assert r["results"][0]["status"] == "match" and r["search_id"]
    page = client.get(f"/report/{r['search_id']}")
    assert page.status_code == 200 and "Сергій Щербина" in page.text and "KMU 2010" in page.text
    d = client.post("/api/decision", json={"search_id": r["search_id"], "decision": "escalation",
                                           "comment": "same DOB", "analyst": "tester"})
    assert d.status_code == 200
    page = client.get(f"/report/{r['search_id']}?lang=en")
    assert "Escalate to Compliance Officer" in page.text and "same DOB" in page.text
    log = client.get("/api/audit").json()
    assert {"search", "decision"} <= {x["action"] for x in log}


def test_english_factor_texts(client):
    r = client.post("/api/search", json={"name": "Юрий Ковальчук", "birth": "1984"}).json()
    f = r["results"][0]["explanation"]["factors"][0]
    assert f["ok"] is False and "false positive" in f["text_en"]


def test_validation_and_errors(client):
    assert client.post("/api/search", json={"name": ""}).status_code == 422
    assert client.post("/api/decision", json={"search_id": 999999, "decision": "freeze"}).status_code == 404
    assert client.get("/report/999999").status_code == 404
    assert client.get("/api/entry/999999").status_code == 404
    assert client.post("/api/admin/update").status_code == 403


def test_entry_detail(client):
    r = client.post("/api/search", json={"name": "Sergey Lavrov"}).json()
    d = client.get(f"/api/entry/{r['results'][0]['entry_id']}").json()
    assert d["source"] == "UN" and len(d["aliases"]) == 2


def test_batch_job(client):
    csv = "imie;nazwisko;data_urodzenia\nSiergiej;Ławrow;1950\nJan;Kowalski;1985\n".encode()
    job = client.post("/api/batch", files={"file": ("k.csv", csv, "text/csv")}, data={"entity_type": "person"}).json()
    assert job["total"] == 2
    for _ in range(100):
        st = client.get(f"/api/batch/{job['job_id']}").json()
        if st["status"] == "done":
            break
        time.sleep(0.05)
    assert st["status"] == "done" and st["summary"] == {"match": 1, "review": 0, "clear": 1}
    out = client.get(f"/api/batch/{job['job_id']}.csv")
    assert out.status_code == 200 and "LAVROV" in out.text


def test_methodology_table(client):
    m = client.get("/api/methodology").json()
    rows = {r["letter"]: r for r in m["rows"]}
    assert rows["щ"]["cells"]["PL_RU"][0]["latin"] == "szcz"
    assert rows["г"]["cells"]["UA_KMU2010"][0]["latin"] == "h"


def test_static_pages(client):
    assert client.get("/").status_code == 200
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/healthz").json()["ok"]


def test_head_requests(client):
    assert client.head("/").status_code == 200
    assert client.head("/healthz").status_code == 200
