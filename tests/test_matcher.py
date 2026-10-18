"""Search + scoring on a small hand-made list (no network, no real data needed)."""
import pytest

from app.matcher import Index, parse_birth, status_for


@pytest.fixture(scope="module")
def index(db_conn):
    return Index().build(db_conn)


def top(index, name, **kw):
    res = index.search(name, **kw)
    return res["results"][0] if res["results"] else None, res


def test_exact_latin_match(index):
    hit, _ = top(index, "Sergey Lavrov")
    assert hit["source_id"] == "4" and hit["status"] == "match"


def test_found_only_through_transliteration(index):
    # Polish spelling of the Russian name: no list alias is spelled like this
    hit, _ = top(index, "Siergiej Ławrow")
    assert hit["source_id"] == "4" and hit["score"] >= 90
    # Ukrainian Cyrillic input against an English KMU/BGN spelling
    hit, _ = top(index, "Сергій Щербина")
    assert hit["source_id"] == "1" and hit["status"] == "match"
    # Polish spelling of a Ukrainian surname
    hit, _ = top(index, "Serhij Szczerbyna")
    assert hit["source_id"] == "1" and hit["score"] >= 90


def test_word_order_does_not_matter(index):
    hit, _ = top(index, "Prigozhin Yevgeny")
    assert hit["source_id"] == "2" and hit["status"] == "match"


def test_cyrillic_alias_matched_directly(index):
    hit, _ = top(index, "Юрий Ковальчук")
    assert hit["source_id"] == "5" and hit["score"] >= 95


def test_belarusian_input(index):
    hit, _ = top(index, "Аляксандр Лукашэнка")
    assert hit["source_id"] == "8" and hit["status"] == "match"


def test_patronymic_is_not_a_first_name(index):
    _, res = top(index, "Олександр Ковальчук")
    tatiana = next(r for r in res["results"] if r["source_id"] == "6")
    assert tatiana["status"] == "weak"


def test_same_surname_other_first_name_is_weak(index):
    _, res = top(index, "Евгений Пригожин")
    pavel = next(r for r in res["results"] if r["source_id"] == "3")
    assert pavel["status"] == "weak"


def test_birth_year_mismatch_lowers_score(index):
    same, _ = top(index, "Юрий Ковальчук", birth="1951")
    other, _ = top(index, "Юрий Ковальчук", birth="1980")
    assert same["score"] > other["score"]
    assert any(f["ok"] is False and "false positive" in f["text"] for f in other["explanation"]["factors"])
    assert other["status"] != "match"


def test_nationality_factor(index):
    hit, _ = top(index, "Sergey Lavrov", nationality="PL")
    assert any(f["field"] == "nationality" and f["ok"] is False for f in hit["explanation"]["factors"])


def test_entity_type_filter(index):
    _, res = top(index, "Kovalchuk Trading", entity_type="person")
    assert all(r["entity_type"] == "person" for r in res["results"])
    hit, _ = top(index, "Kovalchuk Trading", entity_type="entity")
    assert hit["source_id"] == "7"


def test_explanation_names_the_system(index):
    hit, _ = top(index, "Сергій Щербина")
    tokens = hit["explanation"]["tokens"]
    assert all(t["similarity"] >= 90 for t in tokens)
    assert any(t.get("system_codes") for t in tokens)


def test_unknown_person_has_no_strong_hits(index):
    _, res = top(index, "Jan Kowalski")
    assert not [r for r in res["results"] if r["status"] in ("match", "review")]


@pytest.mark.parametrize("s,expected", [("1975", (1975, "")), ("02.04.1975", (1975, "1975-04-02")),
                                        ("1975-4-2", (1975, "1975-04-02")), ("", (None, ""))])
def test_parse_birth(s, expected):
    assert parse_birth(s) == expected


def test_status_thresholds():
    assert status_for(90) == "match" and status_for(89.9) == "review" and status_for(74.9) == "weak"
