"""Parser for the UN Security Council Consolidated List (XML)."""
import xml.etree.ElementTree as ET

from . import Alias, Entry, ParseResult
from .countries import to_iso2

UN_URL = "https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list"


def _txt(el, tag):
    return (el.findtext(tag) or "").strip()


def _whole_name(el):
    parts = [_txt(el, t) for t in ("FIRST_NAME", "SECOND_NAME", "THIRD_NAME", "FOURTH_NAME")]
    return " ".join(p for p in parts if p)


def _entry(el, etype) -> Entry | None:
    name = _whole_name(el)
    if not name:
        return None
    aliases = [Alias(name=name, lang="EN", quality="primary")]
    seen = {name.lower()}
    orig = _txt(el, "NAME_ORIGINAL_SCRIPT")
    if orig and orig.lower() not in seen:
        seen.add(orig.lower())
        aliases.append(Alias(name=orig, lang="ORIG", quality="strong"))
    alias_tag = "INDIVIDUAL_ALIAS" if etype == "person" else "ENTITY_ALIAS"
    for a in el.findall(alias_tag):
        an = _txt(a, "ALIAS_NAME")
        if an and an.lower() not in seen:
            seen.add(an.lower())
            quality = "weak" if _txt(a, "QUALITY").lower() == "low" else "strong"
            aliases.append(Alias(name=an, lang="EN", quality=quality))

    births = []
    for d in el.findall("INDIVIDUAL_DATE_OF_BIRTH"):
        date, year = _txt(d, "DATE"), _txt(d, "YEAR")
        fy, ty = _txt(d, "FROM_YEAR"), _txt(d, "TO_YEAR")
        if not (date or year or fy):
            continue
        y = int(date[:4]) if date[:4].isdigit() else (int(year) if year.isdigit() else None)
        births.append({
            "date": date, "year": y,
            "circa": _txt(d, "TYPE_OF_DATE").upper() in ("APPROXIMATELY", "BETWEEN"),
            "from_year": int(fy) if fy.isdigit() else None,
            "to_year": int(ty) if ty.isdigit() else None,
        })
    nats = []
    for v in el.findall("NATIONALITY/VALUE"):
        nm = (v.text or "").strip()
        iso = to_iso2(nm)
        if nm and not any(n["name"] == nm for n in nats):
            nats.append({"iso2": iso, "name": nm})
    places = []
    for p in el.findall("INDIVIDUAL_PLACE_OF_BIRTH"):
        s = ", ".join(x for x in (_txt(p, "CITY"), _txt(p, "STATE_PROVINCE"), _txt(p, "COUNTRY")) if x)
        if s:
            places.append(s)
    for b in births:
        b.setdefault("place", places[0] if places else "")

    return Entry(
        source="UN",
        source_id=_txt(el, "REFERENCE_NUMBER") or _txt(el, "DATAID"),
        entity_type=etype,
        primary_name=name,
        aliases=aliases,
        birth_dates=births,
        nationalities=nats,
        programs=[_txt(el, "UN_LIST_TYPE")] if _txt(el, "UN_LIST_TYPE") else [],
        listed_on=_txt(el, "LISTED_ON"),
        url=_txt(el, "INTERPOL_LINK") or UN_URL,
        remarks=_txt(el, "COMMENTS1")[:2000],
        extra={
            "reference": _txt(el, "REFERENCE_NUMBER"),
            "dataid": _txt(el, "DATAID"),
            "gender": _txt(el, "GENDER"),
            "function": "; ".join((v.text or "").strip() for v in el.findall("DESIGNATION/VALUE") if v.text),
        },
    )


def parse(path) -> ParseResult:
    entries, list_date = [], ""
    for event, el in ET.iterparse(path, events=("start", "end")):
        if event == "start" and el.tag == "CONSOLIDATED_LIST":
            list_date = (el.get("dateGenerated") or "")[:10]
        elif event == "end" and el.tag in ("INDIVIDUAL", "ENTITY"):
            e = _entry(el, "person" if el.tag == "INDIVIDUAL" else "entity")
            if e:
                entries.append(e)
            el.clear()
    return ParseResult(entries=entries, list_date=list_date)
