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
import pickle
import re
import threading
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
from rapidfuzz import fuzz, process

from .config import DB_PATH, MATCH_THRESHOLD, REVIEW_THRESHOLD, SOURCES, WEAK_THRESHOLD
from .db import connect
from .sources import norm_id, norm_sex
from .text import (
    STOPWORDS,
    SURNAME_SUFFIX,
    looks_like_patronymic,
    norm_cyrillic,
    norm_latin,
    skeleton,
    split_tokens,
)
from .translit import (
    SYSTEM_LABELS,
    by_passport,
    detect_language,
    full_name_examples,
    name_languages,
    name_variants,
    ru_icao,
    russify,
    ua_kmu2010,
)

TOKEN_CUTOFF = 70          # minimum token similarity to become a candidate
SKELETON_DISCOUNT = 0.95   # skeleton matches are fuzzier than explicit variants
MAX_ALIGN_TOKENS = 8
PATRONYMIC_DISCOUNT = 0.75
SURNAME_REVIEW_MIN = 85    # surname similarity below this → never above "weak"
SURNAME_MATCH_MIN = 92     # surname similarity below this → never a full "match"

DATE_TOKEN = re.compile(r"^(\d{4}|\d{1,2}[./-]\d{1,2}[./-]\d{4}|\d{4}-\d{1,2}-\d{1,2})$")
# legal-form words of company names — unmatched ones cost no more than a patronymic
LEGAL_FORMS = {"company", "co", "ltd", "limited", "llc", "ooo", "oao", "zao", "pao", "ao", "pjsc", "jsc", "ojsc",
               "cjsc", "open", "joint", "stock", "public", "closed", "inc", "corp", "corporation", "gmbh", "sa", "ag",
               "plc", "fze", "llp", "sp", "z", "o", "limited liability", "obshchestvo", "s", "de", "rl", "cv"}
CYR_SURNAME = re.compile(r"(ов|ев|ёв|ин|ын|ова|ева|ина|ына|енко|енка|эн?ка|ук|юк|чук|ский|цкий|ський|цький|ская|ська|ич|іч|ко|як|ак)$")


@dataclass(slots=True)
class Form:
    entry: int          # entries.id
    alias: int          # aliases.id
    tokens: tuple       # vocab ids
    skels: tuple        # skeleton vocab ids (-1 for Cyrillic tokens)
    kind: str           # "orig" | "translit:<system>"
    patro: tuple        # True where the token is a patronymic in the middle of the name


_TRANSLIT = {"UA_KMU2010": ua_kmu2010, "BY_PASS": by_passport, "RU_ICAO": ru_icao}


@lru_cache(maxsize=500_000)
def _translit_token(token: str, method: str) -> str:
    return _TRANSLIT[method](token)


def _latin_of(alias: str, script: str) -> tuple[str, str]:
    """Latin rendering of a non-Latin alias for the index + the method used."""
    if script == "cyrillic":
        toks = [norm_cyrillic(t) for t in split_tokens(alias)]
        lang = detect_language(" ".join(toks))
        label = "UA_KMU2010" if lang == ["uk"] else ("BY_PASS" if lang == ["be"] else "RU_ICAO")
        return " ".join(_translit_token(t, label) for t in toks if t), label
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
        self.stats: dict[str, dict] = {}
        self.doc_index: dict[str, set] = {}
        self.forms_by_entry: dict[int, list] = {}
        self.built_at = None
        self.build_seconds = 0.0

    # ------------------------------------------------------------------ build
    CACHE_VERSION = 3   # bump when the index layout or normalisation changes

    def load_or_build(self):
        """Load a pickled index if it matches the current database, otherwise build and save one."""
        db = Path(DB_PATH)
        cache = db.with_name(f"{db.stem}.index-{'-'.join(sorted(SOURCES)).lower()}.pkl")
        sig = None
        if db.exists():
            # keyed on list versions, not on the file: the audit log lives in the same database
            conn = connect()
            meta = tuple(tuple(r) for r in conn.execute(
                "SELECT source, fetched_at, record_count, alias_count FROM source_meta ORDER BY source")
                if r["source"] in SOURCES)
            conn.close()
            sig = (self.CACHE_VERSION, tuple(sorted(SOURCES)), meta)
        if sig and cache.exists():
            t0 = time.time()
            try:
                with open(cache, "rb") as f:
                    saved_sig, state = pickle.load(f)
                if saved_sig == sig:
                    self.__dict__.update(state)
                    self.build_seconds = round(time.time() - t0, 2)
                    self.built_at = time.strftime("%Y-%m-%d %H:%M:%S") + " (cache)"
                    return self
            except Exception:  # a stale or corrupt cache is simply rebuilt
                pass
        self.build()
        if sig:
            try:
                tmp = cache.with_suffix(".tmp")
                with open(tmp, "wb") as f:
                    pickle.dump((sig, self.__dict__), f, protocol=pickle.HIGHEST_PROTOCOL)
                tmp.replace(cache)
            except OSError:
                pass
        return self

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
        enabled = tuple(SOURCES)          # lists switched off via ENABLED_SOURCES are not indexed
        marks = ",".join("?" * len(enabled))
        for r in conn.execute(f"SELECT * FROM entries WHERE source IN ({marks})", enabled):
            entries[r["id"]] = {
                "id": r["id"], "source": r["source"], "source_id": r["source_id"],
                "entity_type": r["entity_type"], "primary_name": r["primary_name"],
                "birth_dates": json.loads(r["birth_dates"]), "nationalities": json.loads(r["nationalities"]),
                "programs": json.loads(r["programs"]), "listed_on": r["listed_on"], "url": r["url"],
            }
            extra = json.loads(r["extra"] or "{}")
            entries[r["id"]]["sex"] = extra.get("sex", "")
            entries[r["id"]]["ids"] = {norm_id(d["number"]): d for d in extra.get("identifiers", [])}
        aliases = {}
        for r in conn.execute("SELECT id, entry_id, name, script, lang, quality FROM aliases"):
            if r["entry_id"] not in entries:
                continue
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

        doc_index, forms_by_entry = {}, {}
        for e in entries.values():
            for n in e["ids"]:
                doc_index.setdefault(n, set()).add(e["id"])
        for f_id, f in enumerate(forms):
            forms_by_entry.setdefault(f.entry, []).append(f_id)
        self.doc_index, self.forms_by_entry = doc_index, forms_by_entry
        self.meta = {r["source"]: dict(r) for r in conn.execute("SELECT * FROM source_meta") if r["source"] in SOURCES}
        self.stats = _stats(entries, aliases)
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
        return {int(v): (float(best[v]), int(a)) for v, a in zip(idx, arg, strict=False)}

    def search(self, name: str, birth: str = "", nationality: str = "", entity_type: str = "any",
               limit: int = 50, min_score: float = WEAK_THRESHOLD, gender: str = "", document: str = "",
               sources: list | None = None) -> dict:
        t0 = time.time()
        # a year or date typed into the name field is treated as the date of birth
        date_tokens = [tk for tk in name.split() if DATE_TOKEN.match(tk)]
        if date_tokens:
            name = " ".join(tk for tk in name.split() if not DATE_TOKEN.match(tk))
            birth = birth or date_tokens[0]
        tvs = [tv for tv in name_variants(name) if tv.variants]
        q = [tv for tv in tvs if tv.variants[0].norm.isdigit()
             or (len(tv.variants[0].norm) >= 2 and tv.variants[0].norm not in STOPWORDS)]
        if q and all(tv.variants[0].norm.isdigit() for tv in q):
            q = []
        if not q:
            return self._empty(name, birth, nationality, entity_type, tvs, time.time() - t0)

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
        # Every query word (a patronymic excepted) must be present in a candidate name form.
        # Forms missing a word could never rise above "weak", so they are not scored at all.
        q_patro = [_is_patronymic(tv) for tv in q]
        # numbers are a mismatch signal (SEA STAR 7 vs 8), not a requirement
        required = {i for i in range(len(q)) if not (q_patro[i] and len(q) > 2)
                    and not q[i].variants[0].norm.isdigit()} or {0}
        args = (q, q_strings, skel_lists, direct, skel, surname_i, q_patro)
        best_by_entry: dict[int, dict] = {}
        for f_id, hit in cand.items():
            if not required <= hit:
                continue
            form = self.forms[f_id]
            entry = self.entries[form.entry]
            if (sources and entry["source"] not in sources) or \
                    (entity_type != "any" and not _type_ok(entry["entity_type"], entity_type)):
                continue
            scored = self._score_form(form, *args)
            if scored is None:
                continue
            prev = best_by_entry.get(form.entry)
            if prev is None or scored["name_score"] > prev["name_score"]:
                best_by_entry[form.entry] = scored

        # A matching document number is strong evidence on its own: score those records
        # even when their names did not make it into the candidate set.
        doc = norm_id(document)
        for entry_id in self.doc_index.get(doc, set()) if len(doc) >= 4 else ():
            entry = self.entries[entry_id]
            if entity_type != "any" and not _type_ok(entry["entity_type"], entity_type):
                continue
            if sources and entry["source"] not in sources:
                continue
            for f_id in self.forms_by_entry.get(entry_id, []):
                scored = self._score_form(self.forms[f_id], *args, floor=False)
                prev = best_by_entry.get(entry_id)
                if scored and (prev is None or scored["name_score"] > prev["name_score"]):
                    best_by_entry[entry_id] = scored

        sex = norm_sex(gender)
        inferred = "" if sex else infer_gender(q)
        results = []
        for entry_id, sc in best_by_entry.items():
            entry = self.entries[entry_id]
            sc = self._score_form(sc["form"], *args, floor=False, explain=True)   # full explanation only now
            score, factors = _adjust(sc["name_score"], entry, birth, nationality, sex or inferred, bool(inferred), doc)
            if sc["explanation"].get("number_mismatch"):
                factors.append(_factor("number", -10, False, "Różne liczby w nazwie (np. numer statku lub spółki)",
                                       "Different numbers in the name (e.g. vessel or company number)"))
                score -= 10
            alias = self.aliases[sc["alias_id"]]
            if alias["quality"] == "weak":
                score -= 5
                factors.append(_factor("alias", -5, None,
                                       "Alias niskiej jakości (weak/low a.k.a.) w liście źródłowej",
                                       "Low-quality alias (weak/low a.k.a.) in the source list"))
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
            "gender": sex, "gender_inferred": inferred, "document": document,
            "sources": sorted(sources) if sources else sorted(SOURCES),
            "results": results[:limit],
            "total_results": len(results),
            "elapsed_ms": round((time.time() - t0) * 1000),
            "lists": self.list_versions(sources),
        }

    def _empty(self, name, birth, nationality, entity_type, tvs, elapsed):
        return {"query": name, "birth": birth, "nationality": nationality, "entity_type": entity_type,
                "languages": name_languages(tvs), "variants": [tv.to_dict() for tv in tvs], "examples": [],
                "combinations": 0, "candidates": 0, "results": [], "total_results": 0, "too_short": True,
                "elapsed_ms": round(elapsed * 1000), "lists": self.list_versions()}

    def _score_form(self, form, q, q_strings, skel_lists, direct, skel, surname_i, q_patro,
                    floor=True, explain=False):
        toks, sks = form.tokens[:MAX_ALIGN_TOKENS], form.skels[:MAX_ALIGN_TOKENS]
        n, m = len(q), len(toks)
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
            if s < TOKEN_CUTOFF and n > 2 and i != surname_i and q_patro[i]:
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
            if tok in STOPWORDS or tok in LEGAL_FORMS or looks_like_patronymic(tok):
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
        # One word is a full hit only when the record has no other significant word
        # ("Rosneft" ↔ "ROSNEFT"), never for people ("Lavrov" ↔ "Sergei LAVROV").
        significant_extra = [x for x in extra if x not in STOPWORDS and x not in LEGAL_FORMS]
        if len(used_q) == 1 and (self.entries[form.entry]["entity_type"] == "person" or significant_extra):
            name_score = _cap(name_score, MATCH_THRESHOLD - 1)
        if sur < SURNAME_REVIEW_MIN:
            name_score = _cap(name_score, REVIEW_THRESHOLD - 1)  # surname must match
        elif sur < SURNAME_MATCH_MIN:
            name_score = _cap(name_score, MATCH_THRESHOLD - 1)
        q_nums = {tv.variants[0].norm for tv in q if tv.variants[0].norm.isdigit()}
        a_nums = {self.vocab[t] for t in form.tokens if self.vocab[t].isdigit()}
        number_mismatch = bool(q_nums and a_nums and q_nums.isdisjoint(a_nums))
        if floor and name_score < WEAK_THRESHOLD - 15:
            return None
        if not explain:
            return {"name_score": max(0.0, min(100.0, name_score)), "form": form}

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
                row.update(channel="direct", variant=v.text if v else q[i].original,
                           systems=[SYSTEM_LABELS.get(x, x) for x in (v.systems if v else ["CYR"])],
                           system_codes=v.systems if v else ["CYR"],
                           via_equivalent=_via_equivalent(q[i], v),
                           equivalent_form=v.source_form if _via_equivalent(q[i], v) else "")
                if not v:
                    row["systems"] = ["zapis oryginalny (cyrylica)"]
            elif prov:
                key = skel_lists[i][prov[1]]
                # show the generated spelling that produced this skeleton, not the internal key
                v = next((v for v in q[i].variants if skeleton(v.norm) == key), None)
                row.update(channel="skeleton", variant=v.text if v else key, skeleton=key,
                           systems=["szkielet fonetyczny"], system_codes=["SKELETON"])
            token_rows.append(row)

        return {
            "name_score": max(0.0, min(100.0, name_score)),
            "form": form,
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
                "number_mismatch": number_mismatch,
            },
        }

    def list_versions(self, only=None):
        return {s: {k: self.meta.get(s, {}).get(k) for k in ("list_date", "fetched_at", "record_count", "alias_count", "status")}
                for s in SOURCES if not only or s in only}

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

def _stats(entries: dict, aliases: dict) -> dict:
    """Per-source composition shown on the "Lists" page."""
    from collections import Counter
    out = {}
    for src in SOURCES:
        ents = [e for e in entries.values() if e["source"] == src]
        ids = {e["id"] for e in ents}
        als = [a for a in aliases.values() if a["entry_id"] in ids]
        progs = Counter(p for e in ents for p in e["programs"])
        nats = Counter(n["iso2"] for e in ents for n in e["nationalities"] if n.get("iso2"))
        out[src] = {
            "entries": len(ents),
            "aliases": len(als),
            "by_type": dict(Counter(e["entity_type"] for e in ents).most_common()),
            "by_script": dict(Counter(a["script"] for a in als).most_common()),
            "top_programs": progs.most_common(8),
            "top_nationalities": nats.most_common(8),
            "with_birth_date": sum(1 for e in ents if e["birth_dates"]),
        }
    return out


def index_ready() -> bool:
    return _index is not None


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


def _factor(field: str, effect: int, ok, pl: str, en: str) -> dict:
    return {"field": field, "effect": effect, "ok": ok, "text": pl, "text_en": en}


def _adjust(name_score: float, entry: dict, birth: str, nationality: str, sex: str = "",
            sex_inferred: bool = False, doc: str = ""):
    """Secondary identifiers: document number, date of birth, nationality, gender."""
    score, factors = name_score, []
    if doc and doc in entry.get("ids", {}):
        d = entry["ids"][doc]
        label = d["type"] + (f", {d['country']}" if d.get("country") else "")
        score = max(score + 15, MATCH_THRESHOLD)
        factors.append(_factor("document", 15, True, f"Numer dokumentu zgodny: {d['number']} ({label})",
                               f"Document number matches: {d['number']} ({label})"))
    year, date = parse_birth(birth)
    births = entry["birth_dates"]
    if year:
        if not births:
            factors.append(_factor("birth", 0, None,
                                   "Brak daty urodzenia w rekordzie — nie można potwierdzić ani wykluczyć",
                                   "No date of birth in the record — cannot confirm or rule out"))
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
                factors.append(_factor("birth", 5, True, f"Data urodzenia zgodna ({date})",
                                       f"Date of birth matches ({date})"))
            elif year_ok:
                score += 3
                factors.append(_factor("birth", 3, True, f"Rok urodzenia zgodny ({year}; lista: {lst})",
                                       f"Year of birth matches ({year}; list: {lst})"))
            elif near:
                factors.append(_factor("birth", 0, None, f"Rok urodzenia zbliżony (±1–2): {year} vs {lst}",
                                       f"Year of birth close (±1–2): {year} vs {lst}"))
            else:
                score -= 15
                factors.append(_factor("birth", -15, False,
                                       f"Inny rok urodzenia: {year} vs {lst} — argument za false positive",
                                       f"Different year of birth: {year} vs {lst} — points to a false positive"))
    nat = (nationality or "").strip().upper()
    if nat:
        nats = [n.get("iso2") for n in entry["nationalities"] if n.get("iso2")]
        if not nats:
            factors.append(_factor("nationality", 0, None, "Brak obywatelstwa w rekordzie",
                                   "No nationality in the record"))
        elif nat in nats:
            score += 3
            factors.append(_factor("nationality", 3, True, f"Obywatelstwo zgodne ({nat})",
                                   f"Nationality matches ({nat})"))
        else:
            score -= 5
            factors.append(_factor("nationality", -5, False,
                                   f"Inne obywatelstwo: {nat} vs {', '.join(nats)} — argument za false positive",
                                   f"Different nationality: {nat} vs {', '.join(nats)} — points to a false positive"))
    if sex and entry["entity_type"] == "person" and entry.get("sex"):
        how_pl = " (wywnioskowana z imienia/nazwiska)" if sex_inferred else ""
        how_en = " (inferred from the name)" if sex_inferred else ""
        if entry["sex"] == sex:
            if not sex_inferred:              # an inferred match adds nothing worth showing
                score += 2
                factors.append(_factor("gender", 2, True, "Płeć zgodna", "Gender matches"))
        else:
            effect = -10 if sex_inferred else -15
            score += effect
            factors.append(_factor("gender", effect, False,
                                   f"Inna płeć: {sex} vs {entry['sex']}{how_pl} — argument za false positive",
                                   f"Different gender: {sex} vs {entry['sex']}{how_en} — points to a false positive"))
    return score, factors


# "-ина" is left out on purpose: Ukrainian surnames like Щербина are used by men too
_FEM = re.compile(r"(овна|евна|ична|івна|ївна|ова|ева|ёва|ская|цкая|ська|цька)$")
_MASC = re.compile(r"(ович|евич|ич|ов|ев|ёв|ин|ын|ский|цкий|ський|цький)$")
_FEM_LAT = re.compile(r"(ovna|evna|ivna|ichna|ova|eva|skaya|tskaya|ska|cka)$")
_MASC_LAT = re.compile(r"(ovich|evich|vych|ov|ev|in|yn|sky|skiy|skyi|skii|ski|cki|tskiy)$")


def infer_gender(q) -> str:
    """Conservative M/F guess from Slavic patronymic or surname endings; '' when unsure or conflicting."""
    votes = set()
    for tv in q:
        c = tv.cyrillic
        lat = tv.variants[0].norm if tv.variants else ""
        if c and len(c) >= 4:
            if _FEM.search(c):
                votes.add("F")
            elif _MASC.search(c):
                votes.add("M")
        elif len(lat) >= 5 and not c:
            if _FEM_LAT.search(lat):
                votes.add("F")
            elif _MASC_LAT.search(lat):
                votes.add("M")
    return votes.pop() if len(votes) == 1 else ""


# ---------------------------------------------------------------------- singleton

_index: Index | None = None
_lock = threading.Lock()


def get_index() -> Index:
    global _index
    with _lock:
        if _index is None:
            _index = Index().load_or_build()
        return _index


def rebuild_index() -> Index:
    global _index
    new = Index().load_or_build()
    with _lock:
        _index = new
    return new
