"""Map free-text country names from the lists to ISO 3166-1 alpha-2 codes."""
from functools import lru_cache

import pycountry

_MANUAL = {
    "russia": "RU", "russian federation": "RU", "iran": "IR", "iran (islamic republic of)": "IR",
    "syria": "SY", "syrian arab republic": "SY", "north korea": "KP", "korea, north": "KP",
    "democratic people's republic of korea": "KP", "south korea": "KR", "korea, south": "KR",
    "republic of korea": "KR", "venezuela": "VE", "bolivia": "BO", "tanzania": "TZ",
    "united republic of tanzania": "TZ", "moldova": "MD", "republic of moldova": "MD",
    "laos": "LA", "vietnam": "VN", "viet nam": "VN", "turkey": "TR", "turkiye": "TR", "türkiye": "TR",
    "burma": "MM", "democratic republic of the congo": "CD", "congo, democratic republic of the": "CD",
    "congo": "CG", "republic of the congo": "CG", "palestinian": "PS", "palestine": "PS",
    "state of palestine": "PS", "west bank": "PS", "gaza": "PS", "kosovo": "XK",
    "united kingdom": "GB", "united kingdom of great britain and northern ireland": "GB", "uk": "GB",
    "united states": "US", "united states of america": "US", "usa": "US", "belarus": "BY",
    "ukraine": "UA", "czech republic": "CZ", "czechia": "CZ", "the former yugoslav republic of macedonia": "MK",
    "macedonia": "MK", "cote d'ivoire": "CI", "côte d'ivoire": "CI", "ivory coast": "CI",
    "cabo verde": "CV", "brunei": "BN", "micronesia": "FM", "region: gaza": "PS", "taiwan": "TW",
    "hong kong": "HK", "macau": "MO", "cuba": "CU", "libya": "LY", "iraq": "IQ", "yemen": "YE",
    "afghanistan": "AF", "sudan": "SD", "south sudan": "SS", "somalia": "SO", "mali": "ML",
}


@lru_cache(maxsize=4096)
def to_iso2(name: str) -> str:
    if not name:
        return ""
    key = name.strip().lower()
    if key in _MANUAL:
        return _MANUAL[key]
    if len(key) == 2 and pycountry.countries.get(alpha_2=key.upper()):
        return key.upper()
    try:
        return pycountry.countries.lookup(name.strip()).alpha_2
    except LookupError:
        pass
    try:
        hits = pycountry.countries.search_fuzzy(name.strip())
        return hits[0].alpha_2 if hits else ""
    except LookupError:
        return ""


def country_name(iso2: str) -> str:
    c = pycountry.countries.get(alpha_2=iso2.upper()) if iso2 else None
    return c.name if c else iso2
