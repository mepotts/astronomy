# ITF linker — mining the MPC's Isolated Tracklet File for unlinked minor planets

**One-liner:** Download the MPC's public file of ~9.4 million observations that no pipeline ever linked
to an orbit, link tracklets across nights into gravitationally valid orbits, vet them hard, and submit
the survivors to the MPC's identifications endpoint — which credits successful linkers **by name** in
an MPEC.

**Scores (U/B/E):** U **2/5** (this is *not* white space — individuals are actively doing it and getting
credited weekly; the barrier is engineering effort, not novelty) · B **5/5** (pure computation over a
135 MB text file; no telescope, no data rights, no gated archive, no ML required) · E **5/5** (the output
is a formal IAU-recognized designation with your name attached — the only item in this repo that produces
a discovery rather than a tool)

**Status:** proposed

**Cost to operate: $0** — one 135 MB download, local compute, free submission endpoint. Fits the
portfolio's zero-marginal-cost rule with no asterisk.

---

## Be honest about the wedge

Most plans in [`IDEAS/`](../IDEAS/README.md) argue a translation-layer gap. **This one does not, and it
would be dishonest to pretend otherwise.** The algorithms are published and open source; the data is
public; and at least half a dozen individuals are working the ITF successfully right now. In July 2026
alone, three separate identification MPECs credited private individuals.

So the framing is different: **this is an open, uncrowded, formally-credited field where the binding
constraint is sustained engineering effort against 9.36 million rows.** You are not inventing a method.
You are doing work that demonstrably pays off and that almost nobody has the patience to do at scale.

What *is* genuinely defensible, and worth building toward:

- **Nobody publishes an ITF triage layer.** The file ships as 80-column text with no orbit fits, no
  quality flags, no per-tracklet linkability score. A public, versioned, regularly-regenerated
  *"here is what's tractable in the current ITF"* dataset would be a real contribution — and it is
  exactly the translation-layer shape the rest of this repo is built on.
- **Cross-archive linking is under-exploited.** Individual surveys link their own data. The ITF's value
  is that F51, W84, G96 and T09 tracklets sit in one file and can be linked *to each other*.
- **The DAD overlap.** NOIRLab's `dad_dr2` has 50,163 tracklets never submitted to the MPC, 6,856 of them
  scoring digest2 ≥ 65 (NEO-likely), with MPC-format records pre-generated. That is a second, disjoint
  pool feeding the same submission pipeline.

## Prior art (adversarial check)

- **HelioLinC** (`github.com/lsst-dm/heliolinc2`) — the Rubin-lineage linking algorithm; propagates
  detections to a common epoch in heliocentric space and clusters. Actively maintained, LSST-backed.
- **THOR** (`github.com/moeyensj/thor`) — Tracklet-less Heliocentric Orbit Recovery. Asteroid Institute /
  B612 ran it over NSC DR2 at industrial scale: 8.5M vCPU-hours on Google Cloud, ~27,500 candidates
  announced 2024-04-30. ⚠️ **Only 104 have a confirmed MPC designation** (from a 30-day window announced
  2022-05-31); the fate of the remaining ~27,400 is **unverified** — no update found after April 2024.
- **FindPOTATOs** (Nugent, Tan & Bauer 2025, PSJ 6, 18, arXiv:2501.12922) — written explicitly for
  archival data. Probably the best starting point for a solo build.
- **find-asteroids** (`github.com/stevenstetzler/find-asteroids`, Stetzler et al. 2025, arXiv:2509.26279)
  — shift-and-stack on *detection catalogs* rather than pixels, 10–10³× speedup.
- **Find_Orb** (`projectpluto.com/find_orb.htm`) — the orbit-determination workhorse; what you actually
  fit with.
- **CANFind** (Fasbender & Nidever, arXiv:2109.00088) — 527,055 tracklets from NSC DR1. Note it is a
  **two-author paper**. Existence proof at individual scale.

**Conclusion:** the tooling is mature and free. Nothing here needs to be invented. The build is
integration, vetting discipline, and throughput.

---

## Data sources & access

**Primary input — the ITF.** `https://www.minorplanetcenter.net/iau/ITF/itf.txt.gz`

| Property | Value (measured 2026-07-28) |
|---|---|
| Size | 134,758,290 bytes gzipped |
| Observations | **9,359,693** |
| Observatory codes | 882 |
| Added during 2026 | 248,810 |
| Auth | **None.** No registration, no key |
| Refresh | Regenerated continuously (`Last-Modified` moves daily) |

Top contributing codes: **F51** Pan-STARRS-1 (2.75M) · **W84** DECam (1.20M) · **G96** Catalina (1.08M) ·
**F52** Pan-STARRS-2 (1.04M) · **T09** Subaru (0.87M) · **C51** NEOWISE (69,886) · **X05** Rubin (64,362) ·
**645** SDSS (28,120).

Format is plain MPC1992 80-column, typically three lines per tracklet:

```
     /7239   4C2015 05 23.30928 11 55 25.17 -01 46 36.9          23.7 z1     T09
```

Field positions: cols 1–5 number · 6–12 packed designation · **13 discovery asterisk** · 16–32 UTC
`YYYY MM DD.dddddd` · 33–44 RA · 45–56 Dec · 66–71 mag+band · **78–80 observatory code**.

**Secondary input — MPC's own solicited target lists.**
`https://www.minorplanetcenter.net/mpcops/orbits/no-orbits-astrometry/` publishes observations lacking
orbits, ready for download: `c51_desigs.txt` (440 NEOWISE designations), `c51.obs` / `c51.xml`,
`no_orbit_desigs.obs` (14.6 MB), `no_orbit_desigs.xml` (85.6 MB — includes 19th-century observations).
**The MPC is explicitly asking for this work.**

**Tertiary input — NOIRLab DAD.** `dad_dr2` via anonymous ADQL at `https://datalab.noirlab.edu/tap`.
662,154 tracklets; `movgrp` carries `digest`, `mpcid`, `mpcsent`; `movmpc` holds 2,974,297 MPC-format
records. Coverage 2012-10-24 → 2018-04-20.

**Output — submission.** JSON to
`https://www.minorplanetcenter.net/mpcops/submissions/identifications/`.
Spec: `.../mpcops/documentation/identifications/submission-format/`.
Reference client: `.../static/submissions/media/identifications_api_example.py`.

**Published acceptance criteria** (`.../identifications/additional/`) — ITF-to-ITF links are
auto-rejected if: fewer than 3 distinct nights · arc < 3 days · exactly 3 nights with arc > 15 days ·
arc both starts *and* ends with a single-detection tracklet. After fitting: rejected if RMS > 0.25″ or
non-convergence. Three-night links additionally need σ(a) < 0.05 AU, σ(q) < 0.05 AU, σ(i) < 0.5°,
σ(e) < 0.05.

---

## Guardrails — read before writing any submission code

This project's failure mode is **not** wasted effort. It is **polluting a shared scientific resource**
and burning your own credibility.

1. **Nothing is submitted without explicit per-batch human review.** Automated end-to-end submission is
   out of scope permanently, not just for v1. The MPC tracks submitter reputation; bad batches cause
   *future* reports to be disregarded.
2. **Validate against the sandbox first — always.** `submit_psv_test` / `submit_xml_test` exist for
   exactly this. Never let a first-run pipeline touch the live endpoint.
3. **Contact SARC before any archival submission** (see [README](README.md#sarc--contact-before-you-submit-archival-astrometry)). For DAD/DECam
   that means Tyler Linder; the DAD residue may be knowingly withheld as unvetted.
4. **Duplicate submissions are actively harmful.** Check `mpcid`/`mpcsent` in DAD, and cross-check every
   candidate against MPChecker, SkyBoT and JPL SBIDENT before claiming it is unlinked.
5. **≥2 observations per object per night.** A single position per night causes the *entire batch* to be
   auto-rejected, often silently.
6. **Do not claim cometary activity you have not seen.** MPC's PCCP warns in capitals:
   *"IF YOU DO NOT DETECT CLEAR COMETARY ACTIVITY, DO NOT CLAIM THAT AN OBJECT IS A COMET."*

---

## Architecture sketch

```
itf-linker/
  ingest/     fetch + parse ITF 80-col → typed Arrow/Parquet; incremental by Last-Modified
  index/      spatial+temporal partitioning (HEALPix × night); tracklet reconstruction
  link/       candidate generation (HelioLinC or FindPOTATOs) over partition neighbourhoods
  fit/        Find_Orb wrapper; residual RMS, covariance, digest2 scoring
  vet/        MPChecker / SkyBoT / SBIDENT cross-checks; acceptance-criteria gate; dedupe vs DAD
  report/     human-review packet per candidate batch — the mandatory approval surface
  submit/     ADES PSV/XML emit; sandbox-first; per-batch confirmation required
```

**Stack:** Python + `polars`/`duckdb` over Parquet (the ITF is ~9.4M rows — trivially in-memory once
parsed, but partitioned storage makes the link step tractable). `astropy` for coordinates and time.
Find_Orb as a subprocess. Matches the repo's existing Python-project conventions (`.venv` per project,
pytest, typer CLI).

**Compute realism:** the ITF itself is a laptop-scale problem — 135 MB compressed, ~9.4M rows. The
combinatorics of linking are what cost, and they are controlled by partitioning tightly in space and
time before generating candidates. This is emphatically *not* the 8.5M vCPU-hour regime THOR ran in;
that was pixel-adjacent work over 412,116 images. Linking pre-existing astrometry is cheap.

---

## Milestones

**M0 — ✅ COMPLETE, 2026-07-29. Verdict: GO WITH CHANGES.** Full detail in
[`itf-linker/M0-RESULTS.md`](../itf-linker/M0-RESULTS.md); the build is at [`itf-linker/`](../itf-linker/).

Counts reproduced to within 0.01% (882 observatory codes exact; X05 and 645 exact). Download 6 s,
parse 9.36M lines 9 s, 2,628,838 tracklets — **the laptop-scale premise is confirmed as written**.

⚠️ **The kill-check as originally specified was invalid and has been replaced.** It called for
re-deriving three July 2026 identification MPECs (2026-O40, O57, O86). Those link previously-*designated*
objects, and **the ITF contains zero designated and zero numbered objects** — so their observations were
never in the file. The test could not have passed on any snapshot, on any day. A 200/200 sensitivity
control confirmed the absence was real rather than a lookup failure.

**The correct ground truth is internal to the ITF:** hide the trkSub linkage on the **2,515 designations
that already span 3+ nights** and confirm the linker rediscovers those groupings from positions and epochs
alone. Snapshot diffing (what vanished between two pulls, and which MPEC claimed it) is the natural second
control — **which requires archiving snapshots starting now.**

**Two findings that change M1:**
- **Lines ≠ observations.** Space-based observations occupy two lines (`S` sky position + `s` spacecraft
  x/y/z *in the RA/Dec columns*). C51 NEOWISE measured exactly half the expected count until this was
  handled. True totals: 9,359,688 lines = **9,322,655 observations** + 37,032 continuations + 1 malformed
  record. Any naive line-count parser is silently wrong.
- **Pairs are cheap; triplets are the wall.** At nside=64 × 3-day: **15.4M pairs but 753M triplets**;
  coarser settings reach 10¹¹. Since the MPC requires 3+ nights, **M1 must never enumerate triplets** —
  pair→predict→confirm (FindPOTATOs) or HelioLinC clustering. Non-negotiable.

**M1 — fit first, link second. No submission.**

⭐ **Start with the 1,046, not the 9 million.** M0 found **2,515 ITF designations that already span 3+
nights** under a single trkSub, of which **1,046 pass the MPC's published night/arc/≥2-per-night gates**
(976 single-observatory, median arc 7 days). **These need orbit *fitting*, not linking** — the hard
combinatorial step is already done for them, by the surveys, for free. That is the cheapest possible path
to a first real candidate and it exercises the whole `fit → vet → review` chain before any linking code
exists.
⚠️ **Verify each against trkSub collision first** — trkSubs are *not* globally unique. `des278` spans 17
nights over 1,154 days and `soho183` spans 12 nights over 3,555 days; those are reused names, not objects.

Then linking proper: **pair→predict→confirm** (FindPOTATOs) or HelioLinC over the recommended sandbox —
the **MJD > 60000 slice, 512,106 tracklets, 1.3M pairs**, where follow-up is still physically possible.
Find_Orb for fits; apply the published acceptance criteria.

**Filter the known bad data first:** 4 pre-1900 sentinel epochs, 1,282 unpaired `S` observations, 3 blank
designations, 1 malformed record (obs 947, Dec seconds `39 8` — a real MPC defect, not a parse failure).

Success metric: ≥1 candidate surviving every published gate and every catalogue cross-check.

**Revised effort estimate (M0's actual job):** *a weekend, not a month*, for a first ranked candidate list —
conditional on Find_Orb integration being the only genuinely new component. The combinatorics are **not**
the bottleneck this plan originally worried about. The bottleneck is orbit fitting and vetting discipline,
which is where the guardrails above are already aimed.

**M2 — vetting and the review packet.**
MPChecker/SkyBoT/SBIDENT integration, DAD dedupe, and the human-review report. This is the milestone
that makes submission *safe*, and it ships before any submission code.

**M3 — sandbox submission, then one real batch.**
Round-trip the identifications format against the test endpoint. Then a single small, hand-reviewed
live submission. Ship only after M2 is green.

**M4 — the citable artifact.**
Publish the triage layer: a versioned, DOI'd dataset of *"linkable structure in the current ITF"* plus
the pipeline. **RNAAS** fits the format exactly (≤1,500 words, one figure or table, $0, ~72 h, ADS-indexed,
"Independent Researcher" affiliation accepted). This is where the work becomes citable rather than merely
credited.

---

## What success looks like

A **provisional designation** and an MPEC carrying `Id.` and your name — the same line that read
`Id. A. Lowe` on 2026-07-20. Followed, if the object survives to 4+ oppositions, by **numbering**, at
which point the discoverer may propose a name to the IAU **WGSBN** for 10 years.

Note the discoverer rule (post-2010): the discoverer is *"the observer who made the earliest-reported
observation at the opposition with the earliest-reported second-night observation."* For ITF work you
are typically the **identifier**, not the discoverer — you get the `Id.` credit, not naming rights. Be
clear-eyed about that distinction before setting expectations.

---

## Sources

- ITF: `https://www.minorplanetcenter.net/iau/ITF/itf.txt.gz`
- Identifications submission: `https://www.minorplanetcenter.net/mpcops/submissions/identifications/` ·
  format `.../documentation/identifications/submission-format/` · criteria `.../identifications/additional/`
- Astrometry guide: `https://www.minorplanetcenter.net/iau/info/Astrometry.html` · 80-col spec
  `.../info/OpticalObs.html` · ADES `.../info/ADES.html` · docs hub `https://docs.minorplanetcenter.net`
- SARC: `https://www.minorplanetcenter.net/mpcops/documentation/sarc/`
- Solicited targets: `https://www.minorplanetcenter.net/mpcops/orbits/no-orbits-astrometry/`
- Naming: `https://www.minorplanetcenter.net/iau/info/HowNamed.html` · `https://www.wgsbn-iau.org/`
- ADES reference implementation: `https://github.com/IAU-ADES/ADES-Master`
- DAD: `https://datalab.noirlab.edu/data/dad` · TAP `https://datalab.noirlab.edu/tap`
- RNAAS: `https://journals.aas.org/research-notes/` · submission `https://journals.aas.org/submission`
