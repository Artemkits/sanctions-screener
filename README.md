# Sanctions Screener: transliteration-aware name screening

[![tests](https://github.com/Artemkits/sanctions-screener/actions/workflows/tests.yml/badge.svg)](https://github.com/Artemkits/sanctions-screener/actions/workflows/tests.yml)
![Python 3.12](https://img.shields.io/badge/python-3.12-12305b)
![License: MIT](https://img.shields.io/badge/license-MIT-12305b)

Screens a person or company name against five sanctions lists: the official **EU**, **UN** and **OFAC** lists, plus the **Polish MSWiA** list and the **UK FCDO** list. It handles the main source of missed hits and false alerts for clients from Ukraine, Russia and Belarus: **one name can be spelled many different ways in Latin script.**

![Demo](docs/demo.gif)

## The problem: the transliteration gap

`Сергій Щербина` can appear in documents, passports and sanctions lists as *Serhii Shcherbyna* (Ukrainian official system), *Serhiy Shcherbina* (BGN/PCGN), *Sergii*, *Sergiy*, *Siergiej Szczerbina* (Polish), *Sergej Schtscherbina* (German), or under the Russian form of the first name, *Sergey*.

A screener that only compares strings sees a different name each time. It either misses the hit or, with a loose threshold, raises alerts on half the customer base.

This matters in Poland in particular. Polish documents and press use **Polish transcription** (*Ławrow*, *Szojgu*, *Kadyrow*, *Wołodin*), while the lists use English spellings. In the measurements below, a naive fuzzy matcher scores *Wiaczesław Wołodin* at **61**: below any reasonable alert threshold, so the hit is missed. Its best "match" is a company called *Citadel Holding*. This tool scores it at **97** against *Vyacheslav VOLODIN* (OFAC, EU, UK).

## What it does

1. **Generates every plausible spelling** of the input name:
   - For Cyrillic input it detects the language from characteristic letters (`і ї є ґ` → Ukrainian, `ъ` → Russian, `ы э` → Russian or Belarusian, `ў` → Belarusian; ambiguous → all three).
   - It transliterates with eight named systems: **KMU 2010** (Ukrainian official), **ICAO 9303** (Russian passports), **GOST 7.79-2000**, **BGN/PCGN**, common English, **Polish (PWN)**, **German (Duden)** and the Belarusian passport system.
   - It adds a weighted beam search over letter-level alternatives (`и/й/ий → i/y/iy/ii/yi`, `х → kh/h/ch`, `щ → shch/sch/szcz`, …), pruned by plausibility.
   - It adds **equivalent given names** across languages (*Сергій ↔ Сергей*, *Олександр ↔ Александр ↔ Аляксандр*) and the Belarusian surname suffix `-енка ↔ -енко`.
   - For Latin input it removes diacritics and generates alternatives between spelling conventions (`sz ↔ sh`, `cz ↔ ch`, `w ↔ v`, Polish `c ↔ ts`, `-ij ↔ -iy ↔ -y`).
2. **Matches against all aliases** in all three lists, including the Cyrillic, Arabic and Greek ones. A *phonetic skeleton* catches spellings that no system produces.
3. **Scores and explains each hit.** The analyst sees which variant matched which alias, which system produced it, and how the secondary identifiers changed the score:
   - date of birth;
   - nationality;
   - gender (entered, or inferred from Slavic patronymic and surname endings);
   - document number: passport, national ID, tax or registration number (31k identifiers parsed from the lists);
   - differing numbers in names (*SEA STAR 7* vs *SEA STAR 8*).

| Score | Status |
|---|---|
| ≥ 90 | **Trafienie / Possible match** |
| 75–89 | **Do weryfikacji / Review** |
| < 75 | weak, hidden by default |

![Match card](docs/match-card.png)

Other features:

- **Match map.** For every search, a diagram shows *query → the variant that produced the hit (and which system generated it) → the list record*. Contradicting identifiers are flagged directly on the record.
- **Escalation report**: a printable page (or PDF) listing what was checked, when, against which list versions, the hits and their rationale, a system recommendation, and a decision form (*false positive / escalation / freeze*) that writes to the audit log. It follows the screening alert → review → decision workflow.
- **Batch screening** of a CSV customer list (comma, semicolon or tab separated), with a progress bar and CSV export.
- **Audit log** of every search, batch run and decision.
- **Lists page**: version, record and alias counts, scripts and top sanctions programmes for each source.
- **Methodology page**: the transliteration table (letter × system) is generated live from the same code that runs the search.
- **Telegram bot**: `/check Сергій Щербина 1975` returns the top 3 hits.
- Polish UI with an English switch.

| Batch | Escalation report |
|---|---|
| ![](docs/batch.png) | ![](docs/report.png) |
| **Sanctions lists** | **Methodology** |
| ![](docs/lists.png) | ![](docs/methodology.png) |

## Results on real list entries

From `python -m scripts.evaluate`. The baseline is a naive screener: unidecode, then the best rapidfuzz `token_sort_ratio` over all ~99k aliases of the five lists.

| Query | This tool | Baseline | Hit |
|---|---:|---:|---|
| Евгений Пригожин, 1961 | **100** | 91 | Yevgeniy Viktorovich PRIGOZHIN (EU, OFAC) |
| Wiaczesław Wołodin | **97** | 61 | Vyacheslav VOLODIN (OFAC, EU, UK) |
| Ramzan Kadyrow | **99** | 69 | Ramzan Akhmadovitch KADYROV (EU) |
| Aleksiej Miller | **100** | 79 | Alexey Borisovich MILLER (UK, OFAC) |
| Ołeksandr Chodakowski | **96** | 72 | Aleksandr KHODAKOVSKII (EU) |
| Ołeh Cariow | **100** | 73 | Oleg Tsariov (EU) |
| Siergiej Ławrow | **100** | 76 | Sergei Viktorovich LAVROV (OFAC, EU) |
| Аляксандр Лукашэнка | **99** | 83 | LUKASHENKO (UK, EU, OFAC) |
| Юрий Ковальчук, 1984, UA | 84 *review* | 83 | Yuriy KOVALCHUK (b. 1951): the date-of-birth conflict is flagged as a false-positive argument |
| Jan Kowalski, 1985, PL | no alert | – | – |

A search over all five lists (~107k name forms) takes 0.05–0.3 s on a laptop. The index is cached on disk, so a restart takes about 2 s. The full output is in [`docs/evaluation.txt`](docs/evaluation.txt).

## Run locally

Requires Python 3.11+.

```bash
./run.sh            # creates .venv, downloads the lists on first run, serves http://localhost:8000
```

Or step by step:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m app.update          # download + parse EU, UN, OFAC into data/sanctions.db
.venv/bin/uvicorn app.main:app --port 8000
.venv/bin/python -m pytest              # 79 tests: transliteration, matching, API
```

The Telegram bot (optional) runs with `TELEGRAM_BOT_TOKEN=... .venv/bin/python -m app.telegram_bot`.

## Data sources

| List | Source | Format |
|---|---|---|
| EU Consolidated Financial Sanctions List | `webgate.ec.europa.eu/fsd/fsf` | XML 1.1 |
| UN Security Council Consolidated List | `scsanctions.un.org/resources/xml/en/consolidated.xml` | XML |
| OFAC SDN List | `sanctionslistservice.ofac.treas.gov/.../SDN.XML` | XML |
| Polish MSWiA sanctions list | OpenSanctions `pl_mswia_sanctions` | CSV |
| UK FCDO Sanctions List | OpenSanctions `gb_fcdo_sanctions` | CSV |

The two national lists come through [OpenSanctions](https://www.opensanctions.org/), because their publishers offer no convenient machine-readable file. That data is licensed **CC BY-NC 4.0**, which permits only non-commercial use such as this demo. Any list can be switched off with `ENABLED_SOURCES=EU,UN,OFAC`.

`python -m app.update` downloads the files again and replaces the data. About 31k document numbers and gender data are parsed along with the names. The UI shows each list's publication date and record count. All aliases are stored in every script that appears in the list (Latin, Cyrillic, Arabic, Greek…). Schema: `app/db.py`.

## How matching works

- **Index.** Every alias becomes a tuple of token ids into a shared vocabulary of ~63k distinct tokens. Non-Latin aliases are also stored in transliterated form. A parallel vocabulary holds phonetic skeletons.
- **Retrieval.** For each query token, *all* its variants are compared against the whole vocabulary in a single vectorised `rapidfuzz.process.cdist` call. Records containing a token with similarity ≥ 70 become candidates. There is no full scan.
- **Scoring:**
  - Query tokens are aligned to alias tokens in the best order, so name order doesn't matter.
  - Score = `0.7 × aligned + 0.3 × surname − penalty for unexplained alias tokens`. `token_sort_ratio` serves as a cross-check.
  - Missing patronymics are ignored. A first name may not "match" somebody's patronymic (*Oleksandr ≠ Oleksandrovna*).
  - The surname must reach 85 for *review* and 92 for *match*. Every query token must be present.
  - Two passes: a fast score for all candidates, then the full explanation only for the records that are shown.
- **Secondary identifiers:**

  | Identifier | Effect on score |
  |---|---|
  | Matching document number | +15, and at least *match* |
  | Matching date of birth | +3 / +5 |
  | Different birth year | −15, flagged as a false-positive argument |
  | Nationality | +3 / −5 |
  | Gender, entered | +2 / −15 |
  | Gender, inferred, mismatch | −10 |
  | Different numbers in the name | −10 |

## API

FastAPI publishes interactive documentation at `/docs`. Example:

```bash
curl -s localhost:8000/api/search -H 'Content-Type: application/json' \
  -d '{"name": "Siergiej Ławrow", "birth": "1950", "nationality": "RU", "entity_type": "person", "min_score": 75, "limit": 10}'
```

| Endpoint | Purpose |
|---|---|
| `POST /api/search` | screening with full explanation |
| `POST /api/batch` + `GET /api/batch/{id}` | CSV job with progress |
| `GET /api/batch/{id}.csv` | CSV export |
| `GET /report/{id}` | escalation report |
| `POST /api/decision` | analyst decision |
| `GET /api/audit` | audit log |
| `GET /api/lists` | list composition |
| `GET /api/methodology` | transliteration table |

## Compared with similar open-source projects

I reviewed two open-source screening engines and adopted their best scoring ideas:

| Project | What it is | Adopted here |
|---|---|---|
| [OpenSanctions yente / nomenklatura](https://www.opensanctions.org/matcher) | Rule-based *logic-v2* matcher: name score plus supporting and contradicting features; aggregated sanctions datasets | **the data feed** for the PL and UK lists; gender-mismatch penalty, number-mismatch penalty, identifier match as strong evidence, a higher weight on the family name |
| [moov-io/watchman](https://github.com/moov-io/watchman) | OFAC/EU/UN screening server in Go | search by document number, `min_score`/`limit` API parameters, periodic background list refresh, per-field debug output |

What this project adds that both lack is the **explicit East Slavic transliteration layer**:

- named national systems, including Polish and Ukrainian official transliteration;
- equivalent given-name forms across languages;
- a per-variant explanation of which system produced the hit.

General engines treat cross-script matching as a known weak spot. OpenSanctions documents increased error rates when comparing names across writing systems.

## Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Artemkits/sanctions-screener)

**Render (free, no credit card).** Sign in to [render.com](https://render.com) with GitHub, then go to **New → Blueprint** and pick this repository. `render.yaml` configures everything else. The free plan (512 MB RAM) fits all five lists; the server uses about 360 MB. It sleeps after 15 minutes idle, and the first request after a sleep takes about a minute.

**Any Linux server** (Ubuntu 22.04+ / Debian 12+, about 1 GB RAM):

```bash
scripts/deploy_vps.sh <ssh-host>
```

The script runs these steps over SSH:

1. Clones this repository into `/opt/sanctions-screener`.
2. Installs a virtualenv.
3. Downloads the lists.
4. Prebuilds the index.
5. Installs a systemd service on port 8090 (`deploy/sanctions-screener.service`) that refreshes the lists every 24 h.

To update later, run the same command again.

Hugging Face Spaces also works with the same `Dockerfile` (`scripts/deploy_hf.sh`), but Docker Spaces now require a PRO subscription.

## Limitations

- **This is a demo, not a compliance system.** It does not replace commercial screening solutions (World-Check, Dow Jones, LexisNexis). It covers five sanctions lists, but has no PEP data and no adverse media.
- The transliteration rules cover Ukrainian, Russian and Belarusian names. Arabic and other scripts are matched only through their Latin aliases or a generic transliteration.
- Scoring weights and thresholds are hand-tuned on a small sample. They are not calibrated on labelled alert data.
- The audit log is a local SQLite table with no authentication. On free hosting it is reset whenever the container restarts.

*Narzędzie demonstracyjne. Nie stanowi podstawy do decyzji compliance.*

## License

MIT. Sanctions data belongs to the respective publishers: European Commission, United Nations, U.S. Treasury, MSWiA and FCDO. The PL and UK lists are delivered by OpenSanctions under CC BY-NC 4.0.
