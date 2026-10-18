"""Printable escalation report (screening alert → review → decision)."""
from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

from .config import SOURCES
from .translit import SYSTEM_LABELS, SYSTEM_LABELS_EN

T = {
    "pl": {
        "title": "Raport do eskalacji — screening sankcyjny", "id": "Nr raportu", "checked_at": "Data sprawdzenia",
        "analyst": "Analityk", "subject": "Sprawdzany podmiot", "name": "Imię i nazwisko / nazwa",
        "birth": "Data urodzenia", "nat": "Obywatelstwo", "type": "Typ", "lists": "Sprawdzone listy",
        "list": "Lista", "version": "Wersja listy", "records": "Rekordów", "fetched": "Pobrano",
        "variants": "Sprawdzone warianty transliteracji", "combos": "Liczba sprawdzonych kombinacji",
        "results": "Wyniki", "score": "Wynik", "status": "Status", "listed": "Nazwa na liście",
        "alias": "Dopasowany alias", "src": "Źródło", "program": "Program sankcji", "dob": "Data ur. (lista)",
        "link": "Link", "none": "Brak trafień powyżej progu.", "why": "Uzasadnienie dopasowania",
        "decision": "Decyzja analityka", "fp": "False positive — brak tożsamości", "esc": "Eskalacja do Compliance Officer",
        "freeze": "Zamrożenie środków / wstrzymanie transakcji", "comment": "Komentarz / uzasadnienie",
        "save": "Zapisz decyzję w dzienniku", "print": "Drukuj / zapisz jako PDF", "sign": "Podpis analityka",
        "prev": "Zarejestrowane decyzje", "person": "osoba fizyczna", "entity": "podmiot", "any": "dowolny",
        "match": "Trafienie", "review": "Do weryfikacji", "weak": "Słabe",
        "disclaimer": "Narzędzie demonstracyjne. Nie stanowi podstawy do decyzji compliance. Dane: oficjalne listy UE, ONZ i OFAC; listy PL MSWiA, UK i UA przez OpenSanctions (CC BY-NC 4.0).",
        "saved": "Decyzja zapisana w dzienniku audytu.", "choose": "Wybierz decyzję.",
        "token": "Token zapytania", "variant": "Użyty wariant", "system": "System", "sim": "Podobieństwo",
        "factors": "Czynniki dodatkowe", "surname": "nazwisko", "rec": "Rekomendacja systemu", "gender": "Płeć", "doc": "Nr dokumentu", "inferred": "(wywnioskowana)",
        "rec_match": "możliwe trafienie — eskalacja do Compliance Officer przed kontynuacją relacji",
        "rec_review": "wymagana weryfikacja analityka (porównanie danych identyfikacyjnych)",
        "rec_clear": "brak trafień powyżej progu 75 — brak podstaw do eskalacji",
        "below": "Najbliżsi kandydaci poniżej progu (do wglądu, nie wymagają działania)",
    },
    "en": {
        "title": "Escalation report — sanctions screening", "id": "Report no.", "checked_at": "Checked at",
        "analyst": "Analyst", "subject": "Screened subject", "name": "Name", "birth": "Date of birth",
        "nat": "Nationality", "type": "Type", "lists": "Lists checked", "list": "List", "version": "List version",
        "records": "Records", "fetched": "Downloaded", "variants": "Transliteration variants checked",
        "combos": "Combinations checked", "results": "Results", "score": "Score", "status": "Status",
        "listed": "Listed name", "alias": "Matched alias", "src": "Source", "program": "Sanctions programme",
        "dob": "DOB (list)", "link": "Link", "none": "No hits above the threshold.", "why": "Match rationale",
        "decision": "Analyst decision", "fp": "False positive — not the same person", "esc": "Escalate to Compliance Officer",
        "freeze": "Freeze funds / hold transaction", "comment": "Comment / rationale", "save": "Save decision to audit log",
        "print": "Print / save as PDF", "sign": "Analyst signature", "prev": "Recorded decisions",
        "person": "individual", "entity": "entity", "any": "any", "match": "Possible match", "review": "Review",
        "weak": "Weak", "disclaimer": "Demo tool. Not a basis for compliance decisions. Data: official EU, UN and OFAC lists; PL MSWiA, UK and UA lists via OpenSanctions (CC BY-NC 4.0).",
        "saved": "Decision saved to the audit log.", "choose": "Choose a decision.", "token": "Query token",
        "variant": "Variant used", "system": "System", "sim": "Similarity", "factors": "Additional factors",
        "surname": "surname", "rec": "System recommendation", "gender": "Gender", "doc": "Document no.", "inferred": "(inferred)",
        "rec_match": "possible match — escalate to the Compliance Officer before continuing the relationship",
        "rec_review": "analyst review required (compare identifying data)",
        "rec_clear": "no hits above 75 — no grounds for escalation",
        "below": "Closest candidates below the threshold (for reference, no action required)",
    },
}
DECISION_KEYS = {"false_positive": "fp", "escalation": "esc", "freeze": "freeze"}


def _e(x) -> str:
    return escape(str(x if x is not None else ""))


def _local(ts: str) -> str:
    try:
        return datetime.fromisoformat(ts).astimezone(ZoneInfo("Europe/Warsaw")).strftime("%Y-%m-%d %H:%M:%S %Z")
    except (ValueError, TypeError):
        return ts or ""


def _num(n: int, lang: str) -> str:
    return f"{n:,}".replace(",", "\u00a0" if lang == "pl" else ",")


def _sys(code: str, lang: str) -> str:
    if lang == "en":
        return SYSTEM_LABELS_EN.get(code, code)
    return {"SKELETON": "szkielet fonetyczny", "CYR": "zapis oryginalny (cyrylica)"}.get(code) or SYSTEM_LABELS.get(code, code)


def _dob(births) -> str:
    out = []
    for b in births or []:
        out.append(b.get("date") or b.get("raw") or
                   (f"{b.get('from_year')}–{b.get('to_year')}" if b.get("from_year") else str(b.get("year") or "")))
    return ", ".join(x for x in out if x)


def render(rec: dict, decisions: list, lang: str = "pl") -> str:
    t = T[lang]
    res, q = rec["payload"], rec["query"]
    lists_rows = "".join(
        f"<tr><td>{_e(SOURCES[s]['label'])} — {_e(SOURCES[s]['name'])}</td><td>{_e(v.get('list_date'))}</td>"
        f"<td>{_e(v.get('record_count'))}</td><td>{_e(_local(v.get('fetched_at') or ''))}</td></tr>"
        for s, v in res.get("lists", {}).items())
    examples = "".join(f"<li><b>{_e(x['text'])}</b> <span class='muted'>— {_e(_sys(x['system'], lang))} · {_e(x['lang'])}</span></li>"
                       for x in res.get("examples", []))
    per_token = "".join(
        f"<li><b>{_e(tv['original'])}</b>: {_e(', '.join(v['text'] for v in tv['variants'][:30]))}"
        f"{' …' if len(tv['variants']) > 30 else ''} <span class='muted'>({len(tv['variants'])})</span></li>"
        for tv in res.get("variants", []))

    shown = [r for r in res.get("results", []) if r["status"] in ("match", "review")]
    below = [] if shown else res.get("results", [])[:3]
    level = "match" if any(r["status"] == "match" for r in shown) else ("review" if shown else "clear")
    rows = "".join(
        f"<tr><td class='num'>{r['score']:.0f}</td><td><span class='badge {r['status']}'>{_e(t[r['status']])}</span></td>"
        f"<td>{_e(r['primary_name'])}</td><td>{_e(r['matched_alias'])}</td><td>{_e(r['source_label'])} {_e(r['source_id'])}</td>"
        f"<td>{_e(', '.join(r['programs']))}</td><td>{_e(_dob(r['birth_dates']))}</td>"
        f"<td class='url'><a href='{_e(r['url'])}'>{_e(r['url'][:60])}</a></td></tr>"
        for r in shown)

    below_rows = "".join(
        f"<tr><td class='num'>{r['score']:.0f}</td><td>{_e(r['primary_name'])}</td><td>{_e(r['matched_alias'])}</td>"
        f"<td>{_e(r['source_label'])} {_e(r['source_id'])}</td></tr>" for r in below)
    why = ""
    for r in shown[:5]:
        ex = r["explanation"]
        toks = "".join(
            f"<tr><td>{_e(x['query_token'])}{' (' + t['surname'] + ')' if x.get('is_surname') else ''}</td>"
            f"<td>{_e(x.get('variant') or '—')}</td><td>{_e(', '.join(_sys(c, lang) for c in x.get('system_codes') or []))}</td>"
            f"<td>{_e(x.get('alias_token') or '—')}</td><td class='num'>{x['similarity']:.0f}</td></tr>"
            for x in ex["tokens"])
        factors = "".join(f"<li>{_e(f.get('text_en') if lang == 'en' else f['text'])} ({f['effect']:+d})</li>"
                          for f in ex.get("factors", []))
        why += (f"<div class='why'><h4>{_e(r['primary_name'])} — {_e(r['source_label'])} · {r['score']:.0f}</h4>"
                f"<table><tr><th>{t['token']}</th><th>{t['variant']}</th><th>{t['system']}</th><th>{t['alias']}</th>"
                f"<th>{t['sim']}</th></tr>{toks}</table>"
                f"<p class='muted'>token_sort_ratio: {ex['token_sort_ratio']:.0f} · alias: {_e(ex['alias_compared_as'])}</p>"
                f"{'<p><b>' + t['factors'] + ':</b></p><ul>' + factors + '</ul>' if factors else ''}</div>")

    prev = "".join(
        f"<li>{_e(_local(d['ts']))} — <b>{_e(t[DECISION_KEYS[d['summary']['decision']]])}</b> — {_e(d['actor'])}"
        f"{': ' + _e(d['summary']['comment']) if d['summary'].get('comment') else ''}</li>" for d in decisions)
    entry_ids = [r["entry_id"] for r in shown]

    return f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t['title']} #{rec['id']}</title>
<link rel="stylesheet" href="/static/report.css"></head><body>
<div class="toolbar no-print"><button onclick="window.print()">{t['print']}</button>
<a href="?lang={'en' if lang == 'pl' else 'pl'}">{'English' if lang == 'pl' else 'Polski'}</a></div>
<main>
<header><div class="brand">SANCTIONS SCREENER</div><h1>{t['title']}</h1>
<table class="meta"><tr><th>{t['id']}</th><td>#{rec['id']}</td><th>{t['checked_at']}</th><td>{_e(_local(rec['ts']))}</td></tr>
<tr><th>{t['analyst']}</th><td>{_e(rec['actor'])}</td><th>{t['combos']}</th><td>{_num(res.get('combinations', 0), lang)}</td></tr></table></header>

<section><h2>{t['subject']}</h2><table class="meta">
<tr><th>{t['name']}</th><td><b>{_e(q.get('name'))}</b></td><th>{t['type']}</th><td>{_e(t.get(q.get('entity_type') or 'any', ''))}</td></tr>
<tr><th>{t['birth']}</th><td>{_e(q.get('birth') or res.get('birth') or '—')}</td><th>{t['nat']}</th><td>{_e(q.get('nationality') or '—')}</td></tr>
<tr><th>{t['gender']}</th><td>{_e(q.get('gender') or (res.get('gender_inferred') and res['gender_inferred'] + ' ' + t['inferred']) or '—')}</td><th>{t['doc']}</th><td>{_e(q.get('document') or '—')}</td></tr></table></section>

<section><h2>{t['lists']}</h2><table><tr><th>{t['list']}</th><th>{t['version']}</th><th>{t['records']}</th><th>{t['fetched']}</th></tr>{lists_rows}</table></section>

<section><h2>{t['variants']}</h2><ul class="examples">{examples}</ul><ul class="small">{per_token}</ul></section>

<section class="rec {level}"><b>{t['rec']}:</b> {t['rec_' + level]}</section>

<section><h2>{t['results']}</h2>{f"<table><tr><th>{t['score']}</th><th>{t['status']}</th><th>{t['listed']}</th><th>{t['alias']}</th><th>{t['src']}</th><th>{t['program']}</th><th>{t['dob']}</th><th>{t['link']}</th></tr>{rows}</table>" if rows else f"<p>{t['none']}</p>"}
{f"<p class='muted'>{t['below']}:</p><table class='small'><tr><th>{t['score']}</th><th>{t['listed']}</th><th>{t['alias']}</th><th>{t['src']}</th></tr>{below_rows}</table>" if below_rows else ""}</section>

{f"<section><h2>{t['why']}</h2>{why}</section>" if why else ""}

<section class="decision"><h2>{t['decision']}</h2>
{f"<p><b>{t['prev']}:</b></p><ul>{prev}</ul>" if prev else ""}
<form id="decision">
<label><input type="radio" name="d" value="false_positive"> {t['fp']}</label>
<label><input type="radio" name="d" value="escalation"> {t['esc']}</label>
<label><input type="radio" name="d" value="freeze"> {t['freeze']}</label>
<p><b>{t['comment']}</b></p><textarea id="comment" rows="5"></textarea>
<div class="sign"><span>{t['analyst']}: ____________________</span><span>{t['sign']}: ____________________</span></div>
<p class="no-print"><button type="submit">{t['save']}</button> <span id="msg"></span></p>
</form></section>

<footer>{t['disclaimer']}</footer></main>
<script>
document.getElementById('decision').addEventListener('submit', async (e) => {{
  e.preventDefault();
  const d = document.querySelector('input[name=d]:checked');
  const msg = document.getElementById('msg');
  if (!d) {{ msg.textContent = {t['choose']!r}; return; }}
  let analyst = '';
  try {{ analyst = localStorage.getItem('analyst') || ''; }} catch (_) {{}}
  const r = await fetch('/api/decision', {{method: 'POST', headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{search_id: {rec['id']}, decision: d.value, comment: document.getElementById('comment').value,
                          analyst, entry_ids: {entry_ids}}})}});
  msg.textContent = r.ok ? {t['saved']!r} : ('Error ' + r.status);
}});
</script></body></html>"""
