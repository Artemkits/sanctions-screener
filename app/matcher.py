"""In-memory search index and scoring.

Index
-----
Every alias of every list entry becomes one or two *name forms*:
  * the alias as written (Latin, or Cyrillic kept as Cyrillic),
  * for non-Latin aliases additionally a Latin form (Cyrillic → KMU 2010 / ICAO /
    BY passport depending on the alias language; Arabic, Greek → unidecode).
Each form is a tuple of token ids into a shared vocabulary of distinct tokens,
plus a parallel tuple of phonetic-skeleton ids.

Search
------
1. For every query token we compare *all* its transliteration variants with the
   whole vocabulary in one vectorised call (rapidfuzz.process.cdist), and the
   query skeletons with the skeleton vocabulary. Only tokens scoring ≥ 70 survive.
2. Name forms containing a surviving token are candidates (inverted index).
3. Each candidate is scored by optimal token alignment (order-independent, so
   "Shcherbyna Serhii" == "Serhii Shcherbyna"), a separate surname check and
   rapidfuzz token_sort_ratio; then date of birth / nationality adjust the score.
"""
from __future__ import annotations

import itertools
import json
import re
import threading
import time
from dataclasses import dataclass

import numpy as np
from rapidfuzz import fuzz, process

from .config import MATCH_THRESHOLD, REVIEW_THRESHOLD, SOURCES, WEAK_THRESHOLD
from .db import connect
from .text import (STOPWORDS, SURNAME_SUFFIX, detect_script, looks_like_patronymic, norm_cyrillic,
                   norm_latin, skeleton, split_tokens)
from .translit import (SYSTEM_LABELS, by_passport, detect_language, full_name_examples, name_languages,
                       name_variants, ru_icao, russify, ua_kmu2010)

TOKEN_CUTOFF = 70          # minimum token similarity to become a candidate
SKELETON_DISCOUNT = 0.95   # skeleton matches are fuzzier than explicit variants
MAX_ALIGN_TOKENS = 8
PATRONYMIC_DISCOUNT = 0.75
SURNAME_REVIEW_MIN = 85    # surname similarity below this → never above "weak"
SURNAME_MATCH_MIN = 92     # surname similarity below this → never a full "match"

CYR_SURNAME = re.compile(r"(ов|ев|ёв|ин|ын|ова|ева|ина|ына|енко|енка|эн?ка|ук|юк|чук|ский|цкий|ський|цький|ская|ська|ич|іч|ко|як|ак)$")


@dataclass
class Form:
    entry: int          # entries.id
    alias: int          # aliases.id
    tokens: tuple       # vocab ids
    skels: tuple        # skeleton vocab ids (-1 for Cyrillic tokens)
    kind: str           # "orig" | "translit:<system>"
    patro: tuple        # True where the token is a patronymic in the middle of the name


def _latin_of(alias: str, script: str) -> tuple[str, str]:
    """Latin rendering of a non-Latin alias for the index + the method used."""
    if script == "cyrillic":
        lang = detect_language(" ".join(norm_cyrillic(t) for t in split_tokens(alias)))
        if lang == ["uk"]:
            fn, label = ua_kmu2010, "UA_KMU2010"
        elif lang == ["be"]:
            fn, label = by_passport, "BY_PASS"
        else:
            fn, label = ru_icao, "RU_ICAO"
        return " ".join(fn(norm_cyrillic(t)) for t in split_tokens(alias)), label
    return norm_latin(alias), "unidecode"


class Index:
    def __init__(self):
        self.entries: dict[int, dict] = {}
        self.aliases: dict[int, dict] = {}
        self.forms: list[Form] = []
        self.vocab: list[str] = []
        self.skel_vocab: list[str] = []
        self.inv: list[list[int]] = []
        self.skel_inv: list[list[int]] = []
        self.meta: dict[str, dict] = {}
        self.built_at = None
        self.build_seconds = 0.0

    # ------------------------------------------------------------------ build
    def build(self, conn=None):
        t0 = time.time()
        conn = conn or connect()
        vocab_ids, skel_ids = {}, {}
        vocab, skel_vocab, inv, skel_inv, forms = [], [], [], [], []

        def vid(tok):
            i = vocab_ids.get(tok)
            if i is None:
                i = vocab_ids[tok] = len(vocab)
                vocab.append(tok)
                inv.append([])
            return i

        def sid(sk):
            i = skel_ids.get(sk)
            if i is None:
                i = skel_ids[sk] = len(skel_vocab)
                skel_vocab.append(sk)
                skel_inv.append([])
            return i

        def add_form(entry_id, alias_id, tokens, latin, kind):
            if not tokens:
                return
            f_id = len(forms)
            t_ids = tuple(vid(t) for t in tokens)
            s_ids = tuple(sid(skeleton(t)) if latin else -1 for t in tokens)
            last = len(tokens) - 1
            patro = tuple(len(tokens) >= 3 and 0 < k < last and looks_like_patronymic(t)
                          for k, t in enumerate(tokens))
            forms.append(Form(entry_id, alias_id, t_ids, s_ids, kind, patro))
            for t in set(t_ids):
                inv[t].append(f_id)
            for s in set(s_ids):
                if s >= 0:
                    skel_inv[s].append(f_id)

        entries = {}
        for r in conn.execute("SELECT * FROM entries"):
            entries[r["id"]] = {
                "id": r["id"], "source": r["source"], "source_id": r["source_id"],
                "entity_type": r["entity_type"], "primary_name": r["primary_name"],
                "birth_dates": json.loads(r["birth_dates"]), "nationalities": json.loads(r["nationalities"]),
                "programs": json.loads(r["programs"]), "listed_on": r["listed_on"], "url": r["url"],
            }
        aliases = {}
        for r in conn.execute("SELECT id, entry_id, name, script, lang, quality FROM aliases"):
            a = dict(r)
            aliases[a["id"]] = a
            if a["script"] == "cyrillic":
                toks = [norm_cyrillic(t) for t in split_tokens(a["name"])]
                add_form(a["entry_id"], a["id"], [t for t in toks if t], False, "orig")
                latin, method = _latin_of(a["name"], "cyrillic")
                add_form(a["entry_id"], a["id"], latin.split(), True, f"translit:{method}")
            elif a["script"] == "latin":
                add_form(a["entry_id"], a["id"], norm_latin(a["name"]).split(), True, "orig")
            else:
                latin, method = _latin_of(a["name"], a["script"])
                add_form(a["entry_id"], a["id"], latin.split(), True, f"translit:{method}")

        self.meta = {r["source"]: dict(r) for r in conn.execute("SELECT * FROM source_meta")}
        self.entries, self.aliases, self.forms = entries, aliases, forms
        self.vocab, self.skel_vocab, self.inv, self.skel_inv = vocab, skel_vocab, inv, skel_inv
        self.built_at = time.strftime("%Y-%m-%d %H:%M:%S")
        self.build_seconds = round(time.time() - t0, 2)
        return self

    # ------------------------------------------------------------------ search
    def _token_hits(self, strings: list[str], vocab: list[str]) -> dict[int, tuple[float, int]]:
        """{vocab_id: (best score, index of the query string that achieved it)}"""
        if not strings or not vocab:
            return {}
        m = process.cdist(strings, vocab, scorer=fuzz.ratio, score_cutoff=TOKEN_CUTOFF,
                          dtype=np.uint8, workers=-1)
        best = m.max(axis=0)
        idx = np.nonzero(best >= TOKEN_CUTOFF)[0]
        if not len(idx):
            return {}
        arg = m[:, idx].argmax(axis=0)
        return {int(v): (float(best[v]), int(a)) for v, a in zip(idx, arg)}

    def search(self, name: str, birth: str = "", nationality: str = "", entity_type: str = "any",
               limit: int = 50, min_score: float = WEAK_THRESHOLD) -> dict:
        t0 = time.time()
        tvs = name_variants(name)
        q = [tv for tv in tvs if norm_latin(tv.original) not in STOPWORDS] or tvs
        if not q:
            return {"query": name, "results": [], "variants": [], "examples": [], "elapsed_ms": 0}

        q_strings, direct, skel = [], [], []
        for tv in q:
            strings = tv.norms() + ([tv.cyrillic] if tv.cyrillic else [])
            q_strings.append(strings)
            direct.append(self._token_hits(strings, self.vocab))
            skel.append(self._token_hits(sorted(tv.skeletons), self.skel_vocab))
        skel_lists = [sorted(tv.skeletons) for tv in q]

        surname_i = _guess_surname(q)
        cand: dict[int, set] = {}
        for i in range(len(q)):
            for v in direct[i]:
                for f in self.inv[v]:
                    cand.setdefault(f, set()).add(i)
            for s in skel[i]:
                for f in self.skel_inv[s]:
                    cand.setdefault(f, set()).add(i)
        # A candidate must hit the surname, or (for 1-token names) the only token.
        need = max(1, len(q) // 2)
        best_by_entry: dict[int, dict] = {}
        for f_id, hit in cand.items():
            if len(hit) < need:
                continue
            form = self.forms[f_id]
            entry = self.entries[form.entry]
            if entity_type != "any" and not _type_ok(entry["entity_type"], entity_type):
                continue
            scored = self._score_form(form, q, q_strings, skel_lists, direct, skel, surname_i)
            if scored is None:
                continue
            prev = best_by_entry.get(form.entry)
            if prev is None or scored["name_score"] > prev["name_score"]:
                best_by_entry[form.entry] = scored

        results = []
        for entry_id, sc in best_by_entry.items():
            entry = self.entries[entry_id]
            score, factors = _adjust(sc["name_score"], entry, birth, nationality)
            alias = self.aliases[sc["alias_id"]]
            if alias["quality"] == "weak":
                score -= 5
                factors.append({"field": "alias", "effect": -5, "ok": None,
                                "text": "Alias niskiej jakości (weak/low a.k.a.) w liście źródłowej"})
            score = max(0.0, min(100.0, score))
            if score < min_score:
                continue
            results.append({
                "entry_id": entry_id,
                "score": round(score, 1),
                "name_score": round(sc["name_score"], 1),
                "status": status_for(score),
                "source": entry["source"],
                "source_label": SOURCES[entry["source"]]["label"],
                "source_id": entry["source_id"],
                "entity_type": entry["entity_type"],
                "primary_name": entry["primary_name"],
                "matched_alias": alias["name"],
                "alias_script": alias["script"],
                "alias_lang": alias["lang"],
                "programs": entry["programs"],
                "birth_dates": entry["birth_dates"],
                "nationalities": entry["nationalities"],
                "listed_on": entry["listed_on"],
                "url": entry["url"],
                "explanation": {**sc["explanation"], "factors": factors},
            })
        results.sort(key=lambda r: (-r["score"], r["primary_name"]))
        return {
            "query": name,
            "birth": birth,
            "nationality": nationality,
            "entity_type": entity_type,
            "languages": name_languages(tvs),
            "variants": [tv.to_dict() for tv in tvs],
            "examples": full_name_examples(tvs),
            "combinations": int(np.prod([max(1, len(tv.variants)) for tv in tvs])),
            "candidates": len(cand),
            "results": results[:limit],
            "total_results": len(results),
            "elapsed_ms": round((time.time() - t0) * 1000),
            "lists": self.list_versions(),
        }

    def _score_form(self, form, q, q_strings, skel_lists, direct, skel, surname_i):
        toks, sks = form.tokens[:MAX_ALIGN_TOKENS], form.skels[:MAX_ALIGN_TOKENS]
        n, m = len(q), len(toks)
        q_patro = [_is_patronymic(tv) for tv in q]
        # similarity matrix with provenance
        sim = [[(0.0, None)] * m for _ in range(n)]
        for i in range(n):
            for j in range(m):
                best = (0.0, None)
                d = direct[i].get(toks[j])
                if d:
                    best = (d[0], ("direct", d[1]))
                if sks[j] >= 0:
                    s = skel[i].get(sks[j])
                    if s and s[0] * SKELETON_DISCOUNT > best[0]:
                        best = (s[0] * SKELETON_DISCOUNT, ("skeleton", s[1]))
                # A given name must not "match" somebody's patronymic (Oleksandr ≠ Oleksandrovna).
                if form.patro[j] and not q_patro[i]:
                    best = (best[0] * PATRONYMIC_DISCOUNT, best[1])
                sim[i][j] = best
        # optimal assignment of query tokens to distinct alias tokens
        cols = list(range(m)) + [None] * max(0, n - m)
        best_total, best_perm = -1.0, None
        for perm in itertools.permutations(cols, n):
            total = sum(sim[i][j][0] if j is not None else 0.0 for i, j in enumerate(perm))
            if total > best_total:
                best_total, best_perm = total, perm

        # patronymic in the query that the list does not have → ignore it
        used_q = []
        for i, j in enumerate(best_perm):
            s = sim[i][j][0] if j is not None else 0.0
            if s < TOKEN_CUTOFF and n > 2 and i != surname_i and _is_patronymic(q[i]):
                continue
            used_q.append(i)
        if not used_q:
            return None
        aligned = sum(sim[i][best_perm[i]][0] if best_perm[i] is not None else 0 for i in used_q) / len(used_q)

        matched_cols = {best_perm[i] for i in used_q if best_perm[i] is not None}
        penalty, extra = 0.0, []
        for j in range(len(form.tokens)):
            if j in matched_cols:
                continue
            tok = self.vocab[form.tokens[j]]
            if tok in STOPWORDS or looks_like_patronymic(tok):
                penalty += 1.0
            else:
                penalty += 3.0
            extra.append(tok)
        penalty = min(penalty, 12.0)

        sur = sim[surname_i][best_perm[surname_i]][0] if best_perm[surname_i] is not None else 0.0
        name_score = 0.7 * aligned + 0.3 * sur - penalty

        # whole-string check with the best variant of each token, rapidfuzz token_sort_ratio
        best_strings = []
        for i in used_q:
            j = best_perm[i]
            prov = sim[i][j][1] if j is not None else None
            best_strings.append(q_strings[i][prov[1]] if prov and prov[0] == "direct" else q[i].norms()[0])
        # same script on both sides: Cyrillic forms are matched with the Cyrillic query string
        alias_str = " ".join(self.vocab[t] for t in form.tokens)
        tsr = fuzz.token_sort_ratio(" ".join(best_strings), alias_str)
        if tsr - 2 > name_score:
            name_score = tsr - 2

        if any(sim[i][best_perm[i]][0] < TOKEN_CUTOFF if best_perm[i] is not None else True for i in used_q):
            name_score = _cap(name_score, REVIEW_THRESHOLD - 1)  # every given token must be present
        if len(used_q) == 1:
            name_score = _cap(name_score, MATCH_THRESHOLD - 1)   # a single token is never a full hit
        if sur < SURNAME_REVIEW_MIN:
            name_score = _cap(name_score, REVIEW_THRESHOLD - 1)  # surname must match
        elif sur < SURNAME_MATCH_MIN:
            name_score = _cap(name_score, MATCH_THRESHOLD - 1)
        if name_score < WEAK_THRESHOLD - 15:
            return None

        token_rows = []
        for i in range(n):
            j = best_perm[i]
            score, prov = sim[i][j] if j is not None else (0.0, None)
            row = {"query_token": q[i].original, "alias_token": self.vocab[form.tokens[j]] if j is not None else None,
                   "similarity": round(score, 1), "is_surname": i == surname_i, "ignored": i not in used_q}
            if prov and prov[0] == "direct":
                strings = q_strings[i]
                s = strings[prov[1]]
                v = next((v for v in q[i].variants if v.norm == s), None)
                row.update(channel="direct", variant=v.text if v else s,
                           systems=[SYSTEM_LABELS.get(x, x) for x in (v.systems if v else ["CYR"])],
                           system_codes=v.systems if v else ["CYR"],
                           via_equivalent=_via_equivalent(q[i], v),
                           equivalent_form=v.source_form if _via_equivalent(q[i], v) else "")
                if not v:
                    row["systems"] = ["zapis oryginalny (cyrylica)"]
            elif prov:
                row.update(channel="skeleton", variant=skel_lists[i][prov[1]],
                           systems=["szkielet fonetyczny"], system_codes=["SKELETON"])
            token_rows.append(row)

        return {
            "name_score": max(0.0, min(100.0, name_score)),
            "alias_id": form.alias,
            "explanation": {
                "form_kind": form.kind,
                "alias_compared_as": alias_str,
                "tokens": token_rows,
                "aligned": round(aligned, 1),
                "surname_similarity": round(sur, 1),
                "token_sort_ratio": round(tsr, 1),
                "unmatched_alias_tokens": extra,
                "penalty": penalty,
            },
        }

    def list_versions(self):
        return {s: {k: self.meta.get(s, {}).get(k) for k in ("list_date", "fetched_at", "record_count", "alias_count", "status")}
                for s in SOURCES}

    def entry_detail(self, entry_id: int) -> dict | None:
        conn = connect()
        r = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
        if not r:
            return None
        d = dict(r)
        for k in ("birth_dates", "nationalities", "programs", "extra"):
            d[k] = json.loads(d[k])
        d["aliases"] = [dict(a) for a in conn.execute(
            "SELECT name, script, lang, quality FROM aliases WHERE entry_id = ? ORDER BY id", (entry_id,))]
        d["source_label"] = SOURCES[d["source"]]["label"]
        d["source_name"] = SOURCES[d["source"]]["name"]
        conn.close()
        return d


# ---------------------------------------------------------------------- helpers

def _cap(score: float, cap: float) -> float:
    """Push a score below `cap` while keeping the relative order of capped scores."""
    return score if score <= cap else cap - 1 - (100 - score) * 0.15


def status_for(score: float) -> str:
    if score >= MATCH_THRESHOLD:
        return "match"
    if score >= REVIEW_THRESHOLD:
        return "review"
    return "weak"


def _type_ok(entry_type: str, wanted: str) -> bool:
    if wanted == "person":
        return entry_type == "person"
    if wanted == "entity":
        return entry_type != "person"
    return True


def _via_equivalent(tv, v) -> bool:
    """True if the variant came only from another-language form of the name (Сергій → Сергей)."""
    if not v or not tv.cyrillic:
        return False
    own = {tv.cyrillic, russify(tv.cyrillic)}
    return all(o[2].replace("'", "") not in own for o in v.origins)


def _is_patronymic(tv) -> bool:
    if tv.cyrillic:
        return bool(re.search(r"(ович|евич|ьевич|овна|евна|ична|ович|йович|івна|ївна|ійович)$", tv.cyrillic))
    return looks_like_patronymic(norm_latin(tv.original))


def _looks_like_surname(tv) -> bool:
    if tv.cyrillic:
        return bool(CYR_SURNAME.search(tv.cyrillic))
    return bool(SURNAME_SUFFIX.search(norm_latin(tv.original)))


def _guess_surname(q) -> int:
    """Index of the query token treated as the surname (last token by default)."""
    if len(q) == 1:
        return 0
    last, first = len(q) - 1, 0
    if _looks_like_surname(q[first]) and not _looks_like_surname(q[last]) and not _is_patronymic(q[first]):
        return first
    if _is_patronymic(q[last]) and len(q) >= 3:
        return first
    return last


def parse_birth(s: str) -> tuple[int | None, str]:
    """→ (year, ISO date or '')."""
    s = (s or "").strip()
    if not s:
        return None, ""
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m:
        return int(m[1]), f"{m[1]}-{int(m[2]):02d}-{int(m[3]):02d}"
    m = re.match(r"^(\d{1,2})[./-](\d{1,2})[./-](\d{4})$", s)
    if m:
        return int(m[3]), f"{m[3]}-{int(m[2]):02d}-{int(m[1]):02d}"
    m = re.search(r"\b(19|20)\d{2}\b", s)
    return (int(m[0]), "") if m else (None, "")


def _adjust(name_score: float, entry: dict, birth: str, nationality: str):
    """Date of birth and nationality as secondary identifiers."""
    score, factors = name_score, []
    year, date = parse_birth(birth)
    births = entry["birth_dates"]
    if year:
        if not births:
            factors.append({"field": "birth", "effect": 0, "ok": None,
                            "text": "Brak daty urodzenia w rekordzie — nie można potwierdzić ani wykluczyć"})
        else:
            listed = []
            exact = year_ok = near = False
            for b in births:
                y, fy, ty = b.get("year"), b.get("from_year"), b.get("to_year")
                listed.append(b.get("date") or b.get("raw") or (f"{fy}–{ty}" if fy else str(y)))
                if date and b.get("date") == date:
                    exact = True
                if y == year or (fy and ty and fy <= year <= ty):
                    year_ok = True
                elif y and abs(y - year) <= (2 if b.get("circa") else 1):
                    near = True
            lst = ", ".join(x for x in listed if x and x != "None")
            if exact:
                score += 5
                factors.append({"field": "birth", "effect": 5, "ok": True, "text": f"Data urodzenia zgodna ({date})"})
            elif year_ok:
                score += 3
                factors.append({"field": "birth", "effect": 3, "ok": True, "text": f"Rok urodzenia zgodny ({year}; lista: {lst})"})
            elif near:
                factors.append({"field": "birth", "effect": 0, "ok": None, "text": f"Rok urodzenia zbliżony (±1–2): {year} vs {lst}"})
            else:
                score -= 15
                factors.append({"field": "birth", "effect": -15, "ok": False,
                                "text": f"Inny rok urodzenia: {year} vs {lst} — argument za false positive"})
    nat = (nationality or "").strip().upper()
    if nat:
        nats = [n.get("iso2") for n in entry["nationalities"] if n.get("iso2")]
        if not nats:
            factors.append({"field": "nationality", "effect": 0, "ok": None, "text": "Brak obywatelstwa w rekordzie"})
        elif nat in nats:
            score += 3
            factors.append({"field": "nationality", "effect": 3, "ok": True, "text": f"Obywatelstwo zgodne ({nat})"})
        else:
            score -= 5
            factors.append({"field": "nationality", "effect": -5, "ok": False,
                            "text": f"Inne obywatelstwo: {nat} vs {', '.join(nats)} — argument za false positive"})
    return score, factors


# ---------------------------------------------------------------------- singleton

_index: Index | None = None
_lock = threading.Lock()


def get_index() -> Index:
    global _index
    with _lock:
        if _index is None:
            _index = Index().build()
        return _index


def rebuild_index() -> Index:
    global _index
    new = Index().build()
    with _lock:
        _index = new
    return new
