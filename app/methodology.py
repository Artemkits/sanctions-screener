"""Reference tables for the methodology page, generated from the live transliteration code."""
from functools import lru_cache

from .translit import SYSTEM_LABELS, bgn, by_passport, german, polish, popular, ru_gost, ru_icao, trace, ua_kmu2010

ALPHABETS = {
    "ru": "абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
    "uk": "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя",
    "be": "абвгдеёжзійклмнопрстуўфхцчшыьэюя",
}

# (column id, system code, language, function)
COLUMNS = [
    ("UA_KMU2010", "UA_KMU2010", "uk", ua_kmu2010),
    ("RU_ICAO", "RU_ICAO", "ru", ru_icao),
    ("RU_GOST", "RU_GOST", "ru", ru_gost),
    ("BGN_RU", "BGN", "ru", lambda w: bgn(w, "ru")),
    ("POP_RU", "POP", "ru", lambda w: popular(w, "ru")),
    ("PL_RU", "PL", "ru", lambda w: polish(w, "ru")),
    ("PL_UK", "PL", "uk", lambda w: polish(w, "uk")),
    ("DE_RU", "DE", "ru", lambda w: german(w, "ru")),
    ("BY_PASS", "BY_PASS", "be", by_passport),
]

# contexts: (label, prefix, suffix) — the letter is placed between them
CONTEXTS = [("initial", "", "ат"), ("middle", "т", "ат"), ("after_vowel", "а", "ат"), ("before_soft", "т", "ет")]

LETTER_ORDER = "абвгґдеєёжзиіїйклмнопрстуўфхцчшщъыьэюя"

EXAMPLES = [("Сергій", "uk"), ("Сергей", "ru"), ("Юрій", "uk"), ("Юрий", "ru"), ("Олександр", "uk"),
            ("Александр", "ru"), ("Аляксандр", "be"), ("Євген", "uk"), ("Евгений", "ru"), ("Щербина", "uk"),
            ("Щербина", "ru"), ("Хмельницький", "uk"), ("Хмельницкий", "ru"), ("Пригожин", "ru"),
            ("Лукашэнка", "be"), ("Наталья", "ru")]


def _outputs(fn, letter: str) -> list[dict]:
    seen, out = {}, []
    for ctx, pre, suf in CONTEXTS:
        pieces = trace(fn, pre + letter + suf)
        pos = len(pre)
        chunk = next((p for p in pieces if p[0] <= pos < p[0] + len(p[1])), None)
        if chunk is None or len(chunk[1]) != 1:      # letter consumed by a multi-letter rule
            continue
        latin = chunk[2]
        if latin not in seen:
            seen[latin] = len(out)
            out.append({"latin": latin, "contexts": [ctx]})
        else:
            out[seen[latin]]["contexts"].append(ctx)
    return out


@lru_cache(maxsize=1)
def letter_table() -> dict:
    rows = []
    for letter in LETTER_ORDER:
        cells = {}
        for col, _, lang, fn in COLUMNS:
            if letter in ALPHABETS[lang]:
                cells[col] = _outputs(fn, letter)
        rows.append({"letter": letter, "langs": [lg for lg, a in ALPHABETS.items() if letter in a], "cells": cells})
    columns = [{"id": c, "system": s, "lang": lg, "label": SYSTEM_LABELS[s]} for c, s, lg, _ in COLUMNS]
    examples = []
    for word, wlang in EXAMPLES:
        w = word.lower()
        examples.append({"word": word, "lang": wlang,
                         "cells": {c: fn(w).capitalize() for c, _, lang, fn in COLUMNS if lang == wlang}})
    return {"columns": columns, "rows": rows, "examples": examples}
