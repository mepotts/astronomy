# Astronomy Projects

[![CI](https://github.com/mepotts/astronomy/actions/workflows/ci.yml/badge.svg?branch=advance-portfolio)](https://github.com/mepotts/astronomy/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Open-data astronomy work along two axes:

1. **Tools** — the usability layer between raw public archives and the humans who want to use them. Astronomy data is now open and abundant, but the translation layer (query linting, aggregation, interactive explanation) is systematically missing.
2. **Discovery** — pipelines that mine those same public archives for genuinely new objects and submit them to the bodies that formally review and credit discoveries: the Minor Planet Center, the Transient Name Server.

Everything here runs on public data, needs no telescope, and is designed for **zero marginal cost** — build once, unlimited users, no per-user charge.

---

## Tools

| Project | What it does | Status |
|---|---|---|
| [`seti-ellipsoid-broker/`](seti-ellipsoid-broker/) | Fuses transient alerts × Gaia DR3 into nightly SN 1987A ellipsoid-crossing target lists | **M1.5 — live, externally validated.** Account-free path (anonymous Gaia DR3 TAP, no token) with the Lindegren+2021 parallax zero-point correction. Crossing epochs reproduce all 217 SN 1987A targets of Nilipour+2023 to <5×10⁻⁴ yr. 84 tests |
| [`pta-explainer/`](pta-explainer/) | Pulsar-timing-array / Hellings–Downs interactive explainer — **[live demo](https://mepotts.github.io/pta-explainer/)** | **M2 — deployed.** HD demo, source sandbox (residuals, sky-map marker, 2-source superposition), and a monopole/dipole/quadrupole overlay showing why only the quadrupole implies gravitational waves. 64 tests |
| [`adql-copilot/`](adql-copilot/) | Schema-aware ADQL linter over Virtual-Observatory TAP endpoints | **M1.1 — correctness hardened.** Deterministic linter validated against the real 6,614-column Gaia `TAP_SCHEMA`; fixed case-sensitivity, `TAP_UPLOAD`, join-key and spatial-clause false positives; honest unchecked-identifier reporting. 46 tests |

## Discovery

[`DISCOVERY/`](DISCOVERY/README.md) is the research dossier: eight sprint-level plans for routes where an individual with public data and no institutional affiliation can find a new object and get it formally recognised. Every URL live-verified 2026-07-28; unconfirmed claims are marked unverified rather than asserted.

Ranked by **whether a recognised body issues a designation** — not by difficulty:

| Tier | Plan | The record you get |
|---|---|---|
| **A** | [ITF linker](DISCOVERY/itf-linker.md) | Provisional designation + your name on an MPEC `Id.` line |
| **A** | [TNS alert miner](DISCOVERY/tns-alert-miner.md) | `AT 2026xyz` IAU designation + ADS bibcode |
| **A** | [Plate archaeology](DISCOVERY/plate-archaeology.md) | IAU designation from century-old glass; near-zero competition |
| **A** | [DAD triage](DISCOVERY/dad-triage.md) | MPC designations — gated on a SARC kill-check |
| **A** | [Coronagraph comets](DISCOVERY/coronagraph-comets.md) | Real IAU comet designation (named for the instrument, not the finder) |
| **B** | [Nebula hunt](DISCOVERY/nebula-hunt.md) · [VSX characterization](DISCOVERY/vsx-characterization.md) | Catalogue entry; weak-to-minimal personal credit |
| **C** | [LSB survey](DISCOVERY/lsb-survey.md) | Co-authorship only — no registry exists for static objects |

Two findings that motivate the whole folder. The MPC publishes a 135 MB file of **9,359,693 observations never linked to any orbit**; link three nights into a valid orbit and it credits you by name — it did so for three separate individuals in July 2026 alone. And on TNS, "discoverer" formally means *first to report*, not first to observe: a two-person team mining the public ZTF alert stream logged ~100 IAU designations in twelve months with no telescope.

The dossier also records what is **closed** — ExoFOP community-TOI submissions paused since March 2026, Rubin imaging proprietary until ~2028, a dozen dormant Zooniverse projects — and the two procedural gates (**SARC**, **ADES**) that otherwise waste a first submission.

**In progress:** [`itf-linker/`](itf-linker/) implements the Tier-A ITF pathway. **M1 complete** — Find_Orb built and validated by a closed loop against JPL Horizons (not merely by compiling), 140 tests. Of 2,515 multi-night ITF designations, 128 pass every published MPC acceptance gate. **None are claimed as discoveries**: catalogue vetting against MPChecker, SkyBoT and JPL SBIDENT is M2 and has not been done, and one candidate already resolved to the known comet 73P-C.

## Planned, not started

Eight sprint-level build plans in [`IDEAS/`](IDEAS/README.md), deliberately in subfields the original research sweep never covered (high-energy, planetary/meteor, satellites/SSA, historical archives) and the AI patterns it skipped (MCP tooling, agentic reproduction, accessibility). Top picks: the **[Gaia DR4 diff auditor](IDEAS/gaia-dr4-diff-auditor.md)** — hard dated catalyst, DR4 releases 2 December 2026 — and **[astro-mcp](IDEAS/astro-mcp.md)**, which turns adql-copilot into an MCP server reaching every LLM client.

Further candidates surfaced but not planned: cosmology tensions monitor, interactive asteroseismology simulator, strong-lens training dataset generator, δ Scuti mode identification, amateur-observation quality weighting, DESI reproducibility kit, AAVSO broker filter, SHARP→NOAA API, multi-messenger overlay, observatory bias auditor, CHIME Cat-2 pipeline, RR Lyrae calibration audit.

---

## Repository conventions

Each project directory is self-contained — its own toolchain, tests, and virtualenv — and holds `SPEC.md` (verified research dossier), `DATA-SOURCES.md` (exact APIs, endpoints, formats, limits), and `BUILD-PLAN.md` (stack decisions, architecture, milestones). There is no root-level build. See [CONTRIBUTING.md](CONTRIBUTING.md) for test commands and the standards this repository holds itself to.

**Citation.** All projects are MIT-licensed with a `CITATION.cff` and `.zenodo.json`; a tagged GitHub release mints a Zenodo DOI. [`adql-copilot/paper/`](adql-copilot/paper/) holds a JOSS paper draft; `seti-ellipsoid-broker/docs/rnaas-draft.md` holds a draft RNAAS tool note, gated on the Nilipour validation, which passes.

**Safety.** Several projects here can write to shared scientific registries. Bad or duplicate submissions pollute resources the whole field depends on and damage submitter reputation such that future reports get disregarded. Automated end-to-end submission is permanently out of scope — every submission path is gated behind per-batch human review and validates against a sandbox endpoint first.

## Origin

The tools began with an agent-driven idea-research run (2026-06-14): 13 subfield sweeps → ~78 candidates → a 15-item ranked shortlist, each adversarially verified for prior art. The three builds above were the top-ranked picks; [`IDEAS/`](IDEAS/README.md) holds the second sweep's white space. The discovery axis came later, from a 2026-07-28 research fan-out that asked a different question — not *what can be built*, but *what can be found and formally credited*. Upstream research notes are kept outside this repo.
