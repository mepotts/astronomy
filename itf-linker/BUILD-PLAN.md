# BUILD PLAN — ITF Linker

Desk/data/software-only build: no telescope, no hardware, no paid service. See
[`SPEC.md`](SPEC.md) for the thesis, [`DATA-SOURCES.md`](DATA-SOURCES.md) for endpoints, and
[`M0-RESULTS.md`](M0-RESULTS.md) for what M0 actually measured.

---

## 1. Chosen stack (justified)

| Concern | Choice | Why | Alternatives considered |
|---|---|---|---|
| Language | **Python 3.11+** | The whole minor-planet toolchain (astropy, Find_Orb wrappers, FindPOTATOs, heliolinc) is Python; matches sibling projects. | None viable. |
| Packaging | **`pyproject.toml` + hatchling**, `src/` layout | Editable installs, clean test isolation; src-layout prevents "works because cwd" bugs. | Poetry (lockfile churn); flat layout (import shadowing). |
| CLI | **`typer`** | Declarative subcommands, free `--help`, type-validated args. | argparse (boilerplate). |
| Columnar engine | **polars + Parquet** | 9.36M lines parsed in **9.1 s** with bounded memory (measured). Vectorised string slicing does the 80-column decode without a Python loop. | pandas (slower, heavier); duckdb (fine too — polars won on the fixed-width slicing API). |
| Storage | **single Parquet + zstd** | 189 MB for 9.3M rows; scans in ~1 s. Partitioned layout deferred until M1 proves it is needed. | SQLite (poor columnar scans at this width). |
| Sky indexing | **astropy-healpix** | Equal-area pixels; pip-installable on Windows (unlike `healpy`). | healpy (no Windows wheels). |
| Time / coords | **astropy** | `Time` pins the hand-rolled MJD conversion in tests. | Hand-rolled only (no independent check). |
| Orbit fitting | **Find_Orb as a subprocess** (M1) | The workhorse; no Python reimplementation is credible. | OpenOrb (less maintained). |
| Tests | **pytest** | 60 tests; markers gate the ones needing the snapshot or network. | unittest (verbose). |

**Deliberately deferred:** no partitioned Parquet, no database, no parallelism. M0 showed the
data layer is seconds-scale; adding infrastructure before M1 proves a bottleneck would be
premature.

---

## 2. Architecture

Implemented in M0:

```
itf_linker/
  mpc80.py          MPC1992 80-col parser -- scalar + vectorised, pinned against each other
  config.py         paths and public endpoints (no credentials anywhere)
  ingest/
    fetch.py        ITF + ObsCodes + MPEC download; provenance sidecar
    parse.py        streaming gz -> typed Parquet, one row group per batch
  index/
    tracklets.py    local-night index; (desig, obscode, night) grouping
    partition.py    HEALPix assignment; exact pair/triplet combinatorics
  verify/
    mpec.py         MPEC residual tables + 80-col blocks; acceptance gate
    killcheck.py    position-based ITF lookup; sensitivity control
  cli.py            fetch / parse / counts / tracklets / killcheck / partition / m0
```

Added in M1:

```
  snapshot.py       ITF snapshot archive: obs keys, delta chain, diffing
  fit/
    wsl.py          Windows <-> WSL path translation and subprocess plumbing
    findorb.py      run `fo`; parse elements, sigmas, RMS, covariance, convergence
    mpcfmt.py       emit MPC 80-col (self-test astrometry only)
    extract.py      pull a designation's ORIGINAL 80-col lines out of the snapshot
    candidates.py   bad-data filter; per-designation view; published pre-fit gate
    collide.py      trkSub collision screens + the post-fit subset guard
    gates.py        the MPC's published post-fit criteria
    pipeline.py     the whole funnel, from observations to a ranked list
    verify.py       closed-loop build verification against JPL Horizons
  cli.py            + snapshot / snapshots / snapshot-diff
                    + fit-selftest / candidates / fit / m1
```

Added in M3:

```
  link/
    geometry.py     observer positions, the r/rdot solve, Kepler propagation, elements
    arrows.py       tracklets with a fitted sky-plane rate -- what HelioLinC consumes
    heliolinc.py    hypothesis grid, spatial hashing, cluster extraction, isolation check
    pipeline.py     overlapping windows, merging, cross-observatory ranking
    assemble.py     link gating; 80-col astrometry relabelled to one id per link
    run.py          the M3 chain: link -> gate -> fit -> gate -> resolve -> rank
    validate.py     the hidden-trkSub ground truth: recall and precision
  cli.py            + link / link-validate / link-fit / m3
```

Added in M4:

```
  link/
    populations.py  re-link real NEOs/Centaurs/TNOs from Horizons astrometry alone
    pipeline.py     + Band: one hypothesis grid per distance range, each with the window
                      its own curvature permits (curvature_window_days)
    heliolinc.py    + geometric grids, the near root below 1 AU, per-band max(a),
                      indexed drop_subsets, hashed isolation check
  fit/
    classify.py     dynamical population from the fitted elements; NEO score (not digest2)
  cli.py            + link-populations; --bands on link / link-validate / m3;
                    + link-fit --completed-only
```

Added in M5:

```
  link/
    priority.py     the fitting order: cross-observatory tier, then a logistic survival
                      score fitted to M4's own 4,461 outcomes (M4's order was worse than
                      shuffling the queue)
    assemble.py     + LineIndex: one gz pass shared by every batch
    run.py          + FitBatch / plan_batches / fit_links_batched / merge_checkpoints:
                      per-batch JSON checkpoints, global conflict resolution on merge
  fit/
    findorb.py      + scratch_dir: run fo on the Linux filesystem, copy back the three
                      files this codebase reads (9x on Windows; identical answers)
  cli.py            + link-fit-all, link-vet-extract
```

Not implemented, gated behind milestones:

```
  report/   human-review packet -- the mandatory approval surface    (M6+)
  submit/   ADES PSV/XML emit; sandbox-first                         (M6+)
```

---

## 3. Milestones

### M0 — kill-check ✅ **COMPLETE** (2026-07-29)

Parse the ITF, reproduce the measured counts, reconstruct tracklets, replay three published
identification MPECs.

**Outcome: GO WITH CHANGES.** Counts reproduce to within 0.01%; 2,628,838 tracklets built;
60 tests green. **The plan's chosen validation was found to be untestable as specified** —
all three reference MPECs link previously-*designated* objects whose observations were never
in the ITF (which contains zero designated and zero numbered objects). Parser and grouping
were validated end-to-end on real MPEC astrometry instead. Full detail in `M0-RESULTS.md`.

### M1 — fit ✅ **COMPLETE** (2026-07-29)

**Outcome: GO.** Full detail in [`M1-RESULTS.md`](M1-RESULTS.md).

Find_Orb built under WSL and verified end-to-end against JPL Horizons (11/12 cases; clean
49-day arcs recover `a` to 7 × 10⁻⁸ relative). 2,515 multi-night designations → 1,120 past
the MPC's published pre-fit gate → 979 past the trkSub collision screen → 975 fitted in
4.5 minutes → **917 converged, 128 pass every published post-fit gate, 99 of those are also
numerically well-constrained.**

**These are designations with acceptable orbit fits, not discoveries** — one submitted
designation came back identified as comet 73P-C, and 100 of the 128 are Rubin (X05) alone.
Catalogue cross-matching is M2.

Two findings that shape M2:
- **σ(q) < 0.05 AU is the binding gate**, met by only 149 of 862 three-night fits (17%).
- **The MPC's published post-fit criteria are not sufficient alone.** The σ limits apply
  only to *exactly* three-night links, so a 5-night fit with σ(a) = 8,173 AU passes on RMS;
  and RMS says nothing about how many observations were used, so a collision that fits a
  6-of-24 subset passes too. Both holes are closed by extra checks labelled as ours.

Not done in M1: any linking, any vetting, any submission code.

### M1 — original entry conditions (all met)

**Entry conditions from M0, all mandatory:**

1. **New ground-truth control.** Hide the trkSub linkage on the 2,515 designations that
   already span 3+ nights in the ITF; confirm the linker rediscovers them from positions and
   epochs alone. Begin archiving daily ITF snapshots for the snapshot-diff control.
2. **Architect around pairs, never triplets** — 10⁷ vs 10¹¹ candidates. Pair → preliminary
   orbit → predict third night → targeted lookup (FindPOTATOs), or hypothesis-propagation
   clustering (HelioLinC).
3. **Sandbox = the recent slice** (MJD > 60000): 512,106 tracklets, 1.3M pairs at
   nside=64 / 15 d, and follow-up still physically possible.
4. **Filter known bad data**: 4 pre-1900 sentinel epochs, 1,282 unpaired `S` observations,
   3 blank designations, 1 malformed record.

**Cheapest first win, ahead of any linking:** 1,046 designations already span 3+ nights and
pass the MPC's night/arc/≥2-per-night gates (976 single-observatory, median arc 7 d). These
need *fitting*, not linking — but each must be checked for trkSub collision first
(`des278`, `soho183` are reused names, not objects).

Then: Find_Orb wrapper, published acceptance criteria applied, ranked candidate list.
**Success metric: ≥1 candidate surviving every published gate and every catalogue cross-check.**
Half met: 128 survive every published gate; the catalogue cross-check is M2.

### M2 — vetting ✅ **COMPLETE** (2026-07-31)

MPChecker / SkyBoT / SBIDENT / SBDB integration and the acceptance gate that makes
submission safe. **7/7 positive controls pass in the same run that produced the numbers**,
including a known comet sitting in the ITF identified by a completely independent route.
Of M1's 128: 114 unmatched, 10 ambiguous, 4 known — and 91 of the 128 carry the Rubin `RL`
prefix, which is the composition warning that shaped M3. Detail in `M2-RESULTS.md`.

### M3 — linking ✅ **COMPLETE** (2026-08-02)

**Renumbered from the original plan.** The plan's M3 was submission; vetting proved to be
the binding constraint and took the M2 slot, so linking — the milestone the whole project
is named after — became M3, and submission moved to M4+. Nothing was submitted.

HelioLinC over the MJD > 60000 slice, ranked cross-observatory first. Validated by hiding
the trkSub linkage on the designations that already span 3+ nights: **87.4% are re-derived
to the exact tracklet** from positions and epochs alone (75.8% embedded in the full
population).

Funnel: 511,274 arrows → **17,060 links** proposed in 3.5 minutes → 13,618 past the MPC's
pre-fit gate → fitted with Find_Orb in 55 minutes → **199 survivors, 73 cross-observatory**.
The orbit fit rejects 98.5% of proposals, and M1's subset guard alone rejects 74% of
converged fits (against 6% on survey-made associations).

⚠️ **Two of the first 30 cross-observatory links vetted resolve to the designated minor
planets 2026 OB4 and 2026 DK65** at 0.5–0.7″ across all three epochs. The links are real
objects; that is also why 26 unmatched is not 26 discoveries. Detail in `M3-RESULTS.md`.

### M4 — widening the distance grid, and the older 80% of the file ✅ **COMPLETE** (2026-08-05)

**Renumbered again.** The plan's M4 was the citable artifact; M3's own assessment named
three concrete improvements instead, and the top two — widen the 1.4–5.6 AU grid, and run
the 2.1M tracklets predating MJD 60000 — became M4. Publication moves to M5. Nothing was
submitted.

Four distance bands spanning **0.55–50 AU** (2,555 hypotheses against M3's 387), each swept
with the window its own orbital curvature permits — 5 days at 0.55 AU, 21 at 5.6 — plus the
*near* root of the line-of-sight/sphere intersection, which is half the physically valid
states inside 1 AU and which M3's solver could not express. Widening was **seven** changes,
six of them found by measurement after the obvious one.

Validated three ways: the `belt` band reproduces M3 to the digit after four rewrites
underneath it; hidden-trkSub recall **rises 0.8735 → 0.9302**; and against JPL Horizons the
widened grid re-derives **11 of 13** real objects across every class against **4 of 13** for
M3's grid, with none merged into a neighbour. It recovers comet **73P-C**, which
`M3-RESULTS.md` states in print cannot be found.

It also ran the pre-60000 slice, which proposes **412,929 gated links to the new slice's
40,623** and whose survivors are **94% cross-observatory** against 36% — and which handed
back **comet 29P/Schwassmann-Wachmann 1** from four 2002 tracklets across two telescopes,
matched to 1.2″ and agreeing with JPL's orbit to 1.3σ. Combined yield: **331 survivors, 180
cross-observatory**; of 30 vetted, **3 are already-catalogued objects**.

⚠️ **The NEO-distance bands produced no near-Earth candidate.** They fitted **5,547
converged near-Earth orbits** (147 Aten, 3,688 Apollo, 1,712 Amor) and all but two were
rejected by the gates — M1's subset guard alone rejects **84.4%** of converged fits here,
against 74% in M3 and 6% on survey-made associations. The two NEO-class survivors are Amors
that M3's own grid already reached; the orbit classifier M4 added is what found them, not
the distances. Detail in `M4-RESULTS.md`.

### M5 — finishing the older slice ✅ **COMPLETE** (2026-08-06)

**Renumbered again.** The plan's M5 was the citable artifact; M4's own assessment named
finishing the pre-60000 slice — 99% unfitted, and where the cross-observatory candidates
are — as the next step instead. Publication moves to M6. Nothing was submitted.

**412,929 of 412,929 gated links fitted, 1.08% → 100%, in 4 h 24 min.** No re-linking: the
proposals, the grid and every gate are M4's, and M4's own 4,461 links come back through the
new batching machinery with all nine of its headline numbers unchanged.

Three things made it finishable. A fitting order derived from M4's outcomes rather than
argued from value — M4's put **none** of its survivors in the first 10% of its own queue
and was worse than a random shuffle; the replacement puts **58%** there. Per-batch JSON
checkpoints plus chunk-level `--resume`, so an interruption loses only work in flight.
And running `fo` on the Linux filesystem instead of `/mnt/c`, which took one measured
40-link chunk from **437 s to 47 s** with identical gate outcomes.

⚠️ **The headline is a negative result.** Fitting 92× more links than M4 produced **zero
additional cross-observatory candidates** past the sixth batch. The cross-survey pool on
the pre-2023 ITF is **213 survivors**, M4's 1% sample already held 96, and ~400,000 further
links held none. Of 3,190 survivors, **2,977 are one observatory's own unlinked residue**
(2,147 Palomar 2005–2006); of **1,850 formally-NEO survivors exactly two are
cross-observatory**, from 47,190 converged near-Earth orbits; no TNO survivor has a
determined orbit. M1's subset guard rejects **77.3%** of converged fits here — a fourth
replication, and it exposes M4's 50.3% as a sampling artefact. Detail in `M5-RESULTS.md`.

### M6 — the citable artifact

Publish the triage layer: a versioned, DOI'd dataset of *"linkable structure in the current
ITF"* plus the pipeline. **RNAAS** fits exactly (≤1,500 words, one figure or table, $0,
~72 h, ADS-indexed, "Independent Researcher" accepted).

---

## 4. Open questions for Matthew

**Answered in M1:**

1. ~~**Find_Orb on Windows.**~~ Confirmed: no supported Windows build (the project's own
   README says so). Built under WSL, driven from Windows through `fit/wsl.py`, verified
   against JPL Horizons. Steps in [`DATA-SOURCES.md` §4](DATA-SOURCES.md).
2. ~~**Snapshot archiving.**~~ Shipped. Baseline plus permanent kilobyte-scale delta chain,
   with a rolling window of full key sets — not 135 MB/day. Today's pull is snapshot #1.
3. ~~**The 3+-night population.**~~ Done, and the collision worry was justified: 141 of the
   1,120 gated designations are name-reuse suspects, and the "implausible sky motion"
   heuristic misses **both** of the examples M0 named.

**Still open:**

4. **SARC contact.** Required before any archival submission (M3), and for DAD/DECam that
   means Tyler Linder. Not urgent, but the lead time is unknown.
5. **How hard to push M2's cross-match?** 100 of M1's 128 passing designations are Rubin
   (X05) alone. Rubin may well have linked them internally already, in which case the
   productive pool is the *other* 28 and the cross-archive slice the plan always argued
   for. Worth checking before building a full vetting stack around the wrong population.
6. **What to do with the 2-night population** (19,287 designations). They need exactly one
   more night, and a 2-night arc constrains where to look — a far better-conditioned
   search than blind 3-way linking, and now that fitting is cheap it is testable.

---

## 5. Cost

**$0.** One 135 MB download per refresh, local compute, free submission endpoint. M0's
measured figures — 6 s fetch, 9 s parse, 189 MB on disk — leave the portfolio's
zero-marginal-cost rule intact with no asterisk.
