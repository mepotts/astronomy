# M3 — the full-sky W4 screen, the funnel, and the coded vetting of every survivor

*2026-08-21 · follows [M2](M2-dossier-and-screen.md), executing M2 §5's own recommendations.
Every externally-sourced number carries its source; anything unsourced is marked UNSOURCED.
**Nothing in this milestone has been submitted, posted, or sent anywhere.** Candidate-level claims
and the Ren+24 note remain Matthew-gated; their gate status is unchanged by this document.*

---

## 0. Pre-registrations

*Written and timestamped **before** the runs they govern, per repo law. Nothing below was chosen
after seeing a result.*

### PR-1 — stopping rules for the W4 pull (declared 2026-08-21, before resume)

The 2026-08-18 launch stalled on 2026-08-19 03:56 and abandoned 99 tiles. The post-mortem
(§1.1) is that the retry budget was consumed by a **server outage**, not by tile difficulty, and
nothing in the driver could tell those apart. The resume therefore runs under four rules fixed in
advance:

| rule | value | why this value |
|---|---|---|
| **wall-clock budget** | **600 min** | 99 tiles × ~111 s mean success time ≈ 3.1 h floor; 600 min allows ~3× that for load-wall retries without running unattended past a working day |
| **instant-failure classifier** | failure returning in **< 5 s** consumes **no** retry budget | MEASURED: 679 of the 680 outage failures returned in **0.2–0.3 s**; every load-wall failure took **181.6 ± 0.3 s**. The two populations do not overlap, so 5 s separates them with a >30× margin either way |
| **outage breaker** | **8** consecutive instant failures arm a cooldown/probe ladder (120 s, doubling, capped 900 s); **6** consecutive failed probes stop the run | 8 is well below the 20-long run of consecutive *load* failures observed during the healthy phase, so the breaker cannot fire on load — only on the instant signature. 6 probes ≈ 50 min of patience before giving up |
| **per-tile instant cap** | 60 free instant retries per tile | bounds the no-retry-consumed path so it cannot loop forever if the probe passes but a tile still fails instantly |

**Reporting rule, fixed now:** whatever coverage exists when a rule fires **is** the result. It will
be reported as a sky fraction with the fraction stated in every projection, and it will **never** be
described as a complete screen. A 48–100% unbiased screen is a real result; a partial screen
reported as complete is not.

**Unbiasedness (the reason a partial screen is usable at all).** Tiles are issued in a deterministic
pseudo-random permutation (seed 20260818, M2 §4.2) of 24 equal-solid-angle declination bands × 8 RA
sectors. Coverage therefore accumulates uniformly in RA, dec and Galactic latitude rather than as a
polar cap or a Galactic-plane strip, so the funnel measured on a partial screen is an unbiased
estimate of the all-sky funnel, and rates scale by the sky fraction. This is checked, not asserted,
in §2.1.

### PR-2 — the funnel (declared before `select` was run at scale)

- Primary grid: **γ ≥ 0.10**, the paper's *stated* initial grid (Suazo et al. 2024 §2.2).
  γ ≥ 0.01 (the floor needed to admit the paper's own candidate F, γ = 0.03) is reported as a
  sensitivity, not as the result.
- Comparison target: Hephaistos II Table 4 rates scaled by the measured sky fraction.
- Uncertainties: **Poisson 68% intervals** on every counted stage (Garwood/exact intervals on the
  observed count), quoted as ratio-to-paper with the interval carried through.
- The stage-by-stage table is emitted by the script from the live manifest, never hand-copied.

### PR-3 — survivor verdicts (declared before any survivor was vetted)

Every pre-visual finalist gets exactly one verdict from this fixed set, decided by the coded gates
below in this order. **The gates and their thresholds were fixed before the survivor list existed.**

| verdict | condition |
|---|---|
| **SUB-THRESHOLD** | the claimed excess is below WISE's own sensitivity at that ecliptic latitude in **both** excess bands, i.e. the "detection" is not a detection the survey can support (candidate I's failure mode) |
| **CONTAMINATION-CONSISTENT** | a centroid offset **larger than the 1–2″ floor** in an excess band, *or* release-inconsistency between AllWISE and All-Sky in the band carrying the excess, *or* `w3nm`/`w4nm` = 0 in the band carrying the excess (coadd-only "detection") |
| **INDETERMINATE** | passes the gates but every axis is at or below its own noise floor — nothing in the archive can move it either way |
| **STILL-CLEAN** | detected in single exposures, release-consistent, above the sensitivity floor, no centroid offset outside the floor, and low chance-alignment prior |

**Every verdict must state the centroid floor for that object.** "No offset detected" means "no
contaminant outside ~1–2″", never "no contaminant" — this is the standing project law from the D
calibration (M2 §1). Any object reaching **STILL-CLEAN** is a **Matthew-gated candidate**: flagged
loudly here, reported nowhere externally.

---

## 0b. What M3 established

1. **The pull did not finish, and the reason is measured, not guessed.** Final coverage
   **93 tiles, 19,874 deg², 48.18% of the sky** — unchanged from where the 2026-08-19 stall left
   it, because ESAC served **zero** tiles in ~3.5 h of trying across two resume attempts. It
   answers `SELECT TOP 5` in 1.3 s and kills every query touching the join tables — including a
   bare 3-table `COUNT(*)` at 79.8 s. The wall is **size-independent** across a 16× range in tile
   area, so splitting cannot help (§1.2). **This is a 48.18% screen and is reported as one.**
2. **The 2026-08-19 stall is diagnosed and can't recur silently.** 679 of the 680 outage failures
   returned in 0.2–0.3 s against 181.6 ± 0.3 s for genuine load failures; the driver could not tell
   them apart and burned 99 tiles' retry budgets in seconds. Instant failures now consume no
   retries, an outage breaker stops the run cleanly, and **no tile is abandoned** — all 100
   outstanding tiles sit in `retry`, resumable (§1.1).
3. **The funnel, at the paper's own stated grid, overproduces pre-visual survivors 4.8×** —
   845 against the 177 Hephaistos II's rates predict for this area [Poisson 4.60–4.94] (§2.1).
4. **The ~9× γ-floor finding is corrected to 5.8×** at the RMSE gate (and 5.0× → 2.9× at the
   pre-visual gate). The pilot overstated it because of the truncated template window (§2.3).
5. **Both method caveats are closed** (§4). The Hα sign convention is sourced three ways and the
   implementation was **already correct** — but closing it showed the cut is **near-inert**
   (0.001 recovery for active M dwarfs) and that **3 of the paper's 7 candidates were never
   testable by it** (G > 17.65, and D misses by 0.011 mag). The template locus is extended
   blueward from PM13's own tabulated colours, validated to rms 0.050 mag, with **zero regression**
   on M1's 7/7 acceptance; the fitted fraction goes from 32% to **98.6%**.
6. **845 finalists vetted, and none survives**: 416 CONTAMINATION-CONSISTENT, 326 INDETERMINATE,
   103 SUB-THRESHOLD, **0 STILL-CLEAN**. **There is no Matthew-gated candidate from this screen**
   (§3.3).
7. **M2's two invented axes fire hard at scale, and one fires in a single direction.** 18.3% of
   finalists were never detected in a single W4 exposure; **13.3% have an excess band that the
   WISE All-Sky release calls a non-detection and AllWISE promotes to a detection — and the reverse
   never happens once** (§3.4).
8. **The centroid axis failed its own validity check and was refused a vote.** At scale the 10″
   peak search locks onto brighter neighbours (a 9.51″ "offset" is a source at 10.24″ that is 2.4×
   brighter; an 11.89″ one is a source at 16.36″ that is 14× brighter). Applying it would have
   convicted hundreds of objects on an unrelated neighbour, so it was disabled rather than retuned
   (§3.2).
9. **M2's prediction that the JWST-vetted sample would become 3 has not come true** — no candidate-A
   result exists as of 2026-08-21, and its data stay closed until 2027-07-16. But **candidate D's
   JWST data are already public** and E's open on 2026-09-09 (§5).
10. **A route to the other half of the sky is measured and handed to M4**: the AIP mirror hosts
    every needed catalogue, **anonymous async works with no account**, and the one gap — Bailer-Jones
    distances — is covered by a parallax proxy calibrated here to **99.09% recall** (§6).

---

## 1. The W4 pull: what stalled it, what was fixed, and where it stopped

### 1.1 Post-mortem of the 2026-08-19 stall — the retry budget was spent on a server outage

The 2026-08-18 launch ran well for ~4 h and then abandoned 99 tiles (21,271 deg², 51.6% of the
sky) inside a few minutes. Reading the log as data rather than as a narrative (903 attempts):

| population | n | time to fail | error |
|---|---|---|---|
| successes | 93 | 111 s mean, 94 s median, 46–220 s range | — |
| failures **before** the last success | 130 | 181.6 ± 0.3 s | `DALServiceError: 500` — M2's load wall |
| failures **after** the last success | 680 | **0.2–0.3 s** (679 of 680) | `DALFormatError: not a VOTABLE` — HTML error page |

The two failure populations do not overlap by a factor of ~600 in time. The driver could not tell
them apart, so a server outage that returned an error page **instantly** burned all 8 retries of a
tile in under two seconds, and then the next tile, and so on: 99 tiles were abandoned at a rate
limited only by the network round-trip. **The lost sky was never hard to get — it was sky that
happened to be asked for while the archive was down.**

Three defects were fixed in `scripts/w4_screen.py` before the resume:

1. **Instant failures no longer consume retry budget.** A failure returning in < `--instant-sec`
   (5 s) is classified as a server error page, is logged as such, and re-queues the tile with its
   `tries` untouched. Bounded by `--max-instant` (60) so it cannot loop for ever.
2. **An outage breaker with a cooldown/probe ladder.** 8 consecutive instant failures trigger a
   120 s cooldown and then a one-row health probe; each failed probe doubles the cooldown (cap
   900 s); 6 consecutive failed probes stop the run cleanly with an explicit reason. The threshold
   of 8 is safely below the longest run of consecutive *load* failures observed while the service
   was healthy (**20**), so the breaker cannot fire on load.
3. **`--reset-failed`**, opt-in and logged, forgives the `tries` of tiles abandoned during an
   outage so a resume can re-attempt them. Without it a resumed run gave each abandoned tile
   exactly one more attempt before re-abandoning it.

Two further bugs were found and fixed while reading the code, both of which would have corrupted
the funnel's denominator rather than crashing:

- **`repair` resurrected the descendants it had just deleted.** It iterates a snapshot of the
  manifest; after popping a split tile's children it still met their stale records later in the
  same loop and re-queued them as retries. The chain `d00r05 → d00r05b → d00r05ba` would have been
  queued *in addition to* its own re-queued parent — 376 deg² of queue for 215 deg² of sky. Fixed
  by skipping records already removed. Measured effect: `repair` now re-queues **1** tile
  (d00r05, 214.9 deg²) where the old code would have queued 3.
- **Area was double-counted across parent/child tiles.** `repair` deliberately keeps a done child
  when it re-queues the parent (the rows are real and `select` de-duplicates on `source_id`), but
  the child's *area* lies inside the parent's, so summing both inflates the sky fraction — the
  denominator of every rate in the funnel. A new `covered_area()` excludes any done tile that has
  a done ancestor, and `pull`, `status` and `select` all use it.

### 1.2 The resume, and a second archive failure — measured, not guessed

`repair` ran clean (1 tile, 214.9 deg²) and the resume launched under PR-1. It met a **third**
failure mode, distinct from both of the above:

```
DALQueryError: Job timeout/aborted     at 61.9, 61.9, 62.2, 123.5 s
```

This is the server killing the job, not a queue wall and not an error page. That mattered, because
M2's standing rule — *retry, never split, the wall is size-independent* — was measured against the
181 s wall and could have been exactly backwards for a job-time limit, which normally **is**
size-dependent. So it was re-measured rather than assumed (`out/m3_route_diag.json`,
`out/m3_join_diag.json`), on a real outstanding tile's footprint:

| test | area | result |
|---|---|---|
| `SELECT TOP 5 source_id` | — | **OK, 1.3 s** — the service is answering |
| 6-table screen query | 107.4 deg² | FAIL 62.4 s |
| 6-table screen query | 53.7 deg² | FAIL 62.1 s |
| 6-table screen query | 26.9 deg² | FAIL 61.8 s |
| 6-table screen query | **13.4 deg²** | **FAIL 61.5 s** |
| 4-table query (2MASS join dropped) | 214.9 deg² | FAIL 61.9 s |
| 4-table query | 107.4 deg² | FAIL 122.4 s |
| **3-table `COUNT(*)`** (no photometry at all) | 214.9 deg² | **FAIL 79.8 s** |
| anonymous async, trivial query | — | **hung > 28 min**, killed — still unusable (M2 found HTTP 500) |

**The wall is size-independent across a 16× range in area, and it kills even a bare
`COUNT(*)` over the three-table join, while a trivial single-table query returns in 1.3 s.** So
this is ESAC load on the join/external tables, not our query's size — splitting is useless (M2's
rule survives, for a new reason), and the only lever is to keep every tile in rotation and wait
for the load to lift. The driver was relaunched with `--retries 40` (a tile stays in the rotation
instead of being abandoned) and a new **politeness backoff**: after every 10 consecutive load
failures it sleeps 180 s rather than retrying into a wall.

*The same 6-table query completed 93 times on 2026-08-18 at 46–220 s. Nothing about the screen
changed; the archive did.*

---

## 2. The funnel, on 48.18% of the sky

### 2.0 What "48.18%" is allowed to mean

**Coverage: 93 tiles, 19,874 deg², 48.18% of the sky.** The pull did **not** complete; it stopped
because ESAC would not serve the join (§1.2), and under PR-1 that is reported as partial coverage,
never as a finished screen.

**The unbiasedness argument, stated because every projection below depends on it.** Tiles are 24
equal-solid-angle declination bands × 8 RA sectors, issued in a fixed pseudo-random permutation
(seed 20260818). Coverage therefore accumulates as a uniform random sample of the sphere rather
than as a polar cap or a Galactic strip, so a rate measured on 48.18% is an unbiased estimate of
the all-sky rate and scales by the sky fraction. Two things this does **not** license: it is not a
*complete* screen, so a rare object may simply be in the missing half; and it assumes the tiles
that failed did so for reasons uncorrelated with the sky (they did — the failures are a server
outage and a server load wall, both time-dependent, not position-dependent).

*Every count below is emitted by `scripts/m3_funnel_report.py` from the live manifest and the
funnel JSONs. Nothing is hand-copied. Intervals are exact (Garwood) Poisson 68% on the observed
count.*

### 2.1 Stage by stage against Hephaistos II Table 4

| stage | γ ≥ 0.10 | γ ≥ 0.01 | paper expected | ratio at γ ≥ 0.10 |
|---|---|---|---|---|
| parent sample (Gaia < 300 pc × 2MASS × AllWISE) | — | — | 2,408,854 | applied server-side |
| **W3 *and* W4 detected (C2a)** | **220,632** | 220,632 | 154,167 | **1.43×** [1.43–1.43] |
| cc_flags clean (C2b) | 161,634 | 161,634 | — | — |
| … with full 10-band photometry | 160,410 | 160,410 | — | — |
| … inside the template M_G window | 158,097 | 158,097 | — | **98.6%** of the above |
| **RMSE ≤ 0.2 star+DS grid fit (C3)** | **4,773** | 27,828 | 5,417 | **0.88×** [0.87–0.89] |
| + Gvar, RUWE, ext_flg, classprob (C5b–e) | 4,257 | 20,292 | 2,475 | **1.72×** [1.69–1.75] |
| **+ W3 & W4 S/N ≥ 3.5 (C6) — pre-visual survivors** | **845** | 2,472 | 177 | **4.77×** [4.60–4.94] |
| final candidates (their C4 CNN + C7 visual) | n/a | n/a | 3.4 | replaced by §3's coded gates |

Sky-wide projections (÷ 0.4818): **457,960** W3W4-detected [456,985–458,938] against the paper's
~3.2 × 10⁵; **9,907** RMSE survivors [9,764–10,053] against 11,243; **1,754** pre-visual survivors
[1,693–1,816] against 368.

### 2.2 What changed against M2's pilot, and why

M2's pilot (752 deg², narrow M_G window) reported the RMSE stage at **0.47×** the paper's rate and
the pre-visual stage at **0.75×**, and said so with the caveat that the RMSE row was a lower bound
because only ~32% of stars were fitted. **Closing the template caveat (§4.2) moved both, in the
direction the caveat predicted:**

| stage | M2 pilot, 752 deg², M_G 6–14.5 | M3, 19,874 deg², M_G 0.5–14 |
|---|---|---|
| stars fitted, as a fraction of full-10-band | 32.3% | **98.6%** |
| RMSE ≤ 0.2 vs paper | 0.47× | **0.88×** |
| pre-visual vs paper | 0.75× | **4.77×** |

**The RMSE stage now reproduces the paper to 0.88×** — the deficit really was the missing
two-thirds of the stars, as M2 suspected. But the *late* stages now overshoot badly, and the reason
is visible in the pass rates rather than the totals:

| stage transition | paper | this screen |
|---|---|---|
| RMSE → + extra cuts | 5,137/11,243 = **45.7%** | 4,257/4,773 = **89.2%** |
| extra cuts → + S/N ≥ 3.5 | 368/5,137 = **7.2%** | 845/4,257 = **19.8%** |

Two separate gaps, and they should not be conflated:

1. **The extra cuts (Gvar, RUWE, ext_flg, classprob) reject 11% where the paper's reject 54%.**
   M1 already established that Gvar is *reference-sample dependent* — it is computed against a
   flux-matched comparison population, and the paper does not publish theirs. This screen computes
   it from its own in-sample medians. That is a documented irreproducibility, not a discovery, and
   it is the largest single unexplained factor in the funnel.
2. **The S/N stage passes 20% where the paper's passes 7%** — and this one is a direct consequence
   of §4.2. Extending the template range blueward admits hotter, intrinsically brighter stars,
   which have systematically better W3/W4 signal-to-noise, so a far larger fraction clears
   S/N ≥ 3.5. The pilot's narrow K/M-dwarf window had removed exactly the population that passes
   this cut most easily.

**The honest reading:** at the paper's own stated grid, with a template range matched to theirs,
this implementation produces **4.8× more pre-visual survivors than their published rate**. Either
their template set or their Gvar reference is doing selectivity this reconstruction cannot see, or
their C4 CNN sits earlier in the chain than the Table 4 ordering suggests. **This is a
reproducibility result, and it is not resolvable from the published material** — which is the same
boundary M1 hit at C4/C7, now measured on 48% of the sky instead of argued from one field.

### 2.3 The γ-floor finding, corrected at scale

M2 measured the cost of relaxing the model grid's γ floor from the paper's stated 0.1 to the 0.01
needed to admit their own candidate F, and found **~9×** at the RMSE gate on 1,762 stars. On
158,097 stars with the corrected template range:

| gate | γ ≥ 0.10 | γ ≥ 0.01 | γ-floor cost |
|---|---|---|---|
| RMSE ≤ 0.2 | 4,773 | 27,828 | **5.83×** *(pilot said 8.76×)* |
| + extra cuts | 4,257 | 20,292 | 4.77× |
| + S/N ≥ 3.5 | 845 | 2,472 | **2.93×** *(pilot said 5.0×)* |

**The ~9× is corrected to 5.8×.** The pilot overstated it, and the reason is the same truncated
template window: restricted to K/M dwarfs, the γ ≥ 0.01 grid could fit a token excess to a much
larger *fraction* of the sample. The qualitative finding survives untouched and is now measured on
~90× more stars: **the γ floor is the funnel's dominant selectivity knob, it is worth a factor of
~6 at the RMSE gate, and the paper's stated grid is incompatible with its own candidate F** (best
RMSE 0.2546 against a 0.2 threshold, §4.2).

### 2.4 One number that does not fit: the parent sample is 1.43× the paper's

The W3+W4-detected population — the first stage, before any modelling — comes out at
**220,632 on 19,874 deg², i.e. 457,960 sky-wide, against the paper's ~3.2 × 10⁵**. The Poisson
interval is [456,985–458,938], so this is not a counting fluctuation; it is a **1.43× systematic**.

M2's pilot saw 1.10× on 752 deg², which was consistent with the paper inside its (much wider)
interval; at 26× the area the discrepancy is unambiguous. **This is flagged, not explained.** The
most likely candidate is the definition of "detected": this screen requires a measured profile-fit
uncertainty in both bands (equivalent to AllWISE `ph_qual` ≠ 'U'), whereas the paper may apply an
S/N floor at this stage rather than at C6. Resolving it needs the paper's exact C2a definition and
is an M4 item — it propagates multiplicatively into every downstream rate, so **no absolute
sky-wide yield from this screen should be quoted until it is settled.** The stage-to-stage *pass
rates* in §2.2 are unaffected, because the factor divides out.

---

## 3. Vetting the survivors — the coded stages that replace the CNN and the eyeball

Hephaistos II's last two stages are C4 (a CNN whose weights are unpublished) and C7 (visual
inspection). Between them they carry almost all of the late-stage selectivity — 11,243 → 5,732 and
368 → 7 — and neither is reproducible. M1 recorded that as the reproducibility boundary; M3
replaces them with five coded gates, all of which run on every finalist and none of which requires
a human to look at a picture. `scripts/m3_vet_survivors.py`.

| gate | what it asks | provenance |
|---|---|---|
| **V1 `w?nm`** | was the source ever detected in a **single exposure**, or only in the coadd? | M2's axis 4, new to this project |
| **V2 release consistency** | do the **same photons**, reduced for the earlier WISE All-Sky Release, still give a detection in the band carrying the excess? | M2's axis 3, new to this project |
| **V3 sensitivity** | is the "detection" above WISE's own **5σ** standard, or is the excess at the instrument floor? | candidate I's failure mode (I-dossier) |
| **V4 chance alignment** | the prior for a faint red background galaxy, from **Suazo et al.'s own 15,000 sr⁻¹**, not Ren et al. 2024's 3616×-slipped figure | M2 §3 |
| **V5 centroid** | does the mid-IR centroid sit on the star, **stated with the 1–2″ floor**? | M1/M2, calibrated on D by JWST |

V3 is deliberately implemented from **the object's own catalogued S/N** rather than from an
external depth table: WISE's depth varies with ecliptic latitude and coverage, and the catalogue's
per-source S/N already encodes the local noise. The on-ecliptic 5σ fluxes (0.86 mJy W3, 5.4 mJy W4;
All-Sky Explanatory Supplement §1.1) are carried as a sourced auxiliary column, and every survivor's
ecliptic latitude is recorded.

### 3.1 Two bugs found by running the machinery at scale, one of which manufactures fake contamination

Neither was visible on the three objects M1/M2 measured. Both are the kind of thing this project
exists to catch, so both are recorded rather than quietly fixed.

**(a) The centroid test returned garbage for objects near a coadd-tile edge — and the garbage
looked exactly like contamination.** `ibe_find_tile()` took the **first row** IBE returns. IBE
returns one row per (tile, band) for every overlapping AllWISE coadd — 16 rows for a typical
position — in no useful order, and the first row is frequently a tile on whose **corner** the
target sits. The Atlas cutout then comes back silently **clipped**: a 90″ request returned a
**39 × 66 px** frame instead of 65 × 65, the target landed a few arcsec from the boundary, and the
"brightest pixel within 10″" search ran off the edge. The offsets it produced on the first five
survivors tested were **7.6″, 9.5″, 10.7″ and 11.9″** — values that, taken at face value, would
have been reported as four contaminated objects. **They are artefacts of the crop.**

Fixed two ways, because either alone is insufficient: (i) `ibe_rank_tiles()` now ranks every
distinct coadd by the target's distance to the **nearest tile edge**, best-centred first, and the
vetting tries up to three tiles per band; (ii) `measure_centroid()` carries an **edge guard** — if
the 10″ search disk is not wholly inside the frame it returns `offset = NaN` and
`edge_clipped = True` rather than a number. An object with no usable tile becomes INDETERMINATE,
never CONTAMINATION-CONSISTENT.

**Regression test:** control C reproduces at **W3 3.72″ ± 0.30** against Ren et al.'s published
3.67″ (M1's acceptance), and D (1.41″/2.55″) and I (2.64″/5.49″) reproduce M1/M2 exactly. The fix
changes nothing that was already validated; it only stops the machinery lying about objects M1/M2
never tested.

**(b) IRSA's TAP accepts exactly one `CONTAINS()` per query.** Two OR'd cones return "Invalid or
unsupported ADQL query string", so the natural batching silently fails and the fallback is one
query per position at ~16 s. Measured workaround: plain `ra`/`dec` `BETWEEN` predicates OR together
without complaint (5 positions in 12 s, 40 per query in production), with the exact radial cut
applied locally. Recorded because it is a property of the service that will bite again.

### 3.2 The centroid axis fails its own validity check at scale — so it does not get a vote

Running V5 on the finalists produced offsets clustering at **8–12″** with *high* aperture S/N —
not the sub-arcsecond values M1/M2 measured on C, D and I. Two objects were checked against the
AllWISE catalogue directly, and the cause is unambiguous:

| object | target | brightest W3 neighbour | measured "offset" |
|---|---|---|---|
| J065543.63+683451.9 | W3 = 11.33, S/N 9.1, 0.43″ from Gaia | **W3 = 10.40, S/N 19.4, at 10.24″** — 2.4× brighter | 9.51″ |
| J074515.30+851656.1 | W3 = 11.09, S/N 10.6, 0.03″ from Gaia | **W3 = 8.38, S/N 49.1, at 16.36″** — 14× brighter | 11.89″ |

**The peak-search centroid locks onto any brighter mid-IR source inside the 10″ search disk — or
onto the PSF wing of one just outside it** (W3 FWHM is 6.5″, W4's is 12″, so a bright source at
16″ still dominates the rim of a 10″ disk). It validated on C, D and I in M1/M2 because none of
those three fields contains such a neighbour. At scale, many do.

**Consequence, and the decision taken.** Applying PR-3's centroid criterion at face value would
have convicted **hundreds** of objects of contamination on the strength of an unrelated
neighbour — a textbook fake win, and precisely what this project exists to prevent. So:

- **V5 is not applied.** The offsets are kept in the output table as data, flagged invalid.
- The 326 objects that V1–V4 could not resolve are **INDETERMINATE**, not
  CONTAMINATION-CONSISTENT.
- Because STILL-CLEAN requires a *valid* centroid measurement, **no object can reach STILL-CLEAN
  in M3.** That is stated as a limitation of the run, not as a property of the objects.
- The search radius was **not** retuned to produce nicer numbers. Choosing a threshold after seeing
  the results is exactly the move the pre-registration exists to forbid.

**What M4 must do** (both, not either): shrink the peak-search radius to the astrometric match
scale (~3″) rather than 10″, and add a neighbour-aware validity check — a centroid is valid only if
no brighter AllWISE source in that band lies within the search radius plus one PSF FWHM. Both are
cheap; neither may be chosen by looking at the answers.

### 3.3 The survivor table — 845 finalists, four verdicts, and no candidate

`out/m3_survivor_table_m3_g0.1.csv`. Every verdict carries the standing centroid floor
(**1–2″**): "no offset detected" would have meant "no contaminant outside ~1–2″", never "no
contaminant" — and in M3 not even that much can be said, because V5 did not return valid
measurements.

| verdict | n | % of 845 |
|---|---|---|
| **CONTAMINATION-CONSISTENT** | **416** | 49.2% |
| **INDETERMINATE** | **326** | 38.6% |
| **SUB-THRESHOLD** | **103** | 12.2% |
| **STILL-CLEAN** | **0** | **0%** |

**There is no Matthew-gated survivor from this screen.** Nothing reached STILL-CLEAN, so nothing
is being flagged as a candidate, and nothing has been reported anywhere.

**Why the 416 were flagged** (reasons co-occur, so the column does not sum):

| axis | n | % of all 845 |
|---|---|---|
| `w4flg = 32` — the independent aperture photometry gives a **95% upper limit**, not a detection | 210 | 24.9% |
| `w3flg = 32` — same, in W3 | 192 | 22.7% |
| `w4nm = 0` — **never detected in a single exposure**, only in the coadd | 112 | 13.3% |
| release-inconsistent in **W4** | 58 | 6.9% |
| `w3nm = 0` | 32 | 3.8% |
| release-inconsistent in **W3** | 25 | 3.0% |

### 3.4 The two axes M2 invented, now measured on 845 objects instead of one

Both were devised on candidate I and neither had ever been run at scale. Both fire hard, and the
release axis fires **in one direction only**:

**(a) Single-exposure detections (`w?nm`).** `w4nm = 0` for **155 of 845 finalists (18.3%)** and
`w3nm = 0` for **70 (8.3%)** — objects whose mid-IR "detection" exists only in the coadd and was
never seen in any individual exposure. The median finalist has `w4nm = 2` against ~11 profile-fit
measurements, so even the detected ones are marginal in single frames.

**(b) Release consistency.** Of the 839 finalists present in both reductions, **112 (13.3%) have a
band that the WISE All-Sky release calls a non-detection ('U') and AllWISE promotes to a
detection** — 38 in W3, 74 in W4. **The reverse never happens: zero objects go from an All-Sky
detection to an AllWISE 'U'.** W1 and W2 show no 'U' in either release, so this is confined
entirely to the two bands that carry the excess.

That one-directional promotion is the general form of candidate I's problem (M2 §2b), and it now
has a population behind it: **at the flux levels where a "Dyson-sphere candidate" lives, more than
one finalist in eight owes its excess band to which WISE reduction you happen to read.** Neither
Hephaistos nor Ren applied this test; it costs one catalogue query per object.

**(c) Sub-threshold excesses.** 103 finalists (12.2%) have **both** excess bands below WISE's own
5σ detection standard (median S/N 4.10 in W3 and 3.80 in W4) while still passing the paper's
C6 ≥ 3.5 cut. The paper's threshold sits below its own survey's detection standard, and the gap
between 3.5 and 5 is populated.

---

## 4. The two method caveats, closed

Both sat unresolved in three documents (M1, M2 §4.2, M2 §5.3). Both are now closed by sources
rather than by inference — and closing them produced two findings that were not the point of the
exercise.

### 4.1 The Gaia `ew_espels_halpha` sign convention — VERIFIED CORRECT, and the gate is near-inert

**The convention: positive = absorption, negative = emission. Units are nm.** Three independent
sources, quoted:

- **Gaia DR3 datamodel**, `astrophysical_parameters`
  ([documentation §20.2.1](https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_astrophysical_parameter_tables/ssec_dm_astrophysical_parameters.html)):
  "Pseudo-equivalent width of the Hα line measured on the RP spectra … **The value is expected to
  be negative when emission is present.**"
- **ESP-ELS module documentation**
  ([§11.3.7](https://gea.esac.esa.int/archive/documentation/GDR3/Data_analysis/chap_cu8par/sec_cu8par_apsis/ssec_cu8par_apsis_espels.html)):
  "**The definition adopted is such that the pEW should be negative when emission is present** in
  the Hα domain."
- **Creevey et al. 2023** (Apsis I, A&A 674, A26; arXiv:2206.05864 §6.4.4): "the Hα pEW peaks in
  absorption (i.e. **positive values**) … the **negative** estimates are expected to belong to
  emission-line stars."

And the paper's own rule, **Suazo et al. 2024 §2.5.1** (not "C5a" — that label is this project's):
"sources with Hα equivalent widths **lower than zero (at 3σ)** are rejected, i.e., sources with Hα
in emission detected at 99.7% confidence."

**The implementation was already right.** `scripts/w1_selection.py` rejects when
`ew_espels_halpha < 0 and |ew| ≥ 3 × uncertainty`, which is algebraically identical to
`ew + 3σ < 0`. **No code change is needed; the caveat was that the direction had never been
sourced, and now it is.** Independent confirmation: the values this project pulled for the seven
published candidates match Suazo et al. Table 5 exactly where that table has entries —
A = 0.248 ± 0.076, E = 0.049 ± 0.100, F = 0.020 ± 0.068, G = 0.024 ± 0.097 — and are null exactly
where it prints "–" (B, C, D).

**Two findings that came out of closing it.** Neither was the object of the search:

1. **Three of the paper's seven candidates were never testable by their own Hα cut.** ESP-ELS was
   run only on targets brighter than **G = 17.65** (stated on every ESP-ELS field in the
   datamodel). The three candidates with null Hα are B (G = 17.713), C (18.393) and D (17.662) —
   and the seven with values are all brighter than 17.65. **The separation is exact, and D misses
   the gate by 0.011 mag.** The cut that Suazo et al. call "one of the most important parameters
   when weeding out interlopers" could not be applied to 3 of the 7 candidates it is quoted as
   defending — including D, which JWST later showed *was* contaminated.
2. **The gate is close to inert in the population the screen actually lives in.** The DR3
   documentation's own recovery fractions for ESP-ELS are 0.5 for Be stars, 0.3 for Herbig Ae/Be,
   0.05 for T Tauri and **0.001 for active M dwarfs** (§11.4.4) — and every Hephaistos candidate is
   an M dwarf. Candidate I demonstrates it on a single object: Gaia gives
   `ew_espels_halpha` = **+0.292 ± 0.167 nm** (= +2.9 Å, absorption, so the cut passes it), while
   Hephaistos III's own NOT/ALFOSC spectroscopy of the same star measures **Hα in emission at
   EW ≈ −2.8 Å** ([I-dossier](I-dossier.md), Korn et al. 2026 §3.2). Same line, same star,
   opposite sign, comparable magnitude. *Caveats, stated: the pEW is measured on 8-nm-resolution
   RP spectra against a local pseudo-continuum and the documentation says it systematically
   understates the true EW; for T_eff < 5000 K a model pEW is subtracted; and M-dwarf Hα is
   genuinely variable between epochs. The honest conclusion is not "Gaia is wrong" but* **"this
   cut cannot gate Hα emission in M dwarfs, and should not be quoted as though it does."**

**Consequence for this screen:** C5a is retained, implemented as written, and reported as
**near-inert** — it is not doing the interloper-rejection work the paper attributes to it, and the
funnel must not be read as though it were.

### 4.2 The template locus blueward — CLOSED, extended, and it was the funnel's biggest distortion

M1/M2 fitted only stars with **M_G 6–14.5** because the empirical photospheric locus was built from
<30 pc dwarfs, while Hephaistos II's 265 template stars spanned **M_G 0–13.6**. That excluded
two-thirds of the full-10-band stars and made the RMSE row of the funnel a **lower bound** rather
than a measurement (M2 §4.3 flagged this honestly and deferred it).

**It turns out nothing needed building.** Pecaut & Mamajek (2013) tabulate W1−W2, W1−W3 and W1−W4
themselves for **B9V…K3V** — 37 rows with M_G < 6.5 carrying all three colours plus Bp−Rp. The
famous gap in that table is **K6V…M5V (M_G 7.02–12.45) only** — precisely the range the empirical
locus was built to fill. Blueward of K5V the sourced colours were there all along.

**The cross-check that makes the splice safe** (`scripts/m3_locus_extend.py`,
`out/m3_locus_blueward_crosscheck.csv`). The same <30 pc query that built the M-dwarf locus also
returned 258 stars with M_G < 6.5. **Every one of them is in WISE's saturated regime (W1 < 8)**, so
they cannot *define* a locus — but they can *test* one:

| M_G bin | n | saturated | W1−W3 PM13 | W1−W3 empirical | diff | W1−W4 PM13 | W1−W4 empirical | diff |
|---|---|---|---|---|---|---|---|---|
| 0.5–3.0 | 9 | 100% | −0.064 | −0.010 | +0.054 | −0.027 | +0.060 | +0.087 |
| 3.0–4.5 | 56 | 100% | −0.045 | −0.035 | +0.010 | −0.014 | +0.020 | +0.034 |
| 4.5–6.5 | 193 | 100% | −0.037 | −0.028 | +0.009 | −0.016 | +0.038 | +0.054 |

Max |diff| **0.087 mag**, rms **0.050 mag**. A systematic in 2 of the 10 RMSE bands propagates as
√(2/10) × 0.050 = **0.022 mag**, against an RMSE gate of 0.2 — a **9× margin**. Splice continuity at
M_G 6.5 is +0.019 mag (W1−W3) and +0.061 mag (W1−W4).

**Regression test, because changing a template can silently break the acceptance that licenses
everything else.** All ten labelled candidates were re-fitted under both loci: RMSE, γ and T_DS
agree to **four decimal places for all ten, at both grid floors**. That is expected, and it is the
point — every one of them is an M dwarf (M_G 8.8–11.7), inside the range the extension does not
touch. **M1's 7/7 acceptance is untouched; the extension is purely additive.** It also reproduces
M2's boundary finding unchanged: candidate F's best RMSE at γ ≥ 0.10 is **0.2546** against a 0.2
threshold, so the paper's stated grid still does not admit the paper's own candidate.

**What it changes.** The template window now admits **158,097 of 160,410** full-10-band stars
(**98.6%**) against ~32% before. The RMSE row of the funnel is a measurement for the first time.

---

## 5. JWST GO 7199's third target — checked, and M2's prediction has NOT yet come true

M2 §0.4 predicted the JWST-vetted sample "will shortly be 3, not 2". **As of 2026-08-21 it is still
2.** The check, and what it found:

**No result on candidate A has been published anywhere.** arXiv API searches (all HTTP 200,
2026-08-21) over `all:Hephaistos` (9 hits, the complete set), `au:Zackrisson` (165), `au:Suazo`
(26), `all:"Dyson sphere(s)"` (50 each), `abs:technosignature` (198), `abs:megastructure` (37),
plus Assef, Siemion, Bik, Nabizadeh, Korn and Ren: **nothing Hephaistos-related after 2026-07-28**,
no "Project Hephaistos V", and no paper of any kind reporting the Object_A observation. Semantic
Scholar and OpenAlex both give arXiv:2607.09460 a citation count of **0**. *(NASA ADS was again
unreachable — 405/401 — as in M1/M2; this negative rests on arXiv + Semantic Scholar + OpenAlex,
and is that much weaker for it.)*

**The collaboration's own most recent papers confirm the negative from the inside.** Ren et al.
(arXiv:2607.03619 **v3, posted 2026-08-07**, accepted MNRAS) still writes in the future tense: "the
**ongoing** JWST GO 7199 observations of Candidates **A, D, and E** will provide the direct results
needed to identify the genuine contributors to their infrared excess." Its standing verdict on A
remains archival only — radio counterpart α = 0.40 ± 0.35, a ~3.3σ centroid-to-stellar offset,
"suggestive". Hephaistos III (Korn et al., arXiv:2607.25701, 2026-07-28 — i.e. 14 days *after* the
Object_A visit) says only "for **two** of our stars, JWST observations have recently revealed
superpositions with very red background galaxies".

**Exclusive access — and a date this project should care about.** GO 7199 carries a 12-month
exclusive access period ([STScI program info](https://www.stsci.edu/jwst-program-info/program/?program=7199&pi=1);
MAST CAOM query, 114 rows, 2026-08-21):

| target | observed (UT) | `t_obs_release` | rights |
|---|---|---|---|
| **Object_A** (MIRI/MRS) | **2026-07-14** | **2027-07-16** | EXCLUSIVE_ACCESS |
| Object_D + background | 2025-07-28 | **2026-07-28** | **PUBLIC — already** |
| Object_E + background | 2025-09-08 | **2026-09-09** | EXCLUSIVE_ACCESS (opens in 19 days) |

**Candidate D's JWST data are already public, and candidate E's open on 2026-09-09.** That is
directly analysable with machinery this project already has, and it is a better near-term lever
than waiting until 2027-07-16 for candidate A.

**One flag, raised but not concluded.** In the STScI visit status report, Obs 4
(Object_A_background) ran **0.46 h of a planned 2.56 h** (18%), is the only visit still marked
"Executed" rather than "Archived", and is the only observation with no calibrated products in MAST.
Consequently **there are no MIRI *imaging* products for Object_A at all** — for D and E the
F560W/F1000W/F1500W frames hang off the `_background` observations, and A's never materialised, so
A's archive holding is MRS spectroscopy with no dedicated background subtraction. Counterweights,
stated: the allocation history shows **no** FAILURE_REPEAT entry, and STScI marks a program
"Completed" once its completion threshold is met. **UNSOURCED: any cause for the short duration.**
This is worth watching, not interpreting.

**Effect on the tally: none yet.** The README premise block stands as written — five candidates with
an identified contaminant (B, C, D, E, G), two of them by JWST. A dated line has been appended to
the README recording that the third JWST target remains unpublished and when its data open.

---

## 6. The route to the other half of the sky — measured, and handed to M4

The pull is blocked on one thing: ESAC will not complete a query that touches the join tables. That
is not a reason to accept 48% for ever, so the alternatives were measured rather than assumed.

| route | result, 2026-08-21 | usable? |
|---|---|---|
| ESAC sync, smaller tiles | wall is **size-independent** (13.4–214.9 deg² all die at 61.5–62.7 s) | no |
| ESAC sync, fewer joins | 4-table dies at 61.9 s; bare **3-table `COUNT(*)` dies at 79.8 s** | no |
| ESAC anonymous async | hung > 28 min on a trivial query, killed (M2 saw HTTP 500) | no |
| ARI-Heidelberg TAP | `OverflowError` on `source_id` in the VOTable — the service returns unusable types | no |
| VizieR TAPVizieR | rejects `gaiadr3.gaia_source` (different schema names) | not as-is |
| **AIP (`gaia.aip.de/tap`)** | **hosts everything needed** and answers in **0.2–0.9 s** | **yes, with work** |

**The AIP mirror is the live lead.** It hosts `catalogs.allwise` (all four bands, `cc_flags`,
`ext_flg`, `ph_qual`), `catalogs.tmass` (`j_m`, `h_m`, `k_m`), and both DR3 cross-match tables
(`allwise_best_neighbour` with `allwise_oid`, `tmass_psc_xsc_best_neighbour`). Crucially,
**anonymous async works there** — a job posted with no credentials returned 303 and reached
COMPLETED — where ESAC's anonymous async is dead. **No account is needed, so the project's hard
rule is not touched.**

Two measured constraints, and the fix for each:

1. **Anonymous limits are tight**: sync statement timeout ≈ **8 s**; async `executionDuration`
   = **30 s** (the 215 deg² join reached EXECUTING and then ERRORed at exactly 30 s). Unlike
   ESAC's wall, this is a genuine *execution* limit, so it **is** size-dependent — the fix is
   smaller tiles (~1/8 of the current 215 deg², i.e. `--rasplit 64`), which is exactly the lever
   that does not work against ESAC.
2. **AIP has no EDR3 Bailer-Jones distances** (only `gaiadr2_contrib.geometric_distance`), so cut
   C1 (`r_med_geo < 300`) has no direct equivalent. **This was calibrated, not guessed**, against
   the 95,310 already-harvested ESAC rows that carry both columns:

   | statistic | value |
   |---|---|
   | median of (1/ϖ − r_BJ)/r_BJ | **+0.36%** |
   | 5th–95th percentile | −0.14% to +1.01% |
   | within 5% / 10% | **99.17% / 99.69%** |
   | recall of `1000/ϖ < 300` against the true `r_med_geo < 300` | **99.09%** |
   | `ϖ > 2.5 mas` as a superset pre-filter | **100%** retained (loses nothing) |

   So `ϖ > 3.333 mas` reproduces the Bailer-Jones cut with ~1% loss, and `ϖ > 2.5 mas` is a
   lossless superset. **Honest limitation:** the pull applied `r_med_geo < 300` server-side, so
   this sample contains no objects *outside* the cut — **recall is measured, purity is not**. M4
   must measure the false-positive rate on a sample that includes the complement before adopting
   the proxy.

**M4's acceptance test is already defined and free:** re-harvest several of the 93 tiles ESAC
*did* deliver, through AIP, and require the same `source_id` set. Anything else is a route
difference that must be understood before the other 52% of sky is trusted.

---

## 7. Recommended M4

1. **Finish the sky through the AIP mirror** (§6). Everything needed is hosted there, anonymous
   async works with no account, and the two constraints are measured: re-tile to ~27 deg² to fit
   the 30 s execution cap, and substitute `ϖ > 3.333 mas` for the Bailer-Jones cut (recall 99.09%
   measured; **purity still to be measured** on a sample that includes the complement).
   **Acceptance test before any new sky is trusted: re-harvest several of the 93 ESAC tiles through
   AIP and require the same `source_id` set.** Keep ESAC's own pull running in parallel under PR-1
   — it costs nothing and the load may lift.
2. **Settle the 1.43× parent-sample discrepancy** (§2.4) before any sky-wide yield is quoted from
   this screen. It needs Suazo et al.'s exact C2a definition, and it multiplies into every
   downstream number.
3. **Attack the Gvar reference-sample gap** (§2.2), which is now the largest unexplained factor in
   the funnel — the extra cuts reject 11% here against the paper's 54%. M1 established that Gvar is
   reference-dependent; M4 should measure how the survivor count moves as the reference sample is
   varied, and quote the funnel with that as a band rather than a point.
4. **Analyse candidate D's public JWST data** (§5). It has been public since 2026-07-28, candidate
   E's opens 2026-09-09, and this project has the machinery. D is the object whose contaminant
   calibrates the centroid floor that every verdict in §3 carries — measuring it directly, rather
   than citing Hephaistos IV for it, would put the project's own number under its own standing law.
5. **Re-run §3's vetting on the full sky** once M4's coverage lands, and re-check any STILL-CLEAN
   survivor against the release-consistency and single-exposure axes before it is called anything.
6. **Matthew's calls, unchanged and still waiting** (M2 §5.5): (a) whether the Ren+24 unit-error
   note is worth submitting given Blain's prior "(sic)", and if so the three manual browser checks
   first (IOP page, PubPeer, ADS); (b) whether the candidate-I dossier becomes a JWST DDT/small-GO
   proposal, an RNAAS note, or stays internal. **Nothing in M3 changes either gate.**

---

## 8. File index (new in M3)

**Document:** `M3-full-screen.md` (this).

**Scripts:**

- `scripts/m3_locus_extend.py` — builds the blueward-extended photospheric locus and prints the
  PM13-vs-empirical cross-check that licenses it (§4.2)
- `scripts/m3_funnel_report.py` — the stage-by-stage funnel with exact Poisson intervals and the
  sky fraction on every projection; the only source of the numbers in §2
- `scripts/m3_vet_survivors.py` — the five coded vetting gates and the PR-3 verdict logic (§3)
- `scripts/m3_route_diag.py` — the ESAC size/join diagnostic that showed the wall is
  size-independent (§1.2)

**Scripts changed:**

- `scripts/w4_screen.py` — instant-failure classifier, outage breaker with cooldown/probe ladder,
  `--reset-failed`, load backoff, `covered_area()` (no parent/child double counting), `repair`
  no longer resurrects popped descendants, `select` takes `--locus` / `--mg-lo` / `--mg-hi`
- `scripts/w2_centroids.py` — `ibe_rank_tiles()` / `ibe_tiles_for()` (best-centred coadd, not
  IBE's first row) and the `edge_clipped` guard in `measure_centroid()` (§3.1a)
- `scripts/w1_selection.py` — `use_locus()` so the template locus is selectable

**Artifacts** (pilot files preserved; M3's carry the `m3_` tag):
`out/w4_funnel_m3_g0.1.json`, `out/w4_funnel_m3_g0.01.json`,
`out/w4_rmse_survivors_m3_g0.1.csv`, `out/w4_previsual_candidates_m3_g0.1.csv` (+ `g0.01`),
`out/m3_funnel_report.md`, `out/m3_funnel_report.json`,
`out/m3_survivor_table_m3_g0.1.csv`, `out/m3_verdict_counts_m3_g0.1.json`,
`out/m3_vet_cache_m3_g0.1.csv` (the cached V1/V2 catalogue axes),
`out/m3_locus_blueward_crosscheck.csv`, `out/m3_route_diag.json`, `out/m3_join_diag.json`,
`data/photometry/wise_locus_extended.csv`.

**Nothing in this milestone has been submitted, posted, or sent anywhere.**
