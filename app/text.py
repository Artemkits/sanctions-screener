"""Low-level text helpers: script detection, normalisation and the phonetic skeleton.

The *skeleton* is a deliberately lossy key that collapses spelling differences
typical for transliterated Slavic names (sh/sz/sch, ch/cz, kh/h/g, y/i/j,
ye/ie/je/e, -iy/-ii/-yi/-y ...). Two spellings of the same name usually share
the same skeleton even when no transliteration system produces both of them.
"""
import re
import unicodedata
from functools import lru_cache

from unidecode import unidecode

CYRILLIC = re.compile(r"[Ѐ-ӿ]")
ARABIC = re.compile(r"[؀-ۿݐ-ݿ]")
GREEK = re.compile(r"[Ͱ-Ͽ]")
LATIN = re.compile(r"[A-Za-zÀ-ɏ]")
APOSTROPHES = "'’ʼ`´‘"


def detect_script(text: str) -> str:
    if CYRILLIC.search(text):
        return "cyrillic"
    if ARABIC.search(text):
        return "arabic"
    if GREEK.search(text):
        return "greek"
    if LATIN.search(text):
        return "latin"
    return "other"


def split_tokens(text: str) -> list[str]:
    """Split a name into word tokens (keeps letters of any script)."""
    text = text.replace("ʼ", "'").replace("’", "'")
    return [t for t in re.split(r"[\s,.;:/()\[\]\"«»\-–—_]+", text) if t.strip("'")]


# Latin look-alikes that appear inside Cyrillic words in official lists ("Сергiй", "Пасiчник").
_HOMOGLYPHS = str.maketrans({"i": "і", "a": "а", "e": "е", "o": "о", "c": "с", "p": "р", "x": "х",
                             "y": "у", "k": "к", "m": "м", "t": "т", "h": "н", "b": "в"})


def fix_homoglyphs(token: str) -> str:
    """Replace Latin look-alike letters in a mostly Cyrillic token."""
    if not CYRILLIC.search(token) or not re.search(r"[a-zA-Z]", token):
        return token
    return token.lower().translate(_HOMOGLYPHS)


@lru_cache(maxsize=500_000)
def norm_cyrillic(token: str) -> str:
    t = fix_homoglyphs(token).lower().replace("ё", "е")
    for a in APOSTROPHES:
        t = t.replace(a, "")
    return re.sub(r"[^Ѐ-ӿ]", "", t)


def norm_latin(text: str) -> str:
    """Lowercase ASCII form: diacritics removed (ł→l, ż→z, ö→o ...)."""
    text = text.replace("ł", "l").replace("Ł", "L")
    for a in APOSTROPHES:
        text = text.replace(a, "")
    text = unicodedata.normalize("NFKC", text)
    text = unidecode(text).lower()
    text = text.replace("'", "")
    return re.sub(r"[^a-z0-9 ]+", " ", text).strip()


# Ordered rewrite rules for the skeleton. Uppercase letters are temporary
# placeholders so that later rules do not re-match the output of earlier ones.
_SKELETON_RULES = [
    (r"schtsch|shtch|shch|szcz|sch|shh|sh|sz", "S"),   # ш / щ
    (r"tsch|tch|cz|ch", "C"),                          # ч (English / Polish / German)
    (r"zh|zs", "z"),                                   # ж
    (r"kh", "G"), (r"h", "G"), (r"g", "G"),            # х / г / h-g
    (r"ck", "k"),
    (r"ts|tz|tc", "T"),                                 # ц
    (r"c(?=[keiy]|$)", "T"), (r"c", "k"),
    (r"x", "ks"), (r"q", "k"), (r"w", "v"), (r"ph", "f"),
    (r"j", "y"),
    (r"(ii|iy|yi|ij|yy|ey|ei|y)$", "I"),               # name endings -ий/-ій/-ей
    (r"[yi]u", "u"), (r"[yi]a", "a"), (r"[yi]o", "o"), (r"[yi]e", "e"),
    (r"y", "i"),
]
_SKELETON_RE = [(re.compile(p), r) for p, r in _SKELETON_RULES]


@lru_cache(maxsize=500_000)
def skeleton(token: str) -> str:
    """Phonetic key of a single *normalised latin* token."""
    s = token
    for rx, rep in _SKELETON_RE:
        s = rx.sub(rep, s)
    return re.sub(r"(.)\1+", r"\1", s.lower())


# Tokens that carry no identifying power on their own.
STOPWORDS = {"al", "el", "bin", "ibn", "bint", "abu", "abd", "von", "van", "der", "de", "la", "le",
             "da", "di", "du", "y", "and", "of", "the", "mr", "mrs", "ms", "dr"}

PATRONYMIC = re.compile(r"(v[iy](?:ch|tch|tsch|tj|tsj|c|cz)|wi?cz|ich|ych|vna|wna|ichna|ivna|yivna|ovny|evny)$")
CYR_PATRONYMIC = re.compile(r"(ович|евич|ёвич|ич|йович|ійович|овна|евна|ична|івна|ївна|авіч|явіч|аўна|еўна|аўна)$")


@lru_cache(maxsize=500_000)
def looks_like_patronymic(token: str) -> bool:
    """Latin or Cyrillic token that looks like a patronymic (Viktorovich, Олександрович)."""
    if len(token) <= 5:
        return False
    if CYRILLIC.search(token):
        return bool(CYR_PATRONYMIC.search(token))
    return bool(PATRONYMIC.search(token))


SURNAME_SUFFIX = re.compile(r"(ov|ev|iev|ova|eva|in|ina|yn|yna|enko|enka|uk|chuk|czuk|ko|sky|ski|skiy|skyi|skii|skij|cki|ckiy|tskyi|tsky|tskiy|ska|skaya|ych|ich|ovych|owicz|ewicz|ak|ek)$")
