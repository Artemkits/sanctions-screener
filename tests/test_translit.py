"""Every test lists spellings that MUST be generated for a real-world name."""
import pytest

from app.text import norm_latin, skeleton
from app.translit import (detect_language, full_name_examples, name_variants, polish, token_variants,
                          ua_kmu2010)


def norms(token):
    return set(token_variants(token).norms())


def assert_generates(token, expected):
    got = norms(token)
    missing = [e for e in expected if norm_latin(e).replace(" ", "") not in got]
    assert not missing, f"{token}: missing {missing}; got {sorted(got)}"


# ---------------------------------------------------------------- language detection

@pytest.mark.parametrize("text,lang", [
    ("Сергій", ["uk"]), ("Їжак", ["uk"]), ("Євген", ["uk"]), ("Ґудзь", ["uk"]),
    ("Объедков", ["ru"]), ("Лукашэнка", ["ru", "be"]), ("Ўладзімір", ["be"]), ("Сымон Іваноў", ["be"]),
    ("Щербина", ["uk", "ru", "be"]),
])
def test_detect_language(text, lang):
    assert detect_language(text) == lang


# ---------------------------------------------------------------- named systems

@pytest.mark.parametrize("cyr,latin", [
    ("сергій", "serhii"), ("щербина", "shcherbyna"), ("житомир", "zhytomyr"), ("згорани", "zghorany"),
    ("юрій", "yurii"), ("олександр", "oleksandr"), ("хмельницький", "khmelnytskyi"), ("ігор", "ihor"),
    ("київ", "kyiv"), ("єнакієве", "yenakiieve"), ("яготин", "yahotyn"),
])
def test_ukrainian_official_kmu2010(cyr, latin):
    assert ua_kmu2010(cyr) == latin


@pytest.mark.parametrize("cyr,lang,expected", [
    ("сергей", "ru", "siergiej"), ("щербина", "ru", "szczerbina"), ("юрий", "ru", "jurij"),
    ("александр", "ru", "aleksandr"), ("пригожин", "ru", "prigożyn"), ("евгений", "ru", "jewgienij"),
    ("хмельницкий", "ru", "chmielnicki"), ("ковальчук", "ru", "kowalczuk"),
    ("олександр", "uk", "ołeksandr"), ("сергій", "uk", "serhij"), ("щербина", "uk", "szczerbyna"),
])
def test_polish_transcription(cyr, lang, expected):
    assert polish(cyr, lang) == expected


# ---------------------------------------------------------------- full generator

def test_serhii_shcherbyna():
    assert_generates("Сергій", ["Serhii", "Serhiy", "Sergii", "Sergiy", "Serhij", "Siergiej", "Sergey", "Sergei"])
    assert_generates("Щербина", ["Shcherbyna", "Shcherbina", "Szczerbina", "Szczerbyna", "Schtscherbina", "Scherbina"])


def test_oleksandr_kovalchuk():
    assert_generates("Олександр", ["Oleksandr", "Olexandr", "Aleksandr", "Alexandr", "Aliaksandr"])
    assert_generates("Ковальчук", ["Kovalchuk", "Kowalczuk", "Kowaltschuk"])


def test_yuriy_kovalchuk():
    assert_generates("Юрий", ["Yuriy", "Yury", "Yuri", "Iurii", "Yurij", "Jurij", "Juri", "Yurii"])


def test_yevgeny_prigozhin():
    assert_generates("Евгений", ["Yevgeniy", "Yevgeny", "Evgeny", "Evgenii", "Evgeniy", "Jewgienij", "Jewgeni"])
    assert_generates("Пригожин", ["Prigozhin", "Prigożyn", "Prigoschin"])


def test_ihor_igor():
    assert_generates("Ігор", ["Ihor", "Igor", "Ihar"])
    assert "igor" in norms("Ihor")
    assert "ihor" in norms("Igor")


def test_khmelnytskyi():
    assert_generates("Хмельницький", ["Khmelnytskyi", "Khmelnytskyy", "Khmelnytskiy", "Khmelnitsky",
                                      "Khmelnitskiy", "Chmielnicki", "Chmelnyćkyj", "Hmelnytsky"])


def test_lukashenko_belarusian_forms():
    assert_generates("Лукашэнка", ["Lukashenka", "Łukaszenka", "Lukashenko"])
    assert_generates("Аляксандр", ["Aliaksandr", "Alyaksandr", "Aleksandr"])


def test_volodymyr_vladimir_equivalence():
    assert_generates("Володимир", ["Volodymyr", "Vladimir", "Wladimir", "Uladzimir"])


def test_olena_yelena():
    assert_generates("Олена", ["Olena", "Elena", "Yelena", "Jelena", "Alena"])


def test_endings_iy_variations():
    # -ий / -ій → -iy / -ii / -yi / -ij / -y
    assert_generates("Віталій", ["Vitalii", "Vitaliy", "Vitalij", "Vitaly", "Vitalyi"])


def test_latin_input_polish_spelling():
    got = norms("Szczerbina")
    assert {"szczerbina", "shcherbina"} <= got
    got = norms("Siergiej")
    assert {"sergey", "sergei"} & got


def test_skeleton_collapses_conventions():
    groups = [
        ["Serhii", "Sergii", "Sergiy", "Sergey", "Sergei", "Siergiej", "Serhiy"],
        ["Shcherbyna", "Szczerbina", "Shcherbina", "Scherbina"],
        ["Yuriy", "Yurii", "Iurii", "Jurij", "Yury", "Yuri"],
        ["Yevgeniy", "Evgeny", "Jewgienij", "Evgenii"],
        ["Kovalchuk", "Kowalczuk"],
    ]
    for g in groups:
        keys = {skeleton(norm_latin(x)) for x in g}
        assert len(keys) == 1, (g, keys)


def test_variant_explosion_is_bounded():
    for tv in name_variants("Святослав Олександрович Щербинський-Хмельницький"):
        assert len(tv.variants) <= 80


def test_full_name_examples_are_labelled():
    rows = full_name_examples(name_variants("Сергій Щербина"))
    texts = {r["text"] for r in rows}
    assert "Serhii Shcherbyna" in texts
    assert all(r["label"] for r in rows)


def test_latin_homoglyphs_inside_cyrillic():
    # The EU list writes some Ukrainian names with a Latin "i": "Сергiй", "Пасiчник"
    assert "serhii" in norms("Сергiй")
    assert "pasichnyk" in norms("Пасiчник")
