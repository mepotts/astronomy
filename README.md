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

**Current state (2026-09-12):** [latest execution](DISCOVERY/EXECUTION-2026-09-12.md).
ITF's stale daily feed recovered: 18 ready / 8 held, two newly held after tracklet
disappearance. E's public-release gate passed, but its unchanged frozen experiment
failed at F560W centroiding. Independent audit confirms a saddle fit on finite data;
no validated contrast or discovery. Portfolio follow-up is now weekly; ITF stays daily.

**Continued discovery work:** [new-route evidence and decisions](DISCOVERY/SEARCH-2026-09-12.md).
[TESS](tess-short-eclipses/M0b-RESULT-2026-09-12.md) recovered three published
eclipse periods and near-target pixel signals. Its
[1,920-trial localization experiment](tess-short-eclipses/M2p-RESULT-2026-09-12.md)
now fails stress rules in two controls; the cleaner control remains incompletely
validated. No unknown-source scan has begun.
[VLASS](vlass-pilot/README.md) recovered a known radio source and established a
12-source same-field comparison ensemble in three epochs. Its subsequent
common-beam validation stopped on control recovery and empirical noise gates;
neither route is discovery-ready.
[ITF notification audit](DISCOVERY/ITF-NOTIFICATIONS-2026-09-12.md): daily archive
and existing-queue monitoring are automated, but a dedicated discovery text/email
sender is not configured or delivery-verified.

**September 8 historical snapshot:**
DASCH's unchanged detector recovered 0/3 published long-term events; a separately
specified bracketed-block method also failed its coverage/recovery gates. Neither
is ready to scale. ITF's September 8 publisher/watch are healthy (20 ready / 6 held
unchanged). Dyson E's September 9 experiment is next; no new discovery or submission.

**September 7:** see the
[completed experiments and actual discovery screen](DISCOVERY/EXECUTION-2026-09-07.md).
DASCH passed a limited matched-colour holdout gate, then screened 42 sources:
361 eligible windows, zero leads. CCOR measured known-star pixels but failed
two frames' training-count gate. A prospectively selected DR11 field gains six
r exposures but only 5.47% lower empirical aperture scatter, below its 10% gate.
ITF's daily archive continues; Rubin/CHIME remain input-limited. PTA full paper
is the selected publication unit. Dyson E (September 9) and Gaia DR4 (planned
December 2) remain future experiments. No scientific submission or new discovery.

### [`exosat-rv`](https://github.com/mepotts/exosat-rv) — a paper-calibrated, conditional reanalysis of the CD-35 2722 B exosatellite claim

> **This project now lives in its own repository:**
> **[github.com/mepotts/exosat-rv](https://github.com/mepotts/exosat-rv)** — the drafts, the
> reduction drivers, the fitter-stage injection tests and period-search scripts, and the full
> milestone record with its retractions. That is the repository the drafts cite, and the only
> copy; the working tree that used to sit here has been removed. The summary below stays as
> the portfolio's account of the work, and every link in it points there.

A reanalysis of Hoy et al. 2026 ([Nature](https://www.nature.com/articles/s41586-026-10751-w)),
which measured the radial velocity of the imaged companion CD-35 2722 B *itself* — not its host
star — and reported a planetary-mass satellite around it. A separately implemented CR2RES/VIPER
extraction, calibrated against the published RV series and therefore **not an independent
reproduction**, recovers the reported ~171-day signal on the 17 nights retained by an internal
quality screen; with all 18 nights the BERV-adjusted searches are compatible with noise.

- **Second satellite:** not reproduced under this project's stated models and priors (a
  different sampler was not tested).
- **eta Tel B:** a same-setting nodding control with no detected signal. Its sensitivity curve is
  pointwise, circular-orbit and conditional on fitter-stage transmission, not an unconditional
  upper limit.
- **Other observing modes:** transfer is unproven. The former "staring" sample was HiRISE fibre
  data processed with a slit recipe, and those claims are withdrawn; the beta Pic extraction is
  host-dominated and is not a companion RV measurement (see the
  [target ledger](https://github.com/mepotts/exosat-rv/blob/main/docs/target-queue.md)).
- **Status:** no discovery is claimed and nothing has been submitted. Read the
  [M37 audit](https://github.com/mepotts/exosat-rv/blob/main/docs/milestones/M37-RESULTS.md) first.

The manuscript drafts in [`docs/paper/`](https://github.com/mepotts/exosat-rv/tree/main/docs/paper),
each with a rendered `.html` alongside its source, are work in progress; none is
submission-ready. [`LESSONS.md`](https://github.com/mepotts/exosat-rv/blob/main/docs/LESSONS.md)
is the consolidated trap catalog.

### [`itf-linker/`](itf-linker/) — linking the Minor Planet Center's orphan observations

The MPC's Isolated Tracklet File holds millions of astrometric observations never
linked to any orbit. This project links them: HelioLinC over a 0.55–50 AU distance
grid, Find_Orb orbit fitting validated round-trip against JPL Horizons, and a
vetting gate (MPChecker / SkyBoT / SBIDENT) so nothing known is "rediscovered."
Validated by hiding the linkages the file already contains: the grid re-derives
**93.0%** of them exactly, and recovers 11 of 13 real objects spanning an Atira to
TNOs. Attributions held in this project's ledger (none submitted) have since been
checked against the MPC's own processing: of the PASS rows whose tracklets the MPC has
since linked and removed from the ITF, 68 of 68 went to exactly the object the ledger
named ([M11](itf-linker/M11-RESULTS.md), 2026-08-23; external validation, claimed as
nothing more). A daily
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
| [`pta-explainer/`](pta-explainer/) | Pulsar-timing-array / Hellings–Downs interactive explainer — **[live demo](https://mepotts.github.io/pta-explainer/)** | Deployed: HD curve and source sandbox. A monopole/dipole overlay (showing why only the quadrupole implies gravitational waves) is in the source but not yet in the live build, which was deployed 2026-07-18. 64 tests |
| [`seti-ellipsoid-broker/`](seti-ellipsoid-broker/) | Fuses transient alerts × Gaia DR3 into ranked SN 1987A ellipsoid-crossing target lists | Offline core complete; runs on a user-supplied alert CSV against anonymous (account-free) Gaia DR3 TAP, while broker auto-ingest (Lasair, ASAS-SN, CHIME) remains stubs. Crossing epochs reproduce all 217 targets of Nilipour+2023 to <5×10⁻⁴ yr, a check of the math against published values rather than of a running service. 84 tests. RNAAS tool note drafted |
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
