# M11 — The shell priced against chance, its deep end sampled, and the ledger refreshed for a second time

**Date:** 2026-08-23 · **Status: COMPLETE** · **ITF universes:** the M7/M8 snapshot
(2026-08-16 20:27:01 GMT, exactly reconstructed — M9 §0.1) for every sweep and fit, and
a **fresh pull taken now** (2026-08-23 18:27:06 GMT, 9,192,976 observations) for the
liveness refresh. **Nothing was submitted anywhere. Candidates are candidates.**
`m8-ledger.json`, `m9-ledger.json`, `m9-combined.json`, `m9-adjudication.json`,
`m10-adjudication.json`, `m10-shell-ledger.json` and **`out/review-queue.csv`** are
read-only inputs; M11 appends only. Tests: 505 green.

**One-line result:** the 15–25 y shell's fit stage is priced against chance for the
first time and **survives outright — 0 of 300 decoy fits are fit-grade against 76 of 300
real, Fisher p = 5.7 × 10⁻²⁶** — with the re-run control reproducing M10's decoy to the
count; the separation turns out to live **entirely in the primary "did fo use the
tracklet" gate**, since the strict RMS gate passes *more* decoys (295) than reals (228).
The MPC then priced the shell independently by **consuming 6 of its PASS rows and
agreeing with all 6**, including all three of 2021 SZ54's −20.6 y tracklets. Against
that, two results cut the other way: the shell's multi-tracklet objects pass their
combined fit only **3 of 10** where the main tier passes 40 of 45 (p = 3.5 × 10⁻⁴), and
the deep end is **dead — 0 fit-grade of 130 fits beyond 20.74 y** on a stratified queue
that cannot be blamed for looking shallow. The refreshed ledger stands at **2,203 rows,
103 consumed, 68 of 68 consumed PASSes agreeing**, and the strict gate now has **five**
measured true negatives plus one partial. `out/review-queue.csv` was **not touched**;
`out/review-queue-v2-20260823.csv` (669 rows) ships beside it with a row-level diff. And
the refresh's first run was wrong in a way nothing in the output showed: **the archive's
retention had pruned the base snapshot**, so "consumed since 08-16" quietly meant
"since 08-21" and read 18 instead of 103.

---

## 0. Pre-registered decisions (written before the runs they govern)

### 0.1 Snapshot discipline — M10 §0.1, unchanged

Two universes, kept strictly apart.

* **Liveness and decay** are questions about *today*. The daily archive last wrote
  2026-08-23 12:26:46 GMT; the MPC regenerated the ITF again at **18:27:06 GMT**, so
  M11 fetches that pull **into a scratch directory outside the repository** and parses
  it there. `data/raw/itf.txt.gz`, `data/parquet/`, `data/snapshots/` and the archive
  clone are **not written to**. The decay series is the archive's slim `obs_key` tables
  for 2026-08-16 20:27:01 · 08-17 12:26:49 · 08-18 15:29:03 · 08-19 12:26:40 ·
  08-20 19:26:57 · 08-21 14:28:19 · 08-22 21:27:04 · 08-23 12:26:46, plus the fresh
  18:27:06 pull: **nine points, eight intervals** (M10 had four and three).
* **Every sweep and every fit** runs against the reconstructed 2026-08-16 snapshot
  (`data/parquet/itf_observations_20260816_reconstructed.parquet`), the universe M8, M9
  and the M10 shell swept.

### 0.2 Ledger refresh scope, and the versioned queue

* The refresh covers **every fitted row of the cumulative ledger**: M8's 900, M9's
  1,000, M7's 3 held, **and M10's 300 shell rows** — 2,203 rows. M10's refresh predates
  the shell ledger and so has never tested it.
* **`out/review-queue.csv` is what Matthew is reviewing and is NOT overwritten.** M11
  writes a *new, versioned* file, `out/review-queue-v2-20260823.csv`, alongside it, with
  `out/review-queue-v2-20260823-summary.json` and an explicit row-level diff
  `out/review-queue-v2-20260823-diff.json` naming every row that entered, left, or
  changed rank. The v1 file, its summary and their mtimes stay exactly as M10 left them.
* **Shell rows stay out of the review queue** (M10 §5.3's three caveats are the reason
  and they are not all answered here). The queue's population rule is unchanged from
  M10: still-live PASS/BORDERLINE rows of `m8-ledger.json` + `m9-ledger.json` + M7's
  held rows.
* **Loud case.** M10 found the strict gate's first two measured true negatives, both on
  `FAIL` rows. A third disagreement matters; a disagreement on a **PASS** row would be
  the first time the chain has ever been contradicted on a row it passed, and is
  reported at the top of §1 if it occurs.

### 0.3 Adjudicating the shell's 18 ambiguities — the frozen standard, verbatim

M9 §0.4 / M10 §0.3's standard with nothing loosened and nothing re-derived. Informative
claimant = SkyBoT ephemeris error **≤ 60″**. Each claimant is fitted against **its own
published astrometry** plus the disputed tracklet, under the frozen strict post-fit gate
and the "tracklet fully used" primary gate; ≤ 5 claimants per candidate. Verdicts:
`RESOLVED_TO_CANDIDATE` · `REJECTED` · `STILL_AMBIGUOUS` (a claimant also passes, or
cannot be fitted — what cannot be fitted cannot be excluded) ·
`RESOLVED_BY_MPC_CONSUMPTION`. Exhaustive over all 18 rows: no stopping rule, no budget,
no standard-loosening. M8's 88 and M9's 60 are **not** re-litigated.
Invocation: `scripts/m9_adjudicate.py --ledgers m10-shell-ledger.json`, tag prefix `mB`
(fits `mBg####` / `mBf####`), output `m11-shell-adjudication.json`.

### 0.4 Combined fits over the shell's multi-tracklet objects

M9 §6's procedure, unchanged: one fo fit of the object's full 08-16-era published
astrometry plus **all** its passing shell tracklets, against an object-only baseline;
per-member fully-used counts matched by epoch **and** observed position (M9's
same-exposure sibling trap); arc extension and σ_a/σ_e/σ_i deltas reported the way M9
reported them for the main tier.

* **Primary tier — shell-only.** Objects with ≥ 2 **PASS** rows inside
  `m10-shell-ledger.json`. That is **10** objects. M10 §5.2's "13 objects carry ≥ 2
  passing shell tracklets" counts *fit-grade* (strict + fully-used) fits; the verdict
  chain then demoted one member each of **2025 HE54**, **2025 ME338** and
  **2025 PG274** (`joint_set_not_used`), so 13 → 10. Both numbers are reported.
* **Secondary tier — cross-tier, reported separately and promoted nowhere.** Six shell
  PASS objects also carry a main-ledger PASS row (2015 KP488, 2025 MV144, 2025 NO313,
  2025 OE638, 2025 PO67, 2025 PY65). Combining a shell tracklet with a main-tier one
  is the sharpest available test of whether a shell row is real, so it is run — but its
  results are a *shell-tier* result and do not enter the review queue.
* Tags `mBc####` / `mBe####`, fit root `data/m11-fits`, output
  `m11-shell-combined.json`. `m9-combined.json` is not touched.

### 0.5 **Pricing the shell's fit stage with a decoy — the protocol and the demotion rule, declared before the run**

M10 §5.3 and §9 item 3 name this as the shell's honest weakness: the half-period decoy
prices the **coarse** stage (76 real vs 23 decoy under 15″), and nothing prices the
**fit** stage, so the shell's 71 PASSes are not yet separated from chance the way the
main tier's are.

1. **The control is re-run, not reused.** `m8_attribution.run_sweep(decoy=True)` discards
   the tracklet row index for decoy matches (`m.pop("row")`), and only the first 100
   unranked decoy matches were stored, so M10's decoy matches are **not fittable**. M11
   re-runs the identical half-period phase-shifted sweep — identical orbit table
   (`m10-orbits.parquet`, U ≤ 6), identical window (15 y < |Δt| ≤ 25 y), identical
   derived gate, identical night set, identical reconstructed snapshot — and attaches
   tracklet identity this time.
2. **Reproduction check, and it is a gate on the whole result.** The re-run must
   reproduce M10's decoy coarse counts: **188,494 matches** and the histogram
   3 / 20 / 66 / 274 / 1,185 in the [0,5) [5,15) [15,30) [30,60) [60,120)″ bins. If it
   does not, this is not the same control and the measurement is void and reported void.
3. **Same ranks.** Decoy matches are ranked by the identical key
   `(encounter, sep_arcsec / gate_radius_arcsec)` and the **top 300** are fitted — the
   same count and the same ranks as the real shell's fitted queue.
4. **Same fit chain.** `m8_attribution.joint_fit` unchanged: the object's real published
   astrometry (08-16-era cache) + the decoy-matched tracklet's verbatim ITF lines,
   relabelled under one 7-character tag, the same fo build, the same strict and
   published gates, the same baselines. Tags `mBa####` / `mBb####`, fit root
   `data/m11-decoy-fits`, checkpoint `data/m11-decoy-fit-state.jsonl`.
5. **Primary metric: strict gate + tracklet fully used** ("fit-grade") — the same
   criterion the real shell's **76 of 300** was measured on and the same one M10's
   stopping rule ran on. Wilson 95 % intervals on both.
6. **The reading is declared here, before the number exists:**

   | decoy fit-grade rate | what it means | pre-declared action |
   |---|---|---|
   | ≥ 25.3 % (≥ 76/300) | the fit stage carries **no** signal in the shell | the **whole shell tier is demoted**: recorded, never candidates, and M10 §5's yield is reported as unpriced chance |
   | 12.7 – 25.3 % (38–75/300) | separation is under a factor of 2 | shell tier is **not submission-grade at any rank**; only strata with a measured excess survive as "recorded" |
   | 8.3 – 12.7 % (25–37/300) | weak separation | reported as **weakly separated**; nothing promoted |
   | ≤ 8.3 % (≤ 25/300) | fit stage priced, real ≥ 3× decoy | the shell's passes are separated from chance — **subject to M10 §5.3's three caveats, which this test does not answer** |

7. **Sub-population reporting is mandatory, not optional**, because M10 §5.3's caveats
   indict specific strata: the fit-grade rate is reported by **sep/gate stratum** and by
   **tracklet length** (2 obs vs 3+ obs) for both arms, and the tracklet-length mix of
   the two heads is reported so a difference in the mix cannot masquerade as a
   difference in the rate.
8. **Budget:** 300 new decoy fits, hard; time backstop 75 minutes. If a budget binds
   first, the rate is reported on the fits actually run, with its interval.
9. **Nothing is retuned to make the shell survive** (standing constraint 5). A demotion
   reported plainly is the success condition of this test.

### 0.6 The shell's deep end — a rank-stratified queue and its stopping rule

M10's fit queue was a single sep/gate-ranked list; it stopped at 300 by its own rule
having reached only −20.74 y, leaving **14,717 coarse matches in the 24–25 y bin**
unfitted. A deeper single list would spend its whole budget at 15–20 y again.

* **Strata:** the five one-year lookback bins **20–21, 21–22, 22–23, 23–24, 24–25 y**.
  Within each, rank by `sep/gate`.
* **Round-robin**, 10 fits per stratum per round (50 fits per tranche). Rows already
  fitted by M10 are reused from checkpoint and do not consume budget.
* **Stopping rule (in-loop, not applied by hand):** after each 50-fit tranche, compute
  the trailing-50 fit-grade rate; **stop when it drops below 10/50 (20 %)** — M10's
  20/100 floor at the same rate. **Per-stratum**, a stratum that produces **0 fit-grade
  in its first 20 new fits** is closed on its own and its budget returns to the others.
  Hard budget **250 new fits**; time backstop **75 minutes**. Whichever binds first is
  the reported stopping reason.
* **Screen before fitting** (M10 trap 4): every queued row passes the self-designation
  identity check *before* an fo run. Rows that fail are removed and counted, not fitted.
* Verdicts come from the same chain (`scripts/m10_verdicts.py`), output
  `m11-deep-ledger.json`, kept **in the shell tier and out of the review queue**.
* Tags `mCa####` / `mCb####`, fit root `data/m11-deep-fits`.

### 0.7 The artefact screens against the shell tier

Two screens, both of which the shell has never had run against it as a population.

* **Self-designation** (M10 §6.2, `m10_pointed.self_designation`): a trkSub that *is*
  the object's own packed provisional designation with the century byte replaced. M10
  measured 0 across the 1,971 M8/M9/M10-shell ledger rows, but never against the
  shell's **coarse** head — which is where the all-sky sweep's 7 hits lived (7 of the
  top 200). M11 screens the shell's coarse ranked **top 2,000**, all 300 M10 shell
  fitted rows, and every deep-end row. Any hit is removed from the tier and named.
* **Pointed-field** (M10 §0.4): `screen_ledger()` covered `m8-ledger.json` and
  `m9-ledger.json` only — 735 rows — so no shell row has ever been screened. M11 runs
  it over every shell PASS/BORDERLINE row. Pre-declared actions are M10's:
  `POINTED_FIELD` → removed from the tier; `SAME_NIGHT_FIELD` → named on the row.
* **The prediction is recorded before the run.** M10 §6.1's explanation of why the
  main-belt regime is clean — "a main-belt precovery sweep proposes tracklets from
  11–25 years before the object was discovered, when by construction nobody was
  pointing at it" — predicts **0** `POINTED_FIELD` in a 15–25 y shell, more strongly
  than for the main tier. If the shell flags any, M10 §6.1 is wrong and that is the
  finding.

### 0.8 What M11 may not do

No submissions, no accounts, no commits, the archive clone untouched. Every prior
verdict is append-only: `m8-ledger.json`, `m9-ledger.json`, `m10-shell-ledger.json`,
`m9-combined.json`, `m9-adjudication.json`, `m10-adjudication.json` and
`out/review-queue.csv` are inputs. Where an M9/M10 script needed a knob to write
somewhere else, the knob is **default-off** so the earlier milestone's numbers stay
reproducible from the same command line.

---

## 1. The ledger refreshed — 2,203 rows, 103 consumed, and the chain still unbeaten on a PASS

`scripts/m10_refresh.py` (M11 invocation: `--extra-ledgers M10-shell=… --series …
--out data/raw/rubin/m11-refresh.json`) tested **every fitted row of M8, M9 and the M10
shell plus M7's three held candidates — 2,203 rows** against nine ITF snapshots spanning
2026-08-16 20:27:01 to a pull taken at **18:27:06 GMT today**, and asked of every
consumed one where its observations actually went.

| | count |
|---|---:|
| Cumulative ledger rows tested | **2,203** (M8 900 · M9 1,000 · **M10-shell 300** · M7 held 3) |
| Still live in the 18:27 ITF | **2,100** |
| Consumed by the MPC since 08-16 | **103** (M10 measured 33 over its shorter window) |
| … `CONSUMED_AND_AGREED` | **97** |
| … `CONSUMED_AND_DISAGREED` | **5** |
| … `CONSUMED_PARTIAL(3/4)` | **1** |
| PASS rows | **825** (M8 482 · M9 272 · shell 71) |
| … **still live** | **757** |
| … consumed | 68, **68 / 68 agreed** |

**The chain has still never been contradicted on a row it passed** — now at *n* = 68
rather than M10's 21, against a pull a week newer. Every one of the 68 consumed PASS
tracklets went to exactly the object the ledger named, across three separate sweeps
including the shell.

### 1.0 The trap that had to be paid for first: the archive pruned M10's base snapshot

M10's refresh built its snapshot series by scanning `data/snapshots/` for directories
that still carry an `observations.parquet`, keeping those at or after
`BASE_SNAPSHOT = 20260816T202701Z`. Run today, that scan returns
**08-21 → 08-22 → 08-23**: the archive's rolling retention has pruned the key sets for
08-16, 08-17, 08-18, 08-19 **and** 08-20. `counts_by_snap[0]` silently becomes the
08-21 snapshot, so every "consumed since 08-16" count measures *consumed since 08-21*
under a heading that says 08-16 — and nothing in the output looks wrong. The first M11
run produced exactly that: **18 consumed**, printed beneath the line
`consumed or partially consumed since 20260816T202701Z`. The true answer is 103.

This is the archive's own delta-of-zero failure wearing a different hat, and it is now
closed twice over:

* `scripts/m10_refresh.py::scan_series` **raises** rather than reporting when the base
  snapshot has no surviving key set, naming the substitute it would otherwise have used.
* `scripts/m11_snapshot_series.py` rebuilds the series exactly. Every pruned snapshot
  kept its `delta.parquet`, and every manifest from 08-16 to 08-23 records
  `delta_status.against` = its *immediate* predecessor, so the chain is contiguous and
  `keys(parent) = keys(child) − appeared(child) + disappeared(child)` inverts it
  exactly. Restricted to the ledger's 2,187 designations each slim table is a few
  hundred kilobytes.

**And the verification caught a second distinction worth writing down.** The obvious
check is the delta walk against `itf_observations_20260816_reconstructed.parquet` — and
it *fails*, 8,452 rows against 8,346. That file is **not the 08-16 table**: M9 §0.1
built it as 08-18's rows whose `obs_key` was also present at 08-16, with every tracklet
that lost any observation **dropped whole**. It is the *intersection* of the two
snapshots — the right universe for a sweep that must not propose an already-taken
tracklet, and the wrong one for "how many observations did this tracklet have on
08-16". Checked where the two must agree, at **08-18**, the walk is identical
(8,346 = 8,346), and the base's 106-row excess is exactly the ledger observations the
MPC consumed between 08-16 and 08-18.

### 1.1 Five disagreements now, and the shell tier has its first

M10 found the strict gate's first two measured true negatives. Both reproduce, and
three more have joined them — **every one still a `FAIL` row**:

| row | ledger | first missing | why the chain refused it | where the MPC put it |
|---|---|---|---|---|
| 2025 MK161 ← `N069282` (W84) | M9 | 08-19 | joint RMS 0.391″ vs 0.083″ baseline, 3/4 used | not into MK161 |
| 2025 ML131 ← `H468861` (T09) | M9 | 08-19 | **0/3 used** — fo refused every observation | not into ML131 |
| 2025 NA213 ← `P10i5Fc` (F51) | M8 | 08-20 | strict gate | not into NA213 |
| **2025 QK176 ← `7T986E0`** (G96) | **M10-shell** | 08-20 | strict gate | not into QK176 |
| 2025 PP82 ← `YCB2C1E` (G96) | M9 | 08-23 | strict gate | not into PP82 |
| 2025 MU229 ← `N081179` (W84) | M9 | 08-22 | strict gate | **3 of 4** observations landed in MU229 — partial |

The count that matters for calibrating the gate: **33 consumed FAIL rows — 27
over-conservative, 5 correct, 1 partial.** M9 saw 8/8 over-conservative and read it as
pure over-conservatism; M10 had 9 and 2; at *n* = 33 the strict gate's rejections are
**~15 % correct refusals**, which is a rate rather than an anecdote. And one of them is
a shell row, so the shell tier's FAILs are not uniformly over-conservative either.

The republication-lag explanation stays refused for the same reason M10 refused it
(§7 trap 1): in the same window 97 other consumptions *did* show up in their attributed
objects' published records.

### 1.2 The decay clock, eight intervals instead of three — M10's headline was a burst

| population | consumed / n | %/2 days (95 % CI) | half-life |
|---|---:|---:|---:|
| **M8 PASS** | 50 / 482 | **3.12 (2.37–4.08)** | **43.8 d** |
| M8 fitted, queue **top half** | 44 / 450 | 2.93 | 46.6 d |
| M8 fitted, queue **bottom half** | 24 / 450 | 1.57 | 87.5 d |
| **M9 PASS** | **12 / 272** | **1.30 (0.74–2.25)** | **106.3 d** |
| **M10-shell PASS** | **6 / 71** | **2.52 (1.15–5.32)** | **54.3 d** |
| all PASS | 68 / 825 | 2.46 | 55.7 d |
| all fitted (2,200) | 103 | 1.38 | 100.0 d |
| all FAIL | 33 / 1,366 | 0.70 | 196.0 d |

**M10's most striking number does not survive a longer baseline.** M10 measured M9 PASS
at **0 of 272** and reported a half-life over 101 days against M8's 32, Fisher
p = 7.1 × 10⁻⁵. Over seven days M9's PASS rows have lost 12: the head-vs-tail effect is
**real but 2.4×, not infinite** (Fisher p = 0.0024), and the M8 queue's own
top-half / bottom-half ratio has fallen from 2.8× to 1.9×. M10 named the reason itself —
a single-interval difference samples one MPC batch sweep — and this is that caveat
collecting. The practical advice is unchanged in direction and weaker in force:
**work the M8 rows first**, but M9's rows are perishable too.

**Burstiness is confirmed and is larger than M10 could see.** Per-interval PASS hazards
across the eight intervals run **0.73 → 1.84 → 1.00 → 2.33 → 1.31 → 0.00 → 1.67 →
0.00 %/day**, with two intervals of exactly zero (08-21→08-22, 1.29 d, 765 at risk; and
08-23 12:26→18:27). Any two-point estimate inherits whichever burst it straddles.

**The shell tier decays at main-tier speed.** 6 of 71 shell PASS rows in seven days is
statistically indistinguishable from M8's PASS rate and faster than M9's. That is not a
nuisance — §4 makes it the shell's strongest evidence.

## 2. `out/review-queue-v2-20260823.csv` — versioned, with the old file untouched

**`out/review-queue.csv` was not written to.** Its md5 is `05ed531d196b47571de06e79234fffac`
before and after this milestone, and `out/review-queue-summary.json` is likewise
untouched. M11 writes three new files:

* `out/review-queue-v2-20260823.csv` — **669 rows, 663 objects, 696 tracklets, 361 KB**
* `out/review-queue-v2-20260823-summary.json`
* `out/review-queue-v2-20260823-diff.json` — the row-level diff below
  (`scripts/m11_queue_diff.py`)

| tier | v1 (08-18) | **v2 (08-23)** | change |
|---|---:|---:|---|
| **A** combined-fit, all members live | 33 | **26** | −7 |
| **B** single tracklet, caveat-free | 527 | **508** | −19 |
| **C** single tracklet, named caveat | 137 | **131** | −6 |
| **D** borderline / held | 4 | **4** | 0 |
| **total** | 701 | **669** | **−32** |

**What changed, exactly: 32 rows left, 0 entered, 0 changed tier, and every departure is
an MPC consumption that agreed with the ledger.** No row was demoted, re-gated or
re-scored; the population rule and the sort key are M10's, unchanged. Ranks below a
departure shift up by 1 to 32 places, which is why the file is versioned rather than
overwritten — a reviewer half-way through v1 can finish it and use the diff, instead of
finding the rows renumbered underneath them.

Departures by tier are 7 A, 19 B and 6 C. The seven tier-A objects that left did so because **every** member tracklet was
consumed and every one agreed: **2025 PJ65** (3/3), **2025 KQ32** (3/3), **2026 EE43**,
**2026 EB7**, **2026 EA75**, **2025 NJ64**, **2018 BC83** (2/2 each). Two departures are
worth naming individually:

* **2025 PJ65 is M10 §4's strongest standing ambiguity**, where lost object 2016 UD180
  fitted 2 of its 3 W84 members fully-used at 0.210″/0.250″ and the row stayed
  `STILL_AMBIGUOUS`. The MPC has now taken all three tracklets **into 2025 PJ65**.
  Reality adjudicated it in the candidate's favour, and the project's standing-ambiguity
  total drops from 4 to 2 (M9's 2025 HO61 ← `N369955`, M10's 2025 MQ287 ← `ZTA92C4`).
* **2025 HJ109 ← `WV89BC5`** was M10 §6.1's only genuinely close `SAME_NIGHT_FIELD`
  flag (1.6 h, 21.0″), kept as a PASS with the flag named. It was consumed **and
  agreed** — the flag was a caution, not a false attribution, which is exactly what
  "name it, don't drop it" was for.

Tier D is unchanged: all three of M7's held tracklets (2025 PD152 ×2, 2025 MQ241 ←
`nf2088`, the last deduplicated as M10 left it) plus M8's BORDERLINE row are **still
live** after seven days. The project's oldest held candidates have not been overtaken.

## 3. The shell's follow-ups: 18 ambiguities adjudicated, 16 multi-tracklet objects combined

### 3.1 Ambiguities — 16 resolved, 1 by the MPC, 1 standing, 0 rejected

`scripts/m9_adjudicate.py --ledgers m10-shell-ledger.json` at M9 §0.4's standard
verbatim (informative claimant ≤ 60″, each fitted against **its own** published
astrometry, strict + fully-used gates, ≤ 5 claimants). Tags `mBg####`/`mBf####` into
`data/m11-fits/`; output `m11-shell-adjudication.json`. `m9-adjudication.json` and
`m10-adjudication.json` are untouched.

| adjudication | count |
|---|---:|
| **RESOLVED_TO_CANDIDATE** | **16** |
| RESOLVED_BY_MPC_CONSUMPTION | 1 (2014 HC409 ← `1000fb`, taken into HC409 on 08-20) |
| **STILL_AMBIGUOUS** | **1** |
| REJECTED | **0** |

**19 of 20 claimants are excluded by their own astrometry** — the same pattern for the
third time, on a window 15–25 y deep that had never been tested. Across the project the
standing total is now **166 ambiguities adjudicated: 157 resolved to the candidate,
4 resolved by MPC consumption, 5 still ambiguous, and not one claimant has ever owned a
tracklet.**

The one that stands: **2025 PO67 ← `0acb89`** (705, −20.6 y) — candidate 0.0986″;
claimant **2015 RA402** (SkyBoT ephemeris error 1.0 × 10⁷ ″) fits it fully used at
0.191″ with both gates passing. It is a **2-observation** tracklet, so "fully used"
means two points, which M10 §5.3 caveat 2 already flagged as a weak constraint — and
§3.2 finds that fo refuses this same tracklet outright when it is offered alongside
2025 PO67's other one. Tightness is not the frozen standard, so it stays
STILL_AMBIGUOUS.

Two of the four ambiguities that were standing before this milestone were **resolved by
the MPC** during it (2025 PJ65's `N044699` and `N106006`, §2), so the live standing list
is three: 2025 HO61 ← `N369955` (M9), 2025 MQ287 ← `ZTA92C4` (M10), 2025 PO67 ←
`0acb89` (M11).

### 3.2 Combined fits — and the shell's multi-tracklet tier does **not** behave like the main tier

This is the milestone's second unfavourable result and it arrived before the decoy did.

M9 §6's procedure unchanged (`scripts/m9_combined.py`, tags `mDc/mDe` and `mEc/mEe`,
per-member used-counts matched by epoch **and** observed position, output
`m11-shell-combined.json` / `m11-crosstier-combined.json`; `m9-combined.json` untouched).

**Population.** M10 §5.2's "13 objects carry ≥ 2 passing shell tracklets" counts
*fit-grade* fits; the verdict chain then demoted one member each of 2025 HE54,
2025 ME338 and 2025 PG274 (`joint_set_not_used`), so the ledger tier is **10 objects**.
Six further objects carry both a shell PASS and a main-ledger PASS and are combined
separately as a cross-tier test.

| tier | objects | **combined_pass** | rate |
|---|---:|---:|---:|
| M9's main tier (for comparison) | 45 | 40 | **89 %** |
| **M11 shell-only** | 10 | **3** | **30 %** (95 % CI 11–60) |
| **M11 cross-tier (shell + main)** | 6 | **2** | 33 % |

Main 40/45 against shell 3/10 is **Fisher one-sided p = 3.5 × 10⁻⁴**; pooling the two
M11 tiers (5 of 16) gives p = 2.8 × 10⁻⁵. **Multi-tracklet corroboration, which is the
main tier's strongest evidence, mostly evaporates in the shell when it is actually
tested.**

The three shell-only passes:

| object | trk | station | Δt | arc ext | joint RMS (base) | σ_a ratio | note |
|---|---:|---|---:|---:|---:|---:|---|
| **2021 SZ54** | 3 | 705 | −20.5 to −20.6 y | **+5,818 d** | 0.159″ (0.152″) | **0.031** | all three tracklets **since consumed by the MPC into 2021 SZ54** (§4.1) |
| 2016 UH221 | 2 | 705 | −19.7 y | +3,694 d | 0.142″ (0.144″) | 0.65 | joint RMS *better* than baseline |
| 2025 NK502 | 4 | 705 | −19.6 to −19.7 y | +6,858 d | 0.134″ (0.072″) | **4.43** | passes both gates but makes σ_a **4.4× worse** — read as weak |

And the seven that fail, which is where the information is:

* **2015 KP488 — M10 §5.2's flagship cross-observatory pair (691 + G96, 8.9″ and 9.9″)
  fails jointly**: both tracklets fully used, joint RMS **0.305″ against a 0.045″
  baseline** (6.7×) and σ_a **88× worse**. Adding the object's own live V00 tracklet
  (cross-tier) does not rescue it: 0.286″, still over the 0.25″ ceiling. The single
  strongest-looking row in M10's table does not survive being combined with its sibling.
* **2025 MV242, 2025 QC153, 2025 NP231** — joint RMS **identical to baseline** and
  σ_a ratio exactly 1.0, with **0 of 2 and 0 of 2** observations used: fo prefers to
  drop all four new observations rather than bend the orbit. M9 §6 found this once
  (2026 EH43); the shell produces it three times in ten.
* **2025 HT100 (1/2 + 0/2), 2025 MM109 (2/2 + 0/2), 2025 PO67 (1/2 + 0/2)** — one
  member survives, the other is refused whole. The two attributions contradict each
  other, so at most one is real.
* **2025 NP231's pair is same-station *and* same-night** (`073e17`/`073e18`, 705,
  n53625): the M9 §6 sibling structure, `shared_night_groups = 1`. Its "two tracklets"
  were never two independent detections.

Cross-tier, the same discriminator fires harder because the main-tier member anchors
the orbit:

| object | members | joint RMS (base) | used | verdict |
|---|---|---:|---|---|
| **2025 NO313** | F51 −11.4 y + F51 −15.4 y | 0.108″ (0.067″) | 3/3 · 3/3 | **combined_pass**, σ_a ×0.0043, arc +5,266 d — **both members since consumed and agreed** |
| **2025 PY65** | F51 −6.0 y + **152** −18.7 y | 0.222″ (0.040″) | 4/4 · 2/2 | **combined_pass** (cross-observatory), σ_a ×0.0031, but RMS 5.5× the baseline |
| 2025 OE638 | F51 −5.7 y + 705 −20.5 y | **4.213″** (0.061″) | 3/3 · 2/2 | fails: a **69× RMS blow-up** with every observation used. The shell tracklet is not this object |
| 2015 KP488 | V00 −0.7 y + G96 −18.8 y + 691 −18.8 y | 0.286″ (0.045″) | all used | fails the 0.25″ ceiling |
| 2025 MV144 | F51 −5.2 y + 705 −20.6 y | 0.093″ (0.061″) | 3/3 · **0/2** | shell member refused whole |
| 2025 PO67 | F51 −5.7 y + 705 ×2 | 0.105″ (0.103″) | 1/4 · **0/2 · 0/2** | both shell members refused whole |

**The honest reading of §3.2.** A shell tracklet that looks good alone frequently does
not survive contact with a second tracklet of the same object — and when the second
tracklet is a *main-tier* one, which is far better anchored, the shell member is dropped
outright in 3 of 6 cases and blows the fit up in a 4th. That is a direct, fit-level
argument against M10 §5.2's "several tracklets at the same small separation" heuristic,
which was the shell's best-looking evidence. It does not by itself condemn the shell's
single-tracklet passes — §4 is where those are priced.

## 4. **The shell's fit stage, priced: 0 of 300 decoys against 76 of 300 real**

This was the milestone's one genuinely open question, its protocol and its demotion rule
were written before the run (§0.5), and the answer is unambiguous.

**The control is the same control.** The re-run of the identical half-period
phase-shifted sweep reproduced M10's decoy **exactly** — 188,494 coarse matches and the
histogram 3 / 20 / 66 / 274 / 1,185 in the [0,5) [5,15) [15,30) [30,60) [60,120)″ bins,
every bin to the count. The reproduction gate (§0.5 item 2) passed, so the fit stage was
allowed to run. 26,924 orbits, 2,553,500 tracklets, 8,424 nights: the shell's universe,
not a re-scoped one.

**The measurement**, 300 decoy fits at the same ranks through the same chain
(`m8_attribution.joint_fit`, real published astrometry + the decoy-matched tracklet,
same fo build, same gates, same baselines; tags `mBa`/`mBb`, 44 minutes):

| arm | fit-grade (strict + fully used) | rate | 95 % CI |
|---|---:|---:|---|
| **real** (M10 §5.2) | **76 / 300** | **25.3 %** | 20.7–30.6 % |
| **decoy** (M11) | **0 / 300** | **0 %** | 0–1.3 % |

Fisher one-sided **p = 5.7 × 10⁻²⁶**. The pre-registered band is row 4 —
**"separated (≥ 3×)"**, by an infinite margin rather than a threefold one. **The shell
tier survives its decoy.**

### 4.1 Every stratum, including the ones M10 §5.3's caveats indict

M10's caveats say the shell's passes concentrate in wide gates, short tracklets and one
observatory. Those are exactly the sub-populations where a chance-driven yield would
show, so §0.5 item 7 required them to be reported. Every one is 0 % in the decoy arm:

| stratum | real | decoy |
|---|---:|---:|
| sep < 15″ | 22 / 61 (36 %) | **0 / 17** |
| sep 15–60″ | 25 / 65 (38 %) | **0 / 51** |
| sep 60–120″ | 27 / 131 (21 %) | **0 / 160** |
| sep ≥ 120″ | 2 / 43 (5 %) | **0 / 72** |
| sep/gate < 0.01 | 13 / 38 (34 %) | **0 / 16** |
| sep/gate 0.01–0.02 | 29 / 81 (36 %) | **0 / 62** |
| sep/gate 0.02–0.03 | 25 / 100 (25 %) | **0 / 94** |
| sep/gate ≥ 0.03 | 9 / 81 (11 %) | **0 / 128** |
| **2-observation tracklets** | **56 / 172 (33 %)** | **0 / 200** |
| 3-observation | 11 / 74 (15 %) | **0 / 58** |
| 4+-observation | 9 / 54 (17 %) | **0 / 42** |

**And the head mixes cannot rescue chance.** The decoy head is *more* 2-observation
heavy than the real head (200 vs 172 of 300) — and M10 §5.3 caveat 2 measured that short
tracklets pass the primary gate **more** easily, so that skew biases the decoy arm
*upward*. It is also slightly wider in `sep/gate` (128 vs 81 rows at ≥ 0.03), which
biases it down; but the real arm still passes 11 % in that same widest bin while the
decoy passes 0 of 128. There is no sub-population, and no mix argument, in which a
chance alignment passed this fit chain.

### 4.2 The finding underneath the finding: the RMS gate does none of the work

Splitting the fit-grade criterion into its two halves is the most useful thing in this
section, and it was not something M11 set out to measure:

| | real | decoy |
|---|---:|---:|
| **strict post-fit gate passes** | 228 / 300 | **295 / 300** |
| joint set ≥ 90 % used | 173 / 300 | 110 / 300 |
| **fo used ≥ 1 tracklet observation** | **162 / 300** | **0 / 300** |
| fo used *every* tracklet observation | 76 / 300 | 0 / 300 |

**The strict gate passes more decoys than reals.** That is not a malfunction — it is the
gate doing exactly what it says. A decoy tracklet is somewhere the object never was, so
fo drops all of its observations and the "joint" fit is the object's own pristine
baseline orbit, which of course passes an orbit-quality gate. 295 of 300 decoy fits
converged to a clean orbit and 299 of 300 converged at all; the median joint RMS in the
decoy arm is **0.082″**.

So the whole of the shell's discriminating power sits in the **primary gate** — *did fo
actually use the tracklet* — and **none** of it in the RMS ceiling or the uncertainty
tests. In 300 decoy fits fo used **zero** tracklet observations, not one, not partially:
`trk_obs_used == 0` on all 300 (Fisher against the real arm's 162/300,
**p = 1.0 × 10⁻⁶²**).

The verdict chain's second line of defence, the `joint_set_not_used` test
(`n_used / n_obs ≥ 0.9`), does discriminate — 173 real against 110 decoy — but only
because dropping a tracklet whole costs the joint set those few observations. It is a
*consequence* of the primary gate, not an independent check.

This is a measurement the repository has needed since M7, which has always *asserted*
the primary gate is the important one (`HANDOFF.md` §2 records the bug where it was
silently inverted). It is now quantified, and the corollary is a warning: **any future
milestone tempted to relax "fully used" to "mostly used", or to lean on the RMS ceiling
as a substitute, would be discarding the only part of the chain that separates a real
attribution from a coincidence.**

### 4.3 The independent pricing the decoy cannot give: the MPC took six of them

The decoy answers "could chance do this?". The refresh (§1) answers a different and
stronger question, and it also came out in the shell's favour:

**The MPC has consumed 12 of the M10 shell's 300 fitted rows since 08-16, and all 6 of
the consumed PASS rows went to exactly the object the shell ledger named.**

| shell row | station | Δt | consumed | agreement |
|---|---|---:|---|---|
| 2021 SZ54 ← `0a8a22` | 705 | −20.61 y | 08-23 | **AGREED** |
| 2021 SZ54 ← `0dc602` | 705 | −20.52 y | 08-23 | **AGREED** |
| 2021 SZ54 ← `0a385e` | 705 | −20.62 y | 08-23 | **AGREED** |
| 2025 NO313 ← `P100mQG` | F51 | −15.36 y | 08-21 | **AGREED** |
| 2025 MY175 ← `0b8476` | 705 | −20.59 y | 08-20 | **AGREED** |
| 2014 HC409 ← `1000fb` | 705 | −19.69 y | 08-20 | **AGREED** |

Plus a BORDERLINE (2019 WJ41 ← `RFBBE7F`, G96, −16.22 y) and 4 of 5 consumed shell
FAILs, agreeing. **2021 SZ54 is
the object M10 §5.2 named as one of the shell's strongest rows** — three 705 tracklets at
5.1″, 5.2″ and 5.9″ inside a 352″ gate, −20.5 to −20.6 y — and the MPC has now linked
all three of them to it. An independent authority made the same 20.6-year precovery
links the shell proposed, at the shell's deepest yield.

That is external ground truth for a window nobody had swept, and it does not depend on
the decoy, the gate formula, or anything else in this repository.

### 4.4 What the decoy does **not** answer, restated so nobody over-reads §4

M10 §5.3's three caveats are about *what the shell's yield is made of*, not about whether
it is chance, and the decoy speaks to none of them:

1. **One observatory.** 47 of 71 passes are station 705 and only 2 of 71 are
   cross-observatory. Surveys link their own data; an unlinked Palomar cluster is a
   weaker submission proposition than a genuine cross-match, however real it is.
2. **Short tracklets.** 56 of 71 are 2-observation. This section shows the length skew
   is not what produces the passes — but a 2-point tracklet is still 2 points, and §3.1's
   one standing ambiguity is exactly such a row.
3. **Wide gates.** The median pass sits at 50″ inside a 3,502″ gate. `sep/gate` does
   carry information (11 % at ≥ 0.03 against 34 % at < 0.01) — but not much.

And §3.2 adds a fourth that the decoy makes sharper rather than softer: **the shell's
multi-tracklet objects mostly fail their combined fit (3 of 10), where the main tier
passes 40 of 45.** A shell row can be a real attribution and still be one whose sibling
contradicts it.

**Standing verdict on the shell tier after M11:** the fit stage is priced and the tier is
not chance — but it stays **out of `out/review-queue.csv`**, because "not chance" is not
the same as "submission-grade", and caveats 1, 2 and §3.2 are all still open. The
credible core is the ~17 rows at sep < 60″ inside a gate < 600″ that M10 identified, now
with 2021 SZ54 confirmed by the MPC and 2015 KP488 demoted by its own combined fit.

## 5. The deep end: the cliff at 20.74 y is real, and it is sharp

### 5.0 M10's premise needed one correction first

M10 §9 item 4 asked for a rank-stratified deep queue because "the coarse sweep has
14,717 matches in the 24–25 y bin that nothing has fitted". Measured against
`m10-shell.json` itself, that is not so: M10's global `sep/gate` head spans **15.26 to
25.00 y** and already contained **90 fits at 21–25 y**, including 40 in the 24–25 y bin.
What stopped at −20.74 y was the **yield**, not the queue — and those 90 deep fits
returned **zero** strict + fully-used passes.

| lookback bin | M10 fits | fit-grade |
|---|---:|---:|
| 15–16 y | 30 | 7 (23 %) |
| 16–17 y | 8 | 2 |
| 17–18 y | 14 | 2 |
| 18–19 y | 19 | 6 |
| 19–20 y | 59 | **31 (53 %)** |
| 20–21 y | 80 | 28 (35 %) |
| **21–22 y** | 16 | **0** |
| **22–23 y** | 17 | **0** |
| **23–24 y** | 17 | **0** |
| **24–25 y** | 40 | **0** |

So the real question is not "has anyone looked" but "is the cliff an artefact of one
ranked list spending its budget shallow?" A stratified queue answers that, and it is what
M11 ran.

### 5.1 The run, and the rule firing after exactly one tranche

`scripts/m11_deep.py`: five one-year strata, each ranked by `sep/gate` on its own,
worked round-robin 10 fits per stratum per round; M10's checkpoint reused read-only.
**Screened before fitting: 0 of the 2,000 queued rows were self-designation artefacts.**

**Stopped at 50 new fits on `trailing_50_fit_grade(5)_below_floor(10)`** — the
pre-registered floor, first tranche, 7.1 s per new fit. Neither the 250-fit budget nor
the 75-minute backstop bound, and no stratum reached its own 20-fit probe.

| stratum | new fits | reused from M10 | **total** | **fit-grade** |
|---|---:|---:|---:|---:|
| **20–21 y** | 10 | 80 | **90** | **33 (37 %)** |
| 21–22 y | 10 | 16 | 26 | **0** |
| 22–23 y | 10 | 17 | 27 | **0** |
| 23–24 y | 10 | 17 | 27 | **0** |
| 24–25 y | 10 | 40 | 50 | **0** |

**220 fits at 20–25 y; every fit-grade row is in 20–21 y and the deepest is −20.739 y.**
Across 21–25 y the count is **0 of 130** (95 % CI 0–2.9 %) against 33 of 90 at 20–21 y:
Fisher one-sided **p = 2.3 × 10⁻¹⁵**. If the deeper strata shared 20–21 y's 37 % rate,
0 of 130 would occur with probability **1.6 × 10⁻²⁶**.

**The cliff is a property of the sky, not of the queue.** Round-robin sampling that gave
each of the four deep strata its own ranked head found exactly what a single ranked list
found: nothing past 20.74 y.

### 5.2 The four new candidates, and where they sit

The verdict chain (`scripts/m10_verdicts.py`, unchanged, over the 50 **new** fits only —
the 170 reused rows are already in `m10-shell-ledger.json` and double-counting them would
inflate the tier) gives **4 PASS, 46 FAIL** → `m11-deep-ledger.json`. All 4 are still
live in the 18:27 pull.

| object | trk | station | Δt | sep / gate | joint RMS | used |
|---|---|---|---:|---|---:|---:|
| 2025 NA310 | `0dc4aa` | 705 | −20.52 y | 138.6″ / 3,657″ | 0.095″ | 2/2 |
| 2025 NO168 | `0d4439` | 705 | −20.54 y | 139.5″ / 3,659″ | 0.111″ | 2/2 |
| 2025 MV144 | `0bb61e` | 705 | −20.59 y | 139.7″ / 3,668″ | 0.214″ | 2/2 |
| 2025 MN189 | `MA42928` | 695 | −20.27 y | 140.4″ / 3,616″ | 0.124″ | 3/3 |

Every one of them is the *weak* kind of shell row M10 §5.3 warned about: single
observatory, no cross-match, 2–3 observations, and ~139″ inside a ~3,660″ U = 6 gate
(`sep/gate` ≈ 0.038 — the widest of the four decoy-priced strata, where the real arm's
fit-grade rate is 11 %). They are **recorded in the shell tier and are not in the review
queue.** 2025 MV144 is also the object whose *other* shell tracklet (`0dd595`) the
cross-tier combined fit refused whole (§3.2) — the same object, two shell tracklets, one
of which fo will not use.

**What this closes.** The 15–25 y window is not uniformly productive: it is productive to
**≈ 20.7 y and then stops**, on 220 fits with a stratified design that cannot be blamed
for looking in the wrong place. There is no case for spending further fo time at
21–25 y, and none for widening beyond 25 y (which is unmeasured anyway — M9 §8's
main-belt envelope breaks at 28 y).

## 6. The artefact screens against the shell tier — the prediction held, twice

`scripts/m11_shell_screens.py`, both screens, over populations neither had covered.

| screen | population | result |
|---|---|---:|
| self-designation | shell **coarse** ranked top 2,000 (never screened; this is where the all-sky sweep's 7 hits lived) | **0** |
| self-designation | all 350 shell-tier fitted rows (M10's 300 + M11's 50) | **0** |
| self-designation | the 2,000-row deep-end queue, *before* any fo run | **0** |
| pointed-field | all 77 shell-tier PASS/BORDERLINE rows | **0 POINTED_FIELD · 0 SAME_NIGHT_FIELD · 0 DUPLICATE · 70 clean · 7 unscreenable** |

**M10 §6.1's prediction, recorded in §0.7 before the run, held.** Its explanation was
that the pointed-field confound is a property of *follow-up*, so it should scale with how
interesting the object already was — and a 15–25 y precovery sweep proposes tracklets
from before the object was discovered. The main-belt ledger scored 0 `POINTED_FIELD` and
**5** `SAME_NIGHT_FIELD` of 735; the shell scores **0 and 0** of 70. The deeper the
lookback, the cleaner the regime, exactly as the explanation predicts. That is a
falsifiable claim surviving a test on a population it was not fitted to.

The 7 unscreenable rows are precisely the 7 shell rows the MPC has since consumed (6
PASS + 1 BORDERLINE): their tracklets have left the ITF, so today's line index has no
astrometry for them. They are also the 7 rows that need the screen least — the MPC has
already linked every one of them to the object the ledger named.

**And the self-designation screen's null is now a real null.** M10 measured 0 of 1,971
*fitted ledger* rows, which is a population that had already survived a fit — and the
whole point of the artefact class is that it survives every fit. Screening 2,000 rows of
the shell's **coarse** head, before any gate, is the test that could have found it. It
did not. The class remains a distant-sweep phenomenon (7 of the all-sky top 200,
0 anywhere in the main-belt or shell regimes).

## 7. Traps hit (all paid for; check before touching this code)

1. **The archive's retention prunes the snapshot a milestone pinned, and the refresh
   answers anyway.** Five days after M10, the key sets for 08-16 … 08-20 are gone;
   `m10_refresh.py`'s directory scan silently promoted 08-21 to element 0 and reported
   **18 consumed** under a heading that said "since 20260816T202701Z". The true figure
   is 103. Guarded now (`scan_series` raises), and recoverable
   (`scripts/m11_snapshot_series.py` inverts the contiguous delta chain).
2. **`itf_observations_20260816_reconstructed.parquet` is not the 08-16 table.** It is
   the 08-16 ∩ 08-18 *intersection* — M9 dropped whole every tracklet that lost any
   observation. Verifying a 08-16 reconstruction against it fails by exactly the
   tracklets consumed in between (106 ledger observations here). Verify at **08-18**,
   where the two must agree, and use the delta walk for 08-16.
3. **A refresh reusing an older milestone's `obs80` "fresh" cache measures nothing.**
   The agreement check asks whether a consumed tracklet's observations are in the
   object's record *now*; against M10's 08-18 cache every consumption in the last five
   days would read as a disagreement. `--fresh-cache` is now explicit and M11 used a
   new directory.
4. **The decoy arm cannot be reconstructed from a finished sweep report.**
   `run_sweep(decoy=True)` does `m.pop("row")` and only `fake[:100]`, unranked, is
   stored. Any milestone that wants to price a fit stage must **re-run** the control —
   and then prove it is the same control. M11's reproduction gate (188,494 matches and
   five histogram bins, exact) is why the 0-of-300 can be compared to M10's 76-of-300
   at all.
5. **A post-fit orbit-quality gate is the wrong instrument for a decoy, and it fails in
   the flattering direction.** 295 of 300 decoy fits pass the strict gate, against 228
   of 300 real, because fo drops the fake tracklet whole and grades the object's own
   pristine orbit. Only "did fo use the tracklet" separates the arms (162/300 vs
   **0/300**). Report both halves or the control looks like it failed.
6. **The combined-fit line source must be pinned to the snapshot, not to today's ITF.**
   `m9_combined.py` took `index.get(key)` from the current `itf.txt.gz`; a tracklet the
   MPC has *partially* consumed since the sweep still appears there with fewer
   observations, so the joint fit would silently be of a different tracklet from the one
   the ledger passed. The live lines are now accepted only when their count matches the
   08-16 slim, else the verbatim `obs.txt` fo actually fitted is used. 2021 SZ54's three
   members took that path this run.
7. **Fit-directory fallbacks resolve by tag prefix, and a new milestone adds one.**
   `tracklet_lines_from_fit_dir` hardcoded `data/m8-fits`; shell rows are `mAa…` in
   `data/m10-shell-fits` and deep rows `mCa…` in `data/m11-deep-fits`. A hardcoded root
   returns `[]`, which reads as "MISSING lines" and skips the object silently.
8. **"13 multi-tracklet objects" and "10 multi-tracklet objects" are both true.** M10's
   13 counts *fit-grade* fits; the verdict chain then demoted one member each of three
   objects, leaving 10 with ≥ 2 **PASS** rows. State which population a tier is built
   from, or the next milestone re-derives a different number and thinks something moved.
9. **A "deepest lookback unfitted" claim needs checking against the fit report.** M10's
   own head already held 90 fits at 21–25 y; only its *yield* stopped at −20.74 y. The
   stratified queue was still worth running — it turned an artefact-of-ranking hypothesis
   into a measured 0 of 130 — but the premise as written was wrong.
10. **A long bash heredoc silently truncates in this harness.** Appending a ~120-line
    document section via `cat > file <<'EOF'` failed with "unexpected EOF" twice; the
    content had been cut before the terminator. Write long files with the file-writing
    tool and `cat` them in.

## 8. Tests

**505 passed** (485 before M11, plus 20 new in `tests/test_m11.py`), ruff clean across
`src`, `scripts` and `tests`. The new tests pin the four things M11 asserts that a unit
test can hold:

* **the decoy's reproduction gate** — it passes on M10's exact control and **fails on a
  single count** in either the total or any histogram bin, and on a missing histogram.
  This is the gate the whole fit-stage pricing rests on, so a near-miss must not slide
  through as a match.
* **the pruned-snapshot guard** — `scan_series` raises on the exact 2026-08-23
  configuration (base pruned, later snapshots surviving) and names the substitute it
  refused, and accepts a surviving base; plus the delta-walk identity
  `keys(parent) = keys(child) − appeared + gone` on a synthetic chain.
* **the deep end's strata and stopping rule** — the five strata partition 20–25 y with
  no gap and no overlap, `|Δt|` exactly at the 25.00 y window bound lands *inside* the
  last stratum (a naive `[24, 25)` would drop it), the 10/50 floor is M10's 20/100 at
  the same rate, and every fit tag is 7 characters.
* **fit-grade semantics** — strict gate *and* every observation used, and explicitly
  **false** for a fit that never ran (`tracklet_lines_missing` has no counts, and
  `None == None` would otherwise read as "fully used").

Plus the default-off contract: `m10_refresh.OUT`, `m10_review_queue.OUT_CSV` and
`m9_combined.OUT` still name M10's and M9's own files, the tag→fit-root maps were
*extended* rather than substituted, and `m11_shell_decoy`'s shell window is identical to
`m10_shell`'s — if that moved, the decoy would be pricing a different window.

## 9. Recommended next milestone (M12)

1. **The submission decision, still.** It was M10's item 1 and it is untouched here
   because it is Matthew's. `out/review-queue-v2-20260823.csv` is the current artifact —
   669 rows, ranked by arc extension, with `out/review-queue-v2-20260823-diff.json`
   saying exactly how it differs from the copy already open. §1.2 says M8's rows are
   still the perishable end, and now says M9's are perishable too. Everything below is
   worth less than a decision, including an explicit decision not to submit.
2. **Re-run the refresh immediately before any submission, and pass `--series`.** It
   costs one ITF pull and two minutes. The base snapshot is pruned, so the series must be
   rebuilt (`scripts/m11_snapshot_series.py`) or the refresh will refuse — which is the
   correct behaviour and will be surprising the first time.
3. **The shell tier is priced but not promoted; the open question is now its
   *composition*, not its reality.** The decoy answered "is it chance" (no, decisively).
   What remains is M10 §5.3 caveats 1–2 and M11 §3.2: one observatory, two-observation
   tracklets, and combined fits that pass only 3 of 10. A useful M12 would ask whether
   the ~17-row credible core (sep < 60″ inside a gate < 600″) behaves like the main tier
   on the one test that has never been applied to it — **arc extension against the
   object's published record**, the review queue's own sort key — and whether a
   705-only cluster is submittable at all given SARC's archival routing
   (standing constraint 3).
4. **Stop spending fo time at 21–25 y.** 220 fits, 0 of 130 beyond 20.74 y,
   p = 2.3 × 10⁻¹⁵ against the 20–21 y rate. The productive window is 15 y < |Δt| ≲ 20.7 y
   and the shell is now swept to its own floor. Do not widen past 25 y: that bound is
   measured, and the main-belt envelope breaks at 28 y.
5. **Tighten what the primary gate is allowed to become.** §4.2 measured that the entire
   discriminating power of the chain sits in "did fo use the tracklet" and none in the
   RMS ceiling. Any future proposal to relax "fully used" — including for 2-observation
   tracklets, where it is weakest — should be measured against a decoy arm before it is
   adopted, not argued from RMS.
6. **The gate's own false-rejection rate now has 33 measurements.** 27 over-conservative,
   5 correct, 1 partial: the strict gate refuses a *wrong* attribution about 15 % of the
   time it refuses anything. `HANDOFF.md` §4 still calls the acceptance gate "the open
   question"; this is the first sample big enough to start answering it, and a further
   week of refreshes would sharpen it for free.
7. **Standing constraints are unchanged.** No submission without explicit per-batch human
   review, sandbox first, SARC before any archival submission, and automation of
   end-to-end submission stays permanently out of scope.

---

*Generated by `scripts/m11_snapshot_series.py`, `scripts/m10_refresh.py`,
`scripts/m10_decay.py`, `scripts/m10_review_queue.py`, `scripts/m11_queue_diff.py`,
`scripts/m9_adjudicate.py`, `scripts/m9_combined.py`, `scripts/m11_shell_decoy.py`,
`scripts/m11_deep.py`, `scripts/m10_verdicts.py` and `scripts/m11_shell_screens.py`.
Regenerable artifacts: `data/raw/rubin/m11-refresh.json`, `m11-decay.json`,
`m11-shell-screens.json`, `m11-shell-coarse.parquet`, `m11-crosstier-input.json`; root
(gitignored) `m11-shell-decoy.json`, `m11-shell-adjudication.json`,
`m11-shell-combined.json`, `m11-crosstier-combined.json`, `m11-deep.json`,
`m11-deep-new.json`, `m11-deep-ledger.json`; and `out/review-queue-v2-20260823.csv`
plus its summary and diff, which are the deliverable. The fresh 2026-08-23 18:27:06 GMT
ITF pull and the rebuilt snapshot series were parsed **outside the repository** and are
not part of the archive. `out/review-queue.csv`, `m8-ledger.json`, `m9-ledger.json`,
`m10-shell-ledger.json`, `m9-combined.json`, `m9-adjudication.json` and
`m10-adjudication.json` were read and not written.*
