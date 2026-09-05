# Astronomy — independent research on public archives

[![CI](https://github.com/mepotts/astronomy/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/mepotts/astronomy/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Independent astronomy research built on public data — no telescope and no
institutional affiliation. The projects are designed for a laptop or workstation and
document the archive inputs, code, and milestone evidence used for each result. Some
reproductions also require bulk data or specialist environments that are deliberately
kept outside Git; each project documents those requirements rather than pretending there
is one repository-wide build.

Two conventions distinguish this repository. **Every claim is gated**: results are
scored against published values or positive controls, adopted changes must pass
injection-recovery, and nothing is submitted anywhere automatically. And **every
dead end stays on the record**: retractions, corrections, and approaches that
failed are indexed, not deleted — for an independent researcher, the audit trail
*is* the credential. See [PUBLISHING.md](PUBLISHING.md) for how this work is
headed into the formal record.

---

## Research

**Current state (2026-09-05):** see the
[executed closeout and remaining gates](DISCOVERY/CLOSEOUT-2026-09-05.md).
The ITF daily archive is repaired and caught up; TNS and CHIME are parked on
specific missing inputs; DASCH's original controls are closed; PTA/eROSITA have
local review packages. Dyson E (September 9) and Gaia DR4 (planned December 2)
remain future experiments, not completed discoveries. The
[new-work comparison](DISCOVERY/NEW-WORK-2026-09-05.md) selected one bounded
CCOR2 known-report control pilot. Nothing scientific has been submitted.

### [`exosat-rv`](https://github.com/mepotts/exosat-rv) — an independent raw-to-RV pipeline for imaged companions

> **This project now lives in its own repository:**
> **[github.com/mepotts/exosat-rv](https://github.com/mepotts/exosat-rv)** — the drafts, the
> reduction drivers, the injection harness and blind period search, and the full milestone
> record with its retractions. That is the repository the papers cite, and the only copy;
> the working tree that used to sit here has been removed. The summary below stays as the
> portfolio's account of the work, and every link in it points there.

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
open front ([M27](https://github.com/mepotts/exosat-rv/blob/main/docs/target-queue.md)): the discovery that the
archive's "staring" datasets are fiber-fed starlight-suppressed HiRISE
observations, including six public nights of beta Pic b.

Five drafts live in [`docs/paper/`](https://github.com/mepotts/exosat-rv/tree/main/docs/paper), each with a rendered
`.html` alongside its source;
[`LESSONS.md`](https://github.com/mepotts/exosat-rv/blob/main/LESSONS.md) is the consolidated trap catalog.

### [`itf-linker/`](itf-linker/) — linking the Minor Planet Center's orphan observations

The MPC's Isolated Tracklet File holds millions of astrometric observations never
linked to any orbit. This project links them: HelioLinC over a 0.55–50 AU distance
grid, Find_Orb orbit fitting validated round-trip against JPL Horizons, and a
vetting gate (MPChecker / SkyBoT / SBIDENT) so nothing known is "rediscovered."
Validated by hiding the linkages the file already contains: the grid re-derives
**93.0%** of them exactly, and recovers 11 of 13 real objects spanning an Atira to
TNOs. Links proposed here have since been independently published by the MPC
(30 at last count — external validation, claimed as nothing more). A daily
local snapshot pipeline keeps the pool current. M13 adds a stale-queue watcher and
builds a human-review payload, but has no submission capability; the scheduled watch
only runs from the repository's default branch. **No MPC submission is automated.**
M14 authenticated the two late-August Rubin aggregates but stopped on a two-row anatomy
accounting residue; all downstream diagnostics are post-stop/noninferential, the runner
is retired, and no M14 candidate queue exists.
An RNAAS method note is drafted in
[`itf-linker/docs/`](itf-linker/docs/).

### [`tns-miner/`](tns-miner/) — low-latitude transient triage

The M2 front is closed, and its cache/input layer was repaired in September 2026 after an
audit found that failed Fink requests could masquerade as empty histories. The reported
3.5%/8.0% precision and 40%/12% artifact measurements are now explicitly historical:
the 2026-09-02 proved rerun sealed the newest closed TNS year but stopped without a
candidate count when one required Fink class timed out even at `n=1`. No pool or candidate
output exists. M2's 37-object list is not a submission queue; nothing was sent to TNS and
no account was created. The operational handoff and exact caveat are in
[`tns-miner/OPERATING-GUIDE.md`](tns-miner/OPERATING-GUIDE.md).

## Newer science fronts

| Project | Current state |
|---|---|
| [`dyson-revet/`](dyson-revet/) | **M7 closed.** The empirical-PSF acceptance test passed, but the published redshift still could not be independently confirmed; any write-up is a human go/no-go. |
| [`erosita-dr2/`](erosita-dr2/) | **M5 write-up complete.** The fader-census draft is not submitted; the optional classifier build remains deferred. |
| [`gaia-dr4/`](gaia-dr4/) | **M9 closed and rehearsed for the planned 2026-12-02 DR4 release.** Release-day analysis and preregistration amendments remain explicitly gated. |
| [`pta-mpta/`](pta-mpta/) | **M6 closed.** One full paper and two RNAAS notes are drafts, all checked against committed result artifacts and none submitted. |
| [`chime-frb-periodicity/`](chime-frb-periodicity/) | **M0 stopped correctly.** Catalog 2 and the 16.35-day control reproduce, but the public exposure product has no time-resolved observing window; no unknown-source scan ran. |
| [`dasch-pilot/`](dasch-pilot/) | **Narrow light-curve/API slice passed; original cutout M0 remains open.** The published T CrB high state survives current DR7 cuts and one nearby field control; the Mira, faint/crowded control, plate-cutout recovery, and blind mining remain unexecuted. |
| [`spherex-pilot/`](spherex-pilot/) | **Broad use case killed; narrow test blocked at privacy gate.** Only 1/223 fitted warm tails clears the conservative 4.8-micron floor, and zero private coordinates were sent. |

## Tools

| Project | What it does | Status |
|---|---|---|
| [`pta-explainer/`](pta-explainer/) | Pulsar-timing-array / Hellings–Downs interactive explainer — **[live demo](https://mepotts.github.io/pta-explainer/)** | Deployed. HD curve, source sandbox, and a monopole/dipole/quadrupole overlay showing why only the quadrupole implies gravitational waves. 64 tests |
| [`seti-ellipsoid-broker/`](seti-ellipsoid-broker/) | Fuses transient alerts × Gaia DR3 into nightly SN 1987A ellipsoid-crossing target lists | Live, externally validated — crossing epochs reproduce all 217 targets of Nilipour+2023 to <5×10⁻⁴ yr. Account-free Gaia TAP path. 84 tests. RNAAS tool note drafted |
| [`adql-copilot/`](adql-copilot/) | Schema-aware ADQL linter for Virtual-Observatory TAP endpoints | Correctness-hardened against the real 6,614-column Gaia `TAP_SCHEMA`; honest unchecked-identifier reporting. 46 tests. JOSS paper drafted in [`adql-copilot/paper/`](adql-copilot/paper/) |

## The lab notebook

The latest repository-wide discovery closeout, in execution order, is
[`DISCOVERY/CAMPAIGN-2026-09-02.md`](DISCOVERY/CAMPAIGN-2026-09-02.md).

[`DISCOVERY/`](DISCOVERY/README.md) and [`IDEAS/`](IDEAS/README.md) are **planning
documents, not results** — kept public because research about *where discovery is
possible* is useful in its own right. Some plans have since become projects (notably
`gaia-dr4`), so their dated assumptions must be rechecked before reuse; project status
files and milestone documents take precedence over an older prospectus.

## Conventions

Project layouts vary because the repository contains packaged tools, data-heavy science
fronts, a static site, and planning dossiers. Start with the project's `README.md` and,
where present, `STATUS.md`, `BUILD-PLAN.md`, or numbered milestone documents. There is no
single root build. [CONTRIBUTING.md](CONTRIBUTING.md) lists the maintained checks and
explains what CI does and does not cover. The repository is MIT-licensed; only projects
that actually carry a `CITATION.cff` have a project-specific citation record. A Git tag
does not by itself mint a DOI — archival remains an explicit owner-controlled release
step described in [PUBLISHING.md](PUBLISHING.md).

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
