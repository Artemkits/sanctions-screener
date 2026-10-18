"use strict";

const I18N = {
  pl: {
    tagline: "Screening UE · ONZ · OFAC z uwzględnieniem transliteracji", analyst: "Analityk",
    disclaimer: "Narzędzie demonstracyjne. Nie stanowi podstawy do decyzji compliance.",
    tab_screen: "Screening", tab_batch: "Batch (CSV)", tab_audit: "Dziennik sprawdzeń",
    f_name: "Imię i nazwisko / nazwa *", f_birth: "Data urodzenia", f_nat: "Obywatelstwo", f_type: "Typ",
    t_person: "osoba fizyczna", t_entity: "podmiot", t_any: "dowolny", check: "Sprawdź",
    variants_title: "Wygenerowane warianty transliteracji", results: "Wyniki", show_weak: "pokaż słabe (< 75)",
    report: "Raport do eskalacji", c_score: "Wynik", c_status: "Status", c_listed: "Nazwa na liście",
    c_alias: "Dopasowany alias", c_source: "Źródło", c_program: "Program", c_dob: "Data ur.", c_link: "Rekord",
    c_name: "Imię i nazwisko", c_best: "Najlepsze trafienie",
    intro_h: "Jedno nazwisko — wiele zapisów",
    intro_p: "Сергій Щербина w różnych dokumentach to Serhii Shcherbyna, Sergiy Shcherbina, Siergiej Szczerbina albo Sergej Schtscherbina. Narzędzie generuje te warianty według oficjalnych systemów transliteracji i sprawdza każdy z nich w listach sankcyjnych UE, ONZ i OFAC.",
    try: "Przykłady:", batch_h: "Sprawdzenie listy klientów",
    batch_p: "Plik CSV z kolumną name (lub imie + nazwisko), opcjonalnie birth i nationality. Do 300 wierszy.",
    batch_sample: "Pobierz przykładowy plik", batch_run: "Sprawdź plik", batch_dl: "Pobierz wyniki (CSV)",
    audit_h: "Dziennik sprawdzeń", refresh: "Odśwież", a_time: "Czas", a_action: "Akcja", a_query: "Zapytanie", a_result: "Wynik",
    foot: "Dane: publiczne skonsolidowane listy UE (FSF), Rady Bezpieczeństwa ONZ oraz OFAC SDN. To nie jest system komercyjny (World-Check, Dow Jones).",
    match: "Trafienie", review: "Do weryfikacji", weak: "Słabe", clear: "Brak trafień",
    records: "rekordów", version: "wersja", list_error: "błąd pobierania", loading_index: "Ładowanie indeksu list…",
    checking: "Sprawdzanie…", checked: "Sprawdzono", in: "w", ms: "ms", combos: "kombinacji wariantów",
    lang_detected: "wykryty język", lang_uk: "ukraiński", lang_ru: "rosyjski", lang_be: "białoruski", lang_latin: "zapis łaciński",
    none: "Brak trafień powyżej progu 75.", none_weak: "Brak trafień powyżej progu 60.",
    hidden_weak: "ukrytych słabych", by_system: "Pełne imię według systemów", per_token: "Wszystkie warianty według tokenów",
    legend_named: "z nazwanego systemu", legend_var: "wariant fonetyczny", legend_eq: "z formy w innym języku (Сергій ↔ Сергей)",
    open_record: "otwórz", why: "Dlaczego to trafienie", factors: "Czynniki dodatkowe", record: "Rekord na liście",
    aliases: "Wszystkie aliasy", calc: "Obliczenie wyniku", surname: "nazwisko", ignored: "pominięte (otczestwo nieobecne na liście)",
    channel_skeleton: "szkielet fonetyczny — dopasowanie mimo różnej pisowni", via_eq: "przez formę",
    no_factors: "Nie podano daty urodzenia ani obywatelstwa — wynik opiera się wyłącznie na nazwie.",
    k_source: "Źródło", k_id: "ID w źródle", k_type: "Typ", k_programs: "Program / podstawa", k_listed: "Data wpisu",
    k_dob: "Data urodzenia", k_pob: "Miejsce urodzenia", k_nat: "Obywatelstwo", k_function: "Funkcja", k_remarks: "Uwagi", k_link: "Link do źródła",
    person: "osoba fizyczna", entity: "podmiot", vessel: "statek", aircraft: "statek powietrzny",
    a_search: "wyszukiwanie", a_batch: "batch", a_decision: "decyzja", a_telegram: "telegram",
    d_false_positive: "false positive", d_escalation: "eskalacja", d_freeze: "zamrożenie",
    batch_running: "Sprawdzanie pliku…", rows: "wierszy", form_kind_orig: "alias porównany w oryginalnym zapisie",
    form_kind_translit: "alias w innym alfabecie porównany po transliteracji",
  },
  en: {
    tagline: "Transliteration-aware EU · UN · OFAC screening", analyst: "Analyst",
    disclaimer: "Demo tool. Not a basis for compliance decisions.",
    tab_screen: "Screening", tab_batch: "Batch (CSV)", tab_audit: "Audit log",
    f_name: "Full name / entity name *", f_birth: "Date of birth", f_nat: "Nationality", f_type: "Type",
    t_person: "individual", t_entity: "entity", t_any: "any", check: "Screen",
    variants_title: "Generated transliteration variants", results: "Results", show_weak: "show weak (< 75)",
    report: "Escalation report", c_score: "Score", c_status: "Status", c_listed: "Listed name", c_alias: "Matched alias",
    c_source: "Source", c_program: "Programme", c_dob: "DOB", c_link: "Record", c_name: "Name", c_best: "Best hit",
    intro_h: "One surname, many spellings",
    intro_p: "Сергій Щербина appears in documents as Serhii Shcherbyna, Sergiy Shcherbina, Siergiej Szczerbina or Sergej Schtscherbina. The tool generates these variants using official transliteration systems and checks each of them against the EU, UN and OFAC sanctions lists.",
    try: "Try:", batch_h: "Screen a customer list",
    batch_p: "CSV file with a name column (or first_name + last_name), optionally birth and nationality. Up to 300 rows.",
    batch_sample: "Download a sample file", batch_run: "Screen file", batch_dl: "Download results (CSV)",
    audit_h: "Audit log", refresh: "Refresh", a_time: "Time", a_action: "Action", a_query: "Query", a_result: "Result",
    foot: "Data: public consolidated lists of the EU (FSF), the UN Security Council and OFAC SDN. Not a commercial system (World-Check, Dow Jones).",
    match: "Possible match", review: "Review", weak: "Weak", clear: "No hits",
    records: "records", version: "version", list_error: "download error", loading_index: "Loading list index…",
    checking: "Screening…", checked: "Checked", in: "in", ms: "ms", combos: "variant combinations",
    lang_detected: "detected language", lang_uk: "Ukrainian", lang_ru: "Russian", lang_be: "Belarusian", lang_latin: "Latin script",
    none: "No hits above 75.", none_weak: "No hits above 60.", hidden_weak: "weak hidden",
    by_system: "Full name by system", per_token: "All variants by token",
    legend_named: "from a named system", legend_var: "phonetic variant", legend_eq: "from another-language form (Сергій ↔ Сергей)",
    open_record: "open", why: "Why this hit", factors: "Additional factors", record: "List record",
    aliases: "All aliases", calc: "Score calculation", surname: "surname", ignored: "ignored (patronymic not in the list)",
    channel_skeleton: "phonetic skeleton — matched despite different spelling", via_eq: "via form",
    no_factors: "No date of birth or nationality given — the score is based on the name only.",
    k_source: "Source", k_id: "Source ID", k_type: "Type", k_programs: "Programme / legal basis", k_listed: "Listed on",
    k_dob: "Date of birth", k_pob: "Place of birth", k_nat: "Nationality", k_function: "Function", k_remarks: "Remarks", k_link: "Source link",
    person: "individual", entity: "entity", vessel: "vessel", aircraft: "aircraft",
    a_search: "search", a_batch: "batch", a_decision: "decision", a_telegram: "telegram",
    d_false_positive: "false positive", d_escalation: "escalation", d_freeze: "freeze",
    batch_running: "Screening file…", rows: "rows", form_kind_orig: "alias compared as written",
    form_kind_translit: "non-Latin alias compared after transliteration",
  },
};
const SYSTEM_EN = {
  "UA — KMU 2010 (oficjalna ukraińska)": "UA — KMU 2010 (Ukrainian official)", "RU — ICAO 9303 (paszporty)": "RU — ICAO 9303 (passports)",
  "angielska potoczna": "common English", "polska (PWN)": "Polish (PWN)", "niemiecka (Duden)": "German (Duden)",
  "BY — paszportowa": "BY — passport", "wariant fonetyczny": "phonetic variant", "zapis łaciński (wejście)": "Latin input",
  "alternatywna pisownia łacińska": "alternative Latin spelling", "szkielet fonetyczny": "phonetic skeleton",
  "zapis oryginalny (cyrylica)": "original script (Cyrillic)",
};

let lang = "pl";
let last = null;          // last search response
const $ = (s, el = document) => el.querySelector(s);
const t = (k) => (I18N[lang][k] ?? I18N.pl[k] ?? k);
const sysName = (s) => (lang === "en" ? SYSTEM_EN[s] || s : s).replace(" · ukr.", lang === "en" ? " · uk" : " · ukr.");
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function store(k, v) { try { v === undefined ? null : localStorage.setItem(k, v); return localStorage.getItem(k); } catch (_) { return null; } }

function applyLang() {
  document.documentElement.lang = lang;
  document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll(".lang button").forEach((b) => b.classList.toggle("on", b.dataset.lang === lang));
  loadStatus();
  if (last) renderSearch(last);
}

/* ---------------- lists strip ---------------- */
async function loadStatus() {
  const box = $("#lists");
  try {
    const r = await fetch("/api/status");
    const s = await r.json();
    box.innerHTML = Object.entries(s.lists).map(([k, v]) => {
      const label = { EU: lang === "pl" ? "UE" : "EU", UN: lang === "pl" ? "ONZ" : "UN", OFAC: "OFAC" }[k];
      if (v.status !== "ok") return `<div class="list-item err"><b>${label}</b> ${t("list_error")}</div>`;
      return `<div class="list-item"><b>${label}</b><span class="n">${Number(v.record_count).toLocaleString(lang)}</span> ${t("records")}
        <span class="muted">${t("version")} ${esc(v.list_date)}</span></div>`;
    }).join("");
  } catch (_) {
    box.innerHTML = `<div class="list-item"><span class="spinner"></span>${t("loading_index")}</div>`;
    setTimeout(loadStatus, 3000);
  }
}

async function loadCountries() {
  const r = await fetch("/api/countries");
  const list = await r.json();
  const sel = $("#nat");
  const top = ["UA", "RU", "BY", "PL"];
  const opt = (c) => `<option value="${c.code}">${esc(c.name)} (${c.code})</option>`;
  sel.innerHTML = `<option value="">—</option>` + list.filter((c) => top.includes(c.code)).map(opt).join("") +
    `<option disabled>──────────</option>` + list.map(opt).join("");
}

/* ---------------- search ---------------- */
async function runSearch(e) {
  if (e) e.preventDefault();
  const btn = $("#search button[type=submit]");
  btn.disabled = true; btn.innerHTML = `<span class="spinner"></span>${t("checking")}`;
  try {
    const body = { name: $("#name").value.trim(), birth: $("#birth").value.trim(), nationality: $("#nat").value,
      entity_type: $("#etype").value, show_weak: true, analyst: $("#analyst").value.trim() };
    const r = await fetch("/api/search", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    if (!r.ok) throw new Error((await r.json()).detail || r.status);
    last = await r.json();
    renderSearch(last);
  } catch (err) {
    $("#out").hidden = false; $("#intro").hidden = true;
    $("#summary").textContent = "Error: " + err.message;
  } finally {
    btn.disabled = false; btn.textContent = t("check");
  }
}

function langLabel(res) {
  if (!res.languages.length) return t("lang_latin");
  return res.languages.map((l) => t("lang_" + l)).join(" / ");
}

function renderSearch(res) {
  $("#out").hidden = false; $("#intro").hidden = true;
  const showWeak = $("#weak").checked;
  const rows = res.results.filter((r) => showWeak || r.status !== "weak");
  const counts = { match: 0, review: 0, weak: 0 };
  res.results.forEach((r) => counts[r.status]++);
  $("#summary").innerHTML = `<strong>${esc(res.query)}</strong>
    <span>${t("lang_detected")}: ${esc(langLabel(res))}</span>
    <span class="pill">${t("checked")} ${res.combinations.toLocaleString(lang)} ${t("combos")} ${t("in")} ${res.elapsed_ms} ${t("ms")}</span>
    <span><span class="badge match">${counts.match}</span> <span class="badge review">${counts.review}</span>
    ${showWeak ? `<span class="badge weak">${counts.weak}</span>` : `<span class="muted">${counts.weak} ${t("hidden_weak")}</span>`}</span>`;
  renderVariants(res);
  $("#report").href = `/report/${res.search_id}?lang=${lang}`;
  const tb = $("#results tbody");
  tb.innerHTML = rows.map((r, i) => `<tr class="${r.status}" data-i="${res.results.indexOf(r)}" tabindex="0">
      <td class="score">${r.score.toFixed(0)}</td>
      <td><span class="badge ${r.status}">${t(r.status)}</span></td>
      <td>${esc(r.primary_name)}<div class="muted" style="font-size:12.5px">${t(r.entity_type)}</div></td>
      <td class="alias-cell">${esc(r.matched_alias)}</td>
      <td class="src">${esc(lang === "en" ? { UE: "EU", ONZ: "UN" }[r.source_label] || r.source_label : r.source_label)}</td>
      <td>${esc(r.programs.join(", "))}</td>
      <td>${esc(dob(r.birth_dates))}</td>
      <td><a href="${esc(r.url)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">${t("open_record")}</a></td>
    </tr>`).join("");
  const empty = $("#empty");
  empty.hidden = rows.length > 0;
  empty.textContent = showWeak ? t("none_weak") : t("none");
}

function dob(list) {
  return (list || []).map((b) => b.date || b.raw || (b.from_year ? `${b.from_year}–${b.to_year}` : b.year || "")).filter(Boolean).join(", ");
}

function renderVariants(res) {
  const total = res.variants.reduce((a, tv) => a + tv.variants.length, 0);
  $("#variants-count").textContent = `(${total})`;
  const sys = res.examples.length ? `<div><h3 class="token-block" style="margin:0 0 6px;font:600 14px var(--cond)">${t("by_system")}</h3>
    <table class="sys-table">${res.examples.map((x) => `<tr><td>${esc(x.text)}</td><td>${esc(sysName(x.label))}</td></tr>`).join("")}</table></div>` : "";
  const tokens = res.variants.map((tv) => `<div class="token-block">
      <h3>${esc(tv.original)}<span class="lang-tag">${tv.langs.length ? tv.langs.map((l) => t("lang_" + l)).join(" / ") : t("lang_latin")} · ${tv.variants.length}</span></h3>
      <div class="vlist">${tv.variants.map((v) => {
        const named = v.systems.some((s) => !["VAR", "LATIN_ALT"].includes(s));
        const eq = v.source_form && tv.script === "cyrillic" && !sameForm(v.source_form, tv.original);
        return `<span class="v ${named ? "named" : ""} ${eq ? "eq" : ""}" title="${esc(v.systems.join(", "))}${eq ? " · " + esc(v.source_form) : ""}">${esc(v.text)}</span>`;
      }).join("")}</div></div>`).join("");
  $("#variants-body").innerHTML = sys + `<div><h3 style="margin:0 0 10px;font:600 14px var(--cond)">${t("per_token")}</h3>
    <div style="display:grid;gap:14px">${tokens}</div></div>
    <div class="legend"><span><span class="v named">Abc</span>${t("legend_named")}</span><span><span class="v">Abc</span>${t("legend_var")}</span>
    <span><span class="v eq">Abc</span>${t("legend_eq")}</span></div>`;
}

function sameForm(form, original) {
  const n = (s) => s.toLowerCase().replace(/ё/g, "е").replace(/['’ʼ]/g, "");
  const a = n(form), b = n(original);
  return a === b || a === b.replace(/([сц])ьк(ий|ій|а|е|и)$/, "$1к$2");
}

/* ---------------- match card ---------------- */
async function openCard(idx) {
  const r = last.results[idx];
  const card = $("#card"), body = $("#card-body");
  body.innerHTML = cardHead(r) + `<p class="muted"><span class="spinner"></span></p>`;
  card.hidden = false; $("#scrim").hidden = false; $("#card-close").focus();
  const d = await (await fetch(`/api/entry/${r.entry_id}`)).json();
  body.innerHTML = cardHead(r) + cardWhy(r) + cardRecord(d);
}

function cardHead(r) {
  return `<div class="src">${esc(r.source_label)} · ${esc(r.source_id)}</div><h2 id="card-title">${esc(r.primary_name)}</h2>
    <div class="card-score"><span class="big">${r.score.toFixed(0)}</span><span class="badge ${r.status}">${t(r.status)}</span>
    <span class="muted">${t("c_alias")}: <b class="alias-cell">${esc(r.matched_alias)}</b></span></div>`;
}

function cardWhy(r) {
  const ex = r.explanation;
  const chains = ex.tokens.map((x) => {
    const systems = (x.systems || []).map((s) => `<b>${esc(sysName(s))}</b>`).join(", ");
    let note = systems;
    if (x.channel === "skeleton") note = `<b>${t("channel_skeleton")}</b> (${esc(x.variant)})`;
    if (x.via_equivalent) note += ` · ${t("via_eq")} ${esc(x.equivalent_form)}`;
    if (x.ignored) note = t("ignored");
    return `<div class="chain ${x.ignored ? "ignored" : ""}">
      <span class="q ${x.is_surname ? "surname" : ""}" data-label="${t("surname")}">${esc(x.query_token)}</span><span class="arrow">→</span>
      <span class="var">${esc(x.channel === "skeleton" ? x.variant : x.variant || "—")}</span><span class="arrow">→</span>
      <span class="hit">${esc(x.alias_token || "—")}<span class="sim">${x.similarity.toFixed(0)}%</span></span>
      <span class="sys">${note}</span></div>`;
  }).join("");
  const f = ex.factors.length ? `<ul class="factors">${ex.factors.map((x) =>
    `<li class="${x.ok === true ? "ok" : x.ok === false ? "bad" : "neutral"}">${esc(x.text)} <span class="muted">(${x.effect > 0 ? "+" : ""}${x.effect})</span></li>`).join("")}</ul>`
    : `<p class="muted">${t("no_factors")}</p>`;
  const kind = ex.form_kind === "orig" ? t("form_kind_orig") : `${t("form_kind_translit")} (${esc(ex.form_kind.split(":")[1])}): ${esc(ex.alias_compared_as)}`;
  return `<h3>${t("why")}</h3>${chains}<p class="muted" style="font-size:13px">${kind}</p>
    <h3>${t("factors")}</h3>${f}
    <h3>${t("calc")}</h3><div class="calc">0.7 × ${ex.aligned} (tokens) + 0.3 × ${ex.surname_similarity} (${t("surname")}) − ${ex.penalty} · token_sort_ratio ${ex.token_sort_ratio}
    → ${r.name_score} ${ex.factors.map((x) => (x.effect >= 0 ? "+ " : "− ") + Math.abs(x.effect)).join(" ")} = ${r.score}</div>`;
}

function cardRecord(d) {
  const kv = (k, v) => (v ? `<dt>${t(k)}</dt><dd>${v}</dd>` : "");
  const pob = (d.birth_dates || []).map((b) => b.place).filter(Boolean)[0];
  return `<h3>${t("record")}</h3><dl class="kv">
    ${kv("k_source", esc(d.source_name))}${kv("k_id", esc(d.source_id + (d.extra.reference && d.extra.reference !== d.source_id ? " · " + d.extra.reference : "")))}
    ${kv("k_type", t(d.entity_type))}${kv("k_programs", esc(d.programs.join(", ")))}${kv("k_listed", esc(d.listed_on))}
    ${kv("k_dob", esc(dob(d.birth_dates)))}${kv("k_pob", esc(pob))}${kv("k_nat", esc(d.nationalities.map((n) => n.name + (n.iso2 ? ` (${n.iso2})` : "")).join(", ")))}
    ${kv("k_function", esc(d.extra.function))}${kv("k_remarks", esc(d.remarks))}
    ${kv("k_link", `<a href="${esc(d.url)}" target="_blank" rel="noopener">${esc(d.url)}</a>`)}</dl>
    <h3>${t("aliases")} (${d.aliases.length})</h3><ul class="aliases">${d.aliases.map((a) =>
      `<li class="${a.quality === "weak" ? "q-weak" : ""}">${esc(a.name)} <span class="muted">${esc(a.lang || "")}</span></li>`).join("")}</ul>`;
}

function closeCard() { $("#card").hidden = true; $("#scrim").hidden = true; }

/* ---------------- batch ---------------- */
async function runBatch(e) {
  e.preventDefault();
  const f = $("#csv").files[0];
  if (!f) return;
  const btn = $("#batch button[type=submit]");
  btn.disabled = true; btn.innerHTML = `<span class="spinner"></span>${t("batch_running")}`;
  const fd = new FormData();
  fd.append("file", f); fd.append("entity_type", $("#batch-type").value); fd.append("analyst", $("#analyst").value.trim());
  try {
    const r = await fetch("/api/batch", { method: "POST", body: fd });
    const res = await r.json();
    if (!r.ok) throw new Error(res.detail || r.status);
    $("#batch-out").hidden = false;
    $("#batch-summary").innerHTML = `<strong>${esc(f.name)}</strong> <span>${res.rows} ${t("rows")}</span>
      <span class="badge match">${res.summary.match}</span> <span class="badge review">${res.summary.review}</span>
      <span class="badge clear">${res.summary.clear}</span>`;
    $("#batch-csv").href = `/api/batch/${res.batch_id}.csv`;
    $("#batch-table tbody").innerHTML = res.results.map((r) => {
      const h = r.hits[0];
      return `<tr><td>${r.row}</td><td>${esc(r.name)}</td><td>${esc(r.birth)}</td>
        <td><span class="badge ${r.status}">${t(r.status)}</span></td><td class="score">${r.score != null ? r.score.toFixed(0) : ""}</td>
        <td>${h ? esc(h.primary_name) + `<div class="muted alias-cell">${esc(h.matched_alias)}</div>` : ""}</td>
        <td class="src">${h ? esc(h.source) : ""}</td></tr>`;
    }).join("");
  } catch (err) {
    $("#batch-out").hidden = false;
    $("#batch-summary").textContent = "Error: " + err.message;
  } finally {
    btn.disabled = false; btn.textContent = t("batch_run");
  }
}

/* ---------------- audit ---------------- */
async function loadAudit() {
  const rows = await (await fetch("/api/audit?limit=200")).json();
  $("#audit-table tbody").innerHTML = rows.map((r) => {
    const q = r.query, s = r.summary;
    let query = "", result = "", link = "";
    if (r.action === "search" || r.action === "telegram") {
      query = esc([q.name, q.birth, q.nationality].filter(Boolean).join(" · "));
      result = `${s.top_score != null ? s.top_score.toFixed(0) : "—"} · <span class="badge match">${s.match ?? 0}</span> <span class="badge review">${s.review ?? 0}</span>`;
      if (r.action === "search") link = `<a href="/report/${r.id}?lang=${lang}" target="_blank" rel="noopener">${t("report")}</a>`;
    } else if (r.action === "batch") {
      query = `${esc(q.file)} (${q.rows})`;
      result = `<span class="badge match">${s.match}</span> <span class="badge review">${s.review}</span> <span class="badge clear">${s.clear}</span>`;
    } else if (r.action === "decision") {
      query = `#${q.search_id}`;
      result = `<b>${t("d_" + s.decision)}</b> ${esc(s.comment || "")}`;
      link = `<a href="/report/${q.search_id}?lang=${lang}" target="_blank" rel="noopener">${t("report")}</a>`;
    }
    return `<tr><td>${r.id}</td><td>${esc(new Date(r.ts).toLocaleString(lang))}</td><td>${esc(r.actor)}</td>
      <td>${t("a_" + r.action)}</td><td>${query}</td><td>${result}</td><td>${link}</td></tr>`;
  }).join("");
}

/* ---------------- wiring ---------------- */
function showTab(name) {
  document.querySelectorAll(".tabs button").forEach((b) => b.classList.toggle("on", b.dataset.tab === name));
  document.querySelectorAll(".tab").forEach((s) => { s.hidden = s.id !== "tab-" + name; });
  if (name === "audit") loadAudit();
}

document.addEventListener("DOMContentLoaded", () => {
  lang = store("lang") === "en" ? "en" : "pl";
  $("#analyst").value = store("analyst") || "";
  $("#analyst").addEventListener("change", (e) => store("analyst", e.target.value.trim()));
  document.querySelectorAll(".lang button").forEach((b) => b.addEventListener("click", () => { lang = b.dataset.lang; store("lang", lang); applyLang(); }));
  document.querySelectorAll(".tabs button").forEach((b) => b.addEventListener("click", () => showTab(b.dataset.tab)));
  $("#search").addEventListener("submit", runSearch);
  $("#weak").addEventListener("change", () => last && renderSearch(last));
  $("#results tbody").addEventListener("click", (e) => { const tr = e.target.closest("tr"); if (tr) openCard(+tr.dataset.i); });
  $("#results tbody").addEventListener("keydown", (e) => { if (e.key === "Enter") { const tr = e.target.closest("tr"); if (tr) openCard(+tr.dataset.i); } });
  $("#card-close").addEventListener("click", closeCard);
  $("#scrim").addEventListener("click", closeCard);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeCard(); });
  document.querySelectorAll(".chip").forEach((c) => c.addEventListener("click", () => {
    $("#name").value = c.dataset.q; $("#birth").value = c.dataset.b || ""; runSearch();
  }));
  $("#batch").addEventListener("submit", runBatch);
  $("#audit-refresh").addEventListener("click", loadAudit);
  applyLang();
  loadCountries();
});
