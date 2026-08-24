# M10 — The ledger refreshed for review, the clock re-measured, and the shell opened

**Date:** 2026-08-18 · **Status: COMPLETE** · **ITF universes:** the M7/M8 snapshot
(2026-08-16 20:27:01 GMT, exactly reconstructed — M9 §0.1) for every sweep and fit, and
a **fresh pull taken now** (2026-08-18 21:26:46 GMT) for the liveness refresh. **Nothing
was submitted anywhere. Candidates are candidates.** `m8-ledger.json`,
`m9-ledger.json`, `m9-combined.json` and `m9-adjudication.json` are read-only inputs;
M10 appends (`m10-refresh.json`, `m10-decay.json`, `m10-adjudication.json`,
`m10-shell.json`, `m10-shell-ledger.json`, `m10-pointed.json`,
`m10-distant-fits.json`) and emits **`out/review-queue.csv`**. Tests: 485 green.

**One-line result:** the whole cumulative ledger was refreshed against an ITF pull taken
that hour — **733 live PASS rows, 33 consumed, and of the 33 the MPC took, 31 went where
the ledger said, including 21 of 21 PASSes**; the two that did not were **both rows the
strict gate had already refused**, which is the gate's first measured true negative. The
decay clock, re-measured across three intervals instead of one, turns out to be
**entirely concentrated in M8's queue head** (half-life 32 d there, against **zero of 272**
M9 PASS rows consumed; Fisher p = 7 × 10⁻⁵), which tells a reviewer not just to hurry but
*where* to hurry. `out/review-queue.csv` puts 701 still-live rows in front of a human in
submission-value order. The 15–25 y main-belt shell, on a gate **derived** from M9's
measured envelope, opens and yields **71 PASS rows across 58 objects out to −20.7 y** —
with three caveats that belong on the same page. M9's 60 ambiguities adjudicate **57–3**
with no claimant ever owning a tracklet. And the pointed-field screen, validated **3/3**
against the pre-registered target, finds **0 of 735** live ledger rows contaminated,
exposes a **second** artefact class on the way (self-designation), and turns the all-sky
distant sweep into a clean negative with both confounds controlled.

---

## 0. Pre-registered decisions (written before the runs they govern)

### 0.1 Snapshot discipline, and which universe each question lives in

Two universes, kept strictly apart, because they answer different questions:

* **Liveness and decay** are questions about *today*, so they run against a pull taken
  now. The daily archive last wrote 2026-08-18 15:29:03 GMT; the MPC regenerated the
  ITF again at **21:26:46 GMT**, so M10 fetches that pull **into a scratch directory
  outside the repository** and parses it there. `data/raw/itf.txt.gz`,
  `data/parquet/itf_observations.parquet`, `data/snapshots/` and the archive clone are
  **not written to** — the archive's chain stays exactly as the daily task left it, and
  M10's liveness answer is still six hours fresher than the newest archived snapshot.
* **Every sweep and every fit** runs against the reconstructed 2026-08-16 snapshot
  (`data/parquet/itf_observations_20260816_reconstructed.parquet`), the universe M8 and
  M9 swept. A candidate found in a different universe is not comparable to the ledger
  it is being appended to.

The decay curve uses the archive's slim `obs_key` tables for **2026-08-16 20:27:01**,
**08-17 12:26:49** and **08-18 15:29:03**, plus the fresh 21:26:46 pull: four points,
three intervals.

### 0.2 The 15–25 y main-belt shell — gate derived, not chosen

M9 §8 measured the perturbed main-belt envelope to ≤ 150″ through 25 years, breaking at
28 (303.8″). The M10 shell gate is the **M7/M8 formula with nothing else changed**:

```
gate(Δt, U) = 120″  +  1.5 × envelope(|Δt|)  +  0.01 × 10^(0.868·U) × |Δt| / 3652.5 d
```

`envelope` is `m9-calibration.json`'s `perturbed_envelope_arcsec_mainbelt_25y`,
monotone-max-accumulated exactly as `m8_attribution.envelope_fn` does it. The floor
(120″), the safety factor (1.5) and the U-runoff are **untouched** — they model the
orbit's own uncertainty and the geocentric approximation, which extending the lookback
does not change. Substituting the measured numbers, the running max at 25 y is 149.43″,
so the envelope term is 224.1″ and the gate is ≈ **346″ at U = 2, 893″ at U = 5**.
(M9 §8's off-hand "near 470″ / near 1,500″" was an estimate made without evaluating the
formula; the derived values above supersede it.)

* **Window: 15 y < |Δt| ≤ 25 y, strictly.** The 0–15 y shell is already swept by M8+M9;
  re-sweeping it would re-propose candidates that are already in the ledger.
* **Orbits:** the union of M8's and M9's swept orbit tables at the frozen U ≤ 6 cut,
  deduplicated by primary designation.
* **Decoy:** the same half-period phase-shifted control, on the identical window, gate
  and night set. Its job is to price the sub-60″ head, as in M7–M9.
* **Stopping rule for the shell fit queue** (in-loop, `--pass-floor-per-100`, not
  applied by hand): tranches of 100 new fits; **stop when the trailing-100 strict +
  fully-used pass rate drops below 20/100**; hard budget **400 new fits**; time
  backstop 90 minutes. Whichever binds first is the reported stopping reason.
* No gate, radius, window or rank formula is touched to keep the queue alive
  (standing constraint 5). A zero yield reported plainly is a result.

### 0.3 Adjudicating M9's 60 new ambiguities — M9 §0.4's standard, verbatim

Nothing loosened, nothing re-derived. Informative claimant = SkyBoT ephemeris error
**≤ 60″** (the frozen PD152-grade bar). Each claimant is fitted against **its own
published astrometry** plus the disputed tracklet, with the frozen strict post-fit gate
and the "tracklet fully used" primary gate; ≤ 5 claimants per candidate. Verdicts:
`RESOLVED_TO_CANDIDATE` · `REJECTED` · `STILL_AMBIGUOUS` (a claimant also passes, or
cannot be fitted — what cannot be fitted cannot be excluded) ·
`RESOLVED_BY_MPC_CONSUMPTION`. Exhaustive over all 60 rows: no stopping rule, no budget,
no standard-loosening. M9's own 88 are **not** re-litigated.

### 0.4 The pointed-field screen — its validation target declared in advance

M9 §8 found the confound: a survey **following a known object** deposits
position-correlated ITF debris near that object's prediction, and the phase-shifted
decoy cannot price it (a decoy orbit's sky position coincides with nobody's pointed
fields). The screen, pre-registered before it was written:

> A candidate is **`POINTED_FIELD`** if the attributed object's own published record
> contains an observation from the **same station** within **±1 hour** of any of the
> tracklet's observation instants. A weaker **`SAME_NIGHT_FIELD`** flag fires at
> ±1 day. Both are computed from the object's published astrometry and the tracklet's
> own, with no reference to which of them "looks right".

**The validation target is declared here, before the screen was run.** Against M9's
three failed distant candidates the screen must:

1. flag **2008 CT190 ← `LA1140`** (published same-station rows at Δt = 0.0 s), and
2. flag **2004 VV130 ← `DT20B11`** (same), and
3. **not** flag **2011 EZ90 ← `s25473`** (M9 verified no same-station published row
   within a day; it failed the *fit*, which is a different and correct reason).

If the screen does anything else it is wrong, and that is what gets reported — it does
not get retuned until it passes. Only if it hits 3/3 is the bounded distant sweep
re-run with it active.

---

## 1. The ledger refreshed: 733 live, 33 consumed, and the first two disagreements

`scripts/m10_refresh.py` tested **every** fitted row of both ledgers plus M7's three
held candidates — **1,903 rows** — against four ITF snapshots, and asked of every
consumed one where its observations actually went (live `get-obs` into a fresh cache,
the ledger's own 2 s / 2″ duplicate rule).

| | count |
|---|---:|
| Cumulative ledger rows tested | **1,903** (M8 900 · M9 1,000 · M7 held 3) |
| Still live in the 21:26 ITF | **1,870** |
| Consumed by the MPC since 08-16 | **33** |
| … `CONSUMED_AND_AGREED` | **31** |
| … `CONSUMED_AND_DISAGREED` | **2** |
| PASS rows | 754 |
| … **still live** | **733** |
| … consumed | 21, **21/21 agreed** |

**The chain has still never been contradicted on a row it passed.** All 21 consumed
PASS rows went to exactly the object the ledger named — M9's 21/21 reproduced
independently against a six-hour-newer pull — plus the ALREADY_LINKED control and 9 of
the 11 consumed FAILs.

### 1.1 The two disagreements — the strict gate's first true negatives

Both fired in the last six hours, and **both are `FAIL` rows**:

| row | verdict | why the chain refused it | where the MPC put it |
|---|---|---|---|
| 2025 MK161 ← `N069282` (W84, −12.13 y) | FAIL | joint RMS **0.391″ vs 0.083″ baseline** (4.7× worse), 3/4 used, joint set 20/27 | not into MK161 |
| 2025 ML131 ← `H468861` (T09, −9.11 y) | FAIL | **0/3 used** — fo refused every observation; joint RMS *identical* to baseline | not into ML131 |

This is the measurement M9 could not make. M9 saw 8 consumed FAILs and all 8 had been
accepted by the MPC into the matched object, which reads as pure over-conservatism. M10
has **11 consumed FAILs: 9 over-conservative, 2 correct** — the first evidence that the
strict gate's rejections are sometimes rejections of *wrong attributions*, not merely of
true ones the MPC's looser published rule would have kept. Both correct rejections came
from the primary gate (did fo use the tracklet), not from the RMS ceiling.

**The obvious alternative explanation was checked and fails.** A consumed tracklet whose
destination record had simply not been republished yet would look identical. It is not
that: the third row consumed in the same six-hour window, **2025 NN366 ← `C3H5VK2`**,
shows NN366's published record gaining **exactly those four G96 rows of 2020-10-15**,
while MK161's and ML131's records are byte-identical to the 08-16 cache. The MPC's object
records update in the same cycle as the ITF removal, so "not there yet" is not available.

## 2. The decay clock, with an uncertainty — and it is not one number

M9 measured the clock from a single difference. The archive's slim `obs_key` tables plus
a pull taken now give **four points and three intervals** (`scripts/m10_decay.py`).

**M9's headline reproduces exactly as a special case:** M8's 900 fitted rows, 30 consumed
over 2.0415 d = **3.27 %/2 d (95 % CI 2.30–4.63)**, half-life **41.7 d**. But pooling was
hiding the structure:

| population | consumed / n | %/2 days (95 % CI) | half-life (95 % CI) |
|---|---:|---:|---:|
| **M8 PASS** | 21 / 482 | **4.27 (2.81–6.44)** | **31.8 d (20.8–48.6)** |
| M8 fitted, queue **top half** | 22 / 450 | 4.79 | 28.2 d |
| M8 fitted, queue **bottom half** | 8 / 450 | 1.74 | 78.9 d |
| **M9 PASS** | **0 / 272** | **0 (0–1.37)** | **> 101 d** |
| … M9-extension PASS | 0 / 220 | 0 (0–1.68) | > 82 d |
| … M9-partitions PASS | 0 / 52 | 0 (0–6.74) | > 20 d |
| all fitted (1,900) | 33 | 1.70 (1.21–2.38) | 80.8 d |

**The decay is concentrated entirely in M8's head.** M8 PASS 21/482 against M9 PASS
0/272 is a **Fisher one-sided p = 7.1 × 10⁻⁵** — not a sampling accident. Inside M8's own
queue the top half decays 2.8× faster than the bottom. What the MPC's designation-time
sweeps eat is exactly the shallow, small-separation head of the same distribution; the
deep-rank and fresh-partition rows M9 added are, on this evidence, not being touched at
all. M9 §5 guessed this ("what the MPC's sweep does *not* appear to reach ... is exactly
where the remaining value sits"); it is now measured, and it is a large effect.

**The hazard is also bursty, not smooth.** Per-interval hazards on the PASS population
run **0.80 %/d → 2.01 %/d → 0.00 %/d** across the three intervals, while the fitted
population sits near-flat at 0.87 / 0.89 / 0.65 %/d. Consumption arrives in MPC batch
sweeps, so any single-interval estimate — M9's included — samples one burst, and the
interval CIs above are the honest width.

**What it implies for review latency.** The perishable asset is M8's PASS head: ~1-month
half-life, ~4 weeks at the very top of the queue. At 4.3 %/2 d that is roughly **10 of
the 461 live M8 PASS rows gone per week**. The 272 M9 PASS rows carry no measurable clock
yet. So the review queue in §3 ranks by submission *value*, and this section supplies the
ordering *within* it: **work the M8 rows first.**

## 3. `out/review-queue.csv` — the artifact

`scripts/m10_review_queue.py` → **701 rows, 694 objects, 737 tracklets, 379 KB** (the cap
was ~2 MB). Only still-live rows; ten spot-check rows repeated at the top under a
`SPOTCHECK` marker; UTF-8 with BOM so Excel does not mangle it.

| tier | rows | what it is |
|---|---:|---|
| **A** | **33** | `combined_pass` objects with every member still live — the project's strongest artifacts |
| **B** | **527** | caveat-free single PASS rows |
| **C** | **137** | PASS rows with a named caveat (a lost-object ambiguity *carrying its adjudication verdict*, or a joint-fit demotion) |
| **D** | **4** | BORDERLINE + M7's held rows — Matthew's call, and always has been |

Within A and B the sort key is **arc extension in days** — how far outside the object's
published arc the new astrometry sits, which is what a submission is actually for. Median
arc extension across the queue is **+1,837 d**, max **+5,056 d**; **627 of 701 rows are
beyond the old 4-year two-body wall**; 28 rows extend nothing and say so ("densifies,
does not extend"). Cross-survey as ever: F51 429 · F52 74 · W84 68 · T09 55 · G96 46 ·
V00 17.

Every row carries what a human can adjudicate on — tracklet key(s), station, arc
extension, joint and baseline RMS, σ_a ratio, an explicit gate string
(`strict=Y published=Y tracklet-used=4/4 sep=71.8"/gate=2658.2"`), SkyBoT status, the
ambiguity verdict, the pointed-field screen (§6), and a one-line *why this is real*.
The head of the file:

| rank | tier | object | trk | arc ext | joint RMS | σ_a ratio |
|---:|---|---|---:|---:|---:|---:|
| 1 | A | 2025 PC147 | 2 | **+5,029 d** | 0.240″ | 0.021 |
| 2 | A | 2025 MB255 | 2 | +4,695 d | 0.084″ | 0.0013 |
| 3 | A | 2026 ED8 | 3 | +4,342 d | 0.079″ | 0.033 |
| 4 | A | 2025 PJ65 | 3 | +4,115 d | 0.131″ | 0.064 |
| 34 | B | 2025 LY5 | 1 | +5,056 d | 0.102″ | — |

One deduplication worth naming: **2025 MQ241 + `nf2088` is both an M7 held row and M8's
BORDERLINE row** — one candidate recorded twice across two milestones, which a reviewer
working from either document alone would have counted twice. The queue emits it once,
from the re-fitted ledger row, with M7's note attached.

## 4. M9's 60 ambiguities, adjudicated — 57 resolved, 3 standing

`scripts/m9_adjudicate.py` (the wired script, M9 §0.4's standard verbatim, nothing
loosened) over M9's 60 PASS-with-ambiguity rows: **75 claimant joint fits + 70 claimant
baselines**, ~40 minutes of fo, tags `mag####`/`maf####` into `data/m10-fits/`.
`m9-adjudication.json` is untouched; the output is `m10-adjudication.json`.

| adjudication | count |
|---|---:|
| **RESOLVED_TO_CANDIDATE** | **57** |
| **STILL_AMBIGUOUS** | **3** |
| REJECTED | **0** |

**72 of 75 claimants are excluded by their own astrometry.** The pattern M9 measured
holds on a second sample: lost objects carrying 10⁵–10⁷ arcsecond ephemeris errors
blanket the ecliptic and claim everything, then predict nothing once their own data is
made to speak. Across both milestones the standing total is **148 ambiguities
adjudicated — 141 resolved to the candidate, 3 resolved by MPC consumption, 4 still
ambiguous, and not one claimant has ever owned a tracklet.**

The three that stand:

* **2025 PJ65 ← `N044699`** (W84, n56772) — candidate 0.104″; claimant **2016 UD180**
  fits it fully used at 0.210″ with both gates passing.
* **2025 PJ65 ← `N106006`** (W84, n56773) — candidate 0.107″; claimant **2016 UD180**
  at 0.250″.
* **2025 MQ287 ← `ZTA92C4`** (G96) — candidate 0.249″; claimant **2016 FB99** at
  **0.218″: the claimant fits *tighter* than the candidate.** The strongest ambiguity
  the project has found.

The first two are **one hypothesis, not two**: 2016 UD180 claims both members of a
consecutive-night W84 pair *inside a tier-A combined object*. That is a coherent rival
explanation of the same evidence, and the queue says so on 2025 PJ65's row
(`STILL_AMBIGUOUS (2/3 members)`) rather than burying it in two unrelated-looking rows;
the third member is separately resolved. Tightness is not the frozen standard, so all
three stay STILL_AMBIGUOUS and the call is Matthew's.

## 5. The 15–25 year main-belt shell: the window opens and it yields

`scripts/m10_shell.py` runs M8's machinery unchanged on the §0.2 substitutions —
the shell window, M9's measured main-belt envelope, and the union of M8's and M9's orbit
tables (**56,659 rows → 26,924 at the frozen U ≤ 6 cut**, zero overlap between the two).
Universe: the reconstructed 08-16 snapshot, **2,553,500 tracklets over 8,424 nights**.

**The derived gate, evaluated rather than guessed:** 261″ at 15 y and **346″ at 25 y for
U = 2**, 589″ → 891″ for U = 5, and 2,682″ → 4,380″ for U = 6 where the frozen U-runoff
term dominates. Nothing was widened by hand; the U = 6 width is the existing formula's,
and §5.3 is where it comes back to bite.

### 5.1 Coarse sweep and decoy, 26,924 orbits × 2.55 M tracklets in 12 minutes

| | real | decoy |
|---|---:|---:|
| coarse matches | 165,297 | **188,494** |
| orbits with ≥ 1 match | 8,861 | 8,921 |
| **[0″, 5″)** | **14** | 3 |
| **[5″, 15″)** | **62** | 20 |
| [15″, 30″) | 85 | 66 |
| [30″, 60″) | 292 | 274 |
| [60″, 120″) | 1,024 | 1,185 |
| median separation | 2,418″ | 2,387″ |

**Sub-15″ head: 76 real vs 23 decoy — a 3.3× excess (4.7× under 5″).** The aggregate
decoy again sits *above* the real count (M8's did too), and again it does not matter: the
decoy's job is to price the head, and the head is priced. The excess is smaller than
M8/M9's 13× at < 5″, which is what a harder window should look like.

Lookback coverage is genuinely the whole shell — coarse |Δt| runs 15.00 to 25.00 y with a
median of 20.5 y and 14,717 matches in the 24–25 y bin — so the shell is not secretly a
15–17 y sweep with a long empty tail.

### 5.2 The fit queue, and the rule firing exactly as written

**Stopped at 300 fits on `trailing_100_pass_rate(14)_below_floor(20)`.** Tranche pass
rates **37 · 25 · 14**; neither the 400-fit budget nor the 90-minute backstop ever bound.
3.78 s per fit. All 300 converged — not one `tracklet_lines_missing`.

The verdict chain (`scripts/m10_verdicts.py`, M8's chain imported unchanged, 73 SkyBoT
cone searches) gives **71 PASS across 58 objects, 2 BORDERLINE, 227 FAIL** —
`m10-shell-ledger.json`, with `m8-ledger.json` and `m9-ledger.json` untouched. **All 71
are still live in the 21:26 ITF.** Lookbacks run **−15.36 y to −20.74 y**. Eighteen carry
lost-object ambiguity flags, named and not yet adjudicated.

The strongest rows are the ones where several tracklets of the same object land at the
*same* small separation — a systematic offset is what a real orbit error looks like;
chance alignments inside a 344″ gate do not cluster:

| object | tracklets | station(s) | Δt | separations | joint RMS |
|---|---:|---|---:|---|---:|
| **2016 UH221** | 2 | 705 | −19.7 y | **2.7″, 2.8″** (gate 344″) | 0.144″, 0.142″ |
| **2021 SZ54** | 3 | 705 | −20.5 to −20.6 y | **5.1″, 5.2″, 5.9″** (gate 352″) | 0.150–0.154″ |
| **2015 KP488** | 2 | **691 + G96** | −18.8 y | **8.9″, 9.9″** (gate 352″) | 0.115″, 0.242″ |
| **2025 HE54** | 2 | 705 | −19.6 y | 5.6″, 7.2″ | 0.065″, 0.048″ (**better than the 0.130″ baseline**) |
| **2025 NK502** | 4 | 705 | −19.6 y | 53.7–86.7″ | — |
| 2025 OU331 | 1 | 705 | −20.70 y | 3.1″ (gate 352″) | 0.123″ |
| 2025 NO313 | 1 | F51 | −15.36 y | 2.1″ | 0.081″ |
| 2025 MQ234 | 1 | 695 | −19.64 y | 4.6″ | 0.048″ |

Thirteen objects carry ≥ 2 passing shell tracklets.

### 5.3 Three caveats that belong on the same page as the yield

This is a positive result and it has to be read with what weakens it, or the next
milestone will over-trust it.

1. **The shell's yield is one observatory's archive.** 47 of the 71 PASSes are station
   **705 (Palomar)**, and only **2 of 71 are cross-observatory** (2015 KP488's
   691 + G96 pair). The ITF's distinctive value is the cross-survey pool — M3 onward
   ranks cross-observatory links first precisely because *surveys link their own data*
   (`HANDOFF.md` §5). A same-station cluster of unlinked Palomar tracklets is a much
   weaker proposition than a genuine cross-match, and every row now says which it is
   (`cross_observatory`, `sibling_stations`).
2. **Short tracklets pass the primary gate more easily.** 56 of the 71 PASSes are
   **2-observation** tracklets, and the pass rate by length is **33 % at 2 obs against
   15 % at 3 and 18 % at 4**. "Fully used" is a weaker constraint when there are only two
   observations to use, so the length distribution is itself a caveat and not a detail.
3. **The gates are wide where U is.** The median PASS sits at 50″ inside a 3,502″ gate,
   because the frozen U-runoff term reaches 4,380″ at 25 y for U = 6. That width was
   inherited, not chosen — but a 100″ match inside a 3,600″ gate is a much weaker prior
   than a 3″ match inside 344″. The ranking does carry information (PASS median sep/gate
   0.018 vs FAIL 0.026), just not much of it.

The honest summary: **the 15–25 y window is open and productive, and its credible core
is small** — the ~17 rows at sep < 60″ inside a gate < 600″, led by the multi-tracklet
and cross-observatory examples above. The other ~54 are wide-gate, short-tracklet,
single-survey rows that deserve a decoy-controlled *fit-stage* test before anyone treats
them as candidates. They are recorded, not promoted, and they are **not** in
`out/review-queue.csv`.

## 6. The pointed-field screen — validated 3/3, and what it found

`scripts/m10_pointed.py` implements §0.4's screen and runs it against the target declared
before the file existed.

| M9 candidate | expected | screen says | evidence |
|---|---|---|---|
| 2008 CT190 ← `LA1140` (688) | flag | **POINTED_FIELD** | 2 published same-station rows at **Δt = 0.0 s**, 34.3″ and 29.6″ away |
| 2004 VV130 ← `DT20B11` (T12) | flag | **POINTED_FIELD** | same-station rows at **Δt = 0.0 s**, 37.1″ away |
| 2011 EZ90 ← `s25473` (645) | do not flag | **clean** | no same-station published row within a day |

**3/3 against the pre-registered target**, and the geometry is unambiguous rather than
marginal: the two flagged cases sit at *exactly* zero seconds, the signature of the same
exposure, not of a coincidence at a tolerance chosen after the fact.

### 6.1 The main-belt ledger is clean of it — measured, not assumed

M9 §8 wrote that the pointed field is "a measured confound the main-belt sweeps never
had". That was an inference from how the regimes differ, not a measurement — and the
main-belt ledger is what is about to be submitted. So the screen was run over **all 735
still-live PASS/BORDERLINE rows**:

| flag | rows |
|---|---:|
| **`POINTED_FIELD`** | **0** |
| `SAME_NIGHT_FIELD` | 5 |
| `DUPLICATE` | 0 |
| clean | 730 |

**Zero of 735.** Four of the five weaker flags sit 20.5–23.9 h and 99–749″ from the
nearest same-station published row — a different night, far away, not a pointed field in
any useful sense. Only **2025 HJ109 ← `WV89BC5`** (G96, −10.58 y) is genuinely close:
1.6 h and 21.0″. It stays a PASS with the flag named on its queue row, because the
screen's pre-registered action at that separation is *name it*, not *drop it*.

Why the regimes differ is worth writing down, because it predicts where the confound
reappears. A distant sweep proposes tracklets near objects surveys **deliberately track**
— recovery astrometry of known TNOs is scheduled work. A main-belt precovery sweep
proposes tracklets from 11–25 years before the object was discovered, when by
construction nobody was pointing at it. **The confound is a property of follow-up, so it
scales with how interesting the object already was.**

### 6.2 A second artefact the screen run exposed: self-designation

The all-sky head's tightest rows included trkSubs like `/18K03H` sitting 2.6″ from
**2018 KH3**, `/24P08P` 0.5″ from **2024 PP8**, `/21G57Q` 0.8″ from **2021 GQ57**,
`/20K11R` 1.6″ from **2020 KR11**. Those seven-character trkSubs *are* each object's own
packed provisional designation (`K18K03H`, `K24P08P`, `K21G57Q`, `K20K11R`) with the
leading century byte replaced by `/`. They are the object's own observations parked in
the ITF under a placeholder designation.

**This would have passed everything.** The separation is tiny because it *is* the object;
the joint fit is excellent for the same reason; the duplicate rule does not fire because
these rows are precisely the ones the MPC has *not* linked; and the SkyBoT cone search
finds the object itself and records it as **confirmation**. A one-line identity check
catches it, and `scripts/m10_pointed.py::self_designation` now does.

Measured across **all 1,971 M8 + M9 + M10-shell ledger rows: 0 matches.**
`out/review-queue.csv` is clean of it, and a test pins that (§8).

### 6.3 The all-sky distant sweep, with both confounds controlled

M9 §12 item 2 asked for this: its own scoping run was restricted to the slow-northern
pool. **4,743 distant orbits (a ≥ 25 AU, bound, U ≤ 6) × 2,585,881 tracklets over 10,136
nights, |Δt| ≤ 28 y**, screens applied to the ranked head *before* anything was fitted.

| | real | decoy |
|---|---:|---:|
| coarse matches | 21,334 | 25,530 |
| **[0″, 5″)** | **11** | 2 |
| [5″, 15″) | 3 | 9 |
| [15″, 30″) | 18 | 24 |
| [30″, 60″) | 32 | 105 |
| sub-60″ total | 64 | 140 |

Only the sub-5″ bin carries an excess (11 vs 2); everything wider is decoy-dominated. So
the bounded fit set is the sub-5″ rows — and **6 of those 11 are artefacts**:

| removed | why |
|---|---|
| 2015 HY194 ← `G1sS1pM` (W84, 0.1″) | POINTED_FIELD + DUPLICATE |
| 2015 HO196 ← `G1tg1JJ` (W84, 0.1″) | POINTED_FIELD + DUPLICATE |
| 2018 KH3, 2024 PP8, 2021 GQ57, 2020 KR11 | SELF_DESIGNATION |

The screens remove **9 of the whole top 200** (2 pointed-field, 7 self-designation) and
**6 of the top 25** — including its two tightest rows. Worth noting what that buys:
**2015 HY194 ← `G1sS1pM` is the exact candidate M9 §4.1 ranked first and had to spend an
fo run to reject.** The screen reaches the same verdict before any fitting.

The five survivors were then fitted through the standard chain
(`scripts/m10_distant_fits.py`, tags `mAh####`):

| candidate | a (AU) | Δt | sep | used | joint RMS (baseline) | verdict |
|---|---:|---:|---:|---:|---:|---|
| **2014 HM208 ← `G1ta1KM`** (W84) | 39.4 | −11.12 y | 0.29″ | **2/2** | 0.0505″ (0.0482″) | **PASS-grade** |
| 2013 HS150 ← `AIXe1M5` (W84) | 61.2 | −13.14 y | 0.43″ | 2/4 | 0.0799″ (0.0886″) | fails |
| 2013 HS150 ← `AIDP1Mt` (W84) | 61.2 | −13.15 y | 3.24″ | 2/3 | 0.0903″ (0.0886″) | fails |
| 2003 UY117 ← `G00FE9` (V30) | 56.0 | −11.46 y | 0.67″ | **0/2** | 0.1542″ (0.1542″) | fails |
| 2017 MZ4 ← `R020211` (W98) | 66.6 | −8.81 y | 3.10″ | 1/3 | 0.2925″ (0.2932″) | fails |

**And the one that passes is already in the ledger.** 2014 HM208 ← `G1ta1KM` is
`m9-ledger.json`'s M9-partitions PASS row `lk455716bd6fa6cea9` — same tracklet, same
station, same night, same 0.0505″ joint RMS — found independently by the main-belt sweep
at a 258″ gate and by the distant sweep at 153″. Two sweeps with different orbit sources,
different windows and different gates converging on one attribution is a good consistency
check. It is not a new candidate.

**So the distant regime's verdict, with the confound M9 named now controlled, is a clean
negative: zero new fit-grade distant attributions.** That is the publishable-shaped
result the milestone was after — the 28-year window is measured and open (≤ 0.45″), the
pool has been swept all-sky rather than in one declination band, the two confounds that
manufacture false heads are identified and screened, and what remains does not survive
the primary gate. The negative is now attributable to the pool rather than to an
uncontrolled systematic.

## 7. Traps hit (all paid for; check before touching this code)

1. **"Consumed but not in the attributed object" is not republication lag.** The
   tempting explanation for a disagreement is that the MPC has not refreshed the
   destination record yet. Measured: in the same six-hour window one candidate's object
   gained exactly the consumed tracklet's four rows while two others' records were
   byte-identical to the 08-16 cache. The object records move in the same cycle as the
   ITF removal, so a consumption that does not appear in the attributed object went
   **somewhere else**.
2. **A single-interval decay difference is a sample of one MPC batch sweep.** Per-interval
   PASS hazards ran 0.80 → 2.01 → 0.00 %/day. Any two-point estimate — M9's included —
   inherits whichever burst it straddled, and pooling across queue depth then hides a
   2.8× difference between the head and the tail of the same queue.
3. **One candidate can be recorded twice across milestones.** 2025 MQ241 + `nf2088` is
   both an M7 held row and M8's BORDERLINE row. A reviewer working from either document
   alone counts it once; a naive queue emits it twice. Deduplicate on
   `(object, tracklet key)`.
4. **Self-designation artefacts sail through every gate.** A trkSub that *is* the
   object's packed provisional designation with a mangled century byte gives a
   sub-arcsecond separation, an excellent joint fit, no duplicate flag (these are exactly
   the rows the MPC has not linked), and a SkyBoT hit recorded as *self-confirmation*.
   Seven of the all-sky head's top 200 were this. Check the identity before the fit.
5. **The decoy control cannot price a pointed field.** A half-period phase shift puts the
   decoy orbit where nobody was looking. It measures chance alignment against the survey
   footprint — a different and easier question than "was this survey tracking the
   object?".
6. **A wide gate is not a strong prior.** The frozen U-runoff term reaches 4,380″ at 25 y
   for U = 6, so a 100″ shell match can look "well inside the gate" while being far
   weaker evidence than a 3″ match inside 344″. Report `sep/gate` *and* `sep`.
7. **Short tracklets pass the primary gate more easily.** In the shell, 2-observation
   tracklets pass strict + fully-used at 33 % against 15–18 % at 3–4 observations.
   "Fully used" constrains less when there is less to use, so a yield's tracklet-length
   distribution is part of the result.
8. **Excel eats plain UTF-8.** `out/review-queue.csv` is written `utf-8-sig`; without the
   BOM every arcsecond sign and en-dash in it is mangled on open.

## 8. Tests

**485 passed** (467 before M10, plus 18 new in `tests/test_m10_screens.py`), ruff clean across `src`, `scripts` and `tests`. The new tests
pin the three things M10 asserts that a unit test can hold: the pointed-field screen's
behaviour at its declared boundary (including that a *different station* at the same
instant does **not** flag, and that a duplicate is reported as a duplicate rather than a
pointed field), the self-designation identity check and its measured 0-of-1,971 result
against the live ledgers, and the arithmetic the decay section and review queue put in
front of a human — a Wilson interval that behaves at zero successes, the exponential
survival fit reproducing M9's 3.3 %/2 d as a special case, and the Fisher test that
finds the head-vs-tail difference.

Three defaults are pinned explicitly because M10 added knobs to M8's script and M8's
numbers must stay reproducible: `MIN_LOOKBACK_DAYS == 0.0`, `CALIBRATION_KEY ==
"perturbed_envelope_arcsec"`, and the seven-character fit-tag width.

## 9. Recommended next milestone (M11)

1. **The submission decision, on the M8 rows first.** `out/review-queue.csv` is ready and
   §2 says which end of it is perishable: M8's PASS head has a ~32-day half-life and its
   top half ~28 days, while M9's 272 PASS rows have lost nothing in the same window.
   Tier A's 33 combined-fit objects are the strongest artifacts the project has produced.
   Everything else in this list is worth less than a decision — including an explicit
   decision not to submit.
2. **Adjudicate the shell's 18 lost-object ambiguities**, and re-run the combined-fit
   step over the shell's 13 multi-tracklet objects. `scripts/m9_adjudicate.py --ledgers
   m10-shell-ledger.json` and `scripts/m9_combined.py --extra-ledgers
   m10-shell-ledger.json` are both already wired for it.
3. **Price the shell's fit stage with a decoy.** §5.3 is the honest weakness: 74 % of the
   shell's passes are 2-observation tracklets at wide U = 6 gates from a single
   observatory. The coarse decoy prices the coarse stage; nothing yet prices the *fit*
   stage, and the cheap way to do it is to fit a matched sample of decoy candidates and
   compare pass rates. Until that exists, treat the shell's ~54 wide-gate rows as
   recorded rather than as candidates.
4. **Finish the shell's deep end.** The fit queue stopped at 300 by its own rule, having
   reached only −20.74 y; the coarse sweep has 14,717 matches in the 24–25 y bin that
   nothing has fitted. A rank-stratified queue (fit the deepest decile too, not only the
   sep/gate head) would test whether the shell's yield holds at 21–25 y or dies.
5. **Re-run the ledger refresh before any submission.** It costs 45 seconds and one ITF
   pull, and it is the only thing standing between a batch and a tracklet the MPC took
   yesterday.
6. **Do not widen past what is measured.** 25 y is the main-belt bound and 28 y is a TNO
   number; the main-belt envelope breaks at 28 (303.8″). Submission automation stays
   permanently out of scope (standing constraints 1–3).

---

*Generated by `scripts/m10_refresh.py`, `scripts/m10_decay.py`,
`scripts/m10_review_queue.py`, `scripts/m9_adjudicate.py` (M10 invocation),
`scripts/m10_shell.py`, `scripts/m10_verdicts.py`, `scripts/m10_pointed.py` and
`scripts/m10_distant_fits.py`. Regenerable artifacts: `data/raw/rubin/m10-refresh.json`,
`m10-decay.json`, `m10-pointed.json`, `m10-orbits.parquet`; root (gitignored)
`m10-adjudication.json`, `m10-shell.json`, `m10-shell-ledger.json`,
`m10-distant-fits.json`; and `out/review-queue.csv` + `out/review-queue-summary.json`,
which are the deliverable and are small enough to keep. The fresh 2026-08-18 21:26:46
GMT ITF pull was parsed **outside the repository** and is not part of the archive.*

---

## Addendum, appended 2026-08-23 by M11 — what a longer baseline changed

**Nothing above has been edited.** Every number in M10 remains what M10 measured on its
own window. These are the four places where M11's longer baseline, larger sample or
extra test changes how an M10 claim should be *cited*. Full detail in `M11-RESULTS.md`.

| M10 claim | Status after M11 | Where |
|---|---|---|
| §2 "**M9 PASS 0 of 272**, half-life > 101 d, Fisher p = 7.1 × 10⁻⁵" — the decay is *entirely* in M8's head | **Superseded — it was a burst.** Over seven days M9's PASS rows lost **12 of 272** (half-life 106 d) against M8's 50 of 482 (43.8 d). The head-vs-tail effect is real but **2.4×, not infinite** (p = 0.0024); M8's own top/bottom ratio fell 2.8× → 1.9×. M10's own trap 2 predicted this exactly | `M11-RESULTS.md` §1.2 |
| §5.3 "the shell's ~54 wide-gate rows deserve a decoy-controlled *fit-stage* test before anyone treats them as candidates" | **Test run, and the shell passed it.** 0 of 300 decoy fits are fit-grade against 76 of 300 real (p = 5.7 × 10⁻²⁶), 0 % in *every* sep, sep/gate and tracklet-length stratum. The wide-gate rows are not chance. Caveats 1 and 2 (one observatory, 2-observation tracklets) are untouched by this and remain open | `M11-RESULTS.md` §4 |
| §5.2 "Thirteen objects carry ≥ 2 passing shell tracklets" — and the strongest-rows table, led by **2015 KP488** (691 + G96, 8.9″/9.9″) | **Refined and partly reversed.** Thirteen counts *fit-grade* fits; the verdict chain leaves **10** objects with ≥ 2 PASS rows. Combined-fitted, only **3 of 10** pass, against the main tier's 40 of 45 (p = 3.5 × 10⁻⁴) — and **2015 KP488 fails**: both tracklets fully used but joint RMS 0.305″ against a 0.045″ baseline and σ_a 88× worse. **2021 SZ54 is confirmed**: it passes combined *and* the MPC has since consumed all three of its tracklets into it | `M11-RESULTS.md` §3.2, §4.3 |
| §9 item 4 "the coarse sweep has 14,717 matches in the 24–25 y bin **that nothing has fitted**" | **Premise wrong; conclusion tested anyway.** M10's own global head spans 15.26–25.00 y and already held 90 fits at 21–25 y (40 at 24–25 y), all zero fit-grade. A rank-stratified round-robin added 40 more deep fits and found the same: **0 fit-grade of 130 beyond 20.74 y** against 33 of 90 at 20–21 y (p = 2.3 × 10⁻¹⁵). The cliff is the sky, not the ranking | `M11-RESULTS.md` §5 |

Two M10 results were *confirmed* on populations they had not been tested against, and
both are worth citing as strengthened rather than merely repeated:

* **§6.1's explanation of the pointed-field confound** ("a property of follow-up, so it
  scales with how interesting the object already was") predicted **0** flags in a 15–25 y
  precovery shell. Recorded as a prediction before the run and confirmed: 0
  `POINTED_FIELD` **and** 0 `SAME_NIGHT_FIELD` across the shell tier's 70 screenable
  PASS/BORDERLINE rows, cleaner than the main tier's 0 and 5 of 735.
* **§6.2's self-designation screen** measured 0 across 1,971 *fitted* ledger rows — a
  population that had already survived a fit, which is the one thing this artefact class
  always does. Screened against the shell's **coarse** ranked top 2,000, before any gate,
  it is still 0.

One M10 artifact is superseded operationally: `out/review-queue.csv` is kept
**byte-identical** (md5 `05ed531d196b47571de06e79234fffac`) so a review in progress is
not renumbered, and `out/review-queue-v2-20260823.csv` (669 rows) ships beside it with
`out/review-queue-v2-20260823-diff.json`. Regenerating M10's numbers from
`scripts/m10_refresh.py` now **requires** `--series`, because the archive's retention has
pruned the 08-16 key set the original command line depended on (`M11-RESULTS.md` §1.0).
