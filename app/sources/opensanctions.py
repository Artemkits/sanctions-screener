"""Parser for OpenSanctions `targets.simple.csv` exports.

Used for national lists that have no convenient official machine-readable file:
the Polish MSWiA list and the UK FCDO list.
OpenSanctions data is licensed CC BY-NC 4.0 — fine for this non-commercial demo.
"""
import csv
import io
import re

from . import Alias, Entry, ParseResult, make_id
from .countries import country_name

TYPE_MAP = {"Person": "person", "Vessel": "vessel", "Airplane": "aircraft"}
ENTITY_URL = "https://www.opensanctions.org/entities/{}/"

csv.field_size_limit(10_000_000)


def _multi(value: str) -> list[str]:
    """OpenSanctions joins multiple values with ';' using CSV quoting inside the cell."""
    if not value:
        return []
    return [v.strip() for v in next(csv.reader(io.StringIO(value), delimiter=";")) if v.strip()]


def _program(sanction: str, source: str) -> str:
    s = sanction.strip()
    if source == "PL":
        return "MSWiA"
    head = s.split(" - ")[0].strip('" ')
    return head[:80]


def parse_for(source: str):
    def parse(path) -> ParseResult:
        entries, last_seen = [], ""
        with open(path, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                name = (r.get("name") or "").strip()
                if not name:
                    continue
                aliases, seen = [Alias(name=name, lang="", quality="primary")], {name.lower()}
                for a in _multi(r.get("aliases", "")):
                    if a.lower() not in seen:
                        seen.add(a.lower())
                        aliases.append(Alias(name=a, lang="", quality="strong"))
                births = []
                for b in _multi(r.get("birth_date", "")):
                    y = int(b[:4]) if b[:4].isdigit() else None
                    births.append({"date": b if len(b) == 10 else "", "year": y, "circa": len(b) < 10, "raw": b})
                nats = [{"iso2": c.upper(), "name": country_name(c.upper())} for c in _multi(r.get("countries", ""))
                        if len(c) == 2]
                ids = [d for d in (make_id("ID", n) for n in _multi(r.get("identifiers", ""))) if d]
                sanctions = _multi(r.get("sanctions", ""))
                programs = []
                for s in sanctions:
                    p = _program(s, source)
                    if p and p not in programs:
                        programs.append(p)
                listed = r.get("first_seen", "")[:10]
                if source == "PL" and sanctions and re.match(r"^\d{4}-\d{2}-\d{2}$", sanctions[0]):
                    listed = sanctions[0]
                last_seen = max(last_seen, r.get("last_seen", "")[:10])
                entries.append(Entry(
                    source=source,
                    source_id=r["id"],
                    entity_type=TYPE_MAP.get(r.get("schema", ""), "person" if r.get("schema") == "Person" else "entity"),
                    primary_name=name,
                    aliases=aliases,
                    birth_dates=births,
                    nationalities=nats,
                    programs=programs[:6],
                    listed_on=listed,
                    url=ENTITY_URL.format(r["id"]),
                    remarks=" | ".join(sanctions)[:1500],
                    extra={"identifiers": ids[:20], "sex": "", "address": (r.get("addresses") or "")[:300],
                           "dataset": r.get("dataset", "")},
                ))
        return ParseResult(entries=entries, list_date=last_seen)
    return parse
