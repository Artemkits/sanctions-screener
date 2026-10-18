"""Parser for the EU Consolidated Financial Sanctions List (XML, schema 1.1)."""
import xml.etree.ElementTree as ET

from ..text import detect_script, norm_latin
from . import Alias, Entry, ParseResult
from .countries import to_iso2

NS = "{http://eu.europa.ec/fpi/fsd/export}"
TYPE_MAP = {"person": "person", "enterprise": "entity"}


def _t(tag):
    return NS + tag


def _pick_primary(aliases: list) -> Alias:
    """Display name: the English/unlabelled Latin alias whose words recur most across all aliases.

    EU entries sometimes tag a minor a.k.a. ("League") as English while the main
    name ("Wagner Group") carries no language, so "first EN alias" is not enough.
    """
    bags = [set(norm_latin(a.name).split()) for a in aliases]
    cands = [i for i, a in enumerate(aliases) if a.lang in ("EN", "") and detect_script(a.name) == "latin"]
    if not cands:
        return aliases[0]

    def support(i):
        words = bags[i]
        return sum(len(words & b) / max(len(words), 1) for j, b in enumerate(bags) if j != i)

    return aliases[max(cands, key=lambda i: (support(i), aliases[i].lang == "EN", -i))]


def parse(path) -> ParseResult:
    entries, list_date = [], ""
    for event, el in ET.iterparse(path, events=("start", "end")):
        if event == "start" and el.tag == _t("export"):
            list_date = (el.get("generationDate") or "")[:10]
            continue
        if event != "end" or el.tag != _t("sanctionEntity"):
            continue
        subject = el.find(_t("subjectType"))
        etype = TYPE_MAP.get(subject.get("code") if subject is not None else "", "entity")

        aliases, seen = [], set()
        for na in el.findall(_t("nameAlias")):
            name = (na.get("wholeName") or "").strip()
            if not name or name.lower() in seen:
                continue
            seen.add(name.lower())
            aliases.append(Alias(name=name, lang=na.get("nameLanguage") or "",
                                 quality="strong" if na.get("strong") == "true" else "weak"))
        if not aliases:
            el.clear()
            continue
        primary = _pick_primary(aliases)
        primary.quality = "primary"

        programs, urls = [], []
        for reg in el.findall(_t("regulation")):
            prog = reg.get("programme")
            if prog and prog not in programs:
                programs.append(prog)
            pub = (reg.findtext(_t("publicationUrl")) or "").strip()
            if pub:
                urls.append((reg.get("regulationType") != "regulation", pub))
        # Link to the original listing act on EUR-Lex (amendments only as a fallback).
        url = sorted(urls, key=lambda u: u[0])[0][1] if urls else ""

        births = []
        for b in el.findall(_t("birthdate")):
            births.append({
                "date": b.get("birthdate") or "",
                "year": int(b.get("year")) if (b.get("year") or "").isdigit() else None,
                "circa": b.get("circa") == "true",
                "place": ", ".join(x for x in (b.get("city"), b.get("countryDescription")) if x and x != "UNKNOWN"),
            })
        nats = []
        for c in el.findall(_t("citizenship")):
            iso = (c.get("countryIso2Code") or "").upper()
            if iso in ("", "00"):
                iso = to_iso2(c.get("countryDescription") or "")
            if iso and not any(n["iso2"] == iso for n in nats):
                nats.append({"iso2": iso, "name": c.get("countryDescription") or iso})

        remarks = " ".join((r.text or "").strip() for r in el.findall(_t("remark")) if r.text)
        functions = sorted({na.get("function").strip() for na in el.findall(_t("nameAlias")) if (na.get("function") or "").strip()})
        genders = {na.get("gender") for na in el.findall(_t("nameAlias")) if na.get("gender")}

        entries.append(Entry(
            source="EU",
            source_id=el.get("logicalId"),
            entity_type=etype,
            primary_name=primary.name,
            aliases=aliases,
            birth_dates=births,
            nationalities=nats,
            programs=programs,
            listed_on=el.get("designationDate") or "",
            url=url,
            remarks=remarks,
            extra={
                "reference": el.get("euReferenceNumber") or "",
                "un_id": el.get("unitedNationId") or "",
                "function": "; ".join(functions)[:600],
                "gender": "/".join(sorted(genders)),
            },
        ))
        el.clear()
    return ParseResult(entries=entries, list_date=list_date)
