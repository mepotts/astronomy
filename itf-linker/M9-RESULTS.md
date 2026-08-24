# M9 — The unconsumed partitions, the queue extended, and the MPC racing the ledger

**Date:** 2026-08-18 · **Status: COMPLETE** · **ITF universe:** the M7/M8 snapshot
(2026-08-16 20:27:01 GMT), exactly reconstructed — see §0.1. **Nothing was submitted
anywhere. Candidates are candidates.** M7's held candidates (2025 PD152 ×2,
2025 MQ241) and every M8 ledger verdict are carried forward untouched;
`m8-ledger.json` was not rewritten — M9 appends (`m9-ledger.json`,
`m9-combined.json`, `m9-adjudication.json`). Tests: 467 green.

**One-line result:** the ground moved underneath the milestone — **the MPC consumed
22,353 ITF observations in the two days since M8, among them 30 of M8's 900 fitted
candidates, and every one went to exactly the object the ledger had attributed it to
(21/21 PASSes, 8/8 of the strict gate's rejections, 1/1 ALREADY_LINKED): the first
external ground truth the chain has ever had, and it agreed completely** — so M9
pinned itself to an exact reconstruction of the 08-16 snapshot (residue 0, §0.1) and
delivered on it: the six unconsumed partitions (one real designation batch plus
bookkeeping; 12,792 net-new objects, 4,288 swept after a 66% U-cut) and the M8 queue
extension (rank 901 → 1,700) together add **272 PASS rows across 258 objects (90%
beyond the old 4-year wall)** under a pre-registered stopping rule that fired exactly
as written in both queues (partition tranches 33 → 19/100; extension tranches
34·23·34·28·38·28·20·19). Combined fits promote **40 of 45** multi-tracklet objects
(arc extensions to +5,107 d, σ_a down 10–10,000×; 33 with zero consumed members) and
demote five for reasons each worth reading (§6); the 88 lost-object ambiguities
adjudicate **87–1 in the candidates' favour** (§7); and the calibration extension
measures the main-belt window openable to ~25 y and the TNO regime at **≤ 0.45″ over
28 years** — where the bounded scoping sweep's 3-vs-0 coarse excess then **fails the
fit chain 0-for-3**, exposing a new pointed-field confound on the way out (§8).

---

## 0. Pre-registered decisions (written before the runs they govern)

### 0.1 The ITF moved under the milestone — pinned snapshot

The daily archive re-pulled the ITF under this repo on 2026-08-18 (15:29:03 GMT).
M8's queue, ledger and coarse counts are statements about the **2026-08-16 20:27:01
GMT** snapshot (9,255,644 observations). Between the two pulls **22,353 observations
left the ITF** (the MPC consuming tracklets — see §5) and 369 appeared.

Every M9 sweep therefore runs on an **exact reconstruction of the 08-16 snapshot**
(`scripts/m9_reconstruct_snapshot.py`): today's full table joined against the
archive's content-addressed `obs_key` set (the key hashes designation, station and
the quantised astrometry, so a key match *is* a content match at 80-column
precision), with every tracklet that lost *any* observation dropped whole and
enumerated (`data/raw/rubin/m9-dropped-tracklets.parquet`). Accounting closed to the
observation: **9,233,291 kept + 22,353 missing = 9,255,644, residue 0**. Tracklets:
**2,606,135 of 2,611,698 named tracklets bit-exact (99.79%)**; 5,563 dropped (5,560
fully consumed, 3 partial). In M8's sweep window the reconstruction holds 2,040,652
tracklets vs M8's 2,045,041 — the deficit of 4,389 is exactly the in-window share of
the dropped set. Nights: 5,298, identical.

**The reconstruction verifies M8's sweep end to end.** Re-run on it (frozen gate,
same orbits), the coarse stage reproduces: real 118,971 vs M8's 119,607 and decoy
128,152 vs 128,602 — deficits fully attributable to the dropped tracklets, with the
decoy's sub-60″ head matching to within 1 count per bin (14/93/263/1124 vs
14/93/264/1125) while the *real* head loses 36 (166/274/457 vs 175/292/466): the
consumed tracklets concentrate in the true-match head, exactly as §5 explains. **All
870 surviving checkpointed fit keys occupy ranks 0–869 of the regenerated queue in
order — zero displacement** — so "M8 rank 901" is the regenerated queue's rank 870,
and the extension resumes with nothing refitted.

### 0.2 Pre-registered stopping rule for both fit queues

Written **before any M9 fit ran**. Applies to (a) the M9 partition fit queue and
(b) the M8 queue extension from rank 901.

1. **Tranches of 100 new fits.** After each tranche, compute the strict+fully-used
   pass rate of the trailing 100 new fits (`tracklet_lines_missing` counts as a
   failure).
2. **Stop when the trailing-100 pass rate drops below 20/100.** Basis: M8's measured
   yield decayed 72/100 (ranks 0–99) → 43/100 (ranks 800–899); the queue is ranked by
   separation/gate, so yield declines with rank; below 20% the marginal fo cost per
   PASS exceeds ~5× the queue-head cost and the tranche signal approaches what the
   decoy prices as chance.
3. **Hard budgets regardless of rate: 1,000 new fits for the M8 extension, 800 for
   the M9 partition queue.** Whichever bound bites first is the reported stopping
   reason.
4. No gate, radius, or rank formula is touched to keep a queue alive (standing
   constraint 5). The rule is implemented *in the fit loop*
   (`--pass-floor-per-100`, default off so M8 behaviour is unchanged), not applied by
   hand.

### 0.3 Orbit file

The **cached 2026-08-16 `mpcorb_extended.json.gz`** is reused deliberately, not
re-pulled: it postdates every unconsumed partition (newest 2026-08-10), and it is the
exact file M8 swept, so M9 candidates are directly comparable. What that choice costs
is measured in §2.

### 0.4 Ambiguity adjudication standard

M8's frozen claimant standard (informative = ephemeris error ≤ 60″) and fit gates,
unchanged. Verdicts: **RESOLVED_TO_CANDIDATE** (every claimant fitted and excluded by
its own astrometry) · **REJECTED** (a claimant owns the tracklet) ·
**STILL_AMBIGUOUS** (a claimant also passes, or cannot be fitted — what cannot be
fitted cannot be excluded) · **RESOLVED_BY_MPC_CONSUMPTION** (reality got there
first, §5). No standard loosened.

## 1. What the six unconsumed partitions actually contain

The watcher flagged four (2026-06-04, -08-03, -08-06, -08-10); the bucket also holds
two smaller ones (2026-06-19, -07-29) above the watcher's own ≥ 1 MB batch rule that
M8 §8 did not name. All six were measured (`scripts/m9_fetch_bulk.py`):

| Partition | bytes | obs | numbered obs | unnumbered objects | discovery `*` | **new vs M8** | dominant desigs |
|---|---:|---:|---:|---:|---:|---:|---|
| 2026-06-04 | 47 MB | 201,428 | 196 | 12,113 | 11 | **11,463** | 2025 (10,959) |
| 2026-06-19 | 3.2 MB | 12,018 | 0 | 418 | 358 | **412** | 2026 (230) |
| 2026-07-29 | 4.4 MB | 16,133 | 0 | 796 | 729 | **796** | 2026 (435) |
| 2026-08-03 | 13 MB | 49,480 | **49,480** | **0** | 0 | 0 | — |
| 2026-08-06 | 13 MB | 49,414 | **49,414** | **0** | 0 | 0 | — |
| 2026-08-10 | 100 MB | 394,836 | **392,551** | 125 | 0 | **123** | 1999 (52), 1995 (34) |

The anatomy matters more than the byte counts: **the "largest partition since
February" (2026-08-10, 100 MB) is 99.4% numbered-asteroid bookkeeping**, and the two
August 13 MB partitions carry *nothing* attribution can use. The real M9 input is the
June-04 designation batch (11,463 net-new 2025-designated objects — the same shape as
February's), the two small partitions' fresh 2026 discoveries (1,208 — so partition
*size* is not a proxy for content in either direction), and August-10's 123
old-provid objects (1995–2000 designations: Rubin recovering ancient
single-opposition objects). Union: **13,450 distinct unnumbered objects, 12,792 new
vs M8** (658 already swept).

## 2. Bulk orbits, and what reusing the 08-16 MPCORB cost

Matching `Principal_desig` *or* `Other_desigs` against the cached MPCORB resolves
**12,097 of 12,792 (94.6%) in 10.9 s**; the 695 misses went through get-orb politely
(1.1 s pacing, ~13 min) and resolved **694** — exactly one object in the six
partitions has no orbit anywhere (**2025 OZ695**). Total: **12,742 orbits**
(m9-orbits.parquet, per-orbit partition membership attached).

**Live verification** (M9 has no cached get-orb reference, so 32 sampled orbits were
fetched live, stratified by U, epoch-bridged with the perturbed integrator):
**29/32 (91%) at element-quantisation level** (median |Δr| = 2.0 × 10⁻⁶ AU); the
worst, 0.041 AU, is **2025 HM95 at U = 9** — a garbage-quality orbit genuinely
*refit* by the MPC since 08-16, not a parse error (a frame error would read 0.1–1 AU
on every row), and the U-cut excludes it from the sweep anyway. That is the measured
cost of pinning the orbit file: near-zero for sweepable orbits.

**The U-cut is brutal on a fresh designation batch: 8,454 of 12,742 (66%) carry
U 7–9** (M8: 48%; M7: 12% — the newer the batch, the shorter the arcs). **Swept:
4,288** (U ≤ 6; histogram 0:1220 · 1:690 · 2:712 · 3:654 · 4:380 · 5:269 · 6:363),
of which 4,010 from June-04, 75/81 from the small partitions, 123 from August-10.

## 3. The sweep, and a decoy that flips sides

**4,288 orbits × 2,040,652 tracklets (5,298 nights) in 75.5 s** (both sweeps), frozen
M8 gate, |Δt| ≤ 15 y:

| | real | decoy |
|---|---:|---:|
| Coarse matches | **14,256** | 12,108 |
| Orbits with ≥ 1 match | 1,748 | 1,747 |
| [0″, 5″) | **26** | 2 |
| [5″, 15″) | **39** | 22 |
| [15″, 30″) | **58** | 58 |
| [30″, 60″) | 212 | 221 |
| ≥ 60″ | 13,921 | 11,805 |
| median separation | 1,048″ | 965″ |
| beyond M7's 4-y wall | 13,691 (96%) | — |

Two readings. First, the sub-15″ head carries the real signal again: **65 real vs 24
decoy (13× at < 5″, the same ratio as M8)** — small in absolute terms because 4,288
young orbits are simply fewer than 22,636. Second, the *aggregate* decoy sits 15%
**below** the real count where M8's sat 7.5% above: the phase-shifted twin samples
different sky against the survey footprints, and the direction of that sampling error
is population-dependent. Neither aggregate direction matters — the decoy's job is to
price the head, and in both milestones the head excess is unmistakable.

## 4. Two fit queues, one pre-registered rule

### 4.1 The M9 partition queue

Ranked by separation/gate as always. **The rule fired at the first opportunity it
could: tranche pass rates 33/100 then 19/100 → stopped at 200 fits**
(`trailing_100_pass_rate(19)_below_floor(20)`), 3.11 s per fit (the obs80 cache and
fo config amortise). Budget unused: 600 of the 800 never ran, and that is the point
of a written rule — the M9 queue's head is 6× shallower than M8's (123 sub-30″
candidates vs 933) and the rule measured exactly that.

**Yield: 52 PASS-grade fits (strict + fully-used) across 52 distinct objects, 49 of
them (94%) beyond the 4-year two-body wall.** Cross-survey, as this pool always is:
F51 (35) · F52 (6) · W84 DECam (4) · G96 (4) · T09 Subaru (2) · V00 (1). By
partition: 51 from June-04, 1 from July-29. Deepest:

| object | tracklet | Δt | sep | joint RMS |
|---|---|---:|---:|---:|
| 2025 LY5 | `P100WnH` F51 | **−14.85 y** | 71.8″ | 0.102″ |
| 2025 NT380 | `P101uUq` F51 | −14.70 y | 24.4″ | 0.138″ |
| 2025 KU46 | `UFB9EE6` G96 | −13.23 y | 171.9″ | 0.211″ |
| 2025 KC60 | `P109hb3` F51 | −12.53 y | 25.3″ | 0.063″ |
| 2025 OK650 | `N020279` W84 | −12.12 y | 175.1″ | 0.221″ |

The verdict chain (§9) turns these fits into ledger rows; the queue's first-ranked
candidate (2015 HY194 ← `G1sS1pM` at 0.10″) *failed* the fit gates and is exactly the
kind of case the chain exists to catch (§9).

### 4.2 The M8 extension from rank 901

M8's `real_matches` array — the ranked queue — turned out to have been **destroyed by
a latent bug in the resume path** (§10, trap 1): the 08-17 tranche-2 run dropped it
from the final report write. The queue was regenerated on the reconstructed snapshot
(§0.1: bit-compatible, 870/900 keys at ranks 0–869, the missing 30 being the consumed
candidates of §5), the bug fixed, and the extension launched with the rule in-loop:

**The rule stopped it at exactly 800 new fits** — trailing-100 pass rates by tranche:
**34 · 23 · 34 · 28 · 38 · 28 · 20 · 19** → `trailing_100_pass_rate(19)_below_floor(20)`.
Neither the 1,000-fit hard budget nor the time backstop ever bound. Fit-phase
economics: 2,300 s, **2.88 s per fit** (the obs80 cache and fo config directories
were warm from the whole session).

Two readings worth writing down:

* **The deep queue is a plateau, not a cliff.** M8's head decayed 72 → 43 per 100
  over ranks 0–900 and §6 of M8 said the floor had not been reached; the extension
  measures ranks ~900–1,700 at a noisy **~28/100 plateau** (even 38/100 at ranks
  1,300–1,400) before slipping under the floor at ~1,600. The sep/gate ranking stops
  predicting fit survival long before yield dies — deep-rank candidates sit at
  100–200″ of wide gates and still fit cleanly at 0.08–0.23″ RMS.
* **Yield: 224 new strict+fully-used passes across 210 distinct objects, 200 of them
  (89%) beyond the 4-year wall** — cross-survey as ever (F51 122 · W84 DECam 30 ·
  T09 Subaru 27 · F52 22 · G96 11 · V00 7), deepest 2025 MD158 ← `P1044Y9` (F51,
  −13.81 y, RMS 0.086″). Five extension passes land on objects that already hold an
  M8 ledger PASS (new combined-fit pairs), and twelve objects collect 2–3 extension
  passes each (2025 PJ65 and 2025 KQ32 with three apiece) — after the verdict chain
  (§9), the multi-tracklet tier grew by 16 objects and the combined top-up fitted
  them all (§6).

Cumulative fitted coverage of the M8 queue after M9: **1,700 of 119,607 coarse
candidates (1.4%)** — 900 by M8 (30 since consumed), 800 by M9 — with the stopping
rule, not exhaustion, as the boundary.

## 5. The MPC raced the ledger — and confirmed it, 30 for 30

Of the 22,353 observations the MPC consumed between 08-16 and 08-18, **30 of M8's 900
fitted candidates lost their tracklets: 21 ledger PASSes, 8 FAILs, 1 ALREADY_LINKED,
across 20 objects.** The MPC does not announce where a consumed tracklet went — but
the objects' fresh published records do (`scripts/m9_consumed_check.py`, live
get-obs into a separate cache, the ledger's 2 s/2″ duplicate rule):

**All 30 went to exactly the object M8 attributed them to. 21/21 PASSes. 8/8 FAILs.
1/1 ALREADY_LINKED.**

Three things follow, in decreasing order of comfort:

1. **The attribution chain just received its first external ground truth, and agreed
   completely.** The deepest example is the flagship: 2025 OK598 ← `P100OPQ` (F51,
   −14.87 y, M8's deepest PASS) is now *in OK598's published record* — the MPC made
   the identical 15-year link two days after the ledger proposed it. The PD152
   mechanism is not just real; it is being harvested.
2. **The strict gate's rejections were correct attributions.** All 8 consumed FAILs
   (e.g. 2025 NK243's pair, 2025 MC314's pair) were accepted by the MPC into the
   objects M8 matched but the strict gate refused — the first measured count of the
   gate's conservatism against MPC practice, and it lands on the same side as the M4
   acceptance-gate finding (the gate discards rows the MPC's published rule keeps).
3. **The ledger's submission value has a measured decay rate: 3.3% of fitted
   candidates (30 of 900) in two days.** Rubin-era designation batches trigger the MPC's own
   archival sweeps, and those sweeps are eating the same head of the same
   distribution. 461 of M8's 482 PASSes remain unconsumed as of 08-18 — but "the MPC
   would get most of these eventually" is now an observation, not a guess. What the
   MPC's sweep does *not* appear to reach on its own timescale is exactly where the
   remaining value sits: the deep, wide-gate, low-rank candidates and the
   ambiguity-flagged ones.

The three M7 held candidates (PD152 ×2, MQ241) are **not** among the consumed; they
remain live and remain Matthew's.

## 6. Combined fits: the multi-tracklet tier, promoted and cross-examined

`scripts/m9_combined.py`: for each of the M8 ledger's 29 multi-tracklet objects, one
fo fit of the object's full 08-16-era astrometry plus **all** its passing tracklets,
against an object-only baseline. (The 08-16 obs80 cache is load-bearing here: for the
seven objects whose tracklets the MPC just consumed, a *fresh* record would contain
those same observations and the fit would double-count them — §5's flags mark which
objects are now validation-only.)

**28 of 29 reach `combined_pass`** — strict gate, every member tracklet fully used
(the PD152 33/33 pattern at scale). Medians across the tier: **arc extension
+2,240 days** (max **+5,107 d** = 14.0 y, 2025 OK598), **σ_a reduced to 0.025× of
baseline** (best 8×10⁻⁵: three orders of magnitude), joint RMS 0.036″–0.24″. Examples:

| object | trk | arc ext | σ_a ratio | joint RMS | consumed |
|---|---:|---:|---:|---:|---:|
| 2025 OK598 | 3 | **+5,107 d** | ~0 | 0.164″ | 3/3 (validation-only) |
| 2025 MB255 | 2 | +4,695 d | 0.001 | 0.084″ | 0/2 |
| 2026 ED8 | 3 | +4,342 d | 0.033 | 0.079″ | 0/3 |
| 2025 PC147 | 2 | +5,029 d | 0.021 | 0.240″ | 0/2 |
| 2026 EE43 | 2 | +3,952 d | 0.033 | 0.046″ | 0/2 |

**The tier splits by independence, and one object was demoted for it.** The first run
of the member-attribution check matched residuals by station + JD window and got
`obs_used > n_obs` on seven objects — because their "two tracklets" are same-station,
same-night siblings whose windows overlap, and in the extreme case measure **the same
exposures**: 2025 MA287's `P11jYa8`/`P11jYeq` share JDs with positions 0.03–0.16″
apart — two Pan-STARRS reductions of the same photons. Matching per observation by
epoch *and* observed position (the residual records carry RA/Dec) fixed six of the
seven; **2025 MA287 stays `combined_below_gate` with each sibling only 2/3 used — fo
itself refuses the redundant near-duplicates.** Its "mutual corroboration" in the M8
ledger is one detection set counted twice, not two independent detections; the
`distinct_member_nights` / `shared_night_groups` fields now expose that structure on
every tier row so a reviewer can weigh same-night pairs (PD152-style, still genuine)
differently from same-exposure duplicates (MA287-style).

Submission-value split: 22 of the 28 passing objects have at least one unconsumed
member; 6 (OK598, NZ274, OJ589, OZ431, DT39, EA22) are fully consumed = pure
validation.

**Top-up after the M9 ledger landed:** the extension's 220 PASSes grow the tier from
29 to **45 objects** (16 new — twelve with 2–3 extension passes of their own, five
pairing an extension pass with an M8 single). Re-run over all 45
(`--extra-ledgers m9-ledger.json`): **40 combined_pass**, median arc extension
+3,299 d, median σ_a ratio 0.025, **33 of the 40 with zero consumed members — the
full-submission-value core of the whole project**. The five demotions are the joint
fit *outperforming* the single fits as a discriminator, each in a different way:

* 2025 MA287 — the same-exposure duplicate pair (above);
* 2025 OA415 and 2026 DR31 — each member passes *alone*, but jointly fo rejects one
  tracklet whole (0/4 used): the two attributions contradict each other, so at most
  one is real. Mutual corroboration, when actually tested, can also mutually refute;
* 2026 DL59 — three members, only one survives jointly (0/3 · 3/3 · 0/5);
* 2026 EH43 — two same-night DECam siblings, *both* rejected jointly (0/5 · 0/5, RMS
  identical to baseline): fo prefers dropping all ten new observations to bending the
  orbit — likely two detections of something else entirely.

These five stay in the ledger as single-tracklet PASSes with a named
`combined_below_gate` cross-reference; the human should read them as *weakened*, not
strengthened, by their siblings.

## 7. The 88 lost-object ambiguities, adjudicated

`scripts/m9_adjudicate.py` fitted every named claimant against its **own published
astrometry** plus the disputed tracklet — 101 claimant joint fits (102 distinct lost
objects claimed 105 times across the 88 rows; the 3 rows the MPC had already
consumed into their candidates needed no fit), M8's frozen gates, ~35 minutes of fo.

| Adjudication | count | meaning |
|---|---:|---|
| **RESOLVED_TO_CANDIDATE** | **84** | every claimant's own astrometry excludes it (fit fails or tracklet not fully used) |
| RESOLVED_BY_MPC_CONSUMPTION | 3 | 2025 OZ431 ← `P115BlK`, 2025 OK598 ← `2014Mi`, 2025 OD414 ← `P1079FL` — the MPC linked them to the candidates while M9 was being planned (§5) |
| **STILL_AMBIGUOUS** | **1** | see below |
| REJECTED | 0 | no claimant owns any tracklet |

Claimant fits: **100 of 101 excluded** — the blanket-claiming lost objects M8 named
as ambiguities predict nothing when their own data is made to speak, which is what
the 60″ informativeness bar said all along. The M8 PASS verdicts survive adjudication
**87 of 88** with nothing loosened.

The one genuine degeneracy: **2025 HO61 ← `N369955` (W84, −6.9 y)** — the candidate's
joint fit stands at 0.075″, but lost object **2022 UE132** (10 observations, SkyBoT
ephemeris error ~19,907″) *also* fits the tracklet fully used at 0.192″ with both
gates passing. Two orbits can own these five DECam detections; the candidate's fit is
2.6× tighter, but tightness is not the frozen standard, so the row is
STILL_AMBIGUOUS and the call is Matthew's (`m9-adjudication.json`, fit `m9g0003`).

## 8. The 25-year calibration; the TNO window opens and its pool comes up empty

`scripts/m9_calibration.py` extends the M7/M8 Horizons methodology to 28 years on
M8's seven calibrators plus four numbered TNOs — (20000) Varuna, (28978) Ixion,
(50000) Quaoar, (136199) Eris — with the main-belt and TNO envelopes kept strictly
apart. The M8 gate stays frozen; nothing here was applied retroactively.

**Main belt:** the envelope holds ≤ 150″ through 25 years (Themis again the ceiling:
93.7″ @12 y → 149.4″ @18 y → 139.6″ @25 y), then breaks at 28 y (303.8″). Opening the
sweep window to ~25 y is therefore *measured as available* for M10 — at 25 y the
U = 2 gate would sit near 470″, U = 5 near 1,500″ — but it is an M10 decision, not an
M9 retrofit.

**TNO regime — the wall does not exist there:** perturbed error **≤ 0.45″ at 28
years** across all four calibrators (two-body alone stays ≤ ~300″: distant orbits are
nearly Keplerian on these timescales). Attribution error for distant objects is
entirely orbit-quality, not propagation.

**The scoping sweep** (`scripts/m9_tno.py`; 4,743 distant orbits with a ≥ 25 AU and
U ≤ 6, from 7,385 bound distant objects in MPCORB; the M7 slow-northern pool =
5,433 tracklets on the reconstructed snapshot; |Δt| ≤ 28 y; gate = 120″ +
1.5 × TNO envelope + U-runoff; **no fits — scoping only**):

| | real | decoy |
|---|---:|---:|
| coarse matches | **3** | 36 |
| sub-60″ | **3** | 0 |
| sub-300″ | 3 | 1 |
| median sep | 35″ | 2,885″ |

Three real candidates, every one inside 60″ of gates that would admit ~120″+, against
a decoy background whose *closest* of 36 chance matches is 300″ out. All three are
beyond the 4-year wall:

| TNO | a (AU) | tracklet | station | night | Δt | sep |
|---|---:|---|---|---:|---:|---:|
| 2008 CT190 | 53.0 | `LA1140` | 688 | 55921 | −14.5 y | 32.5″ |
| 2004 VV130 | 39.8 | `DT20B11` | T12 | 58879 | −6.4 y | 35.0″ |
| **2011 EZ90** | 41.2 | **`s25473`** | **645 (SDSS)** | **52671 (2003-02)** | **−23.4 y** | 56.1″ |

The third row is the regime this niche was queued for: a **2003 SDSS tracklet**
sitting 56″ from a TNO's 23-year back-prediction.

**All three were then fitted through the standard chain (`scripts/m9_tno_fits.py` —
three fits is bounded scoping, not a campaign), and all three fail it — a clean
negative with a new systematic attached:**

* **2008 CT190 and 2004 VV130 are refuted by their own objects' records.** Both
  objects have *published* same-station observations at the same exposure instants
  (Δt = 0.0 s), ~30″ away from the tracklet positions: the surveys were **following
  these TNOs**, the real objects are the published rows, and the ITF tracklets are
  other detections in the pointed field. That is a measured confound the main-belt
  sweeps never had: **fields pointed at a known object deposit position-correlated
  ITF debris near its prediction, and the phase-shifted decoy cannot price it**
  (a decoy orbit's sky position does not coincide with anyone's pointed fields). Any
  M10 distant-object campaign must screen candidates whose object has a published
  same-station row within the same exposure — a one-line check that would have
  removed both here.
* **2011 EZ90 ← `s25473` is a genuine independent epoch** (no same-station published
  row within a day) — and the joint fit rejects it: fo excludes both 2003
  observations (0/2 used, joint RMS unchanged from baseline). A 2-observation
  tracklet 23 years out cannot bend a 74-observation orbit, and the primary
  discriminator answers no. Not an attribution.

So the slow-northern niche's scoping verdict is: **the measured window is wide open
(0.45″ at 28 y) but the pool contains no fit-grade TNO precovery against today's
distant-object orbits** — three coarse candidates, zero survive, one new confound
named for whoever comes next (`m9-tno-fits.json`).

## 9. Candidate ledger: M9 appends

`scripts/m9_verdicts.py` → `m9-ledger.json`: the M8 verdict chain v2 unchanged (rules
block identical, nothing loosened), run over the 1,000 M9 fits — 200 partition-queue
+ 800 extension (the 870 reused fits already carry M8 ledger verdicts and are
skipped; `m8-ledger.json` itself is untouched, per task law). SkyBoT: 276 automated
cone searches. Every row carries provenance (`M9-partitions` / `M9-extension`) and
`in_itf_20260818` — a freshness bit for the reviewer.

**Of 1,000 fitted: 272 PASS (212 caveat-free) · 725 FAIL · 1 BORDERLINE ·
2 SKYBOT_CONFLICT.**

| Ledger, M9 rows | count | reading |
|---|---:|---|
| **PASS** | **272** | 258 distinct objects; 246 (90%) beyond the 4-y wall; median \|Δt\| ≈ 7 y |
| … M9-partitions | 52 | §4.1's yield, all verdicts survived SkyBoT |
| … M9-extension | 220 | of 224 fit-grade: 2 lost to SkyBoT conflicts, 2 to the duplicate/joint-set checks |
| … lost-object ambiguity flagged | 60 | named, not hidden — the M8-§7 pattern again; adjudication of *these* is an M10 item (M9 adjudicated M8's 88, §7) |
| BORDERLINE | 1 | 2026 AK20 + `P221vsE` at RMS 0.2526″ — the MQ241 pattern (published rule passes, strict misses by 0.003″); the verdict is Matthew's |
| SKYBOT_CONFLICT | 2 | 2025 MO329 (2012 TZ367 at 45″) and 2025 NE216 (2008 RZ46 at 13″) — informative claimants, correctly failed |
| ALREADY_LINKED | 0 | the reconstructed-universe discipline: consumed tracklets never entered the queues |

The cumulative candidate ledger for Matthew now reads: **M8's 482 PASS (21 since
consumed and independently confirmed, §5) + M9's 272 PASS = 733 live PASS rows across
~695 objects**, plus M7's three held rows (PD152 ×2, MQ241 — untouched, still live in
the ITF), one M8 borderline + one M9 borderline, and the multi-tracklet tier of §6.
The queue's first-ranked M9 candidate (2015 HY194 ← `G1sS1pM` at 0.10″) is in the
FAIL rows — its joint fit refused the tracklet despite the sub-arcsecond coarse match
— which is the chain doing exactly what it is for: separation alone, however small,
is not an attribution.

## 10. Traps hit (all paid for; check before touching this code)

1. **M8's resume path destroyed the ranked queue.** The tranche-2 resume run rebuilt
   its report dict without re-adding `real_matches`, so the final write silently
   dropped the 119,607-row queue — discovered only when M9 tried to resume from rank
   901. Fixed in `m8_attribution.py` (the resume branch now carries the queue
   forward); the queue itself was regenerated bit-compatibly from the reconstructed
   snapshot. A checkpoint file is not a substitute for the artifact it indexes.
2. **The daily archive re-pulls the ITF under this repo.** `data/parquet/
   itf_observations.parquet` is *not* "the snapshot the last milestone used" — it is
   whatever the archive last wrote. Any resumed or comparative work must pin its
   snapshot explicitly; the archive's content-addressed `obs_key` tables make exact
   reconstruction possible (`scripts/m9_reconstruct_snapshot.py`), which is the only
   reason M9's numbers are comparable to M8's at all.
3. **Same-station siblings break JD-window residual attribution.** Two tracklets from
   one station and night — and in Pan-STARRS pairs, the same *exposures* with
   near-duplicate astrometry 0.03–0.16″ apart — overlap any obscode+JD window. Match
   residual rows per observation by epoch *and* observed RA/Dec (fo's residual
   records carry both), one row per observation. The first combined-fit run
   mis-reported 7 of 29 objects because of this.
4. **Partition size says nothing about attribution content.** The 100 MB "largest
   since February" partition is 99.4% numbered-object rows (123 usable objects); two
   13 MB partitions contain literally zero unnumbered objects; a 3.2 MB one carries
   412 new discoveries. Measure `permid`/`provid`, never bytes.
5. **get-obs freshness cuts both ways.** The consumed-candidate check *requires*
   fresh records (the evidence is their newly-added rows); the combined fits *forbid*
   them (a consumed tracklet would be double-counted). Two cache directories
   (`obs80/` era-pinned, `obs80-m9fresh/`), never one.
6. **A fresh designation batch is mostly unsweepable.** 66% of the June-04 batch
   carries U 7–9 against M8's 48% and M7's 12% — the younger the batch, the more the
   U-cut removes. Plan fit budgets on the *swept* count, not the object count.

## 11. Tests

**467 passed** (the full suite, twice: before any M9 change and after everything),
ruff clean across `src` and `scripts`. M9 added no library code — everything new is
milestone scripts — and the two `m8_attribution.py` changes (the resume-path fix and
the optional `--itf-parquet` / `--max-new-fits` / `--pass-floor-per-100` arguments)
leave every default behaviour byte-identical, which the regenerated-sweep
reproduction of §0.1 tested at production scale far harder than a unit test could.

## 12. Recommended next milestone (M10)

1. **Matthew's ledger review, now with a clock on it.** §5 measured the decay:
   the MPC's own sweeps consumed 21 of 482 PASSes within two days of M8. The
   461 + 52 live PASSes — led by the 22 unconsumed `combined_pass` objects, whose
   joint fits are the strongest single artifacts this project has produced — lose
   value at a measured rate. A submission decision (or an explicit decision not to)
   is worth more than any further widening.
2. **The distant-object niche, if pursued, needs the pointed-field screen first**
   (§8: all three scoping candidates failed the fit chain, two of them because the
   survey was following the object itself). An all-sky distant sweep costs ~2 minutes
   and the 28-y window is measured — but add the same-instant-same-station screen
   before ranking, or the queue head will be pointed-field debris again.
3. **Open the main-belt window to 25 y** using the M9 envelope (measured, §8), re-run
   the M8+M9 orbit sets over the 15–25 y shell only (the 0–15 y shell is done), and
   price it with the decoy.
4. **Adjudicate the 60 new lost-object ambiguities** on M9's PASS rows the way M9
   adjudicated M8's 88 (§7) — `scripts/m9_adjudicate.py --extra-ledgers
   m9-ledger.json` is already wired for it; expect ~1 h of fo and, on M9's evidence,
   nearly all to resolve to the candidates.
5. **Consume the next partitions with the anatomy check first** (trap 4): the watcher
   still runs unscheduled; wiring it to a schedule stays Matthew's call.
6. **Do not widen past what is measured.** 28 y is a TNO number; the main-belt
   envelope breaks there (304″). Submission automation stays permanently out of
   scope (standing constraints 1–3).

---

*Generated by `scripts/m9_reconstruct_snapshot.py`, `scripts/m9_fetch_bulk.py`,
`scripts/m9_attribution.py`, `scripts/m9_consumed_check.py`, `scripts/m9_combined.py`,
`scripts/m9_adjudicate.py`, `scripts/m9_calibration.py`, `scripts/m9_tno.py`,
`scripts/m9_verdicts.py`, plus `scripts/m8_attribution.py --resume-sweep` for the
extension. Regenerable artifacts: `m9-attribution.json`, `m9-ledger.json`,
`m9-combined.json`, `m9-adjudication.json`, `m9-tno-scoping.json` (root, gitignored),
`data/raw/rubin/m9-*.json`, `data/raw/rubin/m9-orbits.parquet`,
`data/parquet/itf_observations_20260816_reconstructed.parquet`. The pre-fix M8 report
is preserved at `data/raw/rubin/m8-attribution-asof-20260817.json`.*
