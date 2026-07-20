# astro-mcp

**One-liner:** An MCP (Model Context Protocol) server that turns astronomy archives — Gaia/VizieR/MAST via TAP, plus SIMBAD/NED name resolution and (opt-in) ADS literature — into conversational tools any Claude/LLM client can call, with every generated ADQL query first validated by the sibling `adql-copilot` deterministic schema-linter before it is allowed to run.

**Scores (U/B/E):** 3 / 5 / 4 — *Underexplored 3*: astronomy MCP servers already exist (see prior art), so this is a **reframe-and-harden play**, not green field; the *validated, distributed* variant is the open slot. *Agent-buildable 5*: pure software, account-free backends, reuses an existing linter, FastMCP makes tool-wrapping near-trivial. *Excitement 4*: distribution leverage — reaches every MCP-client user and converts `adql-copilot`'s small CLI audience into a broad surface; tempered by crowded prior art.

**Status:** proposed

## The wedge

**What already exists (adversarial prior-art check — this space is NOT empty):**

- **`astro_mcp` (SandyYuan)** — the single biggest overlap. A working astronomy MCP server exposing `astroquery_query` (a universal wrapper over "40+ astroquery services" incl. SIMBAD/VizieR/SDSS/Gaia/MAST/IRSA/ESASky), `search_objects` + `get_spectrum_by_id` (DESI via SPARCL/Data Lab), and service-discovery/file tools. It **generates queries from natural language**. Crucially, its README/docs show **no ADQL validation or linting layer** — queries appear to pass straight through to the service ("SQL queries with spatial indexing (Q3C)" with no documented safeguards). It is early-stage: ~5 stars, no tagged releases, **not on PyPI or the MCP registry**, install = manual git clone + conda. (github.com/SandyYuan/astro_mcp; listed on mcpservers.org, glama.ai, lobehub.)
- **`nasa-ads-mcp` (prtc)** and **`ivan-katkov/nasa-ads-mcp`** — ADS literature MCP servers already exist: ~10 tools (paper search, citation metrics/h-index, BibTeX export, library management). Require a NASA ADS API token; author calls it "far from an extensively tested solution" (~9 commits). No object name-resolution. → **ADS literature is already adequately covered; do not lead with it.**
- **arXiv 2607.03946 (Jul 2026)** — "A Model Context Protocol Server for Astrophysical RAG": FAISS semantic search over five *pre-assembled* corpora. Explicitly a *complementary* angle — its own abstract states an MCP server "does not replicate VO infrastructure but instead provides a … LLM-native interface … for … corpus exploration." Different problem (RAG over static corpora, not live schema-validated TAP queries).
- **`ProgramComputer/NASA-MCP-server`, jezweb NASA MCP** — wrap NASA *public web APIs* (APOD/DONKI/etc.), not archives/TAP. Not competitive.
- **No official IVOA / Astropy / Rubin MCP found.** pyvo is the Astropy-affiliated TAP client (our backbone) but ships no MCP wrapper; no IVOA-endorsed NL-query MCP surfaced. That is a genuine gap — and a kill-check to keep watching (see Risks).

**Where the defensible gap is:** every existing astronomy MCP has the LLM *write a query and hope*. None puts a **deterministic, schema-grounded validation gate between the model and the archive.** That gate is exactly what `adql-copilot` already is: it parses ADQL, resolves every table/column against the **live `TAP_SCHEMA`**, and flags unknown columns (with "did you mean?" from real names), missing JOIN keys, un-constrained full-catalog scans, and missing row limits — asserting nothing the live schema doesn't confirm. So the wedge is **"the astronomy MCP whose queries are checked before they run"** plus **"the one actually packaged for distribution"** (PyPI + official registry + claude.ai connector) versus the clone-and-run research code that exists today. This also reframes `adql-copilot` — a CLI with a naturally small audience — as the trusted query engine inside a surface that reaches every MCP-client user.

**Why an agent fleet fills it cheaply:** the hard parts are already built or free — pyvo/astroquery are mature and account-free, `adql-copilot`'s linter is at green M1, and FastMCP reduces "expose a Python function as an MCP tool" to a decorator. The work is connective tissue (wrap functions, add the lint gate, write acceptance tests, publish), which is precisely what an agent does well.

**Why now (2026 catalysts):** (1) MCP distribution matured in 2026 — a metadata-only **official registry** (`server.json` + `mcp-publisher` CLI), `mcp-name:` PyPI markers, and claude.ai **custom connectors** mean a Python package can reach every Claude client. (2) **Gaia DR4 releases 2 December 2026** — a hard-dated schema event: the day Gaia's TAP `TAP_SCHEMA` flips to DR4, a schema-linted MCP exposes the new catalog *correctly* (real column names, DR4 non-single-star / exoplanet tables) while un-validated tools hallucinate against a schema they've never seen.

## Target user & the "who cites this" test

- **Primary user:** a working astronomer / grad student / instrument scientist who already lives in Claude (Desktop, Code, or claude.ai) and wants to ask "pull Gaia sources near M13 with ruwe < 1.4" or "what's the redshift of NGC 4993" without hand-writing ADQL or remembering `phot_g_mean_mag` vs `Gmag`. Secondary: educators/newcomers who can't yet write ADQL at all. **The moment they reach for it:** mid-analysis, in chat, when they need real archive rows *inside* the reasoning loop rather than context-switching to TOPCAT / a notebook.
- **Also an agent-infrastructure user:** anyone building an agentic astronomy pipeline who needs a *trustworthy* archive tool — one that won't silently execute a wrong query.
- **The "who cites this" test:** the citable object is not the chat convenience — it is **the validation guarantee**. A short **RNAAS note** ("a schema-validated MCP interface to VO archives") + a **Zenodo DOI** gives a referenceable artifact; the reproducible claim "LLM-proposed queries are gated by a deterministic live-schema linter before execution" is what a methods section cites when justifying agent-driven archive access. Pursuing an **astroquery/pyvo affiliation** mention makes it citable as tooling, not just consumable.

## Data sources & access

All read/query backends below are **account-free** except ADS (free token). The linter and TAP tools inherit `adql-copilot`'s already-verified endpoints.

| Capability | Backend | Endpoint / interface | Auth | Limits / notes |
|---|---|---|---|---|
| **TAP/ADQL execution** | `pyvo.dal.TAPService(url)` | Gaia `https://gea.esac.esa.int/tap-server/tap`; VizieR `https://tapvizier.cds.unistra.fr/TAPVizieR/tap`; MAST CAOM `https://mast.stsci.edu/vo-tap/api/v0.1/caom`; DESI (NOIRLab) `https://datalab.noirlab.edu/tap` | **None** | Gaia sync capped **2000 rows** (use async/`TOP`); anonymous async kept 3 days. (Verified in `adql-copilot/DATA-SOURCES.md`.) |
| **ADQL validation** | `adql-copilot` linter (library import) | live `TAP_SCHEMA` per endpoint, cached → live → offline fixture | **None** | The trust layer. See "the seam" below. |
| **Name resolution** | `astroquery.simbad` (`query_object`; `query_tap` for ADQL over SIMBAD TAP), `astroquery.ned` | SIMBAD (CDS) / NED (IPAC) | **None** | SIMBAD TAP via astroquery since 2024; NED for extragalactic/redshift. |
| **Cross-match / cone** | pyvo cone (`SCSService`) or ADQL `CONTAINS(POINT,CIRCLE)`; astroquery XMatch (CDS) | per-archive | **None** | Cone/crossmatch expressible as linted ADQL against a positional table. |
| **Literature (opt-in)** | `astroquery.nasa_ads` / ADS dev API | `https://api.adsabs.harvard.edu` | **Free token** (`ADS_DEV_KEY` / `~/.ads/dev_key`) | **5000 queries/day**, per-endpoint, advertised in HTTP headers. |

**Account-free path (called out):** every core tool — `tap_query`, `resolve_name`, `cone_search`, `crossmatch` — works with **zero credentials**. The ADS literature tool is **opt-in**: it self-disables cleanly when no `ADS_DEV_KEY` is present, so the server is fully useful anonymously and the token only unlocks the literature extras. This keeps a hosted claude.ai-connector deployment secret-free.

## Architecture sketch

Minimal-runnable-first: a FastMCP server whose tools are thin wrappers over pyvo/astroquery, with the `adql-copilot` linter mounted as a mandatory gate on anything that produces ADQL.

```
  MCP client (Claude Desktop / Claude Code / claude.ai)
        │  JSON-RPC (stdio local  |  streamable-HTTP remote)
        ▼
  ┌───────────────────────── astro-mcp (FastMCP server) ─────────────────────────┐
  │  @tool resolve_name(name)            → astroquery.simbad / ned  (account-free) │
  │  @tool tap_query(adql, endpoint)     ┐                                         │
  │  @tool cone_search(ra,dec,radius,…)  ├─▶ [ LINT GATE ] adql_copilot.lint(...)  │
  │  @tool crossmatch(...)               ┘        │  LintReport.ok ?               │
  │  @tool ads_search(q)  [opt-in token] │        │  ├─ has ERROR → RETURN diags   │
  │                                      │        │  │   (+structured fixes) — DO  │
  │                                      │        │  │   NOT execute               │
  │                                      │        │  └─ clean → pyvo TAPService     │
  │                                      │        │       .search(sync, TOP n)      │
  └──────────────────────────────────────────────┼─────────────────────────────────┘
                                                  ▼
                              rows (VOTable→astropy Table→JSON) + the LintReport
```

**The contract (inherited from `adql-copilot`):** the model *proposes* an ADQL string; the live schema *disposes*. Whatever the LLM emits is re-run through Parser → live-`TAP_SCHEMA` Resolver → Linter *before* any execution — the same gate for a hand-typed query and a model-generated one. A query with an ERROR-severity diagnostic (unknown table/column) is **never executed**; the tool returns the diagnostics (and, once available, structured fixes) so the model can self-correct and re-submit.

**Stack:** Python 3.11+, **FastMCP** (de-facto standard; `@tool` decorator auto-generates the tool schema; supports **stdio** for local Claude Desktop/Code and **streamable-HTTP** for a remote claude.ai connector). Deps: `mcp`/`fastmcp`, `pyvo`, `astroquery`, and **`adql-copilot`** as a library dependency. Package name `astro-mcp`, registry namespace `io.github.<user>/astro-mcp`.

**The seam to `adql-copilot` (concrete interface ask):** today the linter is reachable as `adql_copilot.linter.lint(parsed, schema, endpoint_key) -> list[Diagnostic]` and end-to-end as the private `adql_copilot.cli._run_pipeline(adql, endpoint_key) -> (LintReport, Schema)`; the JSON form is emitted only by the CLI (`lint --json` → `LintReport.model_dump_json()`). `LintReport` already carries everything astro-mcp needs — `.ok` (True iff no ERROR diagnostics), `.diagnostics[]` (each a stable `code` + `severity` + `message` + `suggestion`), and `.explanation`. **What the linter needs to expose for a clean seam:** (1) a **stable public entrypoint** — e.g. `adql_copilot.lint_report(adql, endpoint="gaia") -> LintReport` — so astro-mcp imports a supported API rather than a `_private` function; and (2) the **structured fix payloads** already on `adql-copilot`'s roadmap — machine-actionable repairs (e.g. `{code, span, replacement}`) beyond the current free-text `suggestion` string — so the MCP tool can hand the model a precise diff to retry, not prose. Both are small additions to the sibling repo; astro-mcp's design assumes them and degrades gracefully to `suggestion` text until they land.

## Cost model (zero marginal cost)

Designed to cost the maintainer **$0 to operate at any scale** — the property that makes it safe to publish a free tool that gets popular.

- **Inference is never on the maintainer's dime.** In an MCP server the *model* runs in the user's client (their Claude Desktop / Code / claude.ai subscription, or their own key). astro-mcp only exposes tools — run this TAP query, resolve this name, lint this ADQL; the user brings the Claude. This is the crux: it turns `adql-copilot`'s "NL→ADQL costs money" problem into someone-else's-already-paid subscription.
- **Backends are account-free and free.** pyvo/astroquery hit anonymous public TAP/SIMBAD/NED — no metered API, no per-call charge. ADS is the only token and it is opt-in + free-tier.
- **Distribution is zero-infra.** Shipped as `pip` / `uvx astro-mcp`, every user runs their **own local copy** (stdio) against their own client — the maintainer hosts nothing. Inference, compute, and bandwidth are all the user's.
- **The one optional cost is bounded.** The M3 claude.ai custom connector (a remote streamable-HTTP instance) is the only piece that needs hosting, and it exposes **account-free tools only** (no secrets, no server-side LLM), so it runs on a free/hobby tier — the model still runs in the *caller's* claude.ai. If even that is unwanted, the local `uvx` path delivers the whole product for $0.

**Design rule:** keep the server a thin, stateless tool layer over free archives. Never add a maintainer-side LLM call or heavy per-request compute — those reintroduce cost-that-scales-with-users. If a feature seems to need server-side inference, push it to the client (which already has a model) or precompute it to static.

## Milestones

- **M0 — Kill checks (cheapest disproofs first).**
  - **Prior-art go/no-go:** read `astro_mcp` and `nasa-ads-mcp` source; actually run `astro_mcp` in Claude Desktop. Confirm the load-bearing claim — that it has **no query-validation layer** and isn't distributed (no PyPI/registry). *Kill/redirect if* it already validates queries against live schema **and** is well-distributed; the wedge would collapse to nothing.
  - **Official-effort check:** scan GitHub orgs `ivoa`, `astropy`, `lsst`, and the astropy/IVOA apps channels for an in-progress official validated-archive MCP. *Kill if* one is shipping.
  - **Data-access + seam smoke test:** from a one-file FastMCP stub, (a) `pyvo.TAPService(Gaia).search("SELECT TOP 5 …")` and `astroquery.simbad` name-resolve — both account-free, no token; (b) `import adql_copilot; lint(...)` returns a `LintReport` for a hand-written query in-process.
  - **Acceptance:** a single `resolve_name` tool callable from Claude Desktop returns a real SIMBAD answer, **and** a written half-page go/no-go on the `astro_mcp` overlap.

- **M1 — Thin end-to-end slice (the minimal runnable product; ONE archive, TWO tools).**
  - `resolve_name(name)` → SIMBAD (NED fallback).
  - `tap_query(adql, endpoint="gaia")` → **lint via `adql-copilot` first**; on ERROR diagnostics, return `{ok:false, diagnostics, explanation}` and **do not execute**; on clean, execute via pyvo sync (`TOP`-capped) and return `{rows, lint_report}`.
  - Packaged; runs as a **stdio** server; addable to Claude Code / Claude Desktop.
  - **Acceptance:** in Claude Desktop, "5 Gaia sources near M13 with ruwe < 1.4" → model calls `resolve_name(M13)` → composes ADQL → `tap_query` lints clean → returns real rows; **and** a query with a wrong column (`Gmag`) is caught (`UNKNOWN_COLUMN`, "did you mean 'phot_g_mean_mag'?") and **not run**. Automated: a pytest drives the tools in-process over a good/bad fixture set (good executes, bad is blocked).

- **M2 — Expansion (more tools, more archives, the repair loop).**
  - Add `cone_search(ra,dec,radius)`, `crossmatch`, `resolve_name` NED path, and **opt-in** `ads_search` (token-gated, self-disabling).
  - Add endpoints VizieR / MAST / DESI (rides `adql-copilot`'s own multi-endpoint milestone; where the linter can't yet schema-validate a non-Gaia endpoint, the tool executes but **flags results `schema_validated: false`** — honest, not silent).
  - **Lint-repair retry loop:** on ERROR diagnostics, return structured fixes; bounded (≤1–2) model self-correction re-submissions before returning ADQL + diagnostics rather than a wrong answer.
  - **Acceptance:** a cross-archive question ("cross-match these Gaia sources against VizieR X") answered end-to-end; ADS tool cleanly absent when no token; broken query auto-repaired within the retry budget on a small eval set.

- **M3 — Distribution & legitimacy.**
  - Publish to **PyPI** with the `mcp-name:` README marker; submit `server.json` to the **official MCP registry** via `mcp-publisher` (github-oidc); list on PulseMCP / Glama / mcpservers.org / lobehub (where the incumbents already sit).
  - Stand up a **hosted streamable-HTTP instance** as a **claude.ai custom connector** (core account-free tools only — no per-user secrets).
  - Write the **RNAAS note** + mint a **Zenodo DOI**; pursue an astroquery/pyvo-affiliation mention.
  - **Acceptance:** `uvx astro-mcp` works from a clean machine; the server resolves in the official registry; the connector is addable on claude.ai and answers a live query.

## First week / first tasks

1. **Kill check first.** Read `astro_mcp` + `nasa-ads-mcp` source; run `astro_mcp` in Claude Desktop; write the half-page go/no-go on the validation/distribution overlap. (If the wedge is dead, stop here — cheapest possible disproof.)
2. **FastMCP "hello archive."** One `resolve_name` tool over `astroquery.simbad`; run it from Claude Code/Desktop; confirm account-free.
3. **Prove the seam.** Add `adql-copilot` as a dependency; show `lint(adql, "gaia")` returns a `LintReport` in-process; file the two-line interface ask against the `adql-copilot` repo (public `lint_report()` entrypoint + structured fix payloads).
4. **Build `tap_query`.** lint → (block on ERROR | execute pyvo sync `TOP n`) → return `{rows, lint_report}`.
5. **Acceptance test + demo transcript.** pytest: good query runs, bad query blocked with a "did you mean" suggestion; capture the M13 chat transcript.
6. **Claim the name.** Decide package name and registry namespace (`io.github.<user>/astro-mcp`); reserve on PyPI.

## Risks & kill criteria

- **Prior art hardens (highest risk).** If `astro_mcp` (or a newcomer) adds a real validation layer *and* proper distribution before ~M2, the wedge narrows to "ours is validated + packaged." **Kill/redirect** if an **astropy- or IVOA-official** schema-validated archive MCP ships. Mitigation: move fast on the validation gate + registry publish; that pairing is the defensible bit.
- **"Validation feels unnecessary" as models improve.** If frontier models get reliable enough at raw ADQL, the gate reads as overhead. But archive schemas are precisely where models hallucinate (the `Gmag`/`phot_g_mean_mag` failure `adql-copilot` exists for), and a full-catalog-scan footgun is a real cost — so the guarantee stays valuable. Watch, don't assume.
- **`adql-copilot` coupling.** It is single-endpoint (Gaia) at green M1; multi-endpoint is its *own* unfinished milestone. Non-Gaia TAP tools therefore **cannot be lint-gated yet** → M1 stays Gaia-only; other archives ship as clearly-flagged un-validated passthrough until the linter generalizes. Do not overclaim "validated" for endpoints the linter can't yet resolve.
- **MCP ecosystem churn.** Transport/spec/registry drift through 2026; low stakes (registry is metadata-only) but needs tracking. FastMCP absorbs most transport change.
- **ADS token friction.** Mitigated structurally — ADS is opt-in; the core is account-free.
- **Kill if:** a well-distributed schema-validated astronomy MCP ships first; **or** anonymous pyvo/TAP access to Gaia/SIMBAD gets locked behind auth; **or** the `adql-copilot` linter can't be consumed cleanly as a library.

## Distribution & legitimacy

- **PyPI** — `astro-mcp`, `uvx`-runnable, with the `mcp-name:` marker in the README (registry requirement).
- **Official MCP registry** — `server.json` published via `mcp-publisher` (github-oidc, no review queue); the canonical discovery surface.
- **Community directories** — PulseMCP, Glama, mcpservers.org, lobehub: meet users where the incumbent astronomy MCPs are already listed.
- **claude.ai custom connector** — a hosted streamable-HTTP deployment (account-free tools only) addable via Customize → Connectors.
- **RNAAS research note** (1-page, citable) + **Zenodo DOI** for the tagged release — the referenceable artifacts; the "schema-validated LLM access to VO archives" framing is also a natural **JOSS** candidate later.
- **astroquery / pyvo affiliation** mention — legitimacy as tooling, since the server is a thin, honest layer over exactly those libraries.

## Rough size

**Effort to M1: small — roughly 1–1.5 agent-weeks.** FastMCP removes the server boilerplate; the backends (pyvo, astroquery) and the validation engine (`adql-copilot`) already exist and are account-free; M1 is essentially "wrap two functions as MCP tools, mount the lint gate, write the acceptance test, run it in Claude Desktop." M2–M3 add tools/endpoints and the publish pipeline — mechanical.

**Single biggest uncertainty:** **whether the wedge survives contact with `astro_mcp`** — i.e., is "validated + distributed" a big enough differentiator, or has the incumbent's 40-service breadth already claimed the mindshare? That is exactly what the M0 kill check exists to answer before any real build. Second-order: the small `adql-copilot` interface work (public `lint_report()` + structured fix payloads) that the clean lint-repair loop depends on lives in a sibling repo and must be sequenced.
