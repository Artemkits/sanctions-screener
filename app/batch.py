"""Batch screening of a CSV file."""
import csv
import io

from .config import REVIEW_THRESHOLD

NAME_COLUMNS = ("name", "full_name", "fullname", "imie_nazwisko", "imię i nazwisko", "imie i nazwisko",
                "nazwa", "имя", "фио", "client", "klient")
FIRST_COLUMNS = ("first_name", "firstname", "imie", "imię", "given_name")
LAST_COLUMNS = ("last_name", "lastname", "nazwisko", "surname", "family_name")
BIRTH_COLUMNS = ("birth", "dob", "birth_date", "date_of_birth", "data_urodzenia", "rok_urodzenia", "year")
NAT_COLUMNS = ("nationality", "citizenship", "obywatelstwo", "country")
MAX_ROWS = 300


def _find(header, candidates):
    low = {h.strip().lower(): h for h in header}
    for c in candidates:
        if c in low:
            return low[c]
    return None


def read_rows(raw: bytes) -> tuple[list[dict], bool]:
    """→ (rows, truncated). Accepts comma, semicolon or tab separated files with a header."""
    text = raw.decode("utf-8-sig", errors="replace")
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    header = reader.fieldnames or []
    name_c, first_c, last_c = _find(header, NAME_COLUMNS), _find(header, FIRST_COLUMNS), _find(header, LAST_COLUMNS)
    birth_c, nat_c = _find(header, BIRTH_COLUMNS), _find(header, NAT_COLUMNS)
    if not name_c and not last_c:
        name_c = header[0] if header else None     # fall back to the first column
    rows, truncated = [], False
    for i, r in enumerate(reader):
        if len(rows) >= MAX_ROWS:
            truncated = True
            break
        name = (r.get(name_c) or "").strip() if name_c else \
            " ".join(x for x in ((r.get(first_c) or "").strip() if first_c else "", (r.get(last_c) or "").strip()) if x)
        if not name:
            continue
        rows.append({"row": i + 1, "name": name,
                     "birth": (r.get(birth_c) or "").strip() if birth_c else "",
                     "nationality": (r.get(nat_c) or "").strip().upper()[:2] if nat_c else ""})
    return rows, truncated


def screen_row(index, r: dict, entity_type: str = "person") -> dict:
    res = index.search(r["name"], birth=r["birth"], nationality=r["nationality"], entity_type=entity_type,
                       limit=3, min_score=REVIEW_THRESHOLD)
    top = res["results"]
    best = top[0] if top else None
    return {**r,
            "status": best["status"] if best else "clear",
            "score": best["score"] if best else None,
            "hits": [{"score": h["score"], "status": h["status"], "source": h["source_label"],
                      "primary_name": h["primary_name"], "matched_alias": h["matched_alias"],
                      "programs": h["programs"], "url": h["url"], "entry_id": h["entry_id"],
                      "conflicts": [f["text_en"] for f in h["explanation"]["factors"] if f.get("ok") is False]}
                     for h in top]}


def screen(index, rows: list[dict], entity_type: str = "person") -> list[dict]:
    return [screen_row(index, r, entity_type) for r in rows]


def summarize(results: list[dict]) -> dict:
    return {s: sum(1 for r in results if r["status"] == s) for s in ("match", "review", "clear")}


def to_csv(results: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["row", "name", "birth", "nationality", "status", "score", "list", "listed_name", "matched_alias",
                "programs", "conflicts", "url", "other_hits"])
    for r in results:
        h = r["hits"][0] if r["hits"] else {}
        w.writerow([r["row"], r["name"], r["birth"], r["nationality"], r["status"], r["score"] or "",
                    h.get("source", ""), h.get("primary_name", ""), h.get("matched_alias", ""),
                    "; ".join(h.get("programs", [])), "; ".join(h.get("conflicts", [])), h.get("url", ""), len(r["hits"]) - 1 if r["hits"] else 0])
    return buf.getvalue()
