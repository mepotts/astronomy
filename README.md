# Astronomy — independent research on public archives

[![CI](https://github.com/mepotts/astronomy/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/mepotts/astronomy/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Independent astronomy research built entirely on public data — no telescope, no
institutional affiliation. Everything here runs on a laptop against open archives
(ESO, MPC, Gaia, TAP services), and every result is reproducible from the code and
milestone documents that sit next to it.

Two conventions distinguish this repository. **Every claim is gated**: results are
scored against published values or positive controls, adopted changes must pass
injection-recovery, and nothing is submitted anywhere automatically. And **every
dead end stays on the record**: retractions, corrections, and approaches that
failed are indexed, not deleted — for an independent researcher, the audit trail
*is* the credential. See [PUBLISHING.md](PUBLISHING.md) for how this work is
headed into the formal record.

---

## Research

### [`exosat-rv/`](exosat-rv/) — an independent raw-to-RV pipeline for imaged companions

> **Arriving from the paper?** This project now has its own repository:
> **[github.com/mepotts/exosat-rv](https://github.com/mepotts/exosat-rv)** — the drafts, the
> reduction drivers, the injection harness and blind period search, and the full milestone
> record with its retractions. That is the repository the papers cite. The copy below is
> retained here for now and is not the canonical one.

The deepest project here: an independent reproduction of Hoy et al. 2026
([Nature](https://www.nature.com/articles/s41586-026-10751-w)), which measured the
radial velocity of the imaged companion CD-35 2722 B *itself* — not its host star —
and reported a planetary-mass satellite around it. The pipeline is not a reconstruction of
theirs, which has never been published — it is an independent route to the same quantity,
and it transfers unmodified across three wavelength settings and both observing modes.

**The primary conclusion reproduces — from the raw data.** An independent
re-reduction (ESO cr2res + viper forward modeling) reaches 70–90 m/s rms against
the paper's published per-epoch RVs, and a blind period search re-detects the
~171-day signal at rank 1 with a barycentric nuisance covariate in the model, on
two independent reduction routes. **The claimed second satellite does not survive
the paper's own table**: nested sampling gives it negative evidence in 10 of 10
configurations, against the paper's reported +2.6.

The validated method was then pointed at every archival CRIRES+
companion-spectroscopy campaign a coordinate census could find. Eighteen systems
adjudicated — one confirmation, one contradiction, four upper limits (including
one on **eta Tel B** for which no previous measurement is known:
msini ≳ 0.51–1.27 M_Jup at 90% across P = 20–300 d), one contamination-limited,
four data-limited — plus a measured resolution gate for slit spectroscopy and an
open front ([M27](exosat-rv/docs/target-queue.md)): the discovery that the
archive's "staring" datasets are fiber-fed starlight-suppressed HiRISE
observations, including six public nights of beta Pic b.

Five drafts live in [`exosat-rv/docs/paper/`](exosat-rv/docs/paper/), each with a rendered
`.html` alongside its source;
[`exosat-rv/LESSONS.md`](exosat-rv/LESSONS.md) is the consolidated trap catalog.

### [`itf-linker/`](itf-linker/) — linking the Minor Planet Center's orphan observations

The MPC's Isolated Tracklet File holds ~9.3 million astrometric observations never
linked to any orbit. This project links them: HelioLinC over a 0.55–50 AU distance
grid, Find_Orb orbit fitting validated round-trip against JPL Horizons, and a
vetting gate (MPChecker / SkyBoT / SBIDENT) so nothing known is "rediscovered."
Validated by hiding the linkages the file already contains: the grid re-derives
**93.0%** of them exactly, and recovers 11 of 13 real objects spanning an Atira to
TNOs. Links proposed here have since been independently published by the MPC
(30 at last count — external validation, claimed as nothing more). A daily
snapshot pipeline keeps the pool current. **No submission is automated; none ever
will be.** An RNAAS method note is drafted in
[`itf-linker/docs/`](itf-linker/docs/).

## Tools

| Project | What it does | Status |
|---|---|---|
| [`pta-explainer/`](pta-explainer/) | Pulsar-timing-array / Hellings–Downs interactive explainer — **[live demo](https://mepotts.github.io/pta-explainer/)** | Deployed. HD curve, source sandbox, and a monopole/dipole/quadrupole overlay showing why only the quadrupole implies gravitational waves. 64 tests |
| [`seti-ellipsoid-broker/`](seti-ellipsoid-broker/) | Fuses transient alerts × Gaia DR3 into nightly SN 1987A ellipsoid-crossing target lists | Live, externally validated — crossing epochs reproduce all 217 targets of Nilipour+2023 to <5×10⁻⁴ yr. Account-free Gaia TAP path. 84 tests. RNAAS tool note drafted |
| [`adql-copilot/`](adql-copilot/) | Schema-aware ADQL linter for Virtual-Observatory TAP endpoints | Correctness-hardened against the real 6,614-column Gaia `TAP_SCHEMA`; honest unchecked-identifier reporting. 46 tests. JOSS paper drafted in [`adql-copilot/paper/`](adql-copilot/paper/) |

## The lab notebook

[`DISCOVERY/`](DISCOVERY/README.md) and [`IDEAS/`](IDEAS/README.md) are **planning
documents, not results** — kept public because verified research about *where
discovery is possible* is useful in its own right. DISCOVERY maps the routes by
which an individual with public data can find a new object and have it formally
recognised (every URL live-verified; unconfirmed claims marked, not asserted), and
records which routes are closed. IDEAS holds sprint-level build plans not yet
started — top picks: a Gaia DR4 diff auditor (DR4 releases 2026-12-02) and an MCP
server built from adql-copilot.

## Conventions

Each project directory is self-contained — its own toolchain, tests, and
virtualenv — and holds `SPEC.md` (verified research dossier), `DATA-SOURCES.md`
(exact endpoints and their failure modes), `BUILD-PLAN.md` (milestones), numbered
`M*-RESULTS.md` findings, and a `HANDOFF.md` that indexes every claim later found
false. There is no root-level build. [CONTRIBUTING.md](CONTRIBUTING.md) has test
commands; all projects are MIT-licensed with `CITATION.cff`, and a tagged release
mints a Zenodo DOI.

**Safety.** Several projects could write to shared scientific registries (MPC,
TNS). Bad submissions pollute resources the whole field depends on, so automated
end-to-end submission is permanently out of scope — every submission path is
gated behind per-batch human review.

## Origin

Started from an agent-driven research sweep (2026-06): 13 subfield sweeps → ~78
candidates → a ranked shortlist, each adversarially checked for prior art. The
tools were the top picks; the research projects grew out of asking a harder
question — not *what can be built*, but *what can be found, tested, and formally
credited*.
