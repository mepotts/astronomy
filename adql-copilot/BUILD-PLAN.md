# BUILD-PLAN — TAP/ADQL Query Copilot

Companion to `SPEC.md` (what + why) and `DATA-SOURCES.md` (the verified VO/TAP/ADQL facts).
This file is the **how**: stack, architecture, milestones, first-task checklist, correctness
strategy, kill criteria, and open questions.

Guiding principle (from SPEC "What we build first"): **deterministic schema-aware linter/explainer
is the always-correct foundation; the NL→ADQL LLM is layered on top and gated by that foundation.**

---

## 1. Stack (chosen, with alternatives considered)

**Chosen: Python library + thin CLI, built as an installable package; web/notebook UI deferred to M3.**

| Decision | Choice | Why | Alternatives rejected |
|---|---|---|---|
| **Form factor** | Python package with a CLI front-end (`adql-copilot lint ...`) | The valuable core (parse → resolve → lint) is pure logic with zero UI. A library is importable from notebooks *and* wrappable by a web app later, so we don't paint ourselves into a UI corner. CLI gives an immediately runnable, scriptable, testable surface. | **Notebook-first**: great for the target audience but not unit-testable or composable as the primitive. **Web-app-first (Gradio/FastAPI)**: the dossier's eventual demo skin, but building UI before the engine inverts the risk — and the engine is what's novel. We keep both as M3 wrappers over the same library. |
| **TAP / schema access** | `pyvo` (primary) + `astroquery` (Gaia convenience/async) | PyVO is the IVOA-standard client: one `TAPService(url)` works for all four endpoints, exposes `.tables` and `TAP_SCHEMA`, does sync + async. astroquery adds Gaia-specific niceties. | Hand-rolled HTTP against TAP — needless; PyVO is the reference impl. |
| **ADQL parser** | `queryparser-python3` (aipescience, Apache-2.0) for parse + identifier extraction; **`lark` documented fallback** | Real ANTLR-based ADQL grammar incl. geometry funcs; pre-built wheel needs only the **pure-Python** `antlr4-python3-runtime` (no Java at runtime). We use it to validate syntax and pull table/column refs; we **ignore** its PostgreSQL translation. | `sqlparse` (doesn't validate ADQL or understand geometry); TOPCAT/STILTS parser (JVM, wrong language). See `DATA-SOURCES.md §4`. |
| **Lint engine** | Our own deterministic rules over the parse tree + cached live schema | This is the product. No dependency can do it. | — |
| **LLM (M2+ only)** | Claude (Anthropic API) as the NL→ADQL generator, schema-grounded and linter-gated | Strong code/structured generation; the dossier already assumes Claude Sonnet. Exact model id chosen at M2 against the current model list — do **not** hardcode now. Provider is pluggable behind one `generate_adql(nl, schema)` interface. | Local fine-tune (e.g. STILTS-NLI's Gemma 2B) — heavier, and our grounding/validation does the accuracy work, not raw model size. Revisit only if API cost/latency bites. |
| **Schema cache** | Local JSON per endpoint (`schemas/<key>.json`) | Avoids re-hitting TAP every lint; matches dossier's schema-store idea; trivially diffable. | A DB — overkill at this scale (~thousands of columns). |
| **CLI / packaging** | `typer` (CLI) + `pydantic` (diagnostic/AST models) + `pyproject.toml` (hatchling) | Typer = ergonomic CLI with help/types; pydantic = clean typed diagnostics that serialize to JSON for free (and feed a future web API); hatchling = standard modern build. | `argparse` (more boilerplate); `setup.py` (legacy). |

**Language:** Python 3.11+. **Python over JS** because the entire VO ecosystem (PyVO, astroquery,
astropy) is Python; a JS ADQL parser would orphan us from schema access and the target users' tooling.

---

## 2. Architecture

A one-directional pipeline. The first three stages are the **deterministic core** (v0/M1, no LLM);
the fourth stage is the **LLM layer** (M2+) that feeds *into the front* of the same pipeline and is
re-validated by it.

```
                         ┌───────────────────────── deterministic core (v0/M1, always-correct) ─────────────────────────┐
  ADQL string  ───────▶  [1] PARSER            [2] LIVE SCHEMA           [3] LINTER + EXPLAINER  ───▶  diagnostics (JSON)
                          queryparser/lark         RESOLVER                  rule engine                + plain-English
                          • valid ADQL?            • load TAP_SCHEMA         • unknown table/col          explanation
                          • extract table &          (cached per endpoint)    (+ "did you mean?"        + [M2+] preview
                            column references       • map refs → real          fuzzy match)               table & notebook
                                                      columns/keys/UCDs     • missing JOIN key             cell
                                                                            • NO spatial constraint
                                                                              (full-scan warning)
                                                                            • TOP/limit advisory
        ▲                                                                                                       │
        │                                                                                                       │
        │   grounded ADQL                                                                                       │ on lint-clean:
        └────────────────────────── [4] NL→ADQL GENERATOR (M2+, LLM) ◀── natural-language prompt                ▼  execute via
                                     • prompt carries the LIVE schema slice (real table/col names, UCDs)     pyvo TAPService
                                     • emits ADQL, then is RE-RUN through stages [1]-[3]                      (sync, TOP n)
                                     • on lint/exec error → one structured retry  ─────────────────────────▶  preview rows
```

**The contract that keeps it honest:** the generator (4) is never trusted. Whatever it emits goes
back through Parser → Resolver → Linter (1-3) exactly as if a human typed it. The LLM *proposes*;
the live schema *disposes*. Same gate for humans and model.

---

## 3. Repo layout

```
adql-copilot/
├── SPEC.md                  # dossier + "what we build first"
├── DATA-SOURCES.md          # endpoints, TAP_SCHEMA, ADQL geometry, parsers
├── BUILD-PLAN.md            # this file
├── README.md
├── pyproject.toml
├── .gitignore
├── src/
│   └── adql_copilot/
│       ├── __init__.py
│       ├── cli.py           # typer entrypoint: `adql-copilot lint <query>`
│       ├── parser.py        # STUB: wrap queryparser; return parsed refs (table/column)
│       ├── schema.py        # STUB: TAPService schema fetch + local JSON cache
│       ├── linter.py        # STUB: deterministic rules over (parse, schema) -> diagnostics
│       ├── explainer.py     # STUB: parse -> plain-English summary
│       ├── models.py        # pydantic: Diagnostic, ParsedQuery, ColumnMeta, ...
│       ├── endpoints.py     # the 4 verified TAP base URLs as named constants
│       └── generate.py      # STUB (M2): generate_adql(nl, schema) behind one interface
├── schemas/                 # cached TAP_SCHEMA JSON per endpoint (gitignored, regenerable)
└── tests/
    └── test_linter_smoke.py # STUB: asserts the mock lint returns expected diagnostic codes
```

---

## 4. Milestones

### M0 — Skeleton (this delivery)
- Package installs (`pip install -e .`); `adql-copilot --help` works.
- `adql-copilot lint` runs on a **hard-coded ADQL string** and prints **mock** diagnostics +
  a stub explanation. No network. Proves the wiring/UX end-to-end.
- All modules present as typed stubs; one smoke test passes.

### M1 — Deterministic linter against ONE live endpoint *(the real first product; ships standalone)*
- Wire `parser.py` to `queryparser` (fallback `lark` if needed): real syntax validation + identifier extraction.
- `schema.py` fetches `TAP_SCHEMA.{tables,columns,keys,key_columns}` for **one** endpoint
  (default candidate: **Gaia** — cleanest schema; see Open Questions) and caches to `schemas/gaia.json`.
- `linter.py` ships these always-correct rules:
  1. **Unknown table / unknown column** vs. live schema, with fuzzy "did you mean?" from real names.
  2. **Missing JOIN key** — JOIN present but `ON` doesn't use a declared FK (`TAP_SCHEMA.keys`).
  3. **No spatial constraint** on a table with RA/Dec (UCD `pos.eq.ra`/`pos.eq.dec`) → full-scan warning.
  4. **No `TOP`/row limit** advisory (esp. Gaia's 2000-row sync cap).
- `explainer.py`: deterministic plain-English summary (tables, columns+units, filters, spatial region).
- `adql-copilot lint --endpoint gaia "<query>"` produces real diagnostics. Tests on a fixture set of
  good/bad ADQL strings. **This is shippable and useful with zero LLM.**

### M2 — NL→ADQL with schema grounding + execution
- `generate.py`: `generate_adql(nl, schema_slice)` via Claude (model id chosen then, not hardcoded);
  prompt embeds the **live** schema slice (real table/col names + UCDs) + ADQL geometry signatures +
  a few worked examples for the endpoint.
- New command `adql-copilot ask --endpoint gaia "stars within 50pc, ruwe<1.4"` →
  generate → **run through M1 linter** → on clean, **execute** via `pyvo` (sync, `TOP n` preview) →
  print ADQL + preview table + a paste-ready notebook cell.
- **Validation loop:** on lint error or TAP execution error, feed the structured error back for **one**
  retry; if still failing, return the ADQL + diagnostics rather than a wrong silent result.
- Small NL→expected-ADQL eval set for regression (grow toward the dossier's 100-query set).

### M3 — Multi-endpoint + UI
- Generalize schema/linter across **all four** endpoints (Gaia, VizieR, MAST CAOM, DESI/NOIRLab);
  per-archive schema normalization (the dossier's "strongest risk" — mechanical, do it explicitly).
- UI wrappers over the same library: a **Gradio** demo and/or **FastAPI** + minimal web front-end;
  optionally a notebook helper. (Rubin DP1 / RSP-auth endpoints considered here, account permitting.)

---

## 5. First-task checklist (concrete, M0→start of M1)

1. [x] Create repo + the three docs (SPEC / DATA-SOURCES / BUILD-PLAN).
2. [x] `pyproject.toml` with real deps (pyvo, astroquery, queryparser-python3, typer, pydantic).
3. [x] Package skeleton + typed stubs + `endpoints.py` with the 4 verified URLs.
4. [x] Runnable stub CLI: `adql-copilot lint` on a hard-coded query → mock diagnostics + stub explain.
5. [x] One passing smoke test; `.gitignore`; README quickstart.
6. [x] `pip install -e .`; confirm `adql-copilot lint` runs offline (the M0 acceptance gate).
7. [x] **M1 kickoff:** point `schema.py` at Gaia, pull `TAP_SCHEMA`, cache JSON; table/column count proves live access (248 tables / 6614 columns / 5 keys fetched live; cached to `schemas/gaia.json`; offline fixture fallback bundled at `fixtures/gaia.json`).
8. [x] Replaced mock parse with `queryparser` (lark fallback wired); replaced mock rules with the four real M1 rules; real good/bad fixture test set (`tests/test_m1_linter.py`).

---

## 6. How we keep generation correct

**Layered defense — the LLM is the least-trusted component:**
1. **Grounding:** the generator only ever sees the **live** schema slice (real table/column names +
   UCDs) for the chosen endpoint — it cannot reference a column the schema doesn't list because the
   real names are in front of it (kills the dossier's "`phot_g_mean_mag` vs `Gmag`" hallucination).
2. **Deterministic gate:** every generated query is re-run through the M1 Parser → Resolver → Linter.
   Unknown identifiers / missing JOIN keys / missing spatial constraints are caught *before* execution.
3. **Live execution check:** lint-clean queries are run against the real TAP endpoint (sync, `TOP n`);
   a TAP error is ground truth.
4. **Single structured retry:** lint/exec errors are fed back once; persistent failure returns the
   ADQL **plus** diagnostics — never a confidently-wrong silent answer.
5. **Regression eval:** an NL→expected-ADQL set guards against prompt/model drift over time.

The deterministic core (1-3 of the architecture) is correct *by construction* — it asserts nothing
the live schema doesn't confirm — and it exists independently of, and as the harness for, the LLM.

---

## 7. Kill criteria (from the dossier)

- **Kill if** a Rubin-official or IVOA-endorsed NL-query tool launches before ~Week 6, **or** the
  Gaia/MAST TAP endpoints add rate-limiting strict enough to block the demo loop.
- **Watch:** Rubin RSP roadmap (`rsp.lsst.io/roadmap.html`) quarterly for a NL-query widget.
- **Note the asymmetry:** even if the *copilot* (LLM layer) is killed, the **deterministic
  linter/explainer (v0/M1) retains standalone value** as an Astropy-affiliated tool — it does not
  depend on the LLM thesis. That is the whole point of building it first.

---

## 8. OPEN QUESTIONS FOR MATTHEW

1. **Which endpoint do we target first for M1?** Recommendation: **Gaia (ESA)** — single well-known
   schema, clean `gaiadr3.gaia_source` table, classic cone-search use case, excellent for exercising
   every lint rule. Alternative: **DESI via NOIRLab** if the DESI/Rubin science angle is the priority.
   (**VizieR** is the hardest first target — tens of thousands of slash-coded catalog tables — better
   second.) **Confirm Gaia-first, or name the endpoint you'd rather lead with.**
2. **UI form factor for the eventual copilot: CLI, notebook helper, or web app (Gradio/FastAPI)?**
   The plan builds a library + CLI now and defers UI to M3 so the choice stays open — but your
   preferred end-user surface (the dossier leans Gradio/HF Spaces) shapes M3 priorities. **Which one
   is the demo you actually want to show?**
3. *(Secondary)* For M2, OK to use the **Claude API** as the generator (small per-query cost), or do
   you want a **local/offline** model path from the start? Default plan: Claude API, pluggable.
4. *(Secondary)* Scope of "explain": one-paragraph plain-English summary (planned), or also
   per-clause annotations and unit/UCD call-outs in the first cut?
