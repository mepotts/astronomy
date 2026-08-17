# M8 — Perturbed attribution at full Rubin-batch scale

**Date:** 2026-08-17 · **ITF snapshot:** the M7 pull (`Last-Modified: Sun, 16 Aug 2026
20:27:01 GMT`, 9,255,644 observations, 2,611,699 tracklets — provenance in
`data/raw/itf.provenance.json`). **Nothing was submitted anywhere. Candidates are
candidates. M7's two held candidates are carried forward untouched — their disposition
is Matthew's.**

**One-line result:** the perturbed ephemeris backend M7 said was "the single change
that converts the validation slice into a production sweep" now exists and is
measured — two-body's 7,545″ at 15 years becomes **≤ 55″** (worst calibrator 94″ at
12 y), which opens |Δt| ≤ 15 years — and the full Feb + April Rubin batches
(**22,636 swept orbits** of 43,917 bulk-parsed, against **2,045,041 tracklets**
across 5,298 nights) produce 119,607 coarse candidates whose aggregate the
amplitude-matched decoy prices as chance (128,602) **but whose sub-30″ head carries
a ≈560-candidate real excess (933 vs 371) that two-body could never resolve** — and
the ranked, checkpointed fit queue (900 fitted, 0.75% of coarse, top-ranked;
resumed through an external kill with zero loss) distils it into **candidate ledger
v2: 482 PASS across 450 distinct objects, 90% beyond the old 4-year wall, deepest
−14.9 years, 29 objects with two-plus independently-passing tracklets** — plus
M7's two held candidates carried forward untouched.

---

## 1. The perturbed backend, measured the M7 way

`attrib/planets.py` + `attrib/perturbed.py`: Sun + eight planets (Earth+Moon as one
barycentric mass) as Newtonian point masses, planet positions from JPL's approximate
mean elements (Table 1, 1800–2050, transcribed verbatim from
`ssd.jpl.nasa.gov/planets/approx_pos.html` on 2026-08-16), GMs from DE440 (Park et
al. 2021), integrated by fixed-step RK4 **vectorised across every orbit in a chunk**
(h = 1 day; halving h changes nothing at the 0.01″ level), with cubic-Hermite dense
output every 8 days. No scipy, no new dependency, ~8 s per 2,000-orbit chunk for a
15-year backward integration.

`scripts/m8_calibration.py` measures it exactly as M7 measured two-body: current
get-orb orbit, propagated back, against JPL Horizons astrometric geocentric truth —
M7's four calibrators plus three stretch targets, on a denser 16-point grid:

| Target | two-body @4y | @15y | **perturbed @4y** | **@10y** | **@15y** | worst |
|---|---:|---:|---:|---:|---:|---:|
| (7) Iris a=2.39 | 491″ | 1,781″ | **0.4″** | 10.3″ | 9.8″ | 10.3″ |
| (170) Maria a=2.55 | 336″ | 978″ | **0.5″** | 1.9″ | 6.7″ | 6.7″ |
| (24) Themis a=3.13 | 57″ | 7,545″ | **4.2″** | 30.8″ | 55.2″ | **93.7″ @12y** |
| (153) Hilda a=3.97 | 106″ | 4,132″ | **0.1″** | 0.6″ | 2.0″ | 2.0″ |
| (433) Eros a=1.46 (NEO end) | 192″ | 1,389″ | **0.1″** | 0.5″ | 0.5″ | 1.0″ |
| (588) Achilles a=5.2 (Trojan) | 478″ | 5,661″ | **0.4″** | 10.6″ | 8.2″ | 12.5″ |
| (944) Hidalgo a=5.7 e=0.66 | 84″ | 1,484″ | **0.1″** | 0.8″ | 0.2″ | 2.7″ |

Two orders of magnitude, and the residual is *physics, not integration*: the worst
cell (Themis) belongs to the calibrator that approaches Jupiter closest (1.6 AU
minimum — most exposed to Jupiter's mean-element error) and to the Themis family's
big unmodelled asteroid perturbers. Full numbers:
`data/raw/rubin/m8-calibration.json`.

Honest notes, both measured:

* **The encounter flag exists and no calibrator trips it.** (944) Hidalgo was chosen
  as the hostile case and stayed outside Jupiter's Hill sphere this 15-year window —
  and calibrates *clean* (≤ 2.7″). The flag (minimum planet distance < 1 Hill radius,
  tracked per orbit during integration) is unit-tested on a constructed 0.2 AU Jupiter
  approach instead; every sweep candidate carries it, because a post-encounter
  prediction inherits nothing from this table.
* **The envelope is frozen from non-encounter calibrators only**, monotonicised (a
  gate that shrank with lookback would claim precision never demonstrated — M7's
  rule): 0.3″ → 4.2″ @4y → 28″ @6.5y → 39″ @8y → 94″ @12y+.

## 2. The gate: same formula, new envelope, same floor

`radius = 120″ + 1.5 × envelope(|Δt|) + runoff(U)·|Δt|/decade` — deliberately
unchanged in *form* from M7, because the floor and the U-term model the **orbit's**
uncertainty and the geocentric approximation, which swapping the propagator does not
touch. What changes is what the envelope now permits:

| |Δt| | M7 (two-body) U=5 | **M8 (perturbed) U=5** | M8 U=2 | M8 U=6 |
|---|---:|---:|---:|---:|
| 4 y | ~1,020″ | **214″** | 127″ | 772″ |
| 8 y | closed | **354″** | 179″ | 1,470″ |
| 15 y | closed | **589″** | 261″ | 2,682″ |

The window triples (|Δt| ≤ 15 y — the measured range, not a preference) *and* the
radius at 4 y tightens 4.8×. The U-runoff still dominates deep lookback for U=6
orbits — a 30-day arc is a 30-day arc no matter how well its state is propagated —
and the decoy control prices exactly what that admits.

## 3. Bulk orbits: one file instead of thirty thousand API calls

M7's get-orb loop at ≥1.1 s/orbit does not scale to ~44k objects (~14 h of API
requests for data the MPC publishes as one file). `scripts/m8_fetch_bulk.py` +
`attrib/bulk.py`:

* **`mpcorb_extended.json.gz`** (181 MB gz, `Last-Modified: Sun, 16 Aug 2026
  23:24:47 GMT`, sha256 recorded), streamed by an index-based `raw_decode` scanner —
  1,557,104 orbit records in **21 s**, constant memory, no new dependency.
* **Batch object lists from the Asteroid Institute partitions** (`created_at`-keyed —
  the M7 trap; nothing filters on designation half-months): the cached Feb 2026-02-06
  partition plus six large April partitions (2026-04-10/22/24/25/27/28, 216 MB,
  production namespace) downloaded with provenance sidecars.
* **Matching on `Principal_desig` *or* `Other_desigs`** (M7 trap 8: batch provids
  merge under new primaries): **42,624 of 44,192 provids (96.5%)** resolve in the bulk
  file; the 1,568 misses go through get-orb one by one, paced, capped at 2,000 (more
  would mean the parse is broken — stop, don't hammer).
* **Keplerian elements → equatorial state** (`elements_to_state`): ecliptic-J2000
  rotation shared with every other attribution input; Kepler solve with a convergence
  guard that refuses rather than mis-places.

**Verification before trust** — the two routes quote different standard epochs
(cached get-orb: MJD 61000; today's MPCORB: 61200), so each cached get-orb state is
carried across the 200-day gap *by the perturbed integrator itself* and compared with
the bulk-parsed state at 61200. Across **398 reference orbits (387 epoch-bridged):
median |Δr| = 2.29 × 10⁻⁷ AU, p99 = 7.7 × 10⁻⁷, max = 8.8 × 10⁻⁷** — exactly the
element-quantisation level (MPCORB prints 7 decimals of a, 5 of the angles). A frame
or anomaly-convention mistake would read ~0.1–1 AU and could not hide. The parse ran
1,557,104 objects in 19.4 s; **0 matched rows were unparsable**; the fallback
resolved **1,568 of 1,568** missing provids (0 without orbits). Numbers:
`data/raw/rubin/m8-bulk-verification.json`.

**The U-parameter cut is the big scale honesty number**: of 43,917 orbits, **21,281
(48%) carry U 7–9** and are excluded exactly as M7 excluded its 49/400 (12%) — the
2026-designated April discoveries are fresher and shorter-arced, so the fraction
grows. **Swept: 22,636 orbits** (U ≤ 6 or no U; histogram: U=0 5,342 · 1 3,558 ·
2 3,686 · 3 3,150 · 4 1,767 · 5 1,521 · 6 3,609 · none 3).

### What the batches actually contain

| Partition | obs | provid obs | unnumbered objects | discovery `*` | dominant designations |
|---|---:|---:|---:|---:|---|
| Feb 2026-02-06 | 245,904 | 244,152 | **19,243** | 17,043 | 2025 (17,269) + 2,000 older re-designations |
| Apr 2026-04-10 | 272,815 | 216,601 | 778 | 7 | 2026 (601) |
| Apr 2026-04-22 | 118,547 | 118,534 | 2,024 | 5 | 2026 (1,863) |
| Apr 2026-04-24 | 279,332 | 279,304 | 4,850 | 26 | 2025 (4,057) |
| Apr 2026-04-25 | 103,062 | 101,226 | 11,816 | 85 | 2025 (10,408) |
| Apr 2026-04-27 | 90,001 | 88,347 | 6,026 | 210 | 2025 (5,277) |
| Apr 2026-04-28 | 80,728 | 80,122 | 3,065 | 36 | 2026 (2,846) |

Union: **44,192 distinct unnumbered objects** (Feb 19,243 + 24,949 April-only). The
"~11k April" of the prospectus undercounted what the April partitions hold: alongside
the 2026-designated new discoveries (5,310) they carry the bulk processing of
2025-designated objects the Feb partition never listed, ~2,600 objects re-designated
from older provisional IDs (1995–2024 — Rubin recovering decade-old single-opposition
objects at scale), and four comet provids. All of it is swept: every one is a
designated object with a current orbit that ITF tracklets could attribute to.

## 4. The sweep at scale

**22,636 orbits × 2,045,041 tracklets (5,298 nights, MJD 55521–61201, |Δt| ≤ 15 y) in
8.6 minutes** — 305 s of vectorised RK4 (15 chunks of ≤1,500 orbits, each integrated
once across the full window) + 211 s of night-stage work, single process. The M7
sweep architecture would not have survived this scale; three changes made it fit:

* **Integrate once, evaluate everywhere.** Each chunk's 15-year trajectory is stored
  as dense Hermite nodes; stage 1 evaluates every orbit at every night midpoint by
  interpolation, stage 2 re-evaluates surviving pairs at the tracklet's own epoch
  with light-time iteration — through the *same* dense representation, so the two
  stages cannot disagree about where the orbit is.
* **Night-outer, orbit-vectorised stage 1.** Per night: one dec-sorted tracklet
  array, `searchsorted` strips per orbit, ragged expansion in ≤4M-pair slices
  (a dense narrow-dec survey night would otherwise allocate multi-GB pair arrays),
  exact separation on the strip. The margin is the gate radius plus
  `|v_obj − v_earth|/Δ × 0.7 d` — the observer's motion *inside* the bound, because
  a main-belt object's apparent rate is mostly parallax reflex.
* **Stage 2 is the M7 gate exactly**: position radius at the pair's own |Δt| and U,
  rate-vector tolerance with the tracklet's endpoint-noise term, light-time
  corrected, plus the encounter flag on every pair (0 orbits flagged in this batch —
  young main-belt discoveries do not graze planets in 15 years).

Result: **119,607 coarse candidates from 10,802 orbits** (median separation 1,112″,
median |Δt| 10.8 y). **114,357 of them — 95.6% — lie beyond M7's 4-year two-body
wall.** Ranking for the fit queue is separation *normalised to the gate radius*
(sep/gate), encounter-flagged last.

## 5. The control at scale

Every one of the 22,636 orbits was also swept half a period out of phase — same
elements, same rates, same sky-time distribution, wrong place (house law: an
unmatched control screens nothing). Same code path, same 8.6 minutes:

| | real | decoy |
|---|---:|---:|
| Coarse matches | 119,607 | **128,602** |
| Orbits with ≥ 1 match | 10,802 | 10,856 |
| Median separation | 1,112″ | 1,116″ |
| **[0″, 5″)** | **175** | **14** |
| **[5″, 15″)** | **292** | **93** |
| **[15″, 30″)** | **466** | **264** |
| [30″, 60″) | 1,232 | 1,125 |
| [60″, 120″) | 4,330 | 4,433 |
| ≥ 120″ | 113,112 | 122,673 |

Two findings, both of which M7 could not produce:

1. **The aggregate is chance, and the decoy over-prices it slightly** (7.5% more
   matches than real, same direction as M7's 914 vs 944): the phase-shifted twin
   samples marginally different sky against the survey footprints. As a background
   price it is conservative.
2. **The small-separation head is now *real signal*.** M7's two-body sweep saw 2 real
   vs 2 decoy below 30″ — nothing. The perturbed gate sees **933 real vs 371 decoy
   below 30″: a ≈560-candidate excess** (12.5× at <5″), which is exactly what a
   population of true attributions sitting at the prediction should look like against
   an area-scaling chance background. The coarse stage still *demonstrates* nothing
   per candidate — the fits and the duplicate check arbitrate, and much of the excess
   should prove to be stale ITF copies of observations the MPC already consumed
   (ALREADY_LINKED, the M7 verdict taxonomy's positive-control class) — but for the
   first time the sweep itself has a measurable true-match population to hand them.

## 6. The fit queue: ranked, budgeted, checkpointed

The queue is every real coarse candidate, ranked by **separation ÷ gate radius**
(encounter-flagged last), because normalised separation is the best available
predictor of fit survival. Each candidate gets the M7 fit exactly: the object's full
published astrometry (get-obs OBS80, cache shared with M7) + the tracklet's verbatim
80-column lines, relabelled under one 7-character tag, fo with perturbers 7fe/DE-440,
strict + published gates, and the *"did fo actually use the tracklet"* question as
the primary discriminator. Every outcome appends to `data/m8-fit-state.jsonl`
**before** the next fit starts.

That checkpoint discipline was then tested involuntarily: the first tranche was
killed externally at fit 500 of 1,200 mid-queue. The resume run reloaded all 500
outcomes from the JSONL, verified them against the queue keys, and continued at 501
— zero fits repeated, zero lost.

**Coverage, honestly: 900 of 119,607 coarse candidates fitted (0.75%), the top 900
by rank.** Economics: 8.4 s per fit cold (get-obs + baseline dominate a new orbit),
**5.26 s warm**; the two tranches totalled ~70 + 35 minutes. Yield against rank —
the number that says whether the budget was placed correctly and when to stop:

| rank | median sep | median sep/gate | strict + fully-used |
|---|---:|---:|---:|
| 0–99 | 4.4″ | 0.005 | **72/100** |
| 100–199 | 10.8″ | 0.012 | 72/100 |
| 200–299 | 16.3″ | 0.018 | 62/100 |
| 300–399 | 23.0″ | 0.023 | 64/100 |
| 400–499 | 30.7″ | 0.028 | 52/100 |
| 500–599 | 36.7″ | 0.033 | 50/100 |
| 600–699 | 50.4″ | 0.038 | 37/100 |
| 700–799 | 60.1″ | 0.043 | 41/100 |
| 800–899 | 69.3″ | 0.047 | **43/100** |

**493 of 900 pass strict + fully-used** (M7: 2 of 150 — the perturbed gate's ranking
is doing what two-body's could not). The decay from 72% to ~40% is real but has
**not reached the chance floor at the cap** — the queue is unexhausted, and
`--resume-sweep` with a larger `--max-fits` continues from fit 901 with nothing
recomputed. That is an M9 line item, not a loosened gate.

## 7. Candidate ledger v2

`scripts/m8_verdicts.py` → `m8-ledger.json`. The M7 taxonomy with SkyBoT folded into
the automated chain (M7 ran it by hand for one candidate; here every survivor gets a
cone search at its tracklet's own epoch and position through the M2 vetting client
and cache — 484 calls, all cached for re-runs), the *"did fo actually use the
tracklet"* question checked and named first, and per-candidate provenance: orbit
source (mpcorb/get-orb + file provenance), gate numbers at the candidate's own
|Δt| and U, fit tag, both gate verdicts, SkyBoT payload, encounter flag, and the
content-addressed `link_key` as the only citable tracklet id.

**Of 900 fitted: 482 PASS (394 with zero caveats) · 414 FAIL · 1 SKYBOT_CONFLICT ·
1 BORDERLINE · 2 ALREADY_LINKED.**

| Ledger v2 | count | reading |
|---|---:|---|
| **PASS** | **482** | converged; strict RMS gate (median joint RMS **0.082″**); tracklet fully used; ≥90% of joint set used; not in the published record; no competitive SkyBoT claimant |
| … of which caveat-free | 394 | the other 88 carry a named `skybot_lost_object_ambiguity` (below) |
| … distinct objects | **450** | **29 objects have 2+ independently-passing tracklets** — the PD152 mutual-corroboration pattern; 2025 OK598, 2025 OW123 and 2026 ED8 have **three each** |
| … beyond M7's 4-y wall | 432 (90%) | median \|Δt\| = 5.8 y, deepest **−14.87 y** (2025 OK598 ← F51 `P100OPQ`, 17″, RMS 0.076″, 3/3 used) |
| FAIL | 414 | mostly tracklet-not-fully-used and strict-gate — the discipline unchanged |
| SKYBOT_CONFLICT | 1 | 2025 PK91's tracklet sits 16.2″ from **2015 TN357** whose ephemeris is good to 4.1″ — a genuinely competitive claimant, correctly failed |
| BORDERLINE | 1 | **2025 MQ241 + `nf2088` at RMS 0.25066″ — the chain independently re-derived M7's manual borderline to the digit.** Not re-litigated; the verdict remains Matthew's |
| ALREADY_LINKED | 2 | stale ITF copies for two older-designation objects (2016 GS76, 2021 TN150) — the positive-control class working |

The candidate pool is **cross-survey, exactly where M4/M5 located the ITF's
distinctive value**: F51 Pan-STARRS 1 (294) · F52 PS2 (48) · **W84 DECam (46)** ·
G96 Catalina (35, reaching its 2011–2012 archive at −14.6 to −14.9 y) · **T09
Subaru (33)** · Mt Lemmon, ATLAS and others. The first-ranked fit of the whole run
is 2025 NF85 ← DECam `IaJM1KT` at **0.5″** separation.

Three honesty notes:

* **Only 2 of 900 came back ALREADY_LINKED.** The excess-over-chance head is *not*
  stale copies of MPC-consumed observations — it is unconsumed archival precovery
  the designation-time sweep left behind, the PD152 mechanism (§M7-RESULTS §7)
  demonstrated at scale: young orbits carry hundreds-of-arcsec uncertainty at
  archival epochs, beyond any tight automated matcher, and only a measured-gate +
  rate-test + full-fit chain reaches them.
* **The 88 lost-object ambiguities are named, not hidden.** The first SkyBoT rule
  ("conflict if sep ≤ 15″ + ephemeris error") let *lost* objects with 10³–10⁶-arcsec
  ephemeris errors blanket-claim every candidate near the ecliptic — 89 false
  conflicts. The shipped rule is the PD152 standard made explicit: a claimant must be
  positionally consistent **and** informative (err ≤ 60″, frozen in the ledger's
  `rules` block). Objects that merely cannot be excluded are recorded on the
  candidate as a named reason; M9's adjudication is to fit the tracklet against the
  claimant's own astrometry.
* **M7's held candidates are carried forward verbatim** (`held_from_m7`, three rows:
  PD152 × 2 PASS, MQ241 borderline) and were not re-litigated. In M8's queue,
  PD152's 197–271″ separations rank ~10,000th — the new head is that much tighter —
  so its fits were not re-run; its M7 evidence stands as written.

**Nothing was submitted.** The ledger is a review artifact for Matthew; submission
machinery does not exist in this repository (standing constraints 1–3).

## 8. The watcher (designed and validated; not scheduled)

`scripts/watch_rubin_batches.py` + `docs/watcher.md`. Two GETs per run: the Asteroid
Institute daily-partition listing (422 partitions baselined; a *new* partition ≥ 1 MB
is the "new bulk batch" signal — real batches are 2.6–100 MB, empty days are 11 kB
markers) and the MPC newsletter archive (which now lives on Buttondown — the
`minorplanetcenter.net/mpcops/newsletters` path 404s; found via the MPC front page).
Exit codes: 0 nothing, 2 new batch, 3 other news, 1 check failed. State in one JSON
file; two consecutive live runs verified (baseline, then clean no-change diff).
**No scheduled task was installed** — scheduling and acting on exit 2 are Matthew's
call; the doc shows the one-line `schtasks` command if he wants it.

The bucket already answers "was this worth building": partitions
**2026-06-04 (47 MB), 2026-08-03 (13 MB), 2026-08-06 (13 MB), 2026-08-10 (100 MB —
the largest since February)** have landed since April and are consumed by no
milestone. That is M9's input queue.

## 9. Traps hit (all paid for; check before touching this code)

1. **A streaming JSON parser that slices its buffer per object is O(chunk × objects).**
   The first `iter_mpcorb_objects` cost hours on the real file; the index-based
   `raw_decode(buf, idx)` scan does 1.56M objects in 21 s. The unit tests pass either
   way — only the real file's scale exposed it.
2. **`designation_asterisk` is an all-null Boolean in the current replica.** The
   discovery asterisk is the `disc` column ('*'); `disc` reproduces M7's 17,043
   exactly. A column named for the thing you want is not the column holding it.
3. **The two orbit routes quote different standard epochs** (get-orb: 61000; MPCORB:
   61200 the same day). A same-epoch state comparison silently verifies nothing —
   bridge the gap with a propagator whose error you have measured, then compare.
4. **`scipy` is not in this venv** — the neighbour search is a per-night dec-sorted
   strip + `searchsorted` expansion, pure numpy, and the per-night Earth ephemeris
   must be precomputed in one vectorised astropy call (a scalar call per night per
   chunk would cost minutes of pure `astropy.Time` overhead).
5. **The stage-1 rate margin must include the observer's motion.** An apparent-rate
   bound from the heliocentric velocity alone under-estimates a main-belt object's
   sky motion, which is mostly parallax reflex; the bound is
   `|v_obj − v_earth|/Δ`.
6. **The MPC newsletter index moved to Buttondown** (`buttondown.com/MPC_newsletter/
   archive/`); every plausible `minorplanetcenter.net` index path 404s. The per-issue
   PDFs under `/media/newsletters/` still resolve.
7. **Windows console is still cp1252** (M7 trap 9) — every M8 script run sets
   `PYTHONIOENCODING=utf-8`.
8. **A SkyBoT "claimant" rule that ignores ephemeris quality lets lost objects
   blanket-claim the ecliptic.** 89 of the first run's conflicts had claimant
   ephemeris errors of 10³–10⁶ arcsec; the PD152 standard weighs accuracy, and the
   shipped rule (§7) requires it. One competitive conflict survived — correctly.
9. **Never quote a number you did not read from the artifact.** A long run piped
   through `tail` keeps its head invisible (and its exit code masked); mid-session,
   a "remembered" orbit count that was never actually printed nearly entered the
   analysis. The parquet and a recount agreed with each other and not with the
   memory. Redirect long runs to files; quote files.

## 10. Recommended next milestone (M9)

1. **Consume the unconsumed batches.** The bucket already holds four bulk partitions
   no milestone has swept — 2026-06-04 (47 MB), 2026-08-03 (13 MB), 2026-08-06
   (13 MB) and **2026-08-10 (100 MB, the largest since February)**. The entire M8
   chain is batch-shaped: add the partitions to `m8_fetch_bulk.py`'s list, re-run.
   This is also the watcher's first real assignment.
2. **Finish the fit queue.** If this run's budget left coarse candidates unfitted
   (see §6 for the honest coverage number), the checkpoint file resumes exactly where
   it stopped: `python scripts/m8_attribution.py --resume-sweep --max-fits <more>`.
3. **Combined fits for multi-tracklet survivors.** M7's PD152 evidence peaked at the
   *combined* 33-of-33 fit of two independently-passing tracklets; the M8 chain fits
   tracklets singly and leaves combination to the human. Automating "same orbit,
   2+ passing tracklets → one joint fit" is a small, high-value verdict-chain v3 step.
4. **The TNO niche, now reachable.** M7 §9 sized the slow-northern pool at 3,239
   robust tracklets (Subaru + SDSS, 2000–2019). Two-body could never touch 2000-era
   epochs; the perturbed backend's measured window still ends at 15 y — extending the
   calibration grid to 25 y (same script, more lookbacks) would say whether the
   SDSS-era slice is gated or closed.
5. **Do not widen past what is measured.** Beyond-15-y sweeps, submission automation,
   and loosening any gate stay out of scope; a zero from the deep window reported
   plainly is a result (standing constraint 5).

---

*Generated by `scripts/m8_calibration.py`, `scripts/m8_fetch_bulk.py`,
`scripts/m8_attribution.py`, `scripts/m8_verdicts.py`. Regenerable artefacts:
`m8-attribution.json`, `m8-ledger.json` (root, gitignored by `/m[0-9]*.json`),
`data/raw/rubin/m8-*.json`, `data/raw/rubin/m8-orbits.parquet`.*
