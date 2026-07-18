# SPEC — TAP/ADQL Query Copilot

> This file reproduces the verified research dossier (the source of truth), then states a
> tightened "What we build first" decision. Everything below the dossier is the build
> directive; the dossier itself is unedited.

---

## Verified research dossier (reproduced)

### TAP/ADQL Query Copilot [sources: arxiv:2602.22357, dp1.lsst.io, github.com/ivoa-std/ADQL, dp0-2.lsst.io, IVOA Interop 2025]

**Pitch (refined):** Build a web-accessible LLM copilot that accepts plain English ("give me all Gaia DR3 stars within 50 pc with parallax_over_error > 10 and RUWE < 1.4") and emits validated ADQL, executes it against MAST, Gaia DR3, and VizieR TAP endpoints via PyVO, and returns a preview table plus a ready-to-paste notebook cell. Target audience: astronomers writing their first Rubin DR1 query and undergrads doing capstone projects — exactly the people the Rubin Science Platform's own documentation currently deflects to the Community Forum. Urgency is real: Rubin DR1 dropped in 2025 and the official tutorials stop at static ADQL recipe pages.

**Landscape (verified):** Adversarial search found no maintained ADQL-specific LLM tool. The closest hits are:
- **STILTS-NLI** (arXiv 2602.22357, Feb 2026, Rhys Shaw): NL → STILTS table-processing commands via fine-tuned Gemma 2B. Public on GitHub (`RhysAlfShaw/stilts-nli`). This is *table manipulation*, not TAP query generation — no ADQL output, no live endpoint execution, no schema-aware validation. Adjacent but does not cover the gap.
- **Generic Text-to-SQL repos** (Awesome-Text2SQL, Tinybird LLM benchmark): none target ADQL's spherical-geometry extensions (`CONTAINS`, `POINT`, `CIRCLE`, `DISTANCE`) or the TAP schema discovery protocol.
- **IVOA ADQL spec repo** (`ivoa-std/ADQL` on GitHub): standards document only, no implementation.
- **Rubin DP0/DP1 ADQL Recipes pages** (`dp0-2.lsst.io`, `dp1.lsst.io`): static HTML cookbooks; the DP1 page explicitly says "get support in the Community Forum." Zero AI tooling present.
- **IVOA June 2025 Interop** (Indico/INAF): no session on LLM/NL interfaces found in the program search.
- **Pathfinder** (arXiv 2408.01556): NL over ADS literature, not over catalog TAP endpoints.

The gap is confirmed real. No maintained, publicly accessible NL-to-ADQL service exists as of June 2026.

**Agent-MVP (1 week):** A fleet of three agents running in parallel can deliver a working proof of concept:
1. *Schema Agent* — hits TAP `/tables` endpoints for MAST, Gaia DR3, and VizieR; serializes column names, UCDs, and units to a JSON schema store (~3,000 columns total). Output: `schemas/mast.json`, `gaia.json`, `vizier.json`.
2. *Query Agent* — Claude Sonnet with the schema JSON as context; system prompt embeds ADQL grammar BNF (from the IVOA spec), spherical-geometry function signatures, and five worked examples per archive; accepts NL input, emits ADQL string. Output: validated ADQL query string.
3. *Validation + Exec Agent* — Submits ADQL to the real TAP endpoint via `pyvo.dal.TAPService`; catches `VOTABLE` errors, parses error messages, feeds them back to the Query Agent for one retry loop; returns a FITS/CSV preview of up to 100 rows plus a Jupyter cell template. Output: `result_preview.csv` + `query_notebook.ipynb` cell block.

The whole loop runs in a single Python script; no GPU or cloud infra required. A Gradio front end wraps it for demo day.

**90-day arc:**
- **Weeks 1–2:** Schema crawler for three archives; prompt engineering for ADQL grammar; local Gradio demo working end-to-end for ten benchmark queries (Gaia parallax cut, MAST HST footprint, VizieR catalog join).
- **Weeks 3–6:** Expand to five TAP endpoints (add DESI DR1, Rubin DP1); build a 100-query eval set (NL → expected ADQL) for regression testing; add retry loop and user-facing error explanations; host on Hugging Face Spaces.
- **Weeks 7–10:** Publish a preprint to arXiv (cs.IR or astro-ph.IM); post to Rubin Community Forum and IVOA-discuss mailing list; file a ticket with the Rubin RSP team proposing integration as an optional Notebook Aspect widget.
- **Day 90:** Hand the repo to the Rubin Science Platform team or IVOA DAL working group; target a citation in the Rubin DR1 user-guide. If neither adopts it within three months, publish as a standalone Astropy-affiliated package.

**Risks / kill criteria:**
- *Strongest risk:* ADQL schema diversity. Each TAP endpoint uses different column-naming conventions and UCD vocabularies; a system prompt that works for Gaia silently fails for VizieR CDS tables. Mitigation requires per-archive schema normalization, which is tedious but mechanical.
- *LLM hallucination of column names:* Claude confidently emits `phot_g_mean_mag` when the archive uses `Gmag` — producing a valid-looking but failing query. The retry loop with live execution errors is the primary mitigation; a column-name fuzzy-matcher is the secondary.
- *Superseded by Rubin official tooling:* The RSP roadmap could add a NL query widget. Monitor `rsp.lsst.io/roadmap.html` quarterly.
- *Kill if:* A Rubin-official or IVOA-endorsed NL query tool launches before Week 6, OR the Gaia/MAST TAP endpoints add rate-limiting strict enough to block a demo loop.

**Tag:** solo-side-project  ·  **Underexplored:** 4/5  ·  **Agent-buildable:** 5/5  ·  **Excitement:** 4/5

**Sources:**
- https://arxiv.org/pdf/2602.22357 (STILTS-NLI paper, Feb 2026)
- https://github.com/RhysAlfShaw/stilts-nli (STILTS-NLI public repo — closest prior art; NL→STILTS not NL→ADQL)
- https://dp1.lsst.io/products/adql_queries.html (Rubin DP1 ADQL guide — no LLM tooling)
- https://dp0-2.lsst.io/data-access-analysis-tools/adql-recipes.html (Rubin DP0.2 ADQL recipes — static only)
- https://github.com/ivoa-std/ADQL (IVOA ADQL spec repo — standards document only)
- https://indico.ict.inaf.it/event/3121/ (IVOA June 2025 Interop — no NL/LLM session found)
- https://arxiv.org/abs/2408.01556 (Pathfinder — NL over ADS literature, not TAP)

---

## What we build first (tightened directive — v0)

**We do NOT start with the LLM.** The dossier's headline is a NL→ADQL copilot, but its own strongest risk
(column-name hallucination, per-archive schema drift) is precisely the part an LLM makes *worse*. So v0 is the
**lower-risk adjacent foundation: a deterministic, schema-aware ADQL linter/explainer with no LLM in the core loop.**
It takes an ADQL string, parses it, resolves every table and column reference against the *live* TAP `TAP_SCHEMA`
metadata for the chosen endpoint, and emits structured diagnostics — unknown table/column (with fuzzy "did you
mean?" suggestions from the real schema), missing JOIN keys, and the classic footgun of a cone/region query with
**no spatial constraint** (a full-catalog scan) — plus a plain-English explanation of what the query does and which
columns/units it touches. This is always-correct because it asserts nothing the live schema doesn't confirm; it is
useful on day one to anyone hand-writing ADQL; and it is the validation harness the copilot will need anyway.
**Only once that foundation is solid do we layer NL→ADQL generation on top** (M2), and that generator is *grounded
in the same live schema* and *gated by the same linter* — the LLM proposes, the deterministic resolver disposes.
We differentiate sharply from **STILTS-NLI** (arXiv 2602.22357): it does NL→STILTS local table-ops; we do
schema-validated ADQL over live VO TAP endpoints. Different layer of the stack, no overlap.
