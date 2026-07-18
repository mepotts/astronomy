# Sprint-plan brief — astronomy "run 2" build candidates

Shared context + template for the new-idea sprint plans. Each plan lives in `IDEAS/<slug>.md`
and follows the template at the bottom. These ideas are deliberately in the **white space** the
original idea-research run (2026-06-14) never swept: high-energy astrophysics, planetary/meteor,
satellites/SSA, historical archives, and the AI-application patterns of literature-mining,
agentic analysis, MCP tooling, and accessibility.

## Portfolio thesis (inherit this framing)

Astronomy data is now open and abundant, but the **usability/translation layer** between raw
archives and the humans who want to use them is systematically missing. The existing portfolio
(seti-ellipsoid-broker, pta-explainer, adql-copilot) attacks that layer. New ideas should too,
and should optimize for three things:

1. **Account-free / low-friction** where possible — anonymous TAP, public broker APIs (Fink,
   ALeRCE, ANTARES), open archives. Avoid anything gated behind institutional data rights as a
   hard dependency (lesson from the Lasair-LSST data-rights wall).
2. **Things professionals cite**, not just consume — a versioned dataset, a validation gate, a
   reproducible audit, a research note. The pro-am bridges that convert effort into citations.
3. **Agent/desk-buildable** — data + software only, no hardware or telescope time. An agent fleet
   can build the connective tissue cheaply.

## Key 2026 data-access facts (verify specifics before relying on them)

- **Gaia DR4** releases **2 December 2026** — full astrometry re-derivation for ~2B sources, plus
  non-single-star solutions, an exoplanet list, epoch/transit data. This is a hard, dated catalyst.
- **Rubin/LSST** is in steady-state survey ops as of July 2026: ~7M alerts/night to seven
  full-stream brokers (ALeRCE, AMPEL, ANTARES, Babamul, Fink, Lasair, Pitt-Google). Fink, ALeRCE,
  ANTARES expose **public REST APIs** (largely tokenless) — the account-free alert sources.
- **eROSITA** eRASS1 (~900k X-ray sources) is public (DR1). X-ray/gamma-ray got zero coverage in run 1.
- **Global Meteor Network** — hundreds of open RMS cameras, public trajectory/orbit data, growing.
- **DASCH** — Harvard's 100+ yr photographic plate archive, fully scanned as of 2024, public API.
- **MCP** (Model Context Protocol) tooling is proliferating in 2026; an MCP server is a distribution
  surface that reaches every Claude/LLM-client user.
- Legitimacy currencies in astronomy: a **Zenodo DOI**, a **JOSS paper** (software), an **RNAAS**
  research note (1-page, citable), an **astroquery/pyvo** affiliation, a **HuggingFace** dataset
  with a leaderboard.

## Buildability & honesty rules for each plan

- Name the **real APIs/endpoints/auth/rate-limits/formats** (verify via web where you can). If a
  data source needs credentials, say so and give the account-free fallback.
- Do an **adversarial prior-art check**: what already exists (tools, papers, services)? State it
  plainly and locate the defensible wedge, or flag the idea as weak. Do not overclaim novelty.
- Give a **kill check** for M0 — the cheapest thing that would prove the idea dead (usually
  "someone already built this well" or "the data isn't actually accessible").
- Do not fabricate numbers, dates, or table values. Cite sources for load-bearing facts.

## Sprint-plan template (use these exact section headers)

```
# <Project name>

**One-liner:** <what it is, in one sentence>
**Scores (U/B/E):** <underexplored / agent-buildable / excitement, 1–5 each, with a word of why>
**Status:** proposed

## The wedge
- What exists already (adversarial prior-art check, named tools/papers/services)
- Where the defensible gap is, and why an agent fleet can fill it cheaply
- Why now (the 2026 catalyst, if any)

## Target user & the "who cites this" test
- Primary user, and the specific moment they reach for it
- What makes it citable / referenceable, not just consumable

## Data sources & access
- Exact APIs / endpoints / archives, auth model, rate limits, formats (account-free path called out)

## Architecture sketch
- Stack, main components, data flow. Keep it minimal-runnable-first.

## Milestones
- M0 (kill checks — cheap disproofs, prior-art emails/searches, data-access smoke test)
- M1 (thin end-to-end slice with an acceptance test)
- M2, M3 (expansion, distribution)
- Each milestone: a concrete acceptance criterion.

## First week / first tasks
- The 3–6 concrete things to do first.

## Risks & kill criteria
- What would make this not worth continuing.

## Distribution & legitimacy
- PyPI / JOSS / RNAAS / Zenodo / MCP registry / astroquery affiliation / HF dataset — pick the real ones.

## Rough size
- Effort estimate to M1, and the single biggest uncertainty.
```
