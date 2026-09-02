# M14 — The anatomy accounting gate failed; all later diagnostics are exploratory

**Date:** 2026-09-02 · **Status: STOPPED AT THE PROSPECTIVE INTERNAL PLAN'S INPUT
GATE; POST-STOP FIT DIAGNOSTIC BOUNDED 0–2/100 AND NONINFERENTIAL** ·
**ITF universe:** frozen archive generation `20260902T062614Z` · **Nothing was
submitted, published, emailed, or exposed. No candidate queue was opened.** The full
identifier-bearing run remains below gitignored `data/m14/`; this document contains only
aggregate counts.

## One-line result

The two canonical files and their bytes are authentic, but the August 19 anatomy has
**two observations with neither `provid` nor `permid`**. Its numbered and unnumbered
counts therefore do not close to the file total. The frozen plan says any accounting
residue stops the run, so the valid M14 result is a **procedural STOP at anatomy**. The
sweep and fits that were mistakenly run afterward are retained only as post-stop
engineering diagnostics, not as plan-conforming discovery evidence.

Those diagnostics exposed a second blocker: the residual selector mixed nearby published
observations into 58/100 fitted tracklets and produced two impossible used-above-total
counts. Exact cross-accounting bounds the corrected post-stop diagnostic at **0–2/100**:
98 rows are definite failures and only the two strict, above-total rows are usage-HOLD.
That range is below the plan's 20/100 continuation floor, but it remains noninferential
because fitting occurred after the anatomy STOP. No candidate queue was opened and M14
supports no formal discovery or no-attribution claim.

## 1. Prospective internal plan and post-run proof audit

[`M14-PLAN.md`](M14-PLAN.md) records that it was written before either Parquet was
downloaded or inspected, but it was neither independently timestamped nor committed before
the outcome. It is therefore a prospectively written internal plan, not an independently
verifiable preregistration. It specified the exact objects, anatomy-first order, U ≤ 6 and 0–15 year bounds, unchanged M8
gate, half-period decoy, prior-ledger alias/link deduplication, 100-fit tranches, 20/100
floor, 400-fit hard cap, 90-minute cap, and private-output boundary.

### Rubin aggregates

| canonical date | GCS generation | bytes | SHA-256 |
|---|---:|---:|---|
| 2026-08-19 | `1787251804470701` | 218,128,899 | `197ad29f0876bbf710f4c3d7f97fb1f1e7a8247dea0220c9700b444396fe1193` |
| 2026-08-24 | `1787684133561106` | 112,384,392 | `eafe99e8121b99f5ea732718e5b48f50d7217fb3435b7eac18859ff86f653704` |

Each local file matched its exact generation, byte count, GCS MD5, ETag and CRC32C
metadata, plus the independent SHA-256 above. No `parquet_generations` shard or approximate
path was accepted.

### Orbit and ITF inputs

- MPCORB: 181,503,061 bytes, server `Last-Modified` 2026-09-02 15:24:54 UTC—strictly
  later than both GCS generation updates—ETag `"ad18455-65a81a31e58f5"`, SHA-256
  `a3b939283f5fc3e119d69759d5490ccfe81309740a63b9fd0341b163884a8f67`.
- ITF raw: 132,378,942 bytes, SHA-256
  `a6e5fb21875fcd686a64941658f180f5fce38c13058debcdf968f7f02d5473b1`.
- Full reparse: 9,132,950 observations, 185,906,567 bytes, SHA-256
  `679f11cc76787e700f158aa10ba0efadf842057d6cd1b6c02098259376a02bec`.
- Frozen raw/full/parser fingerprint:
  `33db1c004b36430dc2ff50a9190d0e67b9dea9ed02521d4cf10c702d15313f61`.
- Recorded M14 sweep/fit contract fingerprint:
  `29051841a7c1c876115daa808d1d5d584d220190ec13b243b47deee5403f25fa`.
- The archived replay map contains the eight source files named by that fingerprint plus
  a copy of the plan. The plan copy was archival only and was not itself bound by the run
  fingerprint.

The recorded contract was **not complete**. `m14_attribution.py` also used the M7 tracklet
loader, the observatory-code fetch/cache implementation, and the cached observatory table,
but their bytes were omitted. A post-run audit found these exact tracked bytes:

| effective input omitted from the run fingerprint | bytes | post-run SHA-256 |
|---|---:|---|
| `scripts/m7_attribution.py` | 24,938 | `1b75a61ce65cd3c3d57fd79f96f687ac996f2b6792a2c4ee6578a7a676008c6d` |
| `src/itf_linker/ingest/fetch.py` | 8,272 | `b002b5b7b351b3716e41456db2605797cf4b6a3b6d4e1d3bf1e97fae306a0164` |
| `data/raw/ObsCodes.html` | 150,793 | `db5a7cd013245585b26989394479cadfee0a8dfd116ac504ac2154ad32ce8377` |

The run-local archived internal-plan copy has SHA-256
`c1cefb3fc416cded921b5ec67e47277f0cf1c093e1ecd03285bba74a66cd90f9`.
It was copied after execution and supplies no independent pre-run timestamp. These hashes
document what was present; they cannot retroactively create a preregistration proof. The
M14 runner is now retired so neither this incomplete contract nor the broken
usage counter can be reused for a new snapshot.

The version-3 post-run counts audit also records, in tracked code, the exact SHA-256 of
the preserved attribution report (`3925d644…dc304b`) and fit checkpoint
(`98410b06…fe20d2`), and requires the first audit summary to reproduce those hashes plus
the frozen-input and run fingerprints. This prevents a coordinated later edit of both
run files from silently changing the diagnostic. It is explicitly a post-run preservation
anchor, not pre-run provenance, and therefore does not change the procedural STOP.

The full Parquet was regenerated from the archived raw file. It was not copied from the
mutable daily developer path. Find_Orb line extraction used that same frozen raw file.

## 2. Anatomy first: the plan-specified input gate fails

| | 2026-08-19 | 2026-08-24 | combined |
|---|---:|---:|---:|
| observations | 865,798 | 446,487 | **1,312,285** |
| numbered observations | 855,934 | 432,922 | **1,288,856** |
| unnumbered observations | 9,862 | 13,565 | **23,427** |
| **unclassified (no `provid`)** | **2** | **0** | **2** |
| distinct unnumbered objects | 403 | 701 | **1,104** |
| discovery `*` | **0** | **0** | **0** |
| previously covered objects | 12 | 23 | **35** |

The two missing-designation rows make the August 19 accounting
`855,934 + 9,862 + 2 = 865,798`. Because the original implementation silently counted
only rows with a nonempty `provid`, it did not enforce the plan's explicit residue stop.
The plan-conforming M14 analysis ends here. The implementation now rejects even one such row.

Among the classified rows, the first aggregate's designations are entirely 2000–2003; the second's are entirely
2000 and 2003–2005. Both carry observation times from 2025-04-22 through 2026-01-05,
despite their August creation dates. This is the same lesson M9 established: a new large
bucket object can be a delayed database operation, not new Rubin discoveries.

The fresh corpus scanned 1,562,078 records and resolved all 1,104 requested aliases with
no `get-orb` fallback. Current primary/alias collapse still left 1,104 unique orbits. The
quality distribution was 923 U=0, 110 U=1, 21 U=2, 15 U=3, 31 U=4, 3 U=5, and 1 U=6, so
all had reported U ≤ 6. A deterministic U-stratified 24-orbit comparison
against live `get-orb` resolved 24/24: median state residual 7.75×10⁻⁷ AU, 95th percentile
6.84×10⁻⁶ AU, maximum 9.68×10⁻⁶ AU. All verification gates passed.

## 3. Post-stop exploratory real/decoy sweep

Everything in this section occurred after the mandatory anatomy STOP. The counts are
preserved to diagnose the pipeline, but they are not a valid plan-conforming comparison and
cannot support a discovery or no-discovery conclusion.

The sweep covered 1,995,488 tracklets on 5,126 nights with M8's measured perturbed
0–15 year gate unchanged.

| separation | real | half-period decoy |
|---|---:|---:|
| < 5″ | 3 | 1 |
| 5–15″ | 9 | 4 |
| 15–30″ | 8 | 16 |
| 30–60″ | 44 | 45 |
| 60–120″ | 172 | 203 |
| 120–300″ | 281 | 329 |
| ≥ 300″ | 0 | 2 |
| **all** | **517** | **600** |

Real matches involved 352 orbits; decoy matches involved 367. The real median separation
was 126.6″ and 461/517 lay beyond four years. Per authenticated input, the real arm held
167 matches from August 19 and 350 from August 24.

All four prior ledgers were fingerprinted before the sweep. Alias-aware `(orbit,
link_key)` deduplication removed **0** exact prior pairs. Five same-tracklet/different-orbit
collisions were retained and labelled rather than hidden; one occurred in the fitted
prefix. No conclusion is drawn from those unresolved alternatives.

The 12-vs-5 real excess below 15″ reverses 8-vs-16 in the 15–30″ bin and the full decoy is
larger. Because this sweep occurred after the anatomy STOP, none of those differences is a
plan-conforming decision statistic.

## 4. Post-stop fit diagnostic: bounded 0–2/100, noninferential

The first 100 ranked pairs took 458 seconds:

| check | count |
|---|---:|
| completed | 100 |
| converged | 99 |
| strict joint-fit gate passed | 67 |
| tracklet fully used under the original counter | 1 |
| **strict and fully used** | **0** |

The historical implementation recorded **0/100** and therefore did not start a second
tranche. That exact zero is not reliable, but the defect's effect is bounded. Of 67 strict
fits, 65 used fewer appended observations than the tracklet total and remain definite
failures; the other two reported impossible above-total usage and are HOLD. The 33
non-strict fits cannot pass the unchanged combined gate. The corrected diagnostic is
therefore **0–2/100**, still below 20/100. No inferential claim is made because all 100
fits occurred after the mandatory anatomy STOP.

## 5. The counts-only usage audit

The unexpected diagnostic was impossible usage: two fits reported more used “tracklet”
residuals than the reparsed tracklet contained. [`scripts/m14_fit_audit.py`](scripts/m14_fit_audit.py)
reopened no network connection and emitted no identifiers. It reproduced every tracklet
from the frozen raw ITF and verified 100 fit-to-cache associations across 92 unique,
content-bound published-astrometry cache files.

| audit result | count |
|---|---:|
| exact published duplicates at 2 s / 2″ | 0 full · 0 partial · 100 none |
| published rows inside M8 residual-selector station/JD window | **58** |
| residual count exceeded actual tracklet size | **58** |
| used count below / equal / above actual size | 97 / 1 / **2** |
| fit's stored total disagreed with reparsed total | 0 |
| strict + fully used with no published overlap | **0** |
| definite post-stop diagnostic failures / usage-HOLD | **98 / 2** |
| corrected post-stop diagnostic yield bound | **0–2 / 100** |

Root cause: `m8_attribution.joint_fit` relabels both the object's published record and the
appended ITF rows with one seven-character designation. It then identifies “tracklet”
residuals only by observatory and the tracklet's JD range (with ±0.0002 d padding). Nearby
published observations from the same observatory fall into that window and are counted as
if they were appended rows. The two above-total counts prove the selector is not a valid
one-to-one provenance map.

The corruption cannot create a recorded above-total PASS, but it **can create false
FAILs** by inflating or misassigning the used count. Here that uncertainty is confined to
the two strict above-total rows; the other 98 cannot pass the unchanged combined gate.
The resulting 0–2/100 range is a post-stop engineering diagnostic, not a scientific yield.

## 6. Required repair before any new attribution campaign

Do not reinterpret or rerun M14 under changed rules. For a future named milestone:

1. Enforce full anatomy accounting against total rows; missing/blank designations are a
   fatal residue, not an implicit third class.
2. Bind every effective source and data dependency before execution, including the plan,
   tracklet loader, observatory loader, and exact observatory-code bytes.
3. Before fitting, reject exact published duplicates as already linked.
4. Preserve an identity for every appended observation—JD, observatory, observed RA/Dec,
   note fields, and input multiplicity—and match Find_Orb residual rows one-to-one to that
   multiset. Station plus a time interval is insufficient.
5. Require every appended row to map at most once, `0 ≤ used ≤ appended_total`, and an
   explicit HOLD if a residual cannot be assigned unambiguously.
6. Add regression fixtures for:
   - a nearby published row at the same station/time but different coordinates;
   - an exact already-published duplicate;
   - repeated equal-time observations and one-to-one multiset consumption;
   - an unmatched residual that must HOLD;
   - the invariant that used count can never exceed appended count.
7. Recalibrate the fit-yield stopping rule only in a separately preregistered future run after
   the counter is repaired. M14's recorded 0/100 and corrected 0–2/100 bound remain
   historical diagnostics, not scientific results.

## 7. Decision

**STOP/HOLD this batch campaign at the anatomy gate.** The authentic files can inform
future input monitoring, but M14 does not establish a real/decoy result or a fit yield.
The active M14 attribution runner is retired. A future canonical aggregate may proceed
only under a new named preregistration after both the accounting/provenance contract and
the observation-identity matcher are repaired.

No candidate identifiers appear in this result, no review queue or M13 payload was built,
and no MPC/TNS submission, repository push, release, or publication occurred.
