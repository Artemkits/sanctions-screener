"""Parser for the OFAC SDN list (classic sdn.xml format)."""
import re
import xml.etree.ElementTree as ET
from datetime import datetime

from . import Alias, Entry, ParseResult, make_id, norm_sex
from .countries import to_iso2

TYPE_MAP = {"Individual": "person", "Entity": "entity", "Vessel": "vessel", "Aircraft": "aircraft"}
# idList entries that describe the record rather than identify it
NOT_IDENTIFIERS = ("risk", "gender", "date", "additional sanctions", "website", "organization type", "prohibited",
                   "target type", "executive order", "year of build", "email", "aircraft model", "aircraft operator",
                   "vessel type", "phone", "flag", "tonnage", "call sign", "nationality of registration")
DETAIL_URL = "https://sanctionssearch.ofac.treas.gov/Details.aspx?id={}"


def _name(el, ns, etype):
    first = (el.findtext(ns + "firstName") or "").strip()
    last = (el.findtext(ns + "lastName") or "").strip()
    # OFAC keeps the surname in lastName; store "First Last" order for individuals.
    return " ".join(p for p in (first, last) if p)


def _parse_dob(s: str) -> dict:
    s = s.strip()
    circa = s.lower().startswith("circa")
    s2 = re.sub(r"(?i)circa\s*", "", s)
    m = re.match(r"^(\d{4})\s*(?:to|-)\s*(\d{4})$", s2)
    if m:
        return {"date": "", "year": None, "circa": True, "from_year": int(m[1]), "to_year": int(m[2]), "raw": s}
    for fmt in ("%d %b %Y", "%b %Y", "%Y"):
        try:
            d = datetime.strptime(s2, fmt)
            return {"date": d.strftime("%Y-%m-%d") if fmt == "%d %b %Y" else "", "year": d.year, "circa": circa, "raw": s}
        except ValueError:
            continue
    y = re.search(r"\d{4}", s2)
    return {"date": "", "year": int(y[0]) if y else None, "circa": True, "raw": s}


def parse(path) -> ParseResult:
    entries, list_date, ns = [], "", ""
    for event, el in ET.iterparse(path, events=("start", "end")):
        if event == "start" and el.tag.endswith("sdnList"):
            ns = el.tag[: el.tag.index("}") + 1] if el.tag.startswith("{") else ""
            continue
        if event != "end":
            continue
        if el.tag == ns + "Publish_Date":
            try:
                list_date = datetime.strptime(el.text.strip(), "%m/%d/%Y").strftime("%Y-%m-%d")
            except (ValueError, AttributeError):
                list_date = el.text or ""
        if el.tag != ns + "sdnEntry":
            continue
        etype = TYPE_MAP.get(el.findtext(ns + "sdnType") or "", "entity")
        name = _name(el, ns, etype)
        aliases, seen = [Alias(name=name, lang="EN", quality="primary")], {name.lower()}
        for aka in el.findall(f"{ns}akaList/{ns}aka"):
            an = _name(aka, ns, etype)
            if an and an.lower() not in seen:
                seen.add(an.lower())
                aliases.append(Alias(name=an, lang="EN", quality=(aka.findtext(ns + "category") or "strong")))
        births = [_parse_dob(d.text) for d in el.iter(ns + "dateOfBirth") if d.text]
        places = [p.text.strip() for p in el.iter(ns + "placeOfBirth") if p.text]
        for b in births:
            b["place"] = places[0] if places else ""
        nats = []
        for tag in ("nationality", "citizenship"):
            for n in el.iter(ns + tag):
                c = (n.findtext(ns + "country") or "").strip()
                iso = to_iso2(c)
                if c and not any(x["name"] == c for x in nats):
                    nats.append({"iso2": iso, "name": c})
        programs = [p.text.strip() for p in el.iter(ns + "program") if p.text]
        uid = el.findtext(ns + "uid")
        gender, ids = "", []
        for i in el.iter(ns + "id"):
            id_type = i.findtext(ns + "idType") or ""
            if id_type == "Gender":
                gender = i.findtext(ns + "idNumber") or ""
            elif not any(w in id_type.lower() for w in NOT_IDENTIFIERS):
                d = make_id(id_type, i.findtext(ns + "idNumber") or "", i.findtext(ns + "idCountry") or "")
                if d and d not in ids:
                    ids.append(d)
        entries.append(Entry(
            source="OFAC",
            source_id=uid,
            entity_type=etype,
            primary_name=name,
            aliases=aliases,
            birth_dates=births,
            nationalities=nats,
            programs=programs,
            listed_on="",
            url=DETAIL_URL.format(uid),
            remarks=(el.findtext(ns + "remarks") or "").strip()[:2000],
            extra={"gender": gender, "sex": norm_sex(gender), "identifiers": ids,
                   "title": (el.findtext(ns + "title") or "").strip()},
        ))
        el.clear()
    return ParseResult(entries=entries, list_date=list_date)
