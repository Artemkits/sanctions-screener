"""Check real names from the lists and compare with a no-transliteration baseline.

Baseline = what a naive screener does: unidecode the input and take the best
rapidfuzz token_sort_ratio over every alias in the database.

    python -m scripts.evaluate
"""
import time

from rapidfuzz import fuzz, process

from app.matcher import get_index
from app.text import norm_latin

CASES = [
    # (query, birth, nationality, what it demonstrates)
    ("Евгений Пригожин", "1961", "", "exact (Russian Cyrillic) + DOB"),
    ("Wiaczesław Wołodin", "", "", "Polish spelling — found only through transliteration"),
    ("Ramzan Kadyrow", "", "", "Polish spelling — found only through transliteration"),
    ("Aleksiej Miller", "", "", "Polish spelling — found only through transliteration"),
    ("Ołeksandr Chodakowski", "", "", "Polish spelling of a Ukrainian name"),
    ("Ołeh Cariow", "", "", "Polish c = ts"),
    ("Siergiej Ławrow", "", "", "Polish press spelling"),
    ("Сергій Цеков", "", "", "Ukrainian Cyrillic, list has Russian form"),
    ("Аляксандр Лукашэнка", "", "", "Belarusian Cyrillic, -енка ↔ -енко"),
    ("Юрий Ковальчук", "1951", "RU", "exact + DOB + nationality"),
    ("Юрий Ковальчук", "1984", "UA", "same name, other DOB/nationality → false positive"),
    ("Siergiej Iwanow", "1990", "PL", "common name → false positive"),
    ("Jan Kowalski", "1985", "PL", "clean customer"),
]


def main():
    ix = get_index()
    all_aliases = [norm_latin(a["name"]) for a in ix.aliases.values()]
    print(f"{'query':28} {'ours':>5} {'base':>5} {'ms':>5}  status    best hit (list) / matched alias")
    for q, b, n, note in CASES:
        t0 = time.time()
        res = ix.search(q, birth=b, nationality=n)
        ms = (time.time() - t0) * 1000
        base = process.extractOne(norm_latin(q), all_aliases, scorer=fuzz.token_sort_ratio)
        hit = res["results"][0] if res["results"] else None
        label = f"{q}{' ' + b if b else ''}{' ' + n if n else ''}"
        if hit:
            print(f"{label[:28]:28} {hit['score']:5.0f} {base[1]:5.0f} {ms:5.0f}  {hit['status']:8}  "
                  f"{hit['primary_name']} ({hit['source']}) / {hit['matched_alias']}")
        else:
            print(f"{label[:28]:28} {'—':>5} {base[1]:5.0f} {ms:5.0f}  clear     —")
        print(f"{'':28} {note}")


if __name__ == "__main__":
    main()
