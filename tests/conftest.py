import pytest

from app.db import connect, dumps
from app.text import detect_script

ENTRIES = [
    # source, id, type, primary, aliases, dob, nationality
    ("EU", "1", "person", "Serhiy Shcherbyna", ["Serhiy Volodymyrovych SHCHERBYNA", "Сергій Володимирович ЩЕРБИНА"],
     [{"date": "1975-04-02", "year": 1975}], [{"iso2": "UA", "name": "Ukraine"}]),
    ("OFAC", "2", "person", "Yevgeniy Viktorovich PRIGOZHIN", ["Yevgeniy Viktorovich PRIGOZHIN", "Evgeny PRIGOZHIN"],
     [{"date": "1961-06-01", "year": 1961}], [{"iso2": "RU", "name": "Russia"}]),
    ("OFAC", "3", "person", "Pavel Evgenyevich PRIGOZHIN", ["Pavel Evgenyevich PRIGOZHIN"],
     [{"year": 1998}], [{"iso2": "RU", "name": "Russia"}]),
    ("UN", "4", "person", "Sergei Viktorovich LAVROV", ["Sergei Viktorovich LAVROV", "Sergey LAVROV"],
     [{"date": "1950-03-21", "year": 1950}], [{"iso2": "RU", "name": "Russia"}]),
    ("EU", "5", "person", "Yuriy Valentinovich KOVALCHUK", ["Yuriy Valentinovich KOVALCHUK", "Юрий Валентинович КОВАЛЬЧУК"],
     [{"date": "1951-07-25", "year": 1951}], [{"iso2": "RU", "name": "Russia"}]),
    ("EU", "6", "person", "Tatiana Aleksandrovna KOVALCHUK", ["Tatiana Aleksandrovna KOVALCHUK"], [], []),
    ("OFAC", "7", "entity", "KOVALCHUK TRADING LLC", ["KOVALCHUK TRADING LLC"], [], []),
    ("EU", "8", "person", "Aliaksandr Ryhoravich LUKASHENKA", ["Аляксандр Рыгоравіч ЛУКАШЭНКА", "Alexandr Grigorievich LUKASHENKO"],
     [{"year": 1954}], [{"iso2": "BY", "name": "Belarus"}]),
]


def make_db(path):
    conn = connect(path)
    for src, sid, et, primary, aliases, dob, nat in ENTRIES:
        cur = conn.execute("INSERT INTO entries (source, source_id, entity_type, primary_name, birth_dates, nationalities,"
                           " programs, url) VALUES (?,?,?,?,?,?,?,?)",
                           (src, sid, et, primary, dumps(dob), dumps(nat), dumps(["TEST"]), "https://example.org"))
        for a in aliases:
            conn.execute("INSERT INTO aliases (entry_id, name, script, lang, quality) VALUES (?,?,?,?,?)",
                         (cur.lastrowid, a, detect_script(a), "", "strong"))
    for src in ("EU", "UN", "OFAC"):
        conn.execute("INSERT INTO source_meta (source, list_date, record_count, status) VALUES (?, '2026-10-15', 3, 'ok')", (src,))
    conn.commit()
    return conn


@pytest.fixture(scope="session")
def db_conn(tmp_path_factory):
    return make_db(tmp_path_factory.mktemp("db") / "test.db")
