"""Parsers for the OpenSanctions CSV format and source filtering."""
from app.sources import norm_id
from app.sources.opensanctions import parse_for

CSV = '''"id","schema","name","aliases","birth_date","countries","addresses","identifiers","sanctions","phones","emails","program_ids","dataset","first_seen","last_seen","last_change"
"NK-1","Person","Sviatlana CHEREPANAVA","Светлана ЧЕРЕПАНОВА;Святлана ЧАРАПАНАВА","1972-10-04","by","","AB 123-456","2023-05-30","","","","Polish List","2024-03-19T19:43:57","2026-10-18T08:27:45","2026-06-30"
"NK-2","Company","Makrochem Sp. z o.o.","""""""Makrochem"""" S.A.""","","pl","Lublin","0000875568;387788117","2023-10-03","","","","Polish List","2024-04-23T16:26:01","2026-10-18T08:27:45","2026-06-30"
'''


def test_opensanctions_parser(tmp_path):
    f = tmp_path / "pl.csv"
    f.write_text(CSV, encoding="utf-8")
    res = parse_for("PL")(f)
    assert res.list_date == "2026-10-18" and len(res.entries) == 2
    person, company = res.entries
    assert person.entity_type == "person" and person.listed_on == "2023-05-30"
    assert [a.name for a in person.aliases] == ["Sviatlana CHEREPANAVA", "Светлана ЧЕРЕПАНОВА", "Святлана ЧАРАПАНАВА"]
    assert person.nationalities[0]["iso2"] == "BY" and person.birth_dates[0]["year"] == 1972
    assert norm_id(person.extra["identifiers"][0]["number"]) == "AB123456"
    assert company.entity_type == "entity" and company.programs == ["MSWiA"]
    assert company.aliases[1].name == '"Makrochem" S.A.'
    assert person.url.startswith("https://www.opensanctions.org/entities/NK-1")


def test_source_filter(db_conn):
    from app.matcher import Index
    ix = Index().build(db_conn)
    assert ix.search("Sergey Lavrov", sources=["EU", "OFAC"])["results"] == [] or \
        all(r["source"] in ("EU", "OFAC") for r in ix.search("Sergey Lavrov", sources=["EU", "OFAC"])["results"])
    assert ix.search("Sergey Lavrov", sources=["UN"])["results"][0]["source"] == "UN"
