"""Telegram bot: /check Сергій Щербина 1975 → top-3 hits with status.

Run:  TELEGRAM_BOT_TOKEN=... python -m app.telegram_bot
Uses long polling against the Bot API directly (no extra dependencies).
"""
import re
import time

import httpx

from . import audit
from .config import REVIEW_THRESHOLD, SOURCES, TELEGRAM_BOT_TOKEN
from .matcher import get_index

API = "https://api.telegram.org/bot{token}/{method}"
STATUS = {"match": "TRAFIENIE", "review": "DO WERYFIKACJI", "weak": "słabe"}
HELP = ("Sanctions Screener (demo)\n\n"
        "/check Imię Nazwisko [rok lub data urodzenia] [kraj ISO2]\n"
        "np. /check Сергій Щербина 1975\n     /check Siergiej Ławrow 1950 RU\n\n"
        "Narzędzie demonstracyjne. Nie stanowi podstawy do decyzji compliance.")


def parse_check(text: str) -> tuple[str, str, str]:
    """'/check Name Surname 1975 UA' → (name, birth, nationality)."""
    body = re.sub(r"^/check(@\w+)?\s*", "", text.strip(), flags=re.I)
    birth = nat = ""
    m = re.search(r"\s(\d{1,2}[./-]\d{1,2}[./-]\d{4}|\d{4}-\d{2}-\d{2}|\d{4})\b", " " + body)
    if m:
        birth = m.group(1)
        body = (" " + body).replace(m.group(0), " ").strip()
    m = re.search(r"\s([A-Z]{2})$", " " + body)
    if m:
        nat = m.group(1)
        body = body[: -2].strip()
    return body.strip(), birth, nat


def format_reply(res: dict) -> str:
    hits = [r for r in res["results"] if r["score"] >= REVIEW_THRESHOLD][:3]
    lines = [f"Zapytanie: {res['query']}" + (f", ur. {res['birth']}" if res.get("birth") else "")]
    lines.append(f"Sprawdzono {res['combinations']} kombinacji wariantów w {res['elapsed_ms']} ms")
    if not hits:
        lines.append("\nBrak trafień (próg 75) na listach UE / ONZ / OFAC.")
    for i, r in enumerate(hits, 1):
        tok = "; ".join(f"{x['query_token']}→{x.get('variant') or '?'}"
                        for x in r["explanation"]["tokens"] if not x.get("ignored"))
        dob = ", ".join(b.get("date") or str(b.get("year") or "") for b in r["birth_dates"][:2])
        lines.append(f"\n{i}. {STATUS[r['status']]} {r['score']:.0f}/100 — {r['primary_name']}\n"
                     f"   lista: {SOURCES[r['source']]['label']} ({', '.join(r['programs'][:3])})"
                     + (f", ur. {dob}" if dob else "") +
                     f"\n   alias: {r['matched_alias']}\n   warianty: {tok}")
        bad = [f["text"] for f in r["explanation"]["factors"] if f.get("ok") is False]
        if bad:
            lines.append("   uwaga: " + "; ".join(bad))
    lines.append("\nNarzędzie demonstracyjne. Nie stanowi podstawy do decyzji compliance.")
    return "\n".join(lines)


def handle(text: str, user: str) -> str:
    if not text.lower().startswith("/check"):
        return HELP
    name, birth, nat = parse_check(text)
    if not name:
        return HELP
    res = get_index().search(name, birth=birth, nationality=nat, entity_type="any", limit=10, min_score=REVIEW_THRESHOLD)
    audit.log("telegram", f"tg:{user}", {"name": name, "birth": birth, "nationality": nat},
              {"top_score": res["results"][0]["score"] if res["results"] else None,
               "match": sum(r["status"] == "match" for r in res["results"]),
               "review": sum(r["status"] == "review" for r in res["results"])})
    return format_reply(res)


def main():
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN (see .env.example)")
    get_index()
    offset = 0
    with httpx.Client(timeout=40) as client:
        print("bot started")
        while True:
            try:
                r = client.get(API.format(token=TELEGRAM_BOT_TOKEN, method="getUpdates"),
                               params={"timeout": 30, "offset": offset})
                for upd in r.json().get("result", []):
                    offset = upd["update_id"] + 1
                    msg = upd.get("message") or {}
                    if not msg.get("text"):
                        continue
                    user = (msg.get("from") or {}).get("username") or str((msg.get("from") or {}).get("id"))
                    client.post(API.format(token=TELEGRAM_BOT_TOKEN, method="sendMessage"),
                                json={"chat_id": msg["chat"]["id"], "text": handle(msg["text"], user)[:4000]})
            except httpx.HTTPError as exc:
                print("telegram error:", exc)
                time.sleep(5)


if __name__ == "__main__":
    main()
