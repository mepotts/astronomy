# Astronomy Projects

[![CI](https://github.com/mepotts/astronomy/actions/workflows/ci.yml/badge.svg?branch=advance-portfolio)](https://github.com/mepotts/astronomy/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Build portfolio for the astronomy opportunities surfaced by a prior **idea-research run** (2026-06-14) that swept the field for AI/agent-buildable projects and ranked them. **This** repo is where the promising ones get built. (The upstream research dossiers are kept outside this repo.)

**The pattern they all attack:** astronomy data is now open and abundant, but the *usability/translation layer* between raw archives and the humans who want to use them (newcomers, amateurs, even working scientists) is systematically missing — aggregation layers, query translators, quality-weighting, interactive explainers. That connective tissue is cheap for an agent fleet to build.

---

## Active builds

| Folder | Project | Scores (U/B/E) | Status (verified 2026-07-18) |
|---|---|---|---|
| [`seti-ellipsoid-broker/`](seti-ellipsoid-broker/) | SETI Ellipsoid Alert Broker — fuses transient alerts × Gaia DR3 into nightly SN 1987A ellipsoid-crossing target lists | 4/4/4 | **M1.5 — live & externally validated.** Account-free live path (`run --transients-csv` + anonymous Gaia DR3 TAP, no token) with the Lindegren+2021 parallax zero-point correction; crossing epochs reproduce all 217 SN 1987A targets of Nilipour+2023 to <5e-4 yr. 84 tests green (+ live-Gaia smoke). |
| [`pta-explainer/`](pta-explainer/) | Pulsar Timing Array / Hellings–Downs interactive explainer — **[live demo](https://mepotts.github.io/pta-explainer/)** | 5/5/4 | **M2 — deployed.** Live HD demo + source sandbox (residuals, sky-map marker, 2-source superposition) + **monopole/dipole/quadrupole overlay** showing why only the quadrupole implies GWs. 64 tests, build green, live on GitHub Pages. |
| [`adql-copilot/`](adql-copilot/) | Schema-aware ADQL linter / NL→ADQL copilot over Virtual-Observatory TAP endpoints | 4/5/4 | **M1.1 — correctness hardened.** Deterministic linter live vs Gaia `TAP_SCHEMA`; fixed case-sensitivity, `TAP_UPLOAD`, join-key & spatial-clause false positives, honest unchecked-identifier reporting, structured fix payloads. 46 tests green. |

Each project folder contains: `SPEC.md` (the verified research dossier), `DATA-SOURCES.md` (exact APIs/endpoints/formats), `BUILD-PLAN.md` (stack decision, architecture, milestones, first tasks), and a minimal runnable skeleton.

**License & citation:** all three are MIT-licensed with a `CITATION.cff` and `.zenodo.json`; cut a tagged GitHub release to mint a Zenodo DOI and make them citable. `adql-copilot/paper/` holds a JOSS paper draft; `seti-ellipsoid-broker/docs/rnaas-draft.md` holds a draft RNAAS tool note (validated against Nilipour 2023).

---

## New build ideas — "run 2" white space

Eight fresh sprint-level plans in [`IDEAS/`](IDEAS/README.md), deliberately in the subfields the original run never swept (high-energy, planetary/meteor, satellites/SSA, historical archives) and the AI patterns it skipped (MCP tooling, agentic reproduction, accessibility). Top picks: the **[Gaia DR4 diff auditor](IDEAS/gaia-dr4-diff-auditor.md)** (hard dated catalyst — DR4 on 2 Dec 2026) and **[astro-mcp](IDEAS/astro-mcp.md)** (turns adql-copilot into an MCP server reaching every LLM client). See the [ranked index](IDEAS/README.md).

---

## Discovery pathways — the other axis

Everything above is a **tool for other people's science**. [`DISCOVERY/`](DISCOVERY/README.md) is the
complementary axis: verified routes where a person with a laptop, no telescope and no affiliation can
download public data, find a genuinely new object, and **submit it to a body that reviews and credits
it**. Researched 2026-07-28 with every URL live-checked.

Eight sprint-level plans, **ranked by whether a recognised body issues you a designation** — five end in a
permanent IAU-recognised record, two in a semi-official catalogue entry, one in a paper and nothing else.

| Tier | Plan | The record you get |
|---|---|---|
| **A** | [ITF linker](DISCOVERY/itf-linker.md) | Provisional designation + your name on an MPEC `Id.` line |
| **A** | [TNS alert miner](DISCOVERY/tns-alert-miner.md) | `AT 2026xyz` IAU designation + ADS bibcode |
| **A** | [Plate archaeology](DISCOVERY/plate-archaeology.md) | IAU designation from century-old glass; near-zero competition |
| **A** | [DAD triage](DISCOVERY/dad-triage.md) | MPC designations — **gated on a SARC kill-check** |
| **A** | [Coronagraph comets](DISCOVERY/coronagraph-comets.md) | Real IAU comet designation (named for the instrument) |
| **B** | [Nebula hunt](DISCOVERY/nebula-hunt.md) · [VSX characterization](DISCOVERY/vsx-characterization.md) | Catalogue entry; weak-to-minimal personal credit |
| **C** | [LSB survey](DISCOVERY/lsb-survey.md) | Co-authorship only — no registry exists for static objects |

Headline: the MPC publishes a 135 MB file of **9,359,693 observations never linked to any orbit**; link
three nights into a valid orbit and it credits you by name (it did so for three separate individuals in
July 2026 alone). And on TNS, "discoverer" formally means *first to report, not first to observe* — a
two-person team mining the public ZTF stream logged ~100 IAU designations in twelve months with no
telescope. The folder also records what's **closed** (ExoFOP cTOI paused since March 2026; Rubin imaging
proprietary to ~2028; a dozen dormant Zooniverse projects) and the two procedural gates (**SARC**,
**ADES**) that will otherwise waste your first submission.

## Backlog (surfaced by the run, not yet started)

Strong Tier-2/3 candidates surfaced by the run (not yet built here):

- **Cosmology Tensions Monitor** (5/3/4) — live H0/S8/w0–wa tracker → adjacent: >2σ disagreement detector
- **Interactive Asteroseismology Simulator** (4/4/4) — pairs with a TESS mode-ID crowdsourcing game
- **Strong-Lens Training Dataset Generator** (4/4/4) — versioned HF dataset → lens-finder leaderboard
- **δ Scuti Mode Identification** (4/4/4, experiment) — per-frequency ML labeling
- **Amateur Observation Quality-Weighting Framework** (4/4/3) — makes citizen data ingestible by pros
- …plus 7 more (DESI reproducibility kit, AAVSO broker filter, SHARP→NOAA API, multi-messenger overlay, observatory bias auditor, CHIME Cat-2 pipeline, RR Lyrae calibration audit).

## Origin

Surfaced by an agent-driven idea-research run (2026-06-14): 13 subfield sweeps → ~78 candidates → a 15-item ranked shortlist, each adversarially verified for prior art. The three builds above are the top-ranked, most agent-buildable picks; [`IDEAS/`](IDEAS/README.md) holds the "run 2" white space. The upstream research notes are kept outside this repo.
