"use strict";

/* =====================================================================
   i18n
   ===================================================================== */
const I18N = {
  pl: {
    tagline: "Screening sankcyjny z uwzględnieniem transliteracji", analyst: "Analityk",
    disclaimer: "Narzędzie demonstracyjne. Nie stanowi podstawy do decyzji compliance.",
    nav_work: "Praca", nav_data: "Dane", tab_screen: "Screening", tab_batch: "Batch (CSV)", tab_audit: "Dziennik",
    tab_lists: "Listy sankcyjne", tab_method: "Metodologia",
    f_name: "Imię i nazwisko / nazwa *", f_birth: "Data urodzenia", f_nat: "Obywatelstwo", f_type: "Typ",
    t_person: "osoba fizyczna", t_entity: "podmiot", t_any: "dowolny", check: "Sprawdź", checking: "Sprawdzanie…",
    intro_eyebrow: "Luka transliteracyjna", intro_h: "Jedno nazwisko, wiele zapisów",
    intro_p: "Ta sama osoba figuruje w paszporcie, w prasie i na liście sankcyjnej pod różnymi zapisami łacińskimi. Narzędzie generuje warianty według oficjalnych systemów transliteracji i sprawdza każdy z nich w sześciu listach sankcyjnych: UE, ONZ, OFAC, polskiej MSWiA, brytyjskiej i ukraińskiej.",
    demo_h: "Scenariusze demonstracyjne", demo_exact: "Trafienie dokładne", demo_translit: "Tylko dzięki transliteracji",
    demo_translit_meta: "pisownia polska", demo_fp: "False positive", demo_by: "Cyrylica białoruska",
    map_h: "Mapa dopasowania", map_sub: "zapytanie → wariant, który dał trafienie → rekord na liście",
    col_query: "Zapytanie", col_variant: "Wariant (system)", col_hit: "Rekord na liście", col_lists: "Listy",
    more_variants: "+ {n} innych wariantów sprawdzonych bez trafienia", no_hits_map: "Żaden z {n} wariantów nie dał trafienia powyżej progu.",
    results: "Wyniki", show_weak: "pokaż słabe (< 75)", report: "Raport do eskalacji",
    c_score: "Wynik", c_status: "Status", c_listed: "Nazwa na liście", c_alias: "Dopasowany alias", c_source: "Lista",
    c_program: "Program", c_dob: "Data ur.", c_name: "Imię i nazwisko", c_best: "Najlepsze trafienie",
    variants_title: "Wygenerowane warianty transliteracji",
    v_match: "Możliwe trafienie — wymaga eskalacji", v_review: "Wymaga weryfikacji analityka", v_clear: "Brak trafień powyżej progu",
    s_match: "Trafienie", s_review: "Do weryfikacji", s_clear: "Czysto",
    match: "Trafienie", review: "Do weryfikacji", weak: "Słabe", clear: "Brak trafień",
    lang_detected: "język", lang_uk: "ukraiński", lang_ru: "rosyjski", lang_be: "białoruski", lang_latin: "zapis łaciński",
    combos: "kombinacji wariantów", in_ms: "w {ms} ms", lists_checked: "listy z dnia",
    none: "Brak trafień powyżej progu 75. Włącz „pokaż słabe”, aby zobaczyć kandydatów poniżej progu.", none_weak: "Brak kandydatów powyżej 60.",
    by_system: "Pełne imię według systemów", per_token: "Wszystkie warianty według słów",
    legend_named: "z nazwanego systemu", legend_var: "wariant fonetyczny", legend_eq: "z formy w innym języku (Сергій ↔ Сергей)",
    why: "Dlaczego to trafienie", factors: "Czynniki dodatkowe", record: "Rekord na liście", aliases: "Wszystkie aliasy",
    calc: "Obliczenie wyniku", surname: "nazwisko", ignored: "pominięte — otczestwa nie ma w rekordzie",
    channel_skeleton: "szkielet fonetyczny — zgodność mimo innej pisowni", via_eq: "przez formę",
    no_factors: "Nie podano daty urodzenia ani obywatelstwa — wynik opiera się wyłącznie na nazwie. Dodaj je, aby potwierdzić lub wykluczyć tożsamość.",
    form_orig: "alias porównany w oryginalnym zapisie", form_translit: "alias w innym alfabecie, porównany po transliteracji",
    open_source: "Otwórz rekord u źródła",
    k_source: "Źródło", k_id: "ID w źródle", k_type: "Typ", k_programs: "Program / podstawa", k_listed: "Data wpisu",
    k_dob: "Data urodzenia", k_pob: "Miejsce urodzenia", k_nat: "Obywatelstwo", k_function: "Funkcja", k_sex: "Płeć", k_docs: "Dokumenty", k_remarks: "Uwagi", k_link: "Link",
    person: "osoba fizyczna", entity: "podmiot", vessel: "statek", aircraft: "statek powietrzny",
    batch_h: "Sprawdzenie listy klientów",
    batch_p: "Plik CSV z kolumną name (lub imie + nazwisko), opcjonalnie birth i nationality. Separator: przecinek, średnik lub tabulator. Do 300 wierszy.",
    batch_drop: "Wybierz plik CSV lub upuść go tutaj", batch_run: "Sprawdź plik", batch_sample: "Przykładowy plik",
    batch_dl: "Pobierz wyniki (CSV)", batch_progress: "Sprawdzono {done} z {total}", rows: "wierszy", batch_trunc: "plik skrócony do 300 wierszy",
    batch_click: "kliknij wiersz, aby otworzyć pełne sprawdzenie",
    audit_h: "Dziennik sprawdzeń", audit_p: "Każde wyszukiwanie, sprawdzenie pliku i decyzja analityka — kto, co i kiedy.",
    refresh: "Odśwież", a_time: "Czas", a_action: "Akcja", a_query: "Zapytanie", a_result: "Wynik",
    a_search: "wyszukiwanie", a_batch: "plik CSV", a_decision: "decyzja", a_telegram: "Telegram", audit_empty: "Dziennik jest pusty — wykonaj pierwsze sprawdzenie.",
    d_false_positive: "false positive", d_escalation: "eskalacja", d_freeze: "zamrożenie",
    lists_h: "Listy sankcyjne",
    lists_p: "Oficjalne skonsolidowane listy pobierane bezpośrednio od wydawców i zapisywane we wspólnym schemacie. Aktualizacja: python -m app.update",
    l_entries: "rekordów", l_aliases: "aliasów", l_dob: "z datą ur.", l_types: "Typy", l_scripts: "Alfabety aliasów",
    l_programs: "Najczęstsze programy", l_os: "Lista krajowa pobierana przez OpenSanctions (licencja CC BY-NC 4.0 — tylko użytek niekomercyjny).",
    f_lists: "Sprawdzane listy", l_version: "Wersja listy", l_fetched: "pobrano", l_source: "źródło danych",
    latin: "łaciński", cyrillic: "cyrylica", arabic: "arabski", greek: "grecki", other: "inne",
    method_h: "Metodologia", method_p: "Jak powstaje wynik — od wpisanego nazwiska do decyzji analityka.",
    p1: "Wykrycie języka", p1d: "і ї є ґ → ukraiński, ъ → rosyjski, ы э → rosyjski lub białoruski, ў → białoruski; brak cech → wszystkie trzy.",
    p2: "Warianty", p2d: "8 systemów transliteracji, wariacje liter z wagą prawdopodobieństwa, odpowiedniki imion (Сергій ↔ Сергей).",
    p3: "Indeks", p3d: "~58 tys. unikalnych słów ze wszystkich aliasów; każdy wariant porównywany ze słownikiem jednym wektorowym wywołaniem.",
    p4: "Dopasowanie", p4d: "Optymalne przypisanie słów (kolejność bez znaczenia), osobna kontrola nazwiska, token_sort_ratio.",
    p5: "Czynniki", p5d: "Data urodzenia i obywatelstwo podnoszą wynik lub wskazują na false positive.",
    p6: "Decyzja", p6d: "Raport do eskalacji: false positive, eskalacja lub zamrożenie — zapis w dzienniku.",
    thr_h: "Progi", thr_weak: "słabe — ukryte", thr_review: "do weryfikacji", thr_match: "trafienie",
    table_h: "Tablica transliteracji", table_sub: "generowana z kodu, który wykonuje wyszukiwanie · kilka wartości = zależność od pozycji litery",
    examples_h: "Przykłady", ctx_initial: "na początku słowa", ctx_middle: "po spółgłosce", ctx_after_vowel: "po samogłosce", ctx_before_soft: "przed е/и/ь",
    letter_not_in: "litera nie występuje w tym języku",
    foot: "Dane: oficjalne listy UE (FSF), Rady Bezpieczeństwa ONZ i OFAC SDN; listy PL MSWiA, UK FCDO i UA RNBO przez OpenSanctions (CC BY-NC 4.0). Projekt demonstracyjny — nie zastępuje systemów komercyjnych (World-Check, Dow Jones).",
    conflict_birth: "inna data urodzenia", conflict_nationality: "inne obywatelstwo", conflict_alias: "słaby alias",
    conflict_gender: "inna płeć", conflict_number: "inny numer w nazwie",
    f_gender: "Płeć", g_m: "mężczyzna", g_f: "kobieta", f_doc: "Nr dokumentu", g_inferred: "płeć wywnioskowana z nazwiska",
    loading: "Ładowanie indeksu list…", loading_short: "Ładowanie indeksu…", new_check: "Nowe sprawdzenie",
    short_h: "Za krótkie zapytanie", short_p: "Wpisz pełne imię i nazwisko lub nazwę podmiotu — sama litera albo przedimek (al, bin) nie wystarczą.", error: "Błąd", list_error: "błąd pobierania",
  },
  en: {
    tagline: "Transliteration-aware sanctions screening", analyst: "Analyst",
    disclaimer: "Demo tool. Not a basis for compliance decisions.",
    nav_work: "Work", nav_data: "Data", tab_screen: "Screening", tab_batch: "Batch (CSV)", tab_audit: "Audit log",
    tab_lists: "Sanctions lists", tab_method: "Methodology",
    f_name: "Full name / entity name *", f_birth: "Date of birth", f_nat: "Nationality", f_type: "Type",
    t_person: "individual", t_entity: "entity", t_any: "any", check: "Screen", checking: "Screening…",
    intro_eyebrow: "The transliteration gap", intro_h: "One surname, many spellings",
    intro_p: "The same person appears in a passport, in the press and on a sanctions list under different Latin spellings. The tool generates the variants using official transliteration systems and checks each one against six sanctions lists: EU, UN, OFAC, the Polish MSWiA list, the UK list and the Ukrainian NSDC register.",
    demo_h: "Demo scenarios", demo_exact: "Exact match", demo_translit: "Found only through transliteration",
    demo_translit_meta: "Polish spelling", demo_fp: "False positive", demo_by: "Belarusian Cyrillic",
    map_h: "Match map", map_sub: "query → the variant that produced the hit → list record",
    col_query: "Query", col_variant: "Variant (system)", col_hit: "List record", col_lists: "Lists",
    more_variants: "+ {n} other variants checked without a hit", no_hits_map: "None of the {n} variants produced a hit above the threshold.",
    results: "Results", show_weak: "show weak (< 75)", report: "Escalation report",
    c_score: "Score", c_status: "Status", c_listed: "Listed name", c_alias: "Matched alias", c_source: "List",
    c_program: "Programme", c_dob: "DOB", c_name: "Name", c_best: "Best hit",
    variants_title: "Generated transliteration variants",
    v_match: "Possible match — escalate", v_review: "Analyst review required", v_clear: "No hits above the threshold",
    s_match: "Hit", s_review: "Review", s_clear: "Clear",
    match: "Possible match", review: "Review", weak: "Weak", clear: "No hits",
    lang_detected: "language", lang_uk: "Ukrainian", lang_ru: "Russian", lang_be: "Belarusian", lang_latin: "Latin script",
    combos: "variant combinations", in_ms: "in {ms} ms", lists_checked: "lists dated",
    none: "No hits above 75. Turn on “show weak” to see candidates below the threshold.", none_weak: "No candidates above 60.",
    by_system: "Full name by system", per_token: "All variants by word",
    legend_named: "from a named system", legend_var: "phonetic variant", legend_eq: "from another-language form (Сергій ↔ Сергей)",
    why: "Why this hit", factors: "Additional factors", record: "List record", aliases: "All aliases",
    calc: "Score calculation", surname: "surname", ignored: "ignored — the record has no patronymic",
    channel_skeleton: "phonetic skeleton — matched despite a different spelling", via_eq: "via form",
    no_factors: "No date of birth or nationality given — the score is based on the name only. Add them to confirm or rule out the identity.",
    form_orig: "alias compared as written", form_translit: "non-Latin alias compared after transliteration",
    open_source: "Open record at source",
    k_source: "Source", k_id: "Source ID", k_type: "Type", k_programs: "Programme / legal basis", k_listed: "Listed on",
    k_dob: "Date of birth", k_pob: "Place of birth", k_nat: "Nationality", k_function: "Function", k_sex: "Gender", k_docs: "Documents", k_remarks: "Remarks", k_link: "Link",
    person: "individual", entity: "entity", vessel: "vessel", aircraft: "aircraft",
    batch_h: "Screen a customer list",
    batch_p: "CSV file with a name column (or first_name + last_name), optionally birth and nationality. Comma, semicolon or tab separated. Up to 300 rows.",
    batch_drop: "Choose a CSV file or drop it here", batch_run: "Screen file", batch_sample: "Sample file",
    batch_dl: "Download results (CSV)", batch_progress: "Screened {done} of {total}", rows: "rows", batch_trunc: "file truncated to 300 rows",
    batch_click: "click a row to open the full check",
    audit_h: "Audit log", audit_p: "Every search, file check and analyst decision — who, what and when.",
    refresh: "Refresh", a_time: "Time", a_action: "Action", a_query: "Query", a_result: "Result",
    a_search: "search", a_batch: "CSV file", a_decision: "decision", a_telegram: "Telegram", audit_empty: "The log is empty — run the first check.",
    d_false_positive: "false positive", d_escalation: "escalation", d_freeze: "freeze",
    lists_h: "Sanctions lists",
    lists_p: "Official consolidated lists downloaded directly from the publishers and stored in one schema. Update: python -m app.update",
    l_entries: "records", l_aliases: "aliases", l_dob: "with DOB", l_types: "Types", l_scripts: "Alias scripts",
    l_programs: "Top programmes", l_os: "National list obtained via OpenSanctions (CC BY-NC 4.0 — non-commercial use only).",
    f_lists: "Lists to check", l_version: "List version", l_fetched: "downloaded", l_source: "data source",
    latin: "Latin", cyrillic: "Cyrillic", arabic: "Arabic", greek: "Greek", other: "other",
    method_h: "Methodology", method_p: "How a score is produced — from the typed name to the analyst's decision.",
    p1: "Language detection", p1d: "і ї є ґ → Ukrainian, ъ → Russian, ы э → Russian or Belarusian, ў → Belarusian; no markers → all three.",
    p2: "Variants", p2d: "8 transliteration systems, weighted letter alternatives, equivalent given names (Сергій ↔ Сергей).",
    p3: "Index", p3d: "~58k distinct words from all aliases; every variant is compared with the vocabulary in one vectorised call.",
    p4: "Matching", p4d: "Optimal word alignment (order-independent), a separate surname check, token_sort_ratio.",
    p5: "Factors", p5d: "Date of birth and nationality raise the score or point to a false positive.",
    p6: "Decision", p6d: "Escalation report: false positive, escalation or freeze — written to the audit log.",
    thr_h: "Thresholds", thr_weak: "weak — hidden", thr_review: "review", thr_match: "possible match",
    table_h: "Transliteration table", table_sub: "generated from the code that runs the search · several values = depends on the letter's position",
    examples_h: "Examples", ctx_initial: "word-initial", ctx_middle: "after a consonant", ctx_after_vowel: "after a vowel", ctx_before_soft: "before е/и/ь",
    letter_not_in: "letter not used in this language",
    foot: "Data: official EU (FSF), UN Security Council and OFAC SDN lists; PL MSWiA, UK FCDO and UA NSDC lists via OpenSanctions (CC BY-NC 4.0). Demo project — not a replacement for commercial systems (World-Check, Dow Jones).",
    conflict_birth: "different date of birth", conflict_nationality: "different nationality", conflict_alias: "weak alias",
    conflict_gender: "different gender", conflict_number: "different number in name",
    f_gender: "Gender", g_m: "male", g_f: "female", f_doc: "Document no.", g_inferred: "gender inferred from the name",
    loading: "Loading list index…", loading_short: "Loading index…", new_check: "New check",
    short_h: "Query too short", short_p: "Enter a full name or an entity name — a single letter or a particle (al, bin) is not enough.", error: "Error", list_error: "download error",
  },
};
const SYS = {
  pl: { UA_KMU2010: "UA — KMU 2010 (oficjalna)", RU_ICAO: "RU — ICAO 9303 (paszporty)", RU_GOST: "RU — GOST 7.79-2000",
        BGN: "BGN/PCGN", POP: "angielska potoczna", PL: "polska (PWN)", DE: "niemiecka (Duden)", BY_PASS: "BY — paszportowa",
        VAR: "wariant fonetyczny", LATIN: "zapis wejściowy", LATIN_ALT: "alternatywna pisownia", SKELETON: "szkielet fonetyczny", CYR: "zapis oryginalny (cyrylica)" },
  en: { UA_KMU2010: "UA — KMU 2010 (official)", RU_ICAO: "RU — ICAO 9303 (passports)", RU_GOST: "RU — GOST 7.79-2000",
        BGN: "BGN/PCGN", POP: "common English", PL: "Polish (PWN)", DE: "German (Duden)", BY_PASS: "BY — passport",
        VAR: "phonetic variant", LATIN: "input spelling", LATIN_ALT: "alternative spelling", SKELETON: "phonetic skeleton", CYR: "original script (Cyrillic)" },
};
const LIST_LABEL = { pl: { EU: "UE", UN: "ONZ", OFAC: "OFAC", PL: "PL MSWiA", UK: "UK", UA: "UA RNBO" },
                     en: { EU: "EU", UN: "UN", OFAC: "OFAC", PL: "PL MSWiA", UK: "UK", UA: "UA NSDC" } };
const OPEN_SANCTIONS = ["PL", "UK", "UA"];

let lang = "pl";
let last = null;          // last search response
let status = null;
const cache = {};
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const t = (k, vars) => {
  let s = I18N[lang][k] ?? I18N.pl[k] ?? k;
  if (vars) Object.entries(vars).forEach(([a, b]) => { s = s.replace(`{${a}}`, b); });
  return s;
};
const sys = (code) => SYS[lang][code] || code;
const listLabel = (src) => LIST_LABEL[lang][src] || src;
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmt = (n) => Number(n || 0).toLocaleString(lang === "pl" ? "pl-PL" : "en-GB");
const factorText = (f) => (lang === "en" && f.text_en ? f.text_en : f.text);
function store(k, v) { try { if (v !== undefined) localStorage.setItem(k, v); return localStorage.getItem(k); } catch (_) { return null; } }
async function getJSON(url, opts) {
  const r = await fetch(url, opts);
  const body = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(typeof body.detail === "string" ? body.detail : `HTTP ${r.status}`);
  return body;
}

function applyLang() {
  document.documentElement.lang = lang;
  $$("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
  $$(".lang button").forEach((b) => b.classList.toggle("on", b.dataset.lang === lang));
  renderSideLists();
  renderIntroFan();
  if (last) renderSearch(last);
  const tab = $(".side button.on")?.dataset.tab;
  if (tab && tab !== "screen") showTab(tab);
}

/* =====================================================================
   sidebar: list versions
   ===================================================================== */
async function loadStatus() {
  try {
    status = await getJSON("/api/status");
  } catch (_) { status = null; }
  renderSideLists();
  renderPick();
  if (!status || !status.ready) setTimeout(loadStatus, 2500);
}

function renderPick() {
  const box = $("#pick");
  if (!status || box.dataset.ready) return;
  let saved = null;
  try { saved = JSON.parse(store("lists") || "null"); } catch (_) {}
  box.innerHTML = Object.keys(status.lists).map((k) =>
    `<label title="${OPEN_SANCTIONS.includes(k) ? "OpenSanctions (CC BY-NC 4.0)" : ""}"><input type="checkbox" value="${k}" ${!saved || saved.includes(k) ? "checked" : ""}>
     ${esc(listLabel(k))}</label>`).join("");
  box.dataset.ready = "1";
  box.addEventListener("change", () => store("lists", JSON.stringify(pickedLists())));
}

function pickedLists() { return $$("#pick input:checked").map((i) => i.value); }

function renderSideLists() {
  const box = $("#side-lists");
  if (!status) { box.innerHTML = `<div class="muted"><span class="spinner dark"></span>${t("loading")}</div>`; return; }
  box.innerHTML = Object.entries(status.lists).map(([k, v]) => v.status !== "ok"
    ? `<div class="side-list err"><b>${listLabel(k)}</b><span>${t("list_error")}</span></div>`
    : `<div class="side-list"><b>${listLabel(k)}</b><span class="n">${fmt(v.record_count)}</span><span class="d">${esc(v.list_date)}</span></div>`).join("")
    + (status.ready ? "" : `<div class="muted"><span class="spinner dark"></span>${t("loading")}</div>`);
}

async function loadCountries() {
  const list = await getJSON("/api/countries");
  const top = ["UA", "RU", "BY", "PL"];
  const opt = (c) => `<option value="${c.code}">${esc(c.name)} (${c.code})</option>`;
  $("#nat").innerHTML = `<option value="">—</option>` + list.filter((c) => top.includes(c.code)).map(opt).join("") +
    `<option disabled>──────────</option>` + list.map(opt).join("");
}

/* =====================================================================
   fan diagram (the match map) — HTML nodes + SVG connectors
   ===================================================================== */
function renderFan(el, cols, edges, animate) {
  el.innerHTML = `<svg class="fan-lines" aria-hidden="true"></svg>` + cols.map((c) =>
    `<div class="fan-col"><div class="fan-col-title">${esc(c.title)}</div>${c.nodes.map((n) =>
      `<div class="node ${n.cls || ""}" data-id="${n.id}" ${n.attrs || ""}>${n.html}</div>`).join("")}</div>`).join("");
  el._edges = edges;
  el.classList.toggle("reveal", !!animate);
  drawEdges(el, animate);
}

function drawEdges(el, animate) {
  const svg = el.querySelector(".fan-lines");
  if (!svg || !el._edges) return;
  const box = el.getBoundingClientRect();
  if (!box.width) return;
  svg.setAttribute("viewBox", `0 0 ${box.width} ${box.height}`);
  const pos = (id) => el.querySelector(`[data-id="${id}"]`)?.getBoundingClientRect();
  svg.innerHTML = el._edges.map((e) => {
    const a = pos(e.from), b = pos(e.to);
    if (!a || !b) return "";
    const x1 = a.right - box.left, y1 = a.top + a.height / 2 - box.top;
    const x2 = b.left - box.left, y2 = b.top + b.height / 2 - box.top;
    const mx = (x1 + x2) / 2;
    return `<path class="${e.cls || ""} ${animate ? "draw" : ""}" d="M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}"/>`;
  }).join("");
  if (animate) svg.querySelectorAll("path").forEach((p, i) => {
    p.style.setProperty("--len", Math.ceil(p.getTotalLength()));
    p.style.animationDelay = `${0.15 + (i % 12) * 0.04}s`;
  });
}

function renderIntroFan() {
  const el = $("#intro-fan");
  if (!el || $("#intro").hidden) return;
  const lists = status ? Object.keys(status.lists) : ["EU", "UN", "OFAC"];
  const variants = [
    ["Serhii Shcherbyna", "UA_KMU2010"], ["Serhiy Shcherbyna", "BGN"], ["Sergii Shcherbina", "VAR"],
    ["Siergiej Szczerbina", "PL"], ["Sergej Schtscherbina", "DE"], ["Sergey Shcherbina", "POP"],
  ];
  const cols = [
    { title: t("col_query"), nodes: [{ id: "q", cls: "query", html: `<div class="t">Сергій Щербина</div><div class="s">${t("lang_uk")}</div>` }] },
    { title: t("col_variant"), nodes: variants.map(([v, s], i) => ({ id: "v" + i, cls: "variant", html: `<div class="t">${v}</div><div class="s"><b>${esc(sys(s))}</b></div>` })) },
    { title: t("col_lists"), nodes: lists.map((s) => ({ id: s, cls: "list", html: `<span class="t">${listLabel(s)}</span><span class="s">${status ? fmt(status.lists[s]?.record_count) : ""}</span>` })) },
  ];
  const edges = variants.map((_, i) => ({ from: "q", to: "v" + i }));
  variants.forEach((_, i) => lists.forEach((s) => edges.push({ from: "v" + i, to: s, cls: "dim" })));
  renderFan(el, cols, edges, true);
}

function conflicts(r) {
  const bad = r.explanation.factors.filter((f) => f.ok === false).map((f) => t("conflict_" + f.field));
  return bad.length ? `<span class="conflict">≠ ${esc(bad.join(" · "))}</span>` : "";
}

function renderMatchFan(res) {
  const el = $("#match-fan");
  const hits = res.results.filter((r) => r.status !== "weak").slice(0, 6);
  const shown = hits.length ? hits : res.results.slice(0, 3);
  const variantIds = new Map();
  const vNodes = [], hNodes = [], edges = [];
  shown.forEach((r, i) => {
    const toks = r.explanation.tokens.filter((x) => !x.ignored && x.variant);
    const text = toks.map((x) => x.variant).join(" ");
    const codes = [...new Set(toks.flatMap((x) => x.system_codes || []))];
    const key = text + "|" + codes.join(",");
    if (!variantIds.has(key)) {
      variantIds.set(key, "v" + variantIds.size);
      vNodes.push({ id: variantIds.get(key), cls: "variant",
        html: `<div class="t">${esc(text)}</div><div class="s">${codes.map((c) => `<b>${esc(sys(c))}</b>`).join(", ")}</div>` });
      edges.push({ from: "q", to: variantIds.get(key), cls: r.status });
    }
    const hid = "h" + i;
    hNodes.push({ id: hid, cls: "hit " + r.status, attrs: `data-i="${res.results.indexOf(r)}" tabindex="0" role="button"`,
      html: `<span class="sc">${r.score.toFixed(0)}</span><span class="t">${esc(r.primary_name)}</span><span class="s">${listLabel(r.source)} · ${esc(r.matched_alias)}</span>`
        + conflicts(r) });
    edges.push({ from: variantIds.get(key), to: hid, cls: r.status });
  });
  const rest = Math.max(0, res.variants.reduce((a, tv) => a + tv.variants.length, 0) - vNodes.length);
  if (!shown.length) {
    vNodes.push({ id: "none", cls: "more", html: `<div class="t">${t("no_hits_map", { n: fmt(res.combinations) })}</div>` });
    edges.push({ from: "q", to: "none", cls: "dim" });
  } else if (rest) {
    vNodes.push({ id: "more", cls: "more", html: `<div class="t">${t("more_variants", { n: fmt(rest) })}</div>` });
    edges.push({ from: "q", to: "more", cls: "dim" });
  }
  const langs = res.languages.length ? res.languages.map((l) => t("lang_" + l)).join(" / ") : t("lang_latin");
  const meta = [res.birth, res.nationality].filter(Boolean).join(" · ");
  const cols = [
    { title: t("col_query"), nodes: [{ id: "q", cls: "query", html: `<div class="t">${esc(res.query)}</div><div class="s">${esc(langs)}${meta ? " · " + esc(meta) : ""}</div>` }] },
    { title: t("col_variant"), nodes: vNodes },
    { title: t("col_hit"), nodes: hNodes.length ? hNodes : [{ id: "nohit", cls: "more", html: `<div class="t">—</div>` }] },
  ];
  renderFan(el, cols, edges, true);
}

let resizeTimer;
window.addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => $$(".fan").forEach((f) => drawEdges(f, false)), 120);
});

/* =====================================================================
   screening
   ===================================================================== */
async function runSearch(e) {
  if (e) e.preventDefault();
  const name = $("#name").value.trim();
  if (!name) { $("#name").focus(); return; }
  const btn = $("#go");
  btn.disabled = true; btn.innerHTML = `<span class="spinner"></span>${status && !status.ready ? t("loading_short") : t("checking")}`;
  try {
    last = await getJSON("/api/search", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, birth: $("#birth").value.trim(), nationality: $("#nat").value,
        entity_type: $("#etype").value, gender: $("#gender").value, document: $("#document").value.trim(),
        sources: pickedLists(),
        show_weak: true, analyst: $("#analyst").value.trim() }) });
    renderSearch(last);
  } catch (err) {
    $("#out").hidden = false; $("#intro").hidden = true;
    $("#verdict").className = "verdict"; $("#verdict").textContent = `${t("error")}: ${err.message}`;
  } finally {
    btn.disabled = false; btn.textContent = t("check");
  }
}

const meter = (score, status, big) =>
  `<div class="meter ${status} ${big ? "big" : ""}"><b>${score.toFixed(0)}</b><span class="track"><i style="width:${Math.min(100, score)}%"></i></span></div>`;

function renderSearch(res) {
  $("#out").hidden = false; $("#intro").hidden = true; $("#reset").hidden = false;
  if (res.birth && !$("#birth").value) {
    $("#birth").value = res.birth;
    $("#name").value = $("#name").value.replace(res.birth, "").replace(/\s+/g, " ").trim();
  }
  if (res.too_short) {
    $("#verdict").className = "verdict";
    $("#verdict").innerHTML = `<div><div class="verdict-status">${t("short_h")}</div><div class="verdict-title">${t("short_p")}</div></div>`;
    $("#match-fan").closest(".block").hidden = true; $("#results").closest(".block").hidden = true; $("#variants").hidden = true;
    return;
  }
  $("#match-fan").closest(".block").hidden = false; $("#results").closest(".block").hidden = false; $("#variants").hidden = false;
  const counts = { match: 0, review: 0, weak: 0 };
  res.results.forEach((r) => counts[r.status]++);
  const level = counts.match ? "match" : counts.review ? "review" : "clear";
  const dates = [...new Set(Object.values(res.lists).map((v) => v.list_date))].join(", ");
  $("#verdict").className = "verdict " + level;
  $("#verdict").innerHTML = `
    <div><div class="verdict-status">${t("s_" + level)}</div><div class="verdict-title">${t("v_" + level)}</div></div>
    <div><div class="verdict-query">${esc(res.query)}${res.birth ? " · " + esc(res.birth) : ""}${res.nationality ? " · " + esc(res.nationality) : ""}${res.gender ? " · " + t("g_" + res.gender.toLowerCase()) : ""}${res.document ? " · " + esc(res.document) : ""}</div>
      <div class="verdict-meta"><span>${fmt(res.combinations)} ${t("combos")} ${t("in_ms", { ms: res.elapsed_ms })}</span>
      <span>${t("lists_checked")} ${esc(dates)}</span>
      ${res.gender_inferred ? `<span>${t("g_inferred")}: ${t("g_" + res.gender_inferred.toLowerCase())}</span>` : ""}</div></div>
    <div class="verdict-counts">
      <div class="count match"><b>${counts.match}</b><span>${t("match")}</span></div>
      <div class="count review"><b>${counts.review}</b><span>${t("review")}</span></div>
      <a class="button solid" href="/report/${res.search_id}?lang=${lang}" target="_blank" rel="noopener" style="align-self:center">${t("report")}</a>
    </div>`;
  renderMatchFan(res);
  renderTable(res);
  renderVariants(res);
}

function dob(list) {
  return [...new Set((list || []).map((b) => b.date || b.raw || (b.from_year ? `${b.from_year}–${b.to_year}` : b.year || "")).filter(Boolean))].join(", ");
}

function renderTable(res) {
  const showWeak = $("#weak").checked;
  const rows = res.results.filter((r) => showWeak || r.status !== "weak");
  $("#results tbody").innerHTML = rows.map((r) => `<tr class="${r.status}" data-i="${res.results.indexOf(r)}" tabindex="0">
      <td data-label="${t("c_score")}">${meter(r.score, r.status)}</td>
      <td data-label="${t("c_status")}"><span class="badge ${r.status}">${t(r.status)}</span></td>
      <td data-label="${t("c_listed")}">${esc(r.primary_name)}<div class="sub">${t(r.entity_type)}</div></td>
      <td data-label="${t("c_alias")}" class="alias-cell">${esc(r.matched_alias)}</td>
      <td data-label="${t("c_source")}" class="src">${listLabel(r.source)}</td>
      <td data-label="${t("c_program")}">${esc(r.programs.slice(0, 4).join(", "))}${r.programs.length > 4 ? " …" : ""}</td>
      <td data-label="${t("c_dob")}">${esc(dob(r.birth_dates))}</td></tr>`).join("");
  $("#empty").hidden = rows.length > 0;
  $("#empty").textContent = showWeak ? t("none_weak") : t("none");
}

function sameForm(form, original) {
  const n = (s) => s.toLowerCase().replace(/ё/g, "е").replace(/['’ʼ]/g, "");
  const a = n(form), b = n(original);
  return a === b || a === b.replace(/([сц])ьк(ий|ій|а|е|и)$/, "$1к$2");
}

function renderVariants(res) {
  const total = res.variants.reduce((a, tv) => a + tv.variants.length, 0);
  $("#variants-count").textContent = `(${total})`;
  const sysRows = res.examples.length ? `<div><h3 class="sub-h">${t("by_system")}</h3><table class="sys-table">${res.examples.map((x) =>
    `<tr><td>${esc(x.text)}</td><td>${esc(sys(x.system))} · ${t("lang_" + x.lang)}</td></tr>`).join("")}</table></div>` : "";
  const tokens = res.variants.map((tv) => `<div class="token-block">
      <h3>${esc(tv.original)}<span class="lang-tag">${tv.langs.length ? tv.langs.map((l) => t("lang_" + l)).join(" / ") : t("lang_latin")} · ${tv.variants.length}</span></h3>
      <div class="vlist">${tv.variants.map((v) => {
        const named = v.systems.some((s) => !["VAR", "LATIN_ALT"].includes(s));
        const eq = tv.script === "cyrillic" && v.source_form && !sameForm(v.source_form, tv.original);
        return `<span class="v ${named ? "named" : ""} ${eq ? "eq" : ""}" title="${esc(v.systems.map(sys).join(", "))}${eq ? " · " + esc(v.source_form) : ""}">${esc(v.text)}</span>`;
      }).join("")}</div></div>`).join("");
  $("#variants-body").innerHTML = sysRows + `<div><h3 class="sub-h">${t("per_token")}</h3><div style="display:grid;gap:14px">${tokens}</div></div>
    <div class="legend"><span><span class="v named">Abc</span>${t("legend_named")}</span><span><span class="v">Abc</span>${t("legend_var")}</span>
    <span><span class="v eq">Abc</span>${t("legend_eq")}</span></div>`;
}

/* =====================================================================
   match card
   ===================================================================== */
async function openCard(idx) {
  const r = last.results[idx];
  if (!r) return;
  const body = $("#card-body");
  body.innerHTML = cardHead(r) + cardWhy(r) + `<p class="muted"><span class="spinner dark"></span></p>`;
  $("#card").hidden = false; $("#scrim").hidden = false; $("#card-close").focus();
  try {
    const d = await getJSON(`/api/entry/${r.entry_id}`);
    body.innerHTML = cardHead(r) + cardWhy(r) + cardRecord(d, r);
  } catch (err) {
    body.insertAdjacentHTML("beforeend", `<p>${t("error")}: ${esc(err.message)}</p>`);
  }
}

function cardHead(r) {
  return `<div class="src">${listLabel(r.source)} · ${esc(r.source_id)} · ${t(r.entity_type)}</div><h2 id="card-title">${esc(r.primary_name)}</h2>
    <div class="card-score">${meter(r.score, r.status, true)}<span class="badge ${r.status}">${t(r.status)}</span></div>`;
}

function cardWhy(r) {
  const ex = r.explanation;
  const chains = ex.tokens.map((x) => {
    let note = (x.system_codes || []).map((c) => `<b>${esc(sys(c))}</b>`).join(", ");
    if (x.channel === "skeleton") note = `<b>${t("channel_skeleton")}</b> <span class="alias-cell">[${esc(x.skeleton || "")}]</span>`;
    if (x.via_equivalent) note += ` · ${t("via_eq")} ${esc(x.equivalent_form)}`;
    if (x.ignored) note = t("ignored");
    return `<div class="chain ${x.ignored ? "ignored" : ""}">
      <span class="q ${x.is_surname ? "surname" : ""}" data-label="${t("surname")}">${esc(x.query_token)}</span><span class="arrow">→</span>
      <span class="var">${esc(x.variant || "—")}</span><span class="arrow">→</span>
      <span class="hit">${esc(x.alias_token || "—")}<span class="sim">${x.similarity.toFixed(0)}%</span></span>
      <span class="sys">${note}</span></div>`;
  }).join("");
  const f = ex.factors.length ? `<ul class="factors">${ex.factors.map((x) =>
    `<li class="${x.ok === true ? "ok" : x.ok === false ? "bad" : "neutral"}">${esc(factorText(x))} <span class="muted">(${x.effect > 0 ? "+" : ""}${x.effect})</span></li>`).join("")}</ul>`
    : `<p class="muted">${t("no_factors")}</p>`;
  const kind = ex.form_kind === "orig" ? t("form_orig") : `${t("form_translit")} (${esc(sys(ex.form_kind.split(":")[1]) || ex.form_kind.split(":")[1])}): <span class="alias-cell">${esc(ex.alias_compared_as)}</span>`;
  const adj = ex.factors.map((x) => (x.effect >= 0 ? " + " : " − ") + Math.abs(x.effect)).join("");
  return `<h3>${t("why")}</h3>${chains}<p class="muted small">${kind}</p>
    <h3>${t("factors")}</h3>${f}
    <h3>${t("calc")}</h3><div class="calc">0.7 × ${ex.aligned} + 0.3 × ${ex.surname_similarity} (${t("surname")}) − ${ex.penalty}<br>
    token_sort_ratio = ${ex.token_sort_ratio} → ${r.name_score}${adj} = <b>${r.score}</b></div>`;
}

function cardRecord(d, r) {
  const kv = (k, v) => (v ? `<dt>${t(k)}</dt><dd>${v}</dd>` : "");
  const pob = [...new Set((d.birth_dates || []).map((b) => b.place).filter(Boolean))].join("; ");
  const ref = d.extra.reference && d.extra.reference !== d.source_id ? " · " + d.extra.reference : "";
  return `<h3>${t("record")}</h3><dl class="kv">
    ${kv("k_source", esc(d.source_name))}${kv("k_id", esc(d.source_id + ref))}${kv("k_programs", esc(d.programs.join(", ")))}
    ${kv("k_listed", esc(d.listed_on))}${kv("k_dob", esc(dob(d.birth_dates)))}${kv("k_pob", esc(pob))}
    ${kv("k_nat", esc(d.nationalities.map((n) => n.name + (n.iso2 ? ` (${n.iso2})` : "")).join(", ")))}
    ${kv("k_sex", d.extra.sex ? t("g_" + d.extra.sex.toLowerCase()) : "")}
    ${kv("k_docs", (d.extra.identifiers || []).slice(0, 8).map((x) => `${esc(x.type)}: <span class="alias-cell">${esc(x.number)}</span>${x.country ? " (" + esc(x.country) + ")" : ""}`).join("<br>"))}
    ${kv("k_function", esc(d.extra.function))}${kv("k_remarks", esc(d.remarks))}</dl>
    <h3>${t("aliases")} (${d.aliases.length})</h3><ul class="aliases">${d.aliases.map((a) =>
      `<li class="${a.quality === "weak" ? "q-weak" : ""} ${a.name === r.matched_alias ? "hl" : ""}">${esc(a.name)} <span class="muted">${esc(a.lang || "")}</span></li>`).join("")}</ul>
    <div class="card-actions"><a class="button solid" href="/report/${last.search_id}?lang=${lang}" target="_blank" rel="noopener">${t("report")}</a>
    ${d.url ? `<a class="button" href="${esc(d.url)}" target="_blank" rel="noopener">${t("open_source")}</a>` : ""}</div>`;
}

function resetSearch() {
  last = null;
  ["#name", "#birth", "#document"].forEach((x) => { $(x).value = ""; });
  $("#nat").value = ""; $("#gender").value = "";
  $("#out").hidden = true; $("#intro").hidden = false; $("#reset").hidden = true;
  renderIntroFan(); $("#name").focus();
}

function closeCard() { $("#card").hidden = true; $("#scrim").hidden = true; }

/* =====================================================================
   batch
   ===================================================================== */
let batchResults = [];
async function runBatch(e) {
  e.preventDefault();
  const f = $("#csv").files[0];
  if (!f) return;
  const btn = $("#batch button[type=submit]");
  btn.disabled = true; btn.innerHTML = `<span class="spinner"></span>${t("batch_run")}`;
  $("#batch-out").hidden = true;
  const fd = new FormData();
  fd.append("file", f); fd.append("entity_type", $("#batch-type").value); fd.append("analyst", $("#analyst").value.trim());
  const prog = $("#batch-progress");
  try {
    const job = await getJSON("/api/batch", { method: "POST", body: fd });
    prog.hidden = false;
    let st;
    for (;;) {
      st = await getJSON(`/api/batch/${job.job_id}`);
      $(".bar span", prog).style.width = `${(100 * st.done) / st.total}%`;
      $("#batch-progress-text").textContent = t("batch_progress", { done: st.done, total: st.total });
      if (st.status === "done") break;
      await new Promise((ok) => setTimeout(ok, 400));
    }
    batchResults = st.results;
    $("#batch-out").hidden = false;
    $("#batch-summary").innerHTML = `<strong>${esc(f.name)}</strong> <span>${st.total} ${t("rows")}${st.truncated ? " · " + t("batch_trunc") : ""}</span>
      <span class="badge match">${st.summary.match} ${t("match")}</span> <span class="badge review">${st.summary.review} ${t("review")}</span>
      <span class="badge clear">${st.summary.clear} ${t("clear")}</span> <span class="muted small">${t("batch_click")}</span>`;
    $("#batch-csv").href = `/api/batch/${job.job_id}.csv`;
    $("#batch-table tbody").innerHTML = st.results.map((r, i) => {
      const h = r.hits[0];
      return `<tr class="${h ? "has-hit" : ""}" data-i="${i}" tabindex="0"><td>${r.row}</td><td>${esc(r.name)}</td><td>${esc(r.birth)}</td>
        <td><span class="badge ${r.status}">${t(r.status)}</span></td><td>${r.score != null ? meter(r.score, r.status) : ""}</td>
        <td>${h ? esc(h.primary_name) + `<div class="sub alias-cell">${esc(h.matched_alias)}</div>` : ""}</td>
        <td class="src">${h ? esc(lang === "en" ? ({ UE: "EU", ONZ: "UN" }[h.source] || h.source) : h.source) : ""}</td></tr>`;
    }).join("");
  } catch (err) {
    $("#batch-out").hidden = false;
    $("#batch-summary").textContent = `${t("error")}: ${err.message}`;
  } finally {
    btn.disabled = false; btn.textContent = t("batch_run");
    setTimeout(() => { prog.hidden = true; }, 600);
  }
}

function openBatchRow(i) {
  const r = batchResults[i];
  if (!r) return;
  $("#name").value = r.name; $("#birth").value = r.birth || ""; $("#nat").value = r.nationality || "";
  showTab("screen"); runSearch();
}

/* =====================================================================
   audit
   ===================================================================== */
async function loadAudit() {
  const rows = await getJSON("/api/audit?limit=200");
  const tb = $("#audit-table tbody");
  if (!rows.length) { tb.innerHTML = `<tr><td colspan="7" class="muted" style="text-align:center;padding:26px">${t("audit_empty")}</td></tr>`; return; }
  tb.innerHTML = rows.map((r) => {
    const q = r.query, s = r.summary;
    let query = "", result = "", link = "";
    if (r.action === "search" || r.action === "telegram") {
      query = esc([q.name, q.birth, q.nationality].filter(Boolean).join(" · "));
      result = `${s.top_score != null ? `<b class="alias-cell">${s.top_score.toFixed(0)}</b> · ` : ""}<span class="badge match">${s.match ?? 0}</span> <span class="badge review">${s.review ?? 0}</span>`;
      if (r.action === "search") link = `<a href="/report/${r.id}?lang=${lang}" target="_blank" rel="noopener">${t("report")}</a>`;
    } else if (r.action === "batch") {
      query = `${esc(q.file)} (${q.rows})`;
      result = `<span class="badge match">${s.match}</span> <span class="badge review">${s.review}</span> <span class="badge clear">${s.clear}</span>`;
    } else if (r.action === "decision") {
      query = `#${q.search_id}${q.name ? " · " + esc(q.name) : ""}`;
      result = `<b>${t("d_" + s.decision)}</b> <span class="muted">${esc(s.comment || "")}</span>`;
      link = `<a href="/report/${q.search_id}?lang=${lang}" target="_blank" rel="noopener">${t("report")}</a>`;
    }
    return `<tr><td>${r.id}</td><td>${esc(new Date(r.ts).toLocaleString(lang === "pl" ? "pl-PL" : "en-GB"))}</td><td>${esc(r.actor)}</td>
      <td>${t("a_" + r.action)}</td><td>${query}</td><td>${result}</td><td>${link}</td></tr>`;
  }).join("");
}

/* =====================================================================
   lists page
   ===================================================================== */
async function loadLists() {
  const box = $("#list-cards");
  if (!cache.lists) {
    box.innerHTML = `<p class="muted"><span class="spinner dark"></span>${t("loading")}</p>`;
    cache.lists = await getJSON("/api/lists");
  }
  const bars = (pairs, total, label) => `<div class="hbars">${pairs.map(([k, n]) =>
    `<div class="hbar"><span>${esc(label ? label(k) : k)}</span><span class="tr"><i style="width:${(100 * n) / total}%"></i></span><span class="n">${fmt(n)}</span></div>`).join("")}</div>`;
  box.innerHTML = Object.entries(cache.lists).map(([k, v]) => {
    const types = Object.entries(v.by_type || {});
    const scripts = Object.entries(v.by_script || {});
    const progs = v.top_programs || [];
    return `<article class="lcard">
      <div class="lcard-head"><span class="lcard-code">${listLabel(k)}</span><span class="muted small">${t("l_version")} <b>${esc(v.list_date)}</b></span></div>
      <div class="lcard-name">${esc(v.name)}</div>
      <div class="lcard-nums"><div><b>${fmt(v.entries)}</b><span>${t("l_entries")}</span></div><div><b>${fmt(v.aliases)}</b><span>${t("l_aliases")}</span></div>
        <div><b>${v.entries ? Math.round((100 * v.with_birth_date) / v.entries) : 0}%</b><span>${t("l_dob")}</span></div></div>
      <div><h3>${t("l_types")}</h3>${bars(types, v.entries, (x) => t(x))}</div>
      <div><h3>${t("l_scripts")}</h3>${bars(scripts, v.aliases, (x) => t(x))}</div>
      <div><h3>${t("l_programs")}</h3>${bars(progs, progs.length ? progs[0][1] : 1)}</div>
      ${v.provider === "opensanctions" ? `<div class="lcard-os">${t("l_os")}</div>` : ""}
      <div class="lcard-foot">${t("l_fetched")} ${esc((v.fetched_at || "").replace("T", " ").slice(0, 16))} UTC ·
        <a href="${esc(v.info_url)}" target="_blank" rel="noopener">${t("l_source")}</a></div>
    </article>`;
  }).join("");
}

/* =====================================================================
   methodology page
   ===================================================================== */
async function loadMethod() {
  $("#pipeline").innerHTML = [1, 2, 3, 4, 5, 6].map((i) => `<li><b>${t("p" + i)}</b><span>${t("p" + i + "d")}</span></li>`).join("");
  if (!cache.method) cache.method = await getJSON("/api/methodology");
  const m = cache.method;
  const th = m.thresholds;
  $("#thresholds").innerHTML = `<div class="thr-track"><div class="w"></div><div class="r"></div><div class="m"></div></div>
    <span class="thr-tick" style="left:0">0</span><span class="thr-tick" style="left:${th.review}%">${th.review}</span>
    <span class="thr-tick" style="left:${th.match}%">${th.match}</span><span class="thr-tick" style="left:100%">100</span>
    <span class="thr-label" style="left:${th.review / 2}%">${t("thr_weak")}</span>
    <span class="thr-label" style="left:${(th.review + th.match) / 2}%">${t("thr_review")}</span>
    <span class="thr-label" style="left:${(th.match + 100) / 2}%">${t("thr_match")}</span>`;
  const head = `<thead><tr><th></th>${m.columns.map((c) => `<th>${esc(sys(c.system))}<small>${t("lang_" + c.lang)}</small></th>`).join("")}</tr></thead>`;
  const ref = "RU_ICAO";
  const body = m.rows.map((r) => {
    const base = (r.cells[ref] || []).map((o) => o.latin).join("/");
    return `<tr><th>${esc(r.letter)}<small>${r.langs.map((l) => l.toUpperCase()).join(" ")}</small></th>${m.columns.map((c) => {
      const cell = r.cells[c.id];
      if (!cell) return `<td class="na" title="${t("letter_not_in")}"></td>`;
      const val = cell.map((o) => o.latin).join("/");
      const html = cell.map((o, i) => `<span class="${i ? "alt" : ""}" title="${o.contexts.map((x) => t("ctx_" + x)).join(", ")}">${esc(o.latin) || "∅"}</span>`).join(" / ");
      return `<td class="${base && val !== base && c.id !== ref ? "diff" : ""}">${html}</td>`;
    }).join("")}</tr>`;
  }).join("");
  $("#letters").innerHTML = head + `<tbody>${body}</tbody>`;
  $("#examples").innerHTML = head + `<tbody>${m.examples.map((e) => `<tr><th>${esc(e.word)}<small>${e.lang.toUpperCase()}</small></th>${m.columns.map((c) =>
    e.cells[c.id] ? `<td>${esc(e.cells[c.id])}</td>` : `<td class="na"></td>`).join("")}</tr>`).join("")}</tbody>`;
}

/* =====================================================================
   wiring
   ===================================================================== */
function showTab(name) {
  $$(".side button").forEach((b) => b.classList.toggle("on", b.dataset.tab === name));
  $$(".tab").forEach((s) => { s.hidden = s.id !== "tab-" + name; });
  if (location.hash !== "#" + name) history.replaceState(null, "", name === "screen" ? location.pathname : "#" + name);
  const run = { audit: loadAudit, lists: loadLists, method: loadMethod }[name];
  if (run) run().catch((err) => console.error(err));
  if (name === "screen") requestAnimationFrame(() => $$(".fan").forEach((f) => drawEdges(f, false)));
}

document.addEventListener("DOMContentLoaded", () => {
  lang = store("lang") === "en" ? "en" : "pl";
  $("#analyst").value = store("analyst") || "";
  $("#analyst").addEventListener("change", (e) => store("analyst", e.target.value.trim()));
  $$(".lang button").forEach((b) => b.addEventListener("click", () => { lang = b.dataset.lang; store("lang", lang); applyLang(); }));
  $$(".side button").forEach((b) => b.addEventListener("click", () => showTab(b.dataset.tab)));
  $("#search").addEventListener("submit", runSearch);
  $("#reset").addEventListener("click", resetSearch);
  $("#weak").addEventListener("change", () => last && renderTable(last));
  const openFrom = (e) => { const el = e.target.closest("[data-i]"); if (el) openCard(+el.dataset.i); };
  $("#results tbody").addEventListener("click", openFrom);
  $("#match-fan").addEventListener("click", openFrom);
  ["#results tbody", "#match-fan"].forEach((s) => $(s).addEventListener("keydown", (e) => { if (e.key === "Enter") openFrom(e); }));
  $("#card-close").addEventListener("click", closeCard);
  $("#scrim").addEventListener("click", closeCard);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeCard();
    if (e.key === "/" && document.activeElement.tagName !== "INPUT" && document.activeElement.tagName !== "TEXTAREA") {
      e.preventDefault(); showTab("screen"); $("#name").focus();
    }
  });
  $$(".demo-card").forEach((c) => c.addEventListener("click", () => {
    $("#name").value = c.dataset.q; $("#birth").value = c.dataset.b || ""; $("#nat").value = c.dataset.n || "";
    $("#gender").value = ""; $("#document").value = ""; runSearch();
  }));
  $("#batch").addEventListener("submit", runBatch);
  $("#csv").addEventListener("change", () => { $("#drop-file").textContent = $("#csv").files[0]?.name || ""; });
  const drop = $("#drop");
  ["dragenter", "dragover"].forEach((ev) => drop.addEventListener(ev, () => drop.classList.add("over")));
  ["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, () => drop.classList.remove("over")));
  $("#batch-table tbody").addEventListener("click", (e) => { const tr = e.target.closest("tr.has-hit"); if (tr) openBatchRow(+tr.dataset.i); });
  $("#audit-refresh").addEventListener("click", loadAudit);
  applyLang();
  loadStatus().then(renderIntroFan);
  loadCountries().catch(() => {});
  const hash = location.hash.slice(1);
  if (["batch", "audit", "lists", "method"].includes(hash)) showTab(hash);
});
