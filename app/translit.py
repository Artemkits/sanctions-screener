"""Transliteration variant generator — the core of the screener.

For a name typed in Cyrillic we produce every plausible Latin spelling:

* named systems (each variant remembers which system produced it):
  - UA_KMU2010  Ukrainian official (Cabinet of Ministers resolution No. 55, 2010)
  - RU_ICAO     Russian passports since 2013 (ICAO Doc 9303)
  - RU_GOST     GOST 7.79-2000, system B (ASCII)
  - BGN         BGN/PCGN (Russian 1947 / Ukrainian 1965 / Belarusian 1979)
  - POP         common English newspaper spelling (Sergey, Yuriy, Serhiy)
  - PL          Polish transcription (PWN rules: Siergiej, Szczerbina, Ołeksandr)
  - DE          German transcription (Duden: Sergej, Schtscherbina)
  - BY_PASS     Belarusian passports (ICAO-based national system)
* VAR — a weighted beam search over per-letter alternatives (и/й/ий → i/y/iy/ii/yi,
  х → kh/h/ch, щ → shch/sch/szcz, ...), pruned by plausibility;
* EQUIV — Ukrainian/Belarusian ↔ Russian forms of the same given name
  (Сергій ↔ Сергей, Олександр ↔ Александр, Аляксандр ↔ Александр), because lists
  often record a Ukrainian citizen under the Russian form of their first name.

For a name typed in Latin we normalise it (diacritics removed) and generate
spelling alternatives between transliteration conventions (sz ↔ sh, cz ↔ ch,
w ↔ v, -ij ↔ -iy ↔ -y ...). Matching additionally uses the phonetic skeleton
from app.text, which catches whatever the explicit variants miss.
"""
from __future__ import annotations

import heapq
import math
import re
from dataclasses import dataclass, field

from .text import detect_script, fix_homoglyphs, norm_cyrillic, norm_latin, skeleton, split_tokens

SYSTEM_LABELS = {
    "UA_KMU2010": "UA — KMU 2010 (oficjalna ukraińska)",
    "RU_ICAO": "RU — ICAO 9303 (paszporty)",
    "RU_GOST": "RU — GOST 7.79-2000 (B)",
    "BGN": "BGN/PCGN",
    "POP": "angielska potoczna",
    "PL": "polska (PWN)",
    "DE": "niemiecka (Duden)",
    "BY_PASS": "BY — paszportowa",
    "VAR": "wariant fonetyczny",
    "LATIN": "zapis łaciński (wejście)",
    "LATIN_ALT": "alternatywna pisownia łacińska",
}

VOWELS = set("аеёиоуыэюяіїє")
SIGNS = set("ьъ'")
HUSHING = set("жшчщц")
SOFTENERS_RU = set("еёюяиь")
SOFTENERS_UK = set("єїюяіь")
SOFTENERS_BE = set("еёюяіь")

MAX_VAR_PER_TOKEN = 24
MAX_LATIN_ALT = 16


# --------------------------------------------------------------------------
# language detection
# --------------------------------------------------------------------------

def detect_language(text: str) -> list[str]:
    """Guess uk / ru / be from characteristic letters; ambiguous → all three."""
    t = text.lower()
    if "ў" in t or ("і" in t and re.search(r"[ыэ]", t)):
        return ["be"]
    if re.search(r"[іїєґ]", t):
        return ["uk"]
    if "ъ" in t:
        return ["ru"]
    if re.search(r"[ыэ]", t):          # ы/э exist in Belarusian too
        return ["ru", "be"]
    return ["uk", "ru", "be"]


# --------------------------------------------------------------------------
# helpers for rule-based systems
# --------------------------------------------------------------------------

def _prev(w, i):
    return w[i - 1] if i > 0 else ""


def _next(w, i, k=1):
    return w[i + k] if i + k < len(w) else ""


def _iotated_pos(w, i):
    """Word start, or after a vowel / soft or hard sign / apostrophe."""
    p = _prev(w, i)
    return i == 0 or p in VOWELS or p in SIGNS


def _run(word: str, rule) -> str:
    out, i = [], 0
    while i < len(word):
        res, used = rule(word, i)
        out.append(res)
        i += used
    return "".join(out)


def _ending(w, i, *endings):
    """True if w[i:] equals one of the given endings."""
    return w[i:] in endings


# --------------------------------------------------------------------------
# named systems
# --------------------------------------------------------------------------

_UA_KMU = dict(а="a", б="b", в="v", г="h", ґ="g", д="d", е="e", є="ie", ж="zh", з="z", и="y", і="i",
               ї="i", й="i", к="k", л="l", м="m", н="n", о="o", п="p", р="r", с="s", т="t", у="u",
               ф="f", х="kh", ц="ts", ч="ch", ш="sh", щ="shch", ь="", ю="iu", я="ia", ы="y", э="e",
               ё="io", ъ="", ў="u")
_UA_KMU["'"] = ""
_UA_KMU_INITIAL = dict(є="ye", ї="yi", й="y", ю="yu", я="ya", ё="yo")


def ua_kmu2010(w: str) -> str:
    def rule(w, i):
        c = w[i]
        if c == "з" and _next(w, i) == "г":
            return "zgh", 2
        if i == 0 and c in _UA_KMU_INITIAL:
            return _UA_KMU_INITIAL[c], 1
        return _UA_KMU.get(c, c), 1
    return _run(w, rule)


_RU_ICAO = dict(а="a", б="b", в="v", г="g", д="d", е="e", ё="e", ж="zh", з="z", и="i", й="i", к="k",
                л="l", м="m", н="n", о="o", п="p", р="r", с="s", т="t", у="u", ф="f", х="kh", ц="ts",
                ч="ch", ш="sh", щ="shch", ъ="ie", ы="y", ь="", э="e", ю="iu", я="ia", і="i", ї="i",
                є="ie", ґ="g", ў="u")
_RU_ICAO["'"] = ""


def ru_icao(w: str) -> str:
    return "".join(_RU_ICAO.get(c, c) for c in w)


_RU_GOST = dict(а="a", б="b", в="v", г="g", д="d", е="e", ё="yo", ж="zh", з="z", и="i", й="j", к="k",
                л="l", м="m", н="n", о="o", п="p", р="r", с="s", т="t", у="u", ф="f", х="x", ч="ch",
                ш="sh", щ="shh", ъ="", ы="y", ь="", э="e", ю="yu", я="ya", і="i", ї="yi", є="ye",
                ґ="g", ў="u")
_RU_GOST["'"] = ""


def ru_gost(w: str) -> str:
    def rule(w, i):
        c = w[i]
        if c == "ц":   # GOST 7.79 B: c before i, e, y, j; cz elsewhere
            return ("c" if _next(w, i) in ("и", "е", "ы", "й", "і", "є") else "cz"), 1
        return _RU_GOST.get(c, c), 1
    return _run(w, rule)


_BGN_COMMON = dict(а="a", б="b", в="v", д="d", ж="zh", з="z", к="k", л="l", м="m", н="n", о="o",
                   п="p", р="r", с="s", т="t", у="u", ф="f", х="kh", ц="ts", ч="ch", ш="sh",
                   щ="shch", ь="", ъ="", ы="y", э="e", ґ="g", ў="w")
_BGN_COMMON["'"] = ""


def bgn(w: str, lang: str) -> str:
    def rule(w, i):
        c = w[i]
        iot = _iotated_pos(w, i) or _prev(w, i) == "й"
        if lang == "uk":
            m = {"г": "h", "е": "e", "и": "y", "і": "i", "й": "y",
                 "є": "ye" if iot else "ie", "ї": "yi" if iot else "i",
                 "ю": "yu" if iot else "iu", "я": "ya" if iot else "ia"}
        elif lang == "be":
            m = {"г": "h", "е": "ye" if iot else "e", "ё": "yo", "і": "i", "и": "i", "й": "y",
                 "ю": "yu", "я": "ya"}
        else:
            m = {"г": "g", "е": "ye" if iot else "e", "ё": "ye" if iot else "e", "и": "i", "й": "y",
                 "ю": "yu", "я": "ya", "і": "i", "ї": "yi", "є": "ye"}
        if c in m:
            return m[c], 1
        return _BGN_COMMON.get(c, c), 1
    return _run(w, rule)


def popular(w: str, lang: str) -> str:
    """Typical English media spelling: Sergey, Evgeny, Yury / Serhiy, Yuriy, Oleksiy."""
    def rule(w, i):
        c = w[i]
        if c in "иіы" and _ending(w, i, "ий", "ій", "ый"):
            return ("iy" if lang == "uk" or c == "і" else "y"), 2
        if c == "е" and _ending(w, i, "ей"):
            return "ey", 2
        m = {"й": "y", "ё": "yo", "ю": "yu", "я": "ya", "х": "kh", "ж": "zh", "ц": "ts", "щ": "shch",
             "є": "ye", "ї": "yi", "і": "i", "ь": "", "ъ": "", "'": "", "ў": "w"}
        if lang == "uk":
            m.update({"г": "h", "и": "y", "е": "e"})
        elif lang == "be":
            m.update({"г": "h", "и": "i", "е": "ye" if _iotated_pos(w, i) else "e"})
        else:
            m.update({"г": "g", "и": "i", "е": "e"})
        if c in m:
            return m[c], 1
        return _BGN_COMMON.get(c, c), 1
    return _run(w, rule)


def polish(w: str, lang: str) -> str:
    """Polish transcription (Słownik ortograficzny PWN rules), with diacritics."""
    soft = SOFTENERS_UK if lang == "uk" else (SOFTENERS_BE if lang == "be" else SOFTENERS_RU)

    def l_form(w, i):
        n = _next(w, i)
        return "l" if n in soft else "ł"

    def rule(w, i):
        c, p, n = w[i], _prev(w, i), _next(w, i)
        iot = _iotated_pos(w, i)
        # -ский / -цкий → -ski / -cki (Russian); -ський / -цький → -śkyj / -ćkyj (Ukrainian)
        if lang != "uk":
            for end, rep in (("ский", "ski"), ("цкий", "cki"), ("ская", "ska"), ("цкая", "cka")):
                if _ending(w, i, end):
                    return rep, len(end)
        if c == "л":
            return l_form(w, i), 1
        if c in "нсзцт" and n == "ь" and (_next(w, i, 2) == "" or _next(w, i, 2) not in VOWELS):
            return {"н": "ń", "с": "ś", "з": "ź", "ц": "ć", "т": "ć"}[c], 2
        if c == "ь" or c == "ъ" or c == "'":
            return "", 1
        if c in ("е", "є"):
            if lang == "uk" and c == "е":
                return "e", 1
            if iot:
                return "je", 1
            if p in HUSHING or p == "л":
                return "e", 1
            return "ie", 1
        if c == "ё":
            return ("jo" if iot else ("o" if p in HUSHING or p == "л" else "io")), 1
        if c in ("ю", "я"):
            v = "u" if c == "ю" else "a"
            if iot:
                return "j" + v, 1
            return (v if p == "л" else "i" + v), 1
        if c == "и":
            if lang == "uk":
                return "y", 1
            return ("y" if p in "жшц" else "i"), 1
        if c == "ї":
            return "ji", 1
        if c == "г":
            return ("h" if lang in ("uk", "be") else "g"), 1
        m = dict(а="a", б="b", в="w", ґ="g", д="d", ж="ż", з="z", і="i", й="j", к="k", м="m", н="n",
                 о="o", п="p", р="r", с="s", т="t", у="u", ф="f", х="ch", ц="c", ч="cz", ш="sz",
                 щ="szcz", ы="y", э="e", ў="u")
        return m.get(c, c), 1
    return _run(w, rule)


def german(w: str, lang: str) -> str:
    """German transcription (Duden): Sergej, Jewgeni, Schtscherbina, Prigoschin."""
    def rule(w, i):
        c, p, n = w[i], _prev(w, i), _next(w, i)
        iot = _iotated_pos(w, i)
        for end, rep in (("ский", "ski"), ("цкий", "zki"), ("ський", "skyj"), ("цький", "zkyj")):
            if _ending(w, i, end):
                return rep, len(end)
        if c in "иі" and _ending(w, i, "ий", "ій"):
            return ("i" if lang != "uk" else "ij"), 2
        if c == "ы" and _ending(w, i, "ый"):
            return "y", 2
        if c == "й":
            return ("j" if p in "еэ" or i == 0 else "i"), 1
        if c == "е":
            return ("je" if iot and lang != "uk" else "e"), 1
        if c == "ё":
            return ("o" if p in HUSHING else "jo"), 1
        if c == "с":
            return ("ss" if p in VOWELS and n in VOWELS else "s"), 1
        m = dict(а="a", б="b", в="w", г=("h" if lang in ("uk", "be") else "g"), ґ="g", д="d", ж="sch",
                 з="s", и=("y" if lang == "uk" else "i"), і="i", ї="ji", є="je", к="k", л="l", м="m",
                 н="n", о="o", п="p", р="r", т="t", у="u", ф="f", х="ch", ц="z", ч="tsch", ш="sch",
                 щ="schtsch", ъ="", ы="y", ь="", э="e", ю="ju", я="ja", ў="w")
        m["'"] = ""
        return m.get(c, c), 1
    return _run(w, rule)


def by_passport(w: str) -> str:
    """Belarusian passport romanisation (ICAO-based): Aliaksandr, Lukashenka."""
    def rule(w, i):
        c = w[i]
        iot = _iotated_pos(w, i)
        m = dict(а="a", б="b", в="v", г="h", ґ="g", д="d", ж="zh", з="z", і="i", и="i", й="i", к="k",
                 л="l", м="m", н="n", о="o", п="p", р="r", с="s", т="t", у="u", ў="u", ф="f", х="kh",
                 ц="ts", ч="ch", ш="sh", щ="shch", ы="y", ь="", ъ="", э="e", ї="i")
        m["'"] = ""
        if c in "ёюяє":
            return "i" + {"ё": "o", "ю": "u", "я": "a", "є": "e"}[c], 1
        if c == "е":
            return ("ie" if iot else "e"), 1
        return m.get(c, c), 1
    return _run(w, rule)


def _systems_for(lang: str):
    if lang == "uk":
        return [("UA_KMU2010", ua_kmu2010), ("BGN", lambda w: bgn(w, "uk")),
                ("POP", lambda w: popular(w, "uk")), ("PL", lambda w: polish(w, "uk")),
                ("DE", lambda w: german(w, "uk"))]
    if lang == "be":
        return [("BY_PASS", by_passport), ("BGN", lambda w: bgn(w, "be")),
                ("POP", lambda w: popular(w, "be")), ("PL", lambda w: polish(w, "be"))]
    return [("RU_ICAO", ru_icao), ("RU_GOST", ru_gost), ("BGN", lambda w: bgn(w, "ru")),
            ("POP", lambda w: popular(w, "ru")), ("PL", lambda w: polish(w, "ru")),
            ("DE", lambda w: german(w, "ru"))]


def russify(w: str) -> str:
    """Spelling of an unmarked token as a Russian word (-ський → -ский)."""
    return re.sub(r"([сц])ьк(ий|ій|а|е|и)$", r"\1к\2", w)


# --------------------------------------------------------------------------
# VAR: weighted letter-level alternatives with beam search
# --------------------------------------------------------------------------

def _var_options(w: str, i: int, lang: str):
    """Return (consumed, [(latin, weight), ...]) for position i."""
    c, p, n = w[i], _prev(w, i), _next(w, i)
    iot = _iotated_pos(w, i)
    rest = w[i:]
    # endings
    if rest in ("ий", "ій", "ый", "ьій"):
        return 2, [("iy", 1.0), ("ii", .9), ("y", .85), ("yi", .85), ("i", .75), ("ij", .6), ("yy", .45)]
    if rest == "ей":
        return 2, [("ey", 1.0), ("ei", .9), ("ej", .6)]
    if rest == "ой":
        return 2, [("oy", 1.0), ("oi", .8), ("oj", .5)]
    if rest == "ай":
        return 2, [("ay", 1.0), ("ai", .9), ("aj", .5)]
    if c == "к" and n == "с":
        return 2, [("ks", 1.0), ("x", .55)]
    table = {
        "а": [("a", 1)], "б": [("b", 1)], "в": [("v", 1), ("w", .5)], "д": [("d", 1)],
        "ґ": [("g", 1)], "з": [("z", 1), ("s", .3)], "к": [("k", 1)], "л": [("l", 1)],
        "м": [("m", 1)], "н": [("n", 1)], "о": [("o", 1)], "п": [("p", 1)], "р": [("r", 1)],
        "с": [("s", 1)], "т": [("t", 1)], "у": [("u", 1)], "ф": [("f", 1)], "ў": [("u", 1), ("w", .8)],
        "г": [("h", 1), ("g", .8)] if lang in ("uk", "be") else [("g", 1), ("h", .35)],
        "ж": [("zh", 1), ("z", .5), ("j", .3), ("sch", .25)],
        "х": [("kh", 1), ("h", .8), ("ch", .55), ("x", .25)],
        "ц": [("ts", 1), ("c", .55), ("tz", .4), ("z", .3)],
        "ч": [("ch", 1), ("cz", .55), ("tch", .3), ("tsch", .25)],
        "ш": [("sh", 1), ("sz", .55), ("sch", .4)],
        "щ": [("shch", 1), ("sch", .6), ("szcz", .55), ("shh", .3), ("schtsch", .25), ("sh", .3)],
        "ь": [("", 1), ("i", .15)], "ъ": [("", 1), ("ie", .2)], "'": [("", 1)],
        "ы": [("y", 1), ("i", .6)], "э": [("e", 1)],
        "і": [("i", 1), ("y", .3)],
        "ї": [("yi", 1), ("i", .8), ("ji", .5)],
        "й": [("y", 1), ("i", .9), ("j", .6)],
    }
    if c == "и":
        opts = [("y", 1), ("i", .8)] if lang == "uk" else [("i", 1), ("y", .45 if p not in HUSHING else .8)]
        return 1, opts
    if c in ("е", "є", "ё"):
        if c == "ё":
            opts = [("e", 1), ("yo", .9), ("io", .6), ("jo", .5)]
        elif c == "є" or iot:
            opts = [("ye", 1), ("e", .9), ("ie", .7), ("je", .5)]
        else:
            opts = [("e", 1), ("ie", .3)]
        return 1, opts
    if c in ("ю", "я"):
        v = "u" if c == "ю" else "a"
        opts = [("y" + v, 1), ("i" + v, .9), ("j" + v, .55)]
        if p == "л" or p == "ь":
            opts.append((v, .3))
        return 1, opts
    return 1, table.get(c, [(c, 1)])


def var_variants(w: str, lang: str, k: int = MAX_VAR_PER_TOKEN) -> list[tuple[str, float]]:
    """Beam search over letter alternatives; returns top-k (latin, plausibility)."""
    units, i = [], 0
    while i < len(w):
        used, opts = _var_options(w, i, lang)
        units.append([(s, math.log(wt)) for s, wt in opts if wt > 0])
        i += used
    beam = [(0.0, "")]
    width = k * 3
    for opts in units:
        cand = [(score + lw, s + o) for score, s in beam for o, lw in opts]
        beam = heapq.nlargest(width, cand)
    seen, out = set(), []
    for score, s in sorted(beam, reverse=True):
        if s not in seen:
            seen.add(s)
            out.append((s, math.exp(score)))
        if len(out) >= k:
            break
    return out


# --------------------------------------------------------------------------
# given-name equivalents (uk / be ↔ ru)
# --------------------------------------------------------------------------

_EQUIV_GROUPS = [
    # (ru, uk, be)
    ("александр", "олександр", "аляксандр"), ("алексей", "олексій", "аляксей"),
    ("сергей", "сергій", "сяргей"), ("юрий", "юрій", "юрый"), ("игорь", "ігор", "ігар"),
    ("андрей", "андрій", "андрэй"), ("дмитрий", "дмитро", "дзмітрый"), ("николай", "микола", "мікалай"),
    ("михаил", "михайло", "міхаіл"), ("владимир", "володимир", "уладзімір"), ("пётр", "петро", "пётр"),
    ("петр", "петро", "пятро"), ("павел", "павло", "павел"), ("евгений", "євген", "яўген"),
    ("виктор", "віктор", "віктар"), ("василий", "василь", "васіль"), ("анатолий", "анатолій", "анатоль"),
    ("иван", "іван", "іван"), ("григорий", "григорій", "рыгор"), ("виталий", "віталій", "віталь"),
    ("валерий", "валерій", "валерый"), ("геннадий", "геннадій", "генадзь"), ("вячеслав", "вячеслав", "вячаслаў"),
    ("олег", "олег", "алег"), ("антон", "антон", "антон"), ("роман", "роман", "раман"),
    ("константин", "костянтин", "канстанцін"), ("леонид", "леонід", "леанід"), ("борис", "борис", "барыс"),
    ("фёдор", "федір", "фёдар"), ("федор", "федір", "фёдар"), ("степан", "степан", "сцяпан"),
    ("тарас", "тарас", "тарас"), ("богдан", "богдан", "багдан"), ("ярослав", "ярослав", "яраслаў"),
    ("елена", "олена", "алена"), ("ольга", "ольга", "вольга"), ("наталья", "наталія", "наталля"),
    ("татьяна", "тетяна", "таццяна"), ("ирина", "ірина", "ірына"), ("юлия", "юлія", "юлія"),
    ("светлана", "світлана", "святлана"), ("екатерина", "катерина", "кацярына"), ("мария", "марія", "марыя"),
    ("анна", "ганна", "ганна"), ("людмила", "людмила", "людміла"), ("галина", "галина", "галіна"),
    ("валентина", "валентина", "валянціна"), ("любовь", "любов", "любоў"), ("надежда", "надія", "надзея"),
    ("оксана", "оксана", "аксана"), ("виктория", "вікторія", "вікторыя"), ("лариса", "лариса", "ларыса"),
]
_EQUIV = {}
for _group in _EQUIV_GROUPS:
    for _lang, _form in zip(("ru", "uk", "be"), _group):
        _EQUIV.setdefault(_form, set()).update(
            (l, f) for l, f in zip(("ru", "uk", "be"), _group) if f != _form)


def name_equivalents(w: str) -> list[tuple[str, str]]:
    """[(lang, form)] — the same given name in the other East Slavic languages."""
    out = sorted(_EQUIV.get(w, set()))
    # Belarusian surnames -енка ↔ Ukrainian/Russian -енко (Лукашэнка / Лукашенко)
    if w.endswith("енка") or w.endswith("энка"):
        out.append(("ru", w[:-4] + "енко"))
    elif w.endswith("енко"):
        out.append(("be", w[:-4] + "энка"))
    return out


# --------------------------------------------------------------------------
# Latin input: alternatives between conventions
# --------------------------------------------------------------------------

_LATIN_UNITS = [
    (r"schtsch", ["schtsch", "shch", "szcz"]), (r"shch", ["shch", "szcz", "sch", "shh"]),
    (r"szcz", ["szcz", "shch", "sch"]), (r"tsch", ["tsch", "ch", "cz"]), (r"sch", ["sch", "sh", "shch", "sz"]),
    (r"iej$", ["iej", "ey", "ei"]), (r"(iy|ii|yi|ij|yj)$", ["iy", "ii", "y", "yi", "ij", "i"]),
    (r"(ey|ei|ej)$", ["ey", "ei", "ej"]),
    (r"sz", ["sz", "sh"]), (r"sh", ["sh", "sz", "sch"]), (r"cz", ["cz", "ch"]), (r"zh", ["zh", "z"]),
    (r"kh", ["kh", "h", "ch"]), (r"ch", ["ch", "kh", "h", "cz"]), (r"ts", ["ts", "c", "tz"]),
    (r"tz", ["tz", "ts", "c"]), (r"(yu|iu|ju)", ["yu", "iu", "ju"]), (r"(ya|ia|ja)", ["ya", "ia", "ja"]),
    (r"(?<=[bcdfghklmnprstvwz])ie", ["ie", "e"]), (r"(ye|je)", ["ye", "e", "ie", "je"]),
    (r"w", ["w", "v"]), (r"v", ["v", "w"]), (r"x", ["x", "ks"]), (r"ks", ["ks", "x"]),
    (r"c(?![hz])", ["c", "ts", "k"]),
    (r"j", ["j", "y", "i"]), (r"y", ["y", "i"]), (r"h", ["h", "g"]), (r"g", ["g", "h"]),
]
_LATIN_RX = re.compile("|".join(f"(?P<u{i}>{p})" for i, (p, _) in enumerate(_LATIN_UNITS)))


def latin_alternatives(token: str, k: int = MAX_LATIN_ALT) -> list[tuple[str, float]]:
    units, pos = [], 0
    for m in _LATIN_RX.finditer(token):
        if m.start() > pos:
            units.append([(token[pos:m.start()], 0.0)])
        idx = int(m.lastgroup[1:])
        orig = m.group(0)
        opts = [(orig, 0.0)] + [(o, math.log(.6)) for o in _LATIN_UNITS[idx][1] if o != orig]
        units.append(opts)
        pos = m.end()
    if pos < len(token):
        units.append([(token[pos:], 0.0)])
    beam = [(0.0, "")]
    for opts in units:
        beam = heapq.nlargest(k * 3, [(s + lw, t + o) for s, t in beam for o, lw in opts])
    seen, out = set(), []
    for s, t in sorted(beam, reverse=True):
        if t not in seen:
            seen.add(t)
            out.append((t, math.exp(s)))
        if len(out) >= k:
            break
    return out


# --------------------------------------------------------------------------
# public API
# --------------------------------------------------------------------------

@dataclass
class Variant:
    text: str                 # display form of the best origin
    norm: str                 # normalised latin form used for matching
    weight: float             # plausibility 0..1
    origins: list = field(default_factory=list)   # [(system, lang, source_form, display)]

    @property
    def systems(self):
        out = []
        for sysname, *_ in self.origins:
            if sysname not in out:
                out.append(sysname)
        return out

    @property
    def source_form(self):
        return self.origins[0][2] if self.origins else ""

    def to_dict(self):
        return {"text": self.text, "norm": self.norm, "weight": round(self.weight, 3),
                "systems": self.systems, "source_form": self.source_form}


@dataclass
class TokenVariants:
    original: str
    script: str
    langs: list
    variants: list            # list[Variant], best first
    cyrillic: str = ""        # normalised Cyrillic original (for direct Cyrillic matching)
    skeletons: set = field(default_factory=set)

    def norms(self):
        return [v.norm for v in self.variants]

    def to_dict(self):
        return {"original": self.original, "script": self.script, "langs": self.langs,
                "variants": [v.to_dict() for v in self.variants], "skeletons": sorted(self.skeletons)}


def _add(bucket: dict, display: str, weight: float, system: str, form: str, lang: str = ""):
    norm = norm_latin(display).replace(" ", "")
    if not norm:
        return
    v = bucket.get(norm)
    origin = (system, lang, form, display)
    if v is None:
        bucket[norm] = Variant(text=display, norm=norm, weight=weight, origins=[origin])
        return
    if origin not in v.origins:
        v.origins.append(origin)
    if weight > v.weight:
        v.weight = weight
        v.origins.remove(origin)
        v.origins.insert(0, origin)
        v.text = display


def token_variants(token: str, langs: list | None = None) -> TokenVariants:
    script = detect_script(token)
    bucket: dict[str, Variant] = {}
    if script == "cyrillic":
        w = norm_cyrillic(token.replace("ʼ", "'").replace("’", "'"))
        w_apos = fix_homoglyphs(token).lower().replace("ʼ", "'").replace("’", "'")
        w_apos = re.sub(r"[^Ѐ-ӿ']", "", w_apos)
        # Language is decided per token: a surname without characteristic letters
        # (Щербина, Ковальчук) is transliterated under all three languages.
        tok_langs = langs or detect_language(w)
        forms = [(lang, w_apos if lang == "uk" else (russify(w) if lang == "ru" else w), 1.0) for lang in tok_langs]
        for lang, form in name_equivalents(w):
            forms.append((lang, form, 0.9))
        for lang, form, fw in forms:
            for sysname, fn in _systems_for(lang):
                _add(bucket, fn(form).capitalize(), fw, sysname, form, lang)
        for lang, form, fw in forms:
            n_var = MAX_VAR_PER_TOKEN if fw == 1.0 else MAX_VAR_PER_TOKEN // 3
            for s, wt in var_variants(form.replace("'", ""), lang, n_var):
                _add(bucket, s.capitalize(), wt * fw * 0.95, "VAR", form, lang)
        variants = sorted(bucket.values(), key=lambda v: (-(v.weight + (0.5 if v.systems != ["VAR"] else 0)), v.norm))
        tv = TokenVariants(token, script, tok_langs, variants, cyrillic=w)
    else:
        base = norm_latin(token).replace(" ", "")
        if base:
            _add(bucket, token, 1.0, "LATIN", token)
            for s, wt in latin_alternatives(base):
                _add(bucket, s.capitalize(), wt, "LATIN_ALT", token)
        variants = sorted(bucket.values(), key=lambda v: (-v.weight, v.norm))
        tv = TokenVariants(token, script, [], variants)
    tv.skeletons = {skeleton(v.norm) for v in tv.variants}
    return tv


def name_variants(name: str) -> list[TokenVariants]:
    """Variants for every token of a full name (order-independent matching happens later)."""
    return [token_variants(t) for t in split_tokens(name)]


NAMED_SYSTEMS = ["UA_KMU2010", "RU_ICAO", "RU_GOST", "BGN", "POP", "PL", "DE", "BY_PASS"]
LANG_LABEL = {"uk": "ukr.", "ru": "ros.", "be": "białor."}


def name_languages(tvs: list[TokenVariants]) -> list[str]:
    """Languages consistent with every token (Сергій + Щербина → uk); ambiguous → all."""
    sets = [set(tv.langs) for tv in tvs if tv.langs]
    if not sets:
        return []
    common = set.intersection(*sets) or set.union(*sets)
    return sorted(common, key=["ru", "uk", "be"].index)


def full_name_examples(tvs: list[TokenVariants]) -> list[dict]:
    """One full-name rendering per (system, language) — shown to the analyst."""
    out, seen = [], set()
    for lang in name_languages(tvs):
        for sysname, _ in _systems_for(lang):
            parts = []
            for tv in tvs:
                origins = [o for v in tv.variants for o in v.origins if o[0] == sysname]
                own = [o for o in origins if o[2] in (tv.cyrillic, russify(tv.cyrillic)) or "'" in o[2]]
                pick = next((o for o in own if o[1] == lang), None) or (own[0] if own else None)
                if pick is None:
                    break
                parts.append(pick[3])
            else:
                text = " ".join(parts)
                if parts and text not in seen:
                    seen.add(text)
                    out.append({"system": sysname, "lang": lang, "text": text,
                                "label": f"{SYSTEM_LABELS[sysname]} · {LANG_LABEL[lang]}"})
    return out
