# Astronomy: independent research on public archives

[![CI](https://github.com/mepotts/astronomy/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/mepotts/astronomy/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Independent astronomy research on public archive data, with no telescope and no institutional
affiliation. It is a portfolio of separate projects, each with its own code and milestone record.
The projects cover minor-planet linking, archival radial-velocity and pulsar-timing reanalyses,
transient triage, and small tools.

Claude Code agents wrote the code under standing verification gates (positive controls,
injection-recovery, scoring against published values). I set the direction and approve every
outward action. See [AI-CHECKLIST.md](AI-CHECKLIST.md).

No discovery is claimed and nothing has been submitted. Corrections and retractions stay on the record.

Dated status is in [STATUS.md](STATUS.md). Publication plans are in [PUBLISHING.md](PUBLISHING.md).

---

## Research

### [`exosat-rv`](https://github.com/mepotts/exosat-rv): a paper-calibrated, conditional reanalysis of the CD-35 2722 B exosatellite claim

> **This project now lives in its own repository:** [github.com/mepotts/exosat-rv](https://github.com/mepotts/exosat-rv).
> It holds the drafts, the reduction drivers, the fitter-stage injection tests and period-search
> scripts, and the full milestone record with its retractions. The drafts cite that repository,
> and it holds the only copy. The working tree that used to sit here has been removed. The summary
> below stays as the portfolio's account of the work, and every link in it points there.

This is a reanalysis of Hoy et al. 2026 ([Nature](https://www.nature.com/articles/s41586-026-10751-w)).
That paper measured the radial velocity of the imaged companion CD-35 2722 B itself (not its host
star) and reported a planetary-mass satellite around it. A separately implemented CR2RES/VIPER
extraction, calibrated against the published RV series, is not an independent reproduction. It
recovers the reported ~171-day signal on the 17 nights retained by an internal quality screen.
With all 18 nights, the BERV-adjusted searches are compatible with noise.

- **Second satellite:** not reproduced under this project's stated models and priors (a
  different sampler was not tested).
- **eta Tel B:** a same-setting nodding control with no detected signal. Its sensitivity curve is
  pointwise, circular-orbit and conditional on fitter-stage transmission. It is not an
  unconditional upper limit.
- **Other observing modes:** transfer is unproven. The former "staring" sample was HiRISE fibre
  data processed with a slit recipe, and those claims are withdrawn. The beta Pic extraction is
  host-dominated and is not a companion RV measurement (see the
  [target ledger](https://github.com/mepotts/exosat-rv/blob/main/docs/target-queue.md)).
- **Status:** no discovery is claimed and nothing has been submitted. Read the
  [M37 audit](https://github.com/mepotts/exosat-rv/blob/main/docs/milestones/M37-RESULTS.md) first.

The manuscript drafts in [`docs/paper/`](https://github.com/mepotts/exosat-rv/tree/main/docs/paper)
are work in progress, and none is submission-ready. Each has a rendered `.html` alongside its
source. [`LESSONS.md`](https://github.com/mepotts/exosat-rv/blob/main/docs/LESSONS.md)
is the consolidated trap catalog.

### [`itf-linker/`](itf-linker/) — linking the Minor Planet Center's orphan observations

The MPC's Isolated Tracklet File holds millions of astrometric observations never
linked to any orbit. This project links them: HelioLinC over a 0.55–50 AU distance
grid, Find_Orb orbit fitting validated round-trip against JPL Horizons, and a
vetting gate (MPChecker / SkyBoT / SBIDENT) so nothing known is "rediscovered."
Validated by hiding the linkages the file already contains: the grid re-derives
**93.0%** of them exactly, and recovers 11 of 13 real objects spanning an Atira to
TNOs. Attributions held in this project's ledger (none submitted) have since been
checked against the MPC's own processing. The MPC linked the tracklets of 68 PASS rows and
removed them from the ITF. All 68 went to exactly the object the ledger named
([M11](itf-linker/M11-RESULTS.md), 2026-08-23). This is external validation and
nothing more. A daily
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
| [`pta-explainer/`](pta-explainer/) | Pulsar-timing-array / Hellings-Downs interactive explainer: **[live demo](https://mepotts.github.io/pta-explainer/)** | Deployed: HD curve and source sandbox. A monopole/dipole overlay (showing why only the quadrupole implies gravitational waves) is in the source but not yet in the live build, which was deployed 2026-07-18. 64 tests |
| [`seti-ellipsoid-broker/`](seti-ellipsoid-broker/) | Fuses transient alerts with Gaia DR3 into ranked SN 1987A ellipsoid-crossing target lists | Offline core complete. It runs on a user-supplied alert CSV against anonymous (account-free) Gaia DR3 TAP, and broker auto-ingest (Lasair, ASAS-SN, CHIME) remains stubs. Crossing epochs reproduce all 217 targets of Nilipour+2023 to within 0.0005 yr. That checks the math against published values and does not test a running service. 84 tests. RNAAS tool note drafted |
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
