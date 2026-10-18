from dataclasses import dataclass, field


@dataclass
class Alias:
    name: str
    lang: str = ""
    quality: str = "strong"   # primary | strong | weak


@dataclass
class Entry:
    source: str
    source_id: str
    entity_type: str
    primary_name: str
    aliases: list = field(default_factory=list)          # list[Alias]
    birth_dates: list = field(default_factory=list)      # list[dict]
    nationalities: list = field(default_factory=list)    # list[{iso2, name}]
    programs: list = field(default_factory=list)
    listed_on: str = ""
    url: str = ""
    remarks: str = ""
    extra: dict = field(default_factory=dict)


@dataclass
class ParseResult:
    entries: list
    list_date: str


def norm_id(number: str) -> str:
    """Document numbers compared without spaces, dashes or case: 'AB 18-7304' == 'ab187304'."""
    return "".join(ch for ch in (number or "").upper() if ch.isalnum())


def norm_sex(value: str) -> str:
    v = (value or "").strip().lower()
    if v in ("m", "male", "mężczyzna"):
        return "M"
    if v in ("f", "female", "k", "kobieta"):
        return "F"
    return ""


def make_id(id_type: str, number: str, country: str = "") -> dict | None:
    n = norm_id(number)
    if len(n) < 4 or not any(ch.isdigit() for ch in n):
        return None
    return {"type": (id_type or "").strip(), "number": (number or "").strip(), "country": (country or "").strip()}
