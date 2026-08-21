# M4 — the sky finished through AIP, the parent reconciled, the Gvar gap closed, and candidate D's JWST data

*2026-08-21 · follows [M3](M3-full-screen.md), executing M3 §7's own recommendations.
Every externally-sourced number carries its source; anything unsourced is marked UNSOURCED.
**Nothing in this milestone has been submitted, posted, or sent anywhere.** The candidate-I dossier
and the Ren+24 note remain Matthew-gated and are unchanged by this document.*

---

## 0. Pre-registrations

*Written and timestamped **before** the runs they govern, per repo law. Nothing below was chosen
after seeing a result.*

### PR-1 — the AIP route: verify before trusting, and the stopping rules (declared before any pull)

M3 §6 handed M4 a route it had **measured in part**: that AIP hosts the catalogues, that anonymous
async works, and that the cap implies ~27 deg² tiles. Before a single row of new sky is trusted,
five things are verified, and **any one of them failing stops the route rather than being worked
around**:

| # | check | pass condition |
|---|---|---|
| V-a | every catalogue the screen joins is hosted at AIP | all five tables present in `TAP_SCHEMA` |
| V-b | anonymous async genuinely works, **with no account** | a job posted with no credentials reaches COMPLETED. **If AIP asks for registration at any point the run stops and reports — no account is created.** |
| V-c | the real per-job limit is **re-measured**, not assumed from M3's 30 s | the largest cell that completes is measured directly, at ≥3 sizes |
| V-d | the screen's cuts mean the **same thing** at AIP as at ESAC | each cut's AIP implementation is checked against its ESAC semantics on real rows before use |
| V-e | **acceptance test**: AIP reproduces ESAC's `source_id` set on sky ESAC already delivered | reported as a set comparison with the disagreements counted, whatever it says |

**Stopping rules**, unchanged in spirit from M3 PR-1 and ported into the new driver: a failure
returning in < 5 s consumes no retry budget (it is an error page, not a hard cell); 8 consecutive
instant failures arm a cooldown/probe ladder; 6 failed probes stop the run cleanly. **Whatever
coverage exists when a rule fires is the result, reported as a sky fraction and never as a complete
screen.**

**One rule that is deliberately the opposite of ESAC's.** M2/M3 established for ESAC: *retry, never
split — the wall is size-independent*. At AIP the limit is a genuine execution timeout, so it **is**
size-dependent, and splitting is the correct response. That inversion is pre-registered here so it
cannot be mistaken for a result-driven choice later.

**Unbiasedness.** Cells are issued in a fixed pseudo-random permutation (seed 20260821), so a
partial run is a uniform sample of the sphere and rates scale by sky fraction — the same law as
M2 §4.2.

### PR-2 — the parallax proxy: purity, measured on a sample containing the complement

M3 measured the proxy's **recall** (99.09%) and stated plainly that purity was unmeasurable from its
data, because the ESAC pull applied `r_med_geo < 300` server-side and therefore contained no objects
outside the cut. M4 fixes the sample, not the statistic:

- the AIP harvest is cut only at `parallax > 2.5 mas`, so it **does** contain the complement;
- exact `r_med_geo` for those rows is then obtained from ESAC and treated as truth;
- purity, recall and F1 are reported for four thresholds fixed in advance
  (`1000/ϖ < 300`, `ϖ > 3.0`, `ϖ > 3.2`, `ϖ > 3.5`) plus two parallax-S/N-gated variants;
- **decision rule, fixed now:** if purity is poor, the screen either (a) uses the exact ESAC
  `r_med_geo` route instead, or (b) states in every downstream number that its parent sample is
  proxy-limited and carries the measured contamination as a correction. It does **not** quietly keep
  the proxy.

### PR-3 — the 1.43× parent discrepancy: what counts as settling it

The deliverable is **either** a corrected parent definition that reconciles with Suazo et al. 2024,
**or** a quantified explanation of why the two legitimately differ. The candidate causes listed by
M3 §7 are tested in this order, and the answer is whichever the paper's own text and this screen's
own data support — not whichever closes the gap:

1. the stage at which Table 4's `~3.2 × 10⁵` row is defined (does it include the contamination flag?);
2. the blueward locus extension (fitted fraction 32% → 98.6%);
3. the DR3-vs-earlier-Gaia baseline;
4. quality-flag differences;
5. the Bailer-Jones/proxy substitution.

**An absolute sky-wide yield may be quoted only if this closes.** If it does not, M3's refusal
stands.

### PR-4 — the Gvar reference gap: close it or bound it

M3 logged Gvar as documented irreproducibility worth "the largest single unexplained factor". Two
attacks, both declared before running:

- **Reconstruct**: Gvar (Suazo Eq. 4, after Vioque et al. 2020) is a ratio to the median of
  "sources with similar fluxes". The reference sample is not published, so it is varied over six
  pre-listed definitions — R1 in-sample W3W4-detected/0.2 mag (M3's own), R2 cc-clean subsample,
  R3 full-10-band subsample, R4 0.1 mag bins, R5 0.5 mag bins, R6 1.0 mag bins — and the funnel is
  reported as the **spread** across them.
- **Bound**: Gvar's cut is monotone, so no reference sample whatsoever can produce more survivors
  than disabling Gvar entirely, or fewer than zero. That two-sided bound is computed and quoted; it
  needs no reference sample and cannot be argued with.

**Also pre-registered, because it is the obvious confound:** the paper's Table 4 puts the nebular
CNN **between** the RMSE gate and the extra cuts. Our funnel has no CNN. Before attributing anything
to Gvar, the stage alignment is checked, and every ratio is quoted against the paper's rate **with
the CNN stage removed** as well as with it.

### PR-5 — candidate D's JWST data: what would count as confirming, and what as calibration

D's GO 7199 products became public 2026-07-28. Declared before the data were touched:

- the attribution is judged **CONFIRMED / CONSISTENT-WITH / IN TENSION** with Hephaistos IV's
  z ≈ 0.9 background galaxy, and "the public imaging alone cannot decide" is an allowed and
  expected answer;
- the number that matters for this project is not the verdict but the pair **(separation,
  contrast)**, because that is what converts into a centroid pull;
- the predicted AllWISE centroid pull is computed as `sep × f_contam/(f_star+f_contam)`, stated as
  an **upper bound** on a profile-fit centroid, and compared against **D's own measured
  1.41″ (W3) / 2.55″ (W4)** from `out/w2_centroid_offsets.csv`;
- the deliverable is a **threshold separation as a function of contrast** — the locus above which an
  archival centroid test can see a contaminant at all — and hence what fraction of the screen's
  pre-visual survivors' contaminants would be invisible to archival methods.

---

*(Everything below is written after the runs. Numbers are emitted by the scripts named, never
hand-copied.)*

---

## 0b. What M4 established

1. **The sky is finished. 41,253 deg², 100.00%, 220 cells, 0 abandoned** — through the AIP mirror,
   anonymously, with no account, while ESAC's join tables stayed dead all day (§1, §6.1).
2. **The AIP route needed four corrections before a single row could be trusted, and three of them
   would have corrupted the harvest silently** (§1): the 30 s cap is a Postgres *statement* timeout,
   not the UWS `executionDuration` M3 named, and the tiling that beats it is a `source_id` range
   rather than a sky box; AIP stores AllWISE's null uncertainty as a **sentinel 0.0**, so ESAC's
   detection predicate silently passes everything and inflated the parent **32×**; the 2MASS join
   key is the **designation, not the oid** — on the oid, **0 of 41,844** designations matched ESAC
   and J was wrong by a median **+5.55 mag** while every other column matched exactly; and AIP
   renames `source_id` to `datalinkID` in every VOTable.
3. **The acceptance test then passed exactly**: on all **220,632** ESAC-harvested rows, AIP returns
   the same source set — **Jaccard 1.00000, 0 rows on either side unmatched**, and `w3mpro`,
   `w4mpro`, `j_m`, `phot_g_mean_mag` agreeing to **max |diff| = 0.00000** (§1.5).
4. **The parallax proxy's purity is measured at last: 98.46%** (recall 98.99%) on 507,382 rows that
   contain the complement M3's sample could not — and it is not needed, because ESAC's *single-table*
   PK lookups still work while its joins do not, so **all 439,923 rows of the parent carry an exact
   Bailer-Jones distance and none falls back to the proxy** (§1.6, §1.7).
5. **The 1.43× parent discrepancy is settled: it was a stage-alignment error.** Suazo et al. §2.1
   says in words that Table 4's "W3/W4 detection ∼3.2 × 10⁵" row is **after** the contamination-flag
   cut. Compared like for like, the parent is **328,937 against 320,000 = 1.03×** (§2). A second,
   independent number in the paper (§5's "∼200,000 with W3/W4 detection and SNR ≥ 3.5") lands at
   **1.011×**. **An absolute sky-wide yield may now be quoted**, and no longer needs projecting.
6. **The Gvar reference gap is closed, and it was never the largest factor.** M3's "the paper's
   extra cuts reject 54%" was the **CNN**: Table 4 puts the nebular classifier *between* the RMSE
   gate and the extra cuts, whose own rejection is **10.4%** against our **11.15%**. Our Gvar
   rejects **more** than the paper's, not less. Across seven reference definitions the pre-visual
   count moves between 1,545 and 1,549, and a **reference-free monotonicity bound** caps the entire
   question at **12 survivors out of 1,557 — 0.77% of the funnel** (§3).
7. **The reference sample itself is reconstructed** from the paper's own published Gvar values:
   ours/paper = **1.2097** (n = 7, sd 0.096), i.e. our cut at 2 is the paper's cut at 1.653 — **our
   implementation is the stricter one** (§3.2).
8. **The 4.2× overproduction is the nebular CNN, and it is measured through Galactic latitude.**
   Every reproducible stage reproduces (parent 1.03×, RMSE 0.84×, extra cuts 0.84×). The residual
   is not spread across the funnel: the pre-visual yield per deg² runs from **20.9× the paper's
   mean at |b| < 5°** to **1.05× [0.94–1.17] at |b| > 50°**, and the conditional S/N pass rate at
   |b| > 50° is 6.9% against the paper's 7.2% (**0.96 ± 0.10×**). **All 7 of the paper's 7
   published candidates lie at |b| > 30°** (p = 0.008 under isotropy) (§4).
9. **M3's own explanation for the S/N stage is refuted by its own data**: **zero** of the 8,428
   extra-cut survivors lie blueward of M_G = 6, so the blueward template extension cannot have
   caused it (§4.2).
10. **Candidate D's contaminant is measured, not cited.** From the public GO 7199 MIRI mosaics —
    a *newer re-reduction* than the paper's — **separation 1.23 ± 0.07″ at PA 33 ± 1°**, contrast
    **0.236 / 7.24 / 83.1** at 5.6 / 10 / 15 μm, point-like, F<sub>ν</sub> ∝ λ<sup>+4.4</sup>, and
    supplying **88% of the 10 μm and 98.8% of the 15 μm flux**. The star is photospheric. The
    contamination is **CONFIRMED**; the z ≈ 0.9 Hot-DOG identification rests on the MRS spectrum and
    is **not independently confirmed here** (§5).
11. **The archival centroid axis is wrong in direction as well as magnitude near the floor.** The
    geometric ceiling on the pull is the separation itself, **1.23″**; our archival W4 offset for D
    (2.55 ± 0.50″) and Ren et al.'s (1.8″) both exceed it, and our W3 offset points **50° away** from
    the real contaminant, at a place where MIRI shows nothing (§5.3).
12. **The floor now has a number**: `sep_thr(ρ) = F · (1 + 1/ρ)`, asymptoting to the floor itself, so
    **≈10% (1″ floor) to ≈40% (2″ floor) of chance-aligned contaminants are invisible to centroid
    vetting at any brightness** (§5.3).
13. **A free by-product: M3's extrapolation from 48% was good to a few percent, not to Poisson** —
    +2.0% on the parent, +13.5% on the pre-visual survivors, against quoted Poisson intervals of
    ±0.2% (§2.4).
14. **The full-sky funnel is delivered at γ ≥ 0.10: 439,923 W3W4-detected → 328,937 parent →
    9,486 RMSE → 8,428 → 1,545 pre-visual survivors** (§6.2). **Vetting those 1,545 was still
    running at session end** and is reported as such, not as finished (§6.3); the one gate that
    needs no network says **260 of them (16.8%) are SUB-THRESHOLD** — both excess bands below WISE's
    own 5σ standard — and that rate **rises** with Galactic latitude (9.6% → 30.0%), a third
    independent check on point 8. **No object has reached STILL-CLEAN and none can while the
    centroid axis is invalid, so there is no Matthew-gated candidate.**

---

## 1. The AIP route — verified, corrected in four places, and run

*`scripts/m4_aip_screen.py`; artifacts `out/m4_aip_route_probe.json`,
`out/m4_aip_acceptance.json`, `out/m4_proxy_purity.json`.*

M3 §6 handed over a route it had measured in part. Under PR-1 it was **re-verified before use**,
and four properties of it had to be corrected or discovered before a single row could be trusted.
**Two were M3 statements that turned out to be wrong** (the nature of the 30 s cap, §1.1; and the
implicit assumption that a hosted catalogue means a transferable cut, §1.2). **Two were found
here** (§1.3, §1.4). **Three of the four would have silently corrupted the other half of the sky**,
and none of the three announced itself — every one produced a query that ran, returned plausible
numbers, and was wrong. This section is mostly about them, because the route itself works.

### 1.0 What was verified (PR-1's five checks)

| check | result |
|---|---|
| **V-a** all five joined catalogues hosted | **PASS** — `gaiadr3.gaia_source`, `gaiadr3.allwise_best_neighbour`, `catalogs.allwise`, `gaiadr3.tmass_psc_xsc_best_neighbour`, `catalogs.tmass`. EDR3 Bailer-Jones distances absent, as M3 said |
| **V-b** anonymous async, **no account** | **PASS** — a job posted with no credentials of any kind returns 303 and reaches COMPLETED in 2.8 s. **AIP never asked for registration at any point in this milestone. No account was created.** |
| **V-c** real per-job limit re-measured | **PASS, and M3's explanation was wrong** — see §1.1 |
| **V-d** cuts mean the same thing at AIP as at ESAC | **FAILED TWICE, then fixed** — see §1.2 and §1.3 |
| **V-e** acceptance against ESAC's own rows | **PASS, exactly** — see §1.4 |

### 1.1 The 30 s cap is a Postgres statement timeout, not a UWS limit — and the fix is a different tiling

M3 reported "async `executionDuration` = 30 s" and inferred ~27 deg² tiles. The parameter is real
but it is **not the binding constraint**: `executionduration` can be set anonymously to 300, 3600 or
**86400** s and the service reports the new value back — and then kills the query anyway at ~30 s
with `canceling statement due to statement timeout`. It is a **backend statement timeout**, and no
UWS parameter touches it.

The tiling consequence is different from M3's. The cost is dominated by how the planner reaches
`gaia_source`, not by sky area:

| query driven by | footprint | DB time |
|---|---|---|
| dec/ra box, `gaia_source` alone with `parallax > 2.5` | 215 deg² | **26.9 s** (before any join) |
| dec/ra box, full 5-table join | 215 deg² | **ERROR at 31.5 s** |
| dec/ra box, full 5-table join | 53.7 deg² | **ERROR at 31.3 s** |
| `CONTAINS(... BOX ...)` instead of `BETWEEN` | 215 deg² | 27.5 s — no better |
| **`source_id BETWEEN a AND b`**, `gaia_source` alone | ~6 deg² | **0.0 s** |
| **`source_id` range, full 5-table join** | ~298 deg² | **18.7 s**, 10,003 rows |
| `source_id` range, full 5-table join | 596 deg² | 21.3 s |
| `source_id` range, full 5-table join | 1,193 deg² | ERROR at 31.6 s |

A dec/ra box forces a scan; a **`source_id` range hits the primary key**. And because Gaia's
`source_id` is (HEALPix level-12 index) × 2³⁵ + sequence, a contiguous `source_id` range **is** a
contiguous sky region covering exactly `span / (12 × 2⁵⁹)` of the sphere — so the sky-area
bookkeeping is exact by construction, with no Monte Carlo and no overlap arithmetic. The screen
therefore tiles in **HEALPix level-2 cells (192 cells, 214.9 deg² each)**, halving any cell that
times out.

*This is also where PR-1's deliberately-inverted rule earns its keep: against ESAC the wall is
size-independent and splitting is useless (M2/M3); against AIP the limit is a genuine execution
timeout and splitting is the correct response. Same symptom, opposite remedy.*

### 1.2 The W3/W4 detection cut does not transfer — AIP stores the null as a sentinel 0.0

The screen's server-side cut C2a is "W3 **and** W4 have a measured profile-fit uncertainty". At ESAC
that is `w3mpro_error IS NOT NULL`, and it is exactly `ph_qual[W3] ≠ 'U'` — **verified: 0 of the
220,632 ESAC-harvested rows carry a 'U' in W3 or W4.**

At AIP the same predicate does nothing. `catalogs.allwise` stores **0.0**, not NULL, where AllWISE
has no uncertainty: of 1,715 sampled rows with `ph_qual[W3] = 'U'`, **0 have `w3sigmpro` NULL and
1,715 have `w3sigmpro` exactly 0.0.** `IS NOT NULL` is therefore true for every row in the
catalogue and the cut silently vanishes.

Caught by the harvest rate: **253 rows/deg² against ESAC's 11.1** — a **32×** inflated parent that
would have propagated into every downstream number. The correct AIP predicate is
**`w3sigmpro > 0 AND w4sigmpro > 0`**.

### 1.3 The 2MASS join key is not the oid — and the acceptance test is the only thing that caught it

`catalogs.tmass` has a `tmass_oid`; `gaiadr3.tmass_psc_xsc_best_neighbour` has a
`clean_tmass_psc_xsc_oid`. On the first rows of the catalogue they agree, because both orderings
start at the south celestial pole — which is exactly why a three-row spot check passed. **They are
different keys.**

Joined on the oid, the acceptance test found:

- **0 of 41,844** 2MASS designations matching ESAC's;
- a **median J-magnitude error of +5.55 mag** — the join returns a *different 2MASS star at a
  similar declination*;
- while `w3mpro`, `w4mpro` and `phot_g_mean_mag` matched ESAC **exactly** (max |diff| = 0.00000).

That last line is why this was dangerous: everything else was perfect, and J/H/Ks are 3 of the 10
bands in the RMSE fit — the funnel would have run, produced plausible-looking numbers, and been
wrong.

The correct join is on the designation string,
`catalogs.tmass.designation = tmass_psc_xsc_best_neighbour.original_ext_source_id`. That join times
out (31.6 s) when driven by a dec/ra box — which is why the oid was tried in the first place — but
completes in **24.3 s** when driven by a `source_id` range. **§1.1's tiling is what makes §1.3's
correct join affordable.** `catalogs.tmass_orig` carries an ESA-looking `oid` and would have been
the natural fix; it is listed in `TAP_SCHEMA` and is **not queryable** ("Table tmass_orig not
found").

*Cost of the error: 42 cells (~9,000 deg²) had to be discarded and re-pulled. They are kept, not
deleted, in `data/w4/aip/cells_BAD_oidjoin/` with the manifest that produced them, so the failure
is auditable. The re-pull returned **identical row counts per cell** — confirming that only the four
2MASS columns were ever wrong.*

### 1.4 A fourth, cosmetic but fatal one: AIP renames `source_id` to `datalinkID`

AIP attaches a DataLink service descriptor keyed on the Gaia `source_id` and, as a side effect,
emits that column in every VOTable under the name **`datalinkID`**. No SQL alias overrides it —
`AS source_id` and `AS gsid` both come back as `datalinkID`. Unhandled, this removes the join key
from every downstream stage. Verified equal to `source_id` before being renamed back
(`read_cell()`): on cell h2c00083, 2,497 rows match ESAC-harvested `source_id`s with max |Δra| = 0.0
and max |ΔW3| = 0.0.

### 1.5 The acceptance test, after the fixes

PR-1's V-e, restricted to the **intersection of the two coverages** (otherwise "ESAC only" is just
sky AIP has not reached):

| | |
|---|---|
| ESAC rows in the overlap | **220,632** |
| AIP rows in the overlap | **220,632** |
| in both | **220,632** |
| ESAC only / AIP only | **0 / 0** |
| **Jaccard** | **1.00000** |
| `w3mpro`, `w4mpro`, `j_m`, `phot_g_mean_mag` | median diff **0.00000**, max abs diff **0.00000** |

**On the full ESAC harvest — all 220,632 rows, not a sample — the AIP route reproduces it exactly:
same sources, same photometry, to the last digit, with not one row on either side unmatched.** The
other half of the sky can be trusted on the same footing as the first half.

*This test earned its keep three times. It caught the 2MASS key error (§1.3); it caught the
`datalinkID` rename (§1.4); and on its first full-sky run it caught **263 missing rows (0.12%)** that
had nothing to do with AIP — a **file-index collision** in the ESAC distance-lookup cache. Batch
files were named `d{count:05d}.csv` from the number of existing files, so after one truncated file
was deleted the next batch silently **overwrote** an existing one, destroying 2,000 lookups. The
263 of those that fell in the ESAC-overlap region were the only visible symptom. Fixed by naming
each batch with the first free index; the ids were re-fetched and the table above is the result.
**Every one of the three was a query that ran, returned plausible numbers, and was wrong.**

### 1.6 The distance cut: exact, not proxied

AIP has no EDR3 Bailer-Jones distances, which M3 identified as the route's one gap and proposed to
cover with a parallax proxy. It turns out the gap does not have to be covered at all.

**ESAC's single-table primary-key lookups still work while its joins are dead.** A query
`SELECT source_id, r_med_geo FROM external.gaiaedr3_distance WHERE source_id IN (…)` returns 2,000
ids in **3.6 s** on the same afternoon that a bare three-table `COUNT(*)` dies at 61 s. So the
screen harvests from AIP under the **lossless parallax superset** and then attaches the **exact**
`r_med_geo` from ESAC, reproducing cut C1 with no proxy at all.

**The superset is measured, not assumed.** Across all 220,632 ESAC-harvested rows — every one of
which satisfies `r_med_geo < 300` — the **minimum parallax is 3.2668 mas**. So `ϖ > 2.5` retains
100.000% with 0.77 mas of margin (M3 measured the same thing on 95,310 rows; this confirms it on
2.3× more). `ϖ > 3.3333` (the naive `1000/ϖ < 300`) retains 98.99%, matching M3's 99.09% recall.

The proxy remains the documented fallback for any row whose ESAC lookup has not landed, and every
funnel counts the proxy-covered rows separately so the proxy-limited fraction of the parent is
always visible rather than hidden.

### 1.7 The parallax proxy's PURITY — measured, which M3 could not do

M3 measured the proxy's **recall** at 99.09% and said plainly why that was not enough: *"the pull
applied `r_med_geo < 300` server-side, so this sample contains no objects outside the cut — recall
is measured, purity is not."* Recall alone cannot bound contamination of the parent, because a
sample that contains no negatives cannot produce a false positive.

PR-2 fixes the sample rather than the statistic. The AIP harvest is cut only at `ϖ > 2.5`, so it
**does** contain the complement; exact `r_med_geo` from ESAC is then truth. On 20,730 AIP rows
carrying both:

| proxy | selected | TP | FP | **purity** | recall | F1 |
|---|---|---|---|---|---|---|
| **`1000/ϖ < 300`** (M3's proxy) | 442,261 | 435,465 | **6,796** | **98.46%** | 98.99% | 0.9872 |
| `ϖ > 3.0` | 507,382 | 439,923 | 67,459 | 86.70% | 100.00% | 0.9288 |
| `ϖ > 3.2` | 466,708 | 439,923 | 26,785 | 94.26% | 100.00% | 0.9705 |
| `ϖ > 3.5` | 414,792 | 410,084 | 4,708 | 98.86% | 93.22% | 0.9596 |
| `1000/ϖ < 300` **&** `ϖ/σ_ϖ > 5` | 436,632 | 434,704 | **1,928** | **99.56%** | 98.81% | 0.9918 |
| `1000/ϖ < 300` **&** `ϖ/σ_ϖ > 10` | 428,186 | 427,922 | **264** | **99.94%** | 97.27% | 0.9859 |

**The proxy's purity is 98.46%** on 507,382 rows — contamination of the parent would be **1.54%**,
and the recall (98.99%) reproduces M3's 99.09% independently. The contaminants are what they should
be: distant stars scattered above the threshold by parallax error, which is why gating on
`ϖ/σ_ϖ > 5` removes 72% of them (6,796 → 1,928) for 0.2% of recall, and `ϖ/σ_ϖ > 10` removes 96%
(→ 264) for 1.7%.

*Measurement note: the denominator is the `ϖ > 3.0` population, because that is what `distances`
looks up — no source with `r_med_geo < 300` can have `ϖ ≤ 3.0` (the minimum over 220,632 such rows
is 3.2668 mas, and this sample independently shows recall 100.00% at `ϖ > 3.0`). Rows with
2.5 < ϖ ≤ 3.0 are all true negatives that the proxy does not select, so including them would change
neither purity nor recall.*

**Under PR-2's decision rule this is moot in the best way**: the screen does not use the proxy for
the parent at all — it uses the exact ESAC `r_med_geo` (§1.6). In the delivered full-sky funnel
**every one of the 439,923 rows inside C1 carries an exact Bailer-Jones distance and none falls back
to the proxy**, so the parent's proxy contamination is **zero**, not 1.54%. The purity number is
what licenses the proxy as a *fallback*: if ESAC's PK lookups go down too, the screen can fall back
to `1000/ϖ < 300 & ϖ/σ_ϖ > 5` and carry a **measured** 0.44% contamination rather than an unmeasured
one. **The parent sample of this screen is not proxy-limited.**


---

## 2. The 1.43× parent discrepancy — SETTLED, and it was a stage-alignment error

*Numbers from `scripts/m4_funnel_reconcile.py --parent aip`,
`out/m4_funnel_reconcile_m4full.json`. **All of §2–§4 is measured on 100% of the sky**, not
projected; `out/m4_funnel_reconcile_m4.json` holds the same analysis on M3's 48.18% for comparison,
and the two agree throughout.*

### 2.1 What Table 4's "W3/W4 detection" row actually is

M3 §2.4 flagged the parent sample as **1.43× the paper's** — 457,960 projected against
~3.2 × 10⁵ — called it "a 1.43× systematic", named the most likely cause as the definition of
"detected", and correctly refused to quote an absolute sky-wide yield until it was settled.

It is settled, and the cause was not a definition of "detected". It is the **stage** at which
Table 4's row sits. **Suazo et al. 2024 §2.1**, verbatim:

> "Following the above mentioned criteria, our initial sample comprised approximately 5 million
> sources. Subsequently, we implemented an additional selection criterion, demanding detections in
> the 12 and 22 μm bands (W3 and W4, respectively) from WISE. … **We additionally excluded sources
> that exhibited contamination according to the WISE contamination flag.** As a result of **this
> filtering step**, our sample was downsized to approximately 320,000 stars."

The ~320,000 is therefore the count **after** the contamination-flag cut. Table 4 has no separate
`cc_flags` row, so there is nowhere else for that cut to live. M3 compared our count from **before**
`cc_flags` against a paper number from **after** it:

| our funnel row, **all sky** | count | vs the paper's 3.2 × 10⁵ |
|---|---|---|
| W3 **and** W4 detected, **before** `cc_flags` | 439,923 | **1.375×** ← M3's comparison |
| W3 **and** W4 detected, **after** `cc_flags` | **328,937** | **1.028×** ← the paper's own definition |

Our `cc_flags` pass rate is 74.77%. **The like-for-like parent is 1.028× the paper's, not 1.43×.**
The whole discrepancy is one cut applied on one side of a comparison.

### 2.2 A second, independent check from a different part of the paper

Suazo et al. §5, computing their contamination rate, state a number that never appears in Table 4:

> "…we must use it on the sample of stars with W3/W4 detection and signal-to-noise ratios ≥ 3.5 in
> these bands, corresponding to **∼200,000 sources**."

That is an independent handle on the parent, at a different cut. Ours, all sky:

| reading of "W3/W4 detection and SNR ≥ 3.5" | ours | vs ~200,000 |
|---|---|---|
| with `cc_flags` applied | 143,507 | 0.718× |
| without `cc_flags` applied | **202,188** | **1.011×** |

The looser reading matches to **1.1%** — 202,188 against "∼200,000". The sentence is loose enough
that it does not decide which cut it means, so it is corroboration rather than a measurement; but
on the reading that matches, it matches to a percent, and **neither reading is anywhere near
1.43×**.

### 2.3 What is left: a residual ~3%, and the candidates for it

The reconciliation is not exact. **1.028×** means our parent is ~3% larger than the paper's — which
"approximately 320,000" at two significant figures very nearly absorbs, but not quite. Candidates,
none of them tested here and all of them small:

- the AllWISE ⟷ Gaia crossmatch table version (this screen joins `gaiadr3.allwise_best_neighbour`;
  the paper says only that it used "the `allwise_best_neighbour` … catalogues provided by the Gaia
  consortium", §2.1, without naming a data release);
- `ph_qual ≠ 'U'` versus a numerical S/N floor as the operational meaning of "detection" — M3 §2.4's
  original hypothesis, which survives, demoted from a 1.43× effect to a ~3% one;
- rounding: "approximately 320,000" is stated to two significant figures.

### 2.4 A free by-product: how good M3's extrapolation from 48% actually was

The screen is now complete, so M3's projections from 48.18% can be graded against the truth — a
check on the "a partial screen is an unbiased sample" law that every M2/M3 number leaned on:

| quantity | M3 projected from 48.18% | measured on 100% | projection error |
|---|---|---|---|
| W3W4-detected, pre-`cc_flags` | 457,960 | 439,923 | **+4.1%** |
| W3W4-detected, post-`cc_flags` | 335,500 | 328,937 | **+2.0%** |
| RMSE ≤ 0.2 survivors | 9,907 | 9,486 | **+4.4%** |
| pre-visual survivors | 1,754 | 1,545 | **+13.5%** |

**The law held, but to a few percent — not to the Poisson interval M3 quoted.** M3's parent
interval was [456,985–458,938], ±0.2%, and the truth sits 4% outside it. The reason is structural
and worth recording: the sky is dominated by the Galactic plane, so a 93-tile sample has
**much** larger variance than Poisson on the counts, and the pre-visual stage — which §4 shows is
concentrated in the plane — is the most affected of all (+13.5%). **A pseudo-random tiling makes a
partial screen unbiased in expectation; it does not make its counting error Poisson.** Future
partial-screen projections in this project should carry a few-percent systematic, and a
plane-weighted one for any plane-concentrated quantity.

### 2.5 Consequence — an absolute sky-wide yield may now be quoted

M3's refusal was conditional on exactly this: *"no absolute sky-wide yield from this screen should
be quoted until it is settled."* Under PR-3 the condition is met — the parent reconciles to 1.03× on
the paper's own definition, with the residual bounded and its candidate causes named — and the
sky-wide yield no longer needs projecting at all, because the screen now covers the sky. **Absolute
rates are quoted from here on.**

---

## 3. The Gvar reference gap — CLOSED, and it was never the largest factor

*M3 §2.2 recorded: "the extra cuts (Gvar, RUWE, ext_flg, classprob) reject 11% where the paper's
reject 54% … that is a documented irreproducibility, not a discovery, and it is the largest single
unexplained factor in the funnel." Three separate measurements say otherwise, and the first
disposes of the premise.*

### 3.1 The 54% was the CNN, not Gvar — Table 4's own row order

Hephaistos II Table 4, in the paper's order:

| stage | number |
|---|---|
| RMSE ≤ 0.2 | 11,243 |
| **Nebular classifier (the CNN)** | **5,732** |
| Extra cuts | 5,137 |
| SNR W3/W4 > 3.5 | 368 |

The CNN sits **between** the RMSE gate and the extra cuts. M3 computed 5,137/11,243 = 45.7% and
attributed the missing 54.3% to the extra cuts — but 11,243 → 5,732 is the **CNN** (49.0%
rejected) and 5,732 → 5,137 is the extra cuts (**10.4%** rejected). This screen has no CNN, so the
like-for-like comparison is against 10.4%.

**Ours rejects 11.15%. The paper's rejects 10.38%. The gap M3 measured does not exist.**

Per criterion, against the paper's own §2.5.6 accounting ("A total of 282 sources are rejected by
[RUWE] alone, which corresponds to roughly half of all sources rejected by any criteria in Section
2.5. The Hα emission, the optical variability, and the extended flag criteria equally contribute to
the rest of the cuts"):

| criterion, applied alone | ours, of 9,486 RMSE survivors | paper, of its 5,732 post-CNN |
|---|---|---|
| RUWE ≥ 1.4 | 401 = **4.23%** | 282 = **4.92%** (stated) |
| `ext_flg` ≠ 0 | 513 = **5.41%** | ~104 = ~1.82% (inferred) |
| `classprob` ≤ 0.9 | 207 = **2.18%** | not separately reported (§2.5.6 omits it from "the rest") |
| **Gvar ≥ 2** | **290 = 3.06%** | **~104 = ~1.82%** (inferred) |
| all together | 1,058 = **11.15%** | 595 = **10.38%** (stated) |

**Our Gvar rejects more than the paper's (3.06% vs ~1.82%), not less.** The direction M3 assumed is
backwards.

### 3.2 The reference sample, reconstructed from the paper's own published Gvar values

Gvar (Suazo Eq. 4, after Vioque et al. 2020) is a ratio to "the median value of sources with similar
fluxes". That reference population is never published — that is the irreproducibility. But
**Suazo et al. Table 5 publishes Gvar for the seven candidates**, and M1 computed ours for the same
seven stars from our own in-sample reference (`out/w1_acceptance.csv`). The ratio *is* the
reference-sample offset, measured on real objects instead of guessed:

| | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| ours | 1.364 | 1.094 | 1.054 | 1.023 | 1.089 | 1.213 | 1.271 |
| paper | 1.03 | 0.94 | 0.90 | 0.97 | 0.90 | 0.93 | 0.99 |
| ratio | 1.324 | 1.164 | 1.171 | 1.055 | 1.210 | 1.305 | 1.284 |

**Median ours/paper = 1.2097** (sd 0.096, range 1.055–1.324, n = 7). Our Gvar runs ~21% high, so
our cut at 2 is the paper's cut at **1.653** — **our implementation is the stricter one**.
Rescaling our threshold to 2 × 1.2097 = 2.419, to match the paper's effective cut, moves the
pre-visual survivor count from 1,545 to **1,549**.

### 3.3 The bound that needs no reference sample at all

Gvar's cut is monotone: a different reference sample can only move objects across a single
threshold. So the **entire** question — for every reference population that could ever be
chosen — is bounded by turning the cut off:

| Gvar reference | Gvar ≥ 2 rejected | pre-visual survivors | vs paper |
|---|---|---|---|
| R1 in-sample W3W4-detected, 0.2 mag (M3's) | 289 | 1,546 | 4.20× |
| R2 cc-clean subsample, 0.2 mag | 290 | 1,545 | 4.20× |
| R3 full-10-band subsample, 0.2 mag | 290 | 1,545 | 4.20× |
| R4 in-sample, 0.1 mag bins | 288 | 1,545 | 4.20× |
| R5 in-sample, 0.5 mag bins | 291 | 1,545 | 4.20× |
| R6 in-sample, 1.0 mag bins | 291 | 1,545 | 4.20× |
| R8 threshold rescaled to the paper's published Gvar (§3.2) | 228 | 1,549 | 4.21× |
| **Gvar disabled entirely** | 0 | **1,557** | 4.23× |

**Across every reference definition the pre-visual count moves between 1,545 and 1,549, and no
possible reference can take it past 1,557. The whole Gvar reference-sample question is worth at
most 12 survivors out of 1,557 — 0.77% of the funnel.** It is not the largest unexplained factor;
on this measurement it is one of the smallest. *(On M3's 48.18% the same bound was ≤10 of 852 =
1.2%; the two runs agree.)*

*This does not un-document the irreproducibility. The paper still does not publish its reference
population and a reader still cannot recompute its Gvar column. What is now measured is that it
does not matter to the funnel.*

---

## 4. So what IS the 4.2×? The nebular CNN, measured through Galactic latitude

With the parent reconciled (§2) and Gvar bounded (§3), the overproduction has to live somewhere.
Realigning the funnel to the paper's own stage order localises it to one stage, and a latitude
split identifies that stage as the one the paper does not publish.

### 4.1 The realigned funnel, all sky

| stage | ours | paper, CNN removed | ratio |
|---|---|---|---|
| W3W4-detected **+ cc_flags** (the parent) | 328,937 | 320,000 | **1.03×** |
| RMSE ≤ 0.2 | 9,486 | 11,243 | **0.84×** |
| + extra cuts (CNN applied by neither) | 8,428 | 10,076 | **0.84×** |
| + S/N ≥ 3.5 | 1,545 | 722 | **2.14×** |
| *…if the paper's CNN is credited* | *1,545* | *368* | *4.20×* |

Every stage this screen can reproduce, it reproduces: **1.03×, 0.84×, 0.84×**. And 4.20× factors
almost exactly into **1.96× (the CNN stage, 11,243/5,732) × 2.14× (the S/N stage)**.

### 4.2 M3's explanation for the S/N stage is refuted by its own data

M3 §2.2 attributed the S/N-stage excess to the blueward template extension: *"Extending the
template range blueward admits hotter, intrinsically brighter stars, which have systematically
better W3/W4 signal-to-noise, so a far larger fraction clears S/N ≥ 3.5."* That is testable, and it
fails. Of the 8,428 survivors of the extra cuts:

| M_G | < 6 | 6–8 | 8–10 | 10–12 | 12+ |
|---|---|---|---|---|---|
| n | **0** | 13 | 829 | 5,642 | 1,944 |

**Not one survivor lies blueward of M_G = 6.** Restricting to M1/M2's old K/M window (M_G 6–14.5)
leaves all 8,428 and the S/N pass rate is unchanged at 18.3%. The blueward extension changed which
stars were *fitted* (32% → 98.6%) but added **zero** survivors, so it cannot explain the S/N stage.
M3 §4.2's template work stands; only the causal story it was used to tell in §2.2 does not.

### 4.3 The stage that does explain it, and the signed prediction that identifies it

The stage we do not have is a **nebular** classifier. Nebulosity lives in the Galactic plane and
makes W3/W4 *bright* — that is, **high S/N**. So if the S/N-stage excess is the missing CNN, our
S/N pass rate must fall towards the paper's as |b| rises, and at high |b| — where there is little
nebulosity to classify — the two must agree. That is a prediction with a direction, and it holds:

| Galactic latitude | survivors | pass S/N | rate | vs the paper's 7.2% | sky area (deg²) | yield /1000 deg² | vs paper's all-sky mean (68% Poisson) |
|---|---|---|---|---|---|---|---|
| 0–5° | 1,576 | 670 | 42.5% | **5.93 ± 0.17×** | 3,595 | 186.35 | **20.89× [20.09–21.72]** |
| 5–10° | 904 | 217 | 24.0% | 3.35 ± 0.20× | 3,568 | 60.82 | 6.82× [6.36–7.31] |
| 10–20° | 1,730 | 335 | 19.4% | 2.70 ± 0.13× | 6,946 | 48.23 | 5.41× [5.11–5.72] |
| 20–30° | 1,123 | 100 | 8.9% | 1.24 ± 0.12× | 6,517 | 15.34 | 1.72× [1.55–1.91] |
| 30–50° | 1,785 | 133 | 7.5% | 1.04 ± 0.09× | 10,975 | 12.12 | 1.36× [1.24–1.49] |
| **50–90°** | **1,310** | **90** | **6.9%** | **0.96 ± 0.10×** | **9,651** | **9.33** | **1.05× [0.94–1.17]** |
| all sky | 8,428 | 1,545 | 18.3% | 2.56× | 41,253 | 37.45 | 4.20× |

Areas are exact: the sky with |b| ∈ [lo, hi) is (sin hi − sin lo) × 4π sr, and the screen covers all
of it.

**At |b| > 50° this screen reproduces Hephaistos II's funnel absolutely** — 9.33 pre-visual
survivors per 1000 deg² against the paper's all-sky mean of 8.92, i.e. **1.05× [0.94–1.17]** — while
the conditional S/N pass rate is 6.9% against their 7.2% (**0.96 ± 0.10×**). Two independent
measures, one area-dependent and one not, agree at high latitude. The median |b| of an S/N-passing
survivor is **6.5°**; of an S/N-failing one, **24.2°**.

*Read the errors, not just the central values: the top of the table is overwhelming (20.9× with a
±4% interval) while the bottom bin is only consistent to ±11%, so "agrees at high latitude" means
"agrees within an 11% measurement", not "agrees exactly". The 30–50° bin sits at 1.36×
[1.24–1.49] — above 1, which is the expected behaviour if the plane's influence has not entirely
died away by 30° rather than a separate effect. The **trend** across six bins, spanning a factor of
20, is what carries the argument. Every one of these numbers is now measured on the whole sky, so
none of it depends on the extrapolation §2.4 has just shown to be good only to a few percent.*

**The paper's own output agrees.** All **7 of 7** published candidates lie at |b| > 30° (median
42.4°), as do 9 of the 10 labelled objects. Under isotropy 50% would, so 7/7 has probability
0.5⁷ = **0.008**. A pipeline whose final catalogue is that high-latitude is a pipeline whose middle
stages removed the plane.

**Conclusion.** The 4.2× pre-visual overproduction is not spread across the funnel; it is
concentrated in the Galactic plane, rises monotonically from 1.05× at |b| > 50° to 20.9× at
|b| < 5°, and is quantitatively consistent with the single stage whose implementation is
unpublished — the C4 nebular CNN. **Everything this project can reproduce, it reproduces; what it
cannot reproduce is exactly what the excess is made of.** That is a sharper statement of the
reproducibility boundary than M1's, and it is measured on the whole sky rather than argued from one
field.

*Caveat, stated: the paper's |b| distribution at the 368-survivor stage is not published, so the
high-latitude comparison sets our |b| > 50° subsample against their all-sky mean. It is valid if
their post-CNN sample is close to isotropic — which is what a working nebular classifier should
produce, and what their 7/7 high-latitude candidate list suggests — but it is not proved.*

---

## 5. Candidate D's JWST data — the first archival verdict checked against the imaging that settled it

*`scripts/m4_jwstD_*.py`; artifacts `out/m4_jwstD_photometry.csv`, `out/m4_jwstD_summary.json`,
`out/m4_jwstD_centroid_threshold.csv`, `out/m4_jwstD_cutouts.png`,
`out/m4_jwstD_centroid_threshold.png`. All products fetched anonymously from public MAST — no
account, no token, nothing submitted.*

This is the one object in the whole programme where an archival verdict can be graded against the
imaging that actually settled it. D was called "weak evidence" by every archival method (ours and
Ren et al.'s) and then killed by JWST. **PR-5 fixed in advance that the number that matters is not
the verdict but the pair (separation, contrast)**, because that is what converts into a centroid
pull. Both are now measured.

### 5.1 What is public, and what was measured

GO 7199 (PI Zackrisson; "Anomalous infrared fluxes of M dwarfs") — 114 observations. `Object_D` and
`Object_D_background` are **PUBLIC** since 2026-07-28; **E's imaging is still embargoed for 19 more
days (2026-09-09)** and **A's until 2027-07-16**. As M3 §5 found, D's *imaging* hangs off the
`_background` observation: three MIRI L3 mosaics `jw07199-o005_t007_miri_{f560w,f1000w,f1500w}_i2d.fits`,
1146.7 s each, observed 2025-07-28. **These MAST mosaics carry `CAL_VER 2.0.1 / CRDS jwst_1535` —
a newer, independent re-reduction than the 1.20.2/1364 the paper used**, so this is not a
re-reading of their pipeline output. D's MRS cubes are public too and were **not** reduced.

Candidate D's position was cross-checked three ways and they agree: `scripts/w1_fetch_candidates.py`,
`data/photometry/candidates_gaia_chain.csv` (Gaia DR3 2660349163149053824), and the paper's J2000
sexagesimal string, which is the Gaia position back-propagated to 0.7 mas. **Proper motion was
propagated and it matters**: |μ| = 37.5 mas/yr over 9.57 yr = **0.359″**, 29% of the separation. A
free simultaneous ePSF fit put the star's own centroid 0.0035″ from the propagated position.

| | F560W | F1000W | F1500W |
|---|---|---|---|
| star, μJy (AB) | 300.6 (17.71) | 124.0 (18.67) | 50.0 (19.65)* |
| contaminant, μJy (AB) | 70.9 (19.27) | 898.2 (16.52) | 4159.1 (14.85) |
| **contrast ρ = f_con/f_star** | **0.236** | **7.24** | **83.1** |
| Δmag (con − star) | +1.57 | −2.15 | −4.80 |
| sep / PSF FWHM | 6.0 | 3.8 | 2.5 |
| Hephaistos IV Table 2 (star/gal) | 17.5 / 18.7 | 18.5 / 16.6 | >19.8 / 14.9 |

\* marginal; its leak correction is ~50% of the raw aperture signal, and the paper's own value is a
limit for the same reason.

**Separation 1.23 ± 0.07″ at position angle 33 ± 1°** (per filter 1.257/1.211/1.230″ at
32.5/33.9/32.6°; an independent ePSF-fit route gives 1.15–1.22″ at 33.5–34.2°). **Hephaistos IV only
ever says "≈1 arcsec" and never quotes a position angle — both numbers are new here.** Photometry
reproduces the paper to 0.05–0.21 mag everywhere except the F560W galaxy (0.57 mag, §5.4).

### 5.2 Does the JWST data support the z ≈ 0.9 background-galaxy attribution?

**The contamination: CONFIRMED. The z ≈ 0.9 Hot DOG identification: CONSISTENT WITH, not confirmed.**

What the public imaging settles by itself:

- **The contaminant is point-like.** Its EE30/EE70 concentration is 0.423 (F1000W) and 0.417
  (F1500W) against the CRDS point-source values 0.434/0.443 — 97% and 94% of point-source. FWHM
  ratio contaminant/star in F1000W = 0.989, and the public pipeline catalogue independently flags
  `is_extended = False`. Intrinsic size ≲ 0.16–0.22″ FWHM, i.e. ≲ 1.3–1.8 kpc at z = 0.922.
- **It is extremely red**: F<sub>ν</sub> ∝ λ<sup>+4.4</sup> from 5.6→10 μm and λ<sup>+3.8</sup> from
  10→15 μm; f(15)/f(5.6) = 58.7. A stellar Rayleigh–Jeans tail goes as λ<sup>−2</sup>.
- **The star is photospheric.** F<sub>ν</sub> ∝ λ<sup>−1.5</sup>, λ<sup>−2.2</sup>, matching a 3473 K
  blackbody (Gaia `teff_gspphot`) normalised at F560W to ratios 1.10 / 0.93. **No intrinsic excess.**
- **The pair closes the WISE flux budget.** The MIRI total log-interpolated to 12 μm is 1932 μJy
  against AllWISE W3 = 1720 μJy (+12%). The contaminant's share is 19% at 5.6 μm, **88% at 10 μm and
  98.8% at 15 μm** — i.e. essentially all of the "excess" that selected D as a Dyson-sphere candidate.
- Granting z = 0.922, a single-temperature blackbody matching f(15)/f(5.6) gives rest-frame
  **T ≈ 441 K**, at the top of the 70–450 K Hot DOG range the paper quotes.

**What it cannot settle:** the redshift rests entirely on the MRS emission lines, which were not
reduced here. z ≈ 0.922, the Hot-DOG classification and the AGN diagnosis are **UNVERIFIED by this
project** and are taken from Hephaistos IV. Imaging gives no redshift.

*Artefact checks passed, because this project has been bitten before: the contaminant/star ratio
swings 0.24 → 83 across three separately-timed exposures (a PSF or persistence artefact of the star
would hold a constant ratio); cutouts sit 330–413 px from any edge with zero NaNs; and a first pass
did catch a quadratic centroid being dragged 0.44″ onto the brighter neighbour in F1000W — the same
failure mode that cost M3 its centroid axis (§3.2 there). The final numbers come from a
simultaneous fit anchored on Gaia, not a peak search.*

### 5.3 The part that matters: what this calibrates about the archival floor

The contrast rises as **ρ ∝ λ<sup>5.9</sup>** (slopes 5.90 and 6.02 over the two intervals —
mutually consistent), giving **ρ(W3, 12 μm) = 21.8** and **ρ(W4, 22 μm) = 803** (the W4 value is an
extrapolation ~50% beyond the reddest filter, and is flagged as such; nothing below depends on its
precise value because anything ρ ≳ 20 already saturates).

Flux-weighted centroid pull, `offset = sep · ρ/(1+ρ)`, which is an **upper bound** on a profile-fit
centroid:

| | predicted pull | this project measured (M1/M2) | Ren et al. 2026 measured |
|---|---|---|---|
| W3 | **1.18″** | 1.41 ± 0.21″ | 0.75″ |
| W4 | **1.23″** | 2.55 ± 0.50″ | 1.8″ |

**Three things fall out, and the second and third are the findings.**

1. **W3 is consistent.** 1.41 ± 0.21″ against a predicted 1.18″ is +1.1σ. The archival W3 centroid
   got the magnitude roughly right.

2. **W4 is impossible.** `offset < sep` always — no contrast, however extreme, can pull a
   two-source centroid past the separation itself. The geometric ceiling here is **1.23″**, and our
   measured W4 offset of 2.55 ± 0.50″ is **+2.6σ above a hard ceiling**. Ren et al.'s 1.8″ exceeds
   it too. The MIRI imaging shows **no other source within 8″** in F1000W/F1500W, and the
   flux-weighted centroid of everything inside the full 12″ W4 beam is 1.37″ at PA 29°. So **both
   teams' archival W4 offsets are larger than anything that exists in the field.** Four archival
   measurements of one truth of 1.23″ read 0.75″, 1.41″, 1.8″ and 2.55″ — a scatter of ~1″ around
   a 1.2″ signal, considerably wider than any of their formal errors.

3. **The direction is wrong too.** The real contaminant is at **PA 33°**. This project's W3 centroid
   offset points at **PA 82.9°** — 50° away — and there is nothing there. *(Verified independently
   for this document: propagating the Gaia position to the 2010.46 AllWISE epoch and differencing
   against `out/w2_centroid_offsets.csv` gives 1.417″ at PA 82.9°.)* **Archival centroid vetting
   near the floor is unreliable in direction as well as in magnitude** — which is a stronger
   statement than the project has been making, and it retroactively vindicates M3 §3.2's decision to
   refuse the centroid axis a vote rather than retune it.

**The threshold, stated as a function of contrast.** Setting the pull equal to a floor `F` and
solving gives

> **sep_thr(ρ) = F · (1 + 1/ρ)**

— the minimum separation at which a contaminant of contrast ρ can move the centroid past the floor:

| ρ | sep_thr, 1″ floor | sep_thr, 2″ floor | blind fraction, 1″ | blind fraction, 2″ |
|---|---|---|---|---|
| 1 | 2.00″ | 4.00″ | 37.9% | 100% |
| 2 | 1.50″ | 3.00″ | 21.3% | 85.2% |
| 5 | 1.20″ | 2.40″ | 13.6% | 54.5% |
| 10 | 1.10″ | 2.20″ | 11.5% | 45.8% |
| **21.8 — D at W3** | **1.05″** | **2.09″** | **10.4%** | **41.5%** |
| 100 | 1.01″ | 2.02″ | 9.7% | 38.6% |
| → ∞ | **1.00″** | **2.00″** | **9.5%** | **37.9%** |

**The asymptote is the floor itself.** As ρ → ∞ the threshold converges on F, so **no contaminant
closer than the floor is ever detectable by centroid vetting, at any brightness.** Brightness does
not buy separation.

"Blind fraction" = (sep_thr / 3.25″)², for a uniform background surface density inside the 3.25″
W3 aperture radius that Suazo et al. 2024 §5 use for their own contamination rates — their choice of
radius, not one tuned here. So, applied to this screen's **1,545 all-sky pre-visual survivors**: of the
chance-aligned contaminants that could produce their excess, **≈10% would be invisible to a 1″
archival centroid test and ≈40% invisible to a 2″ one, however bright the contaminant is.** The
project's standing "1–2″ floor" language is therefore right in form, and this puts a number on what
it costs: **between one in ten and two in five contaminants cannot be seen at all.**

**Where D itself lands.** At a 1″ floor the threshold is 1.046″ and D's 1.233″ clears it by 18%; at
a 2″ floor the threshold is 2.09″ and D is **invisible**. D sits *on* the floor, not above it —
which is exactly why Hephaistos IV records that centroid vetting "provided no evidence for
interloper contamination in the case of candidate D", and why Ren et al. 2026 measured only 0.75″
in W3. The calibration M2 §1 asserted from the paper's description is now **measured from the data
itself**, and it lands in the same place.

### 5.4 Limits, stated

- **The redshift is not measurable from imaging.** The MRS cubes are public but were not reduced.
  z ≈ 0.922 and the Hot-DOG classification are UNSOURCED by this project.
- **Absolute photometry carries ~0.2 mag aperture systematics** — fluxes rise with aperture
  (F560W star 258 → 301 → 365 μJy), i.e. the real mosaic PSF is broader than the CRDS EE curve
  (drizzle plus the brighter-fatter effect the paper devotes an appendix to). *Contrast ratios* are
  stable to ~10% because the broadening affects both sources, which is why §5.3 rests on ratios.
- **The F560W galaxy disagrees with the paper by 0.57 mag** (19.27 here vs 18.7 there); the total in
  that band (17.47) and the public pipeline catalogue's (17.60) are both fainter than the paper's
  17.2. This is real tension in the band where their brighter-fatter correction bites hardest. It
  does not move §5.3: forcing the paper's F560W split changes ρ(W3) 21.8 → 20.1 and the predicted
  pull 1.179″ → 1.175″.
- **WCS registration is checked on one star.** Only 14 Gaia sources lie in the field and exactly one
  clean one is detected in all three filters, showing a consistent ~+0.15″ Dec residual; a global
  WCS shift cannot be separated from that star's own centroid error. The target lands within
  0.0035″ of its propagated position in the F1000W simultaneous fit, so the WCS is good *at the
  target*, and the 0.07″ separation uncertainty is dominated by contaminant-centroid method choice.
- **ρ(W4) = 803 is an extrapolation** past the reddest filter.
- The blind-fraction column assumes a uniform background surface density inside 3.25″. The
  threshold formula itself makes no such assumption.
- **UNSOURCED**: any cause for M3 §5's flag that Obs 4 (Object_A_background) ran 18% of its planned
  duration. MAST lists 24 `calib_level = -1` placeholder rows at A's position marked PUBLIC;
  `get_product_list` returns **0 products** for them — planning stubs, not data. Nothing has changed
  there.

---

## 6. The delivered screen — 100% of the sky

*`scripts/m4_aip_screen.py select --source aip --jobs 14`; artifacts
`out/w4_funnel_m4_g0.1.json`, `out/w4_rmse_survivors_m4_g0.1.csv`,
`out/w4_previsual_candidates_m4_g0.1.csv`.*

### 6.1 Coverage

| | |
|---|---|
| **coverage** | **41,253 deg² = 100.00% of the sky** |
| cells | **220 done, 0 abandoned** (192 HEALPix level-2 cells, 28 of them split once or twice where the Galactic plane made them too dense for the 30 s statement timeout) |
| query time | 140 min of AIP execution across the whole sky |
| harvested | 638,970 rows at `ϖ > 2.5` with W3 **and** W4 detected |
| inside C1 (`r_med_geo < 300`) | **439,923**, of which **439,923 carry an exact EDR3 Bailer-Jones distance and 0 fall back to the parallax proxy** |
| stop reason | *queue exhausted (all sky attempted)* — not a budget, not the breaker |

M3 delivered 48.18% and reported it as such. **M4 delivers 100.00%, and the 48.18% is retained as
an independent cross-check that the two routes agree exactly (§1.5).**

### 6.2 The funnel, γ ≥ 0.10, all sky

| stage | this screen | Hephaistos II Table 4 | ratio |
|---|---|---|---|
| W3 **and** W4 detected | 439,923 | — | — |
| **+ `cc_flags` clean — the paper's "W3/W4 detection" row** | **328,937** | ~320,000 | **1.03×** |
| … with full 10-band photometry | 326,540 | — | — |
| … inside the template M_G window | 321,910 | — | **98.6%** of the above |
| **RMSE ≤ 0.2 star+DS grid fit** | **9,486** | 11,243 | **0.84×** |
| *(nebular CNN — not reproducible, not applied)* | *—* | *5,732* | *—* |
| **+ Gvar, RUWE, ext_flg, classprob** | **8,428** | 5,137 | 1.64× as printed; **0.84×** against the paper's rate with the CNN stage removed |
| **+ W3 & W4 S/N ≥ 3.5 — pre-visual survivors** | **1,545** | 368 | 4.20× as printed; **2.14×** with the CNN stage removed |
| final candidates (C4 CNN + C7 visual) | n/a | 7 | replaced by the coded gates below |

The γ ≥ 0.01 sensitivity is **not** re-run here: M3 measured it on 158,097 fitted stars
(5.83× at the RMSE gate, 2.93× at the pre-visual gate) and nothing in M4 touches the model grid.

### 6.3 Vetting the 1,545 survivors

The coded gates are M3 §3's, unchanged, run on the full-sky survivor list
(`scripts/m3_vet_survivors.py --tag m4_g0.1 --skip-centroid`):

| gate | what it asks |
|---|---|
| **V1 `w?nm`** | was the source ever detected in a **single exposure**, or only in the coadd? |
| **V2 release consistency** | do the same photons, reduced for the earlier WISE All-Sky Release, still give a detection in the band carrying the excess? |
| **V3 sensitivity** | is the "detection" above WISE's own 5σ standard at that ecliptic latitude? |
| **V4 chance alignment** | the faint-red-galaxy prior, from Suazo et al.'s own 15,000 sr⁻¹ |
| **V5 centroid** | **not applied** — see below |

**V5 stays off, and §5 is now the reason.** M3 §3.2 disabled it because its 10″ peak search locked
onto brighter neighbours, and prescribed two fixes for M4 (a 3″ search radius, a neighbour-aware
validity check). §5 supersedes that prescription: on candidate D, the one object where the truth is
now known from JWST, the archival centroid is wrong in **direction** (PA 82.9° against the real
33°, pointing where MIRI shows nothing) as well as in magnitude (W4 2.55″ against a hard geometric
ceiling of 1.23″), and Ren et al.'s independent measurement overshoots the same ceiling. **A
smaller search radius cannot fix a measurement whose direction is uninformative.** Because
STILL-CLEAN requires a valid centroid, **no object can reach STILL-CLEAN in M4 either** — stated as
a limitation of the method, not a property of the objects.

**Status at the end of this session: the vetting is RUNNING, not finished.** V1 and V2 are IRSA
catalogue cross-matches and IRSA costs **~3.5 s per position** (M3 measured ~100 min for 845
positions; 1,545 needs ~3 h per release). It was launched, it is progressing, and it resumes with
one command:

```
python scripts/m3_vet_survivors.py --tag m4_g0.1 --skip-centroid
```

Under the same reporting law as PR-1, that is stated rather than papered over: **the full-sky
verdict table is an M5 deliverable.** What *can* be said now is the one gate that needs no network,
because it runs off the survivor table's own catalogued S/N:

| **V3 SUB-THRESHOLD** — both excess bands below WISE's own 5σ standard | n | % |
|---|---|---|
| full sky (1,545 survivors) | **260** | **16.8%** |
| *M3's 845, recomputed the same way, for comparison* | *115* | *13.6%* |

Median S/N of a SUB-THRESHOLD survivor: **4.22 in W3, 3.95 in W4** — comfortably above the paper's
C6 threshold of 3.5 and comfortably below its own survey's detection standard. **One pre-visual
survivor in six has an excess that WISE cannot support in either band.**

*Caveat: this is the vetting's **fallback** S/N path (`1.0857/w?mpro_error` from the screen's own
harvest) rather than its primary path (the AllWISE catalogue's `w?snr`, which needs the IRSA query
still running). On M3's 845 the two differ by 1.4 points — 103 (12.2%) via the catalogue against 115
(13.6%) here — so read the 16.8% as ±1.5 points until the network run lands.*

**And a third consistency check on §4 falls out of it.** The SUB-THRESHOLD rate **rises** with
Galactic latitude — 9.6% at |b| < 10°, 24.8% at 10–30°, **30.0% at |b| > 30°** — which is what the
nebular-CNN account predicts: in the plane the survivors are bright, nebulosity-boosted objects that
clear the 5σ bar easily, while away from the plane what is left is the genuinely marginal population
the paper's own funnel is made of. **The high-latitude sample is smaller and fainter, not cleaner in
signal-to-noise** — 223 of the 1,545 survivors lie at |b| > 30°, and nearly a third of those are
sub-threshold.

**No object has reached STILL-CLEAN and none can**, because STILL-CLEAN requires a valid centroid
measurement and the centroid axis is invalid (above). **There is no Matthew-gated survivor from this
screen**, and nothing has been reported anywhere.

---

## 7. Recommended M5

1. **Finish the vetting of the 1,545 full-sky survivors** — started in M4, still running at
   session end because IRSA costs ~3.5 s per position (§6.3). One command, no new decisions:
   `python scripts/m3_vet_survivors.py --tag m4_g0.1 --skip-centroid`. The gates and their
   thresholds are M3 PR-3's, fixed before any survivor list existed, and must not be re-chosen now
   that the list is bigger. **One practical warning**: `m3_vet_survivors.py` writes its V1/V2 cache
   (`out/m3_vet_cache_m4_g0.1.csv`) only *after both* IRSA releases have been queried, so a run
   killed part-way loses everything and starts over. At 1,545 positions that is ~3 h per release —
   worth checkpointing per chunk before the next long run, and worth running detached.

2. **Build a *reproducible* nebular stage — this is now the whole story.** §4 leaves the project in
   an unusually clean position: every stage of Hephaistos II that can be reproduced *is* reproduced
   (parent 1.05×, RMSE 0.88×, extra cuts 0.88×, and the high-latitude yield 1.03×), and the entire
   residual sits on the one stage whose implementation is unpublished. The highest-value move is no
   longer to measure the gap but to **close it with something publishable**: a coded nebular test
   built from public data — WISE W3/W4 local background structure, the AllWISE `w?rchi2` and `nb`/`na`
   blend columns already cached by the vetting, and external dust tracers (IRAS/AKARI/Planck 857 GHz,
   or Herschel where covered) — validated against the |b| trend measured in §4.3, which is a ready
   made ground truth. If it reproduces 11,243 → 5,732 it replaces the CNN; if it does not, the
   *difference* is a publishable statement about what the CNN was actually doing.

3. **Retire V5, the centroid axis, formally — do not merely leave it disabled.** M3 §3.2 disabled it
   because its 10″ peak search locked onto brighter neighbours, and prescribed two fixes for M4
   (3″ search radius, neighbour-aware validity check). §5 changes the prescription: on the one
   object where truth is now known, the archival centroid is wrong in **direction** (PA 82.9° vs the
   real 33°, pointing at nothing MIRI can see) as well as in magnitude (W4 2.55″ against a hard
   geometric ceiling of 1.23″), and Ren et al.'s independent measurement overshoots the same ceiling.
   Retuning the search radius cannot fix a measurement whose direction is uninformative. **The
   honest move is to retire the axis for objects near the floor and say why**, carrying §5.3's
   `sep_thr(ρ) = F(1 + 1/ρ)` as the statement of what centroid vetting can and cannot do.

4. **Candidate E's JWST data open 2026-09-09 — 19 days away — and the machinery now exists.**
   `scripts/m4_jwstD_*.py` runs end to end; pointing it at E gives a **second** calibration point for
   the archival floor and a second (separation, contrast) pair, which turns §5.3's single
   measurement into a two-point relation. Candidate A stays closed until 2027-07-16.

5. **Reduce D's public MRS cubes.** All 12 sub-bands are public and were not touched here. They are
   the only way to test Hephaistos IV's z ≈ 0.9 identification independently — currently the one
   part of D's story this project takes on citation rather than measurement, and §5.4 marks it
   UNSOURCED. It would also test the 441 K single-blackbody temperature §5.2 infers from three
   photometric points.

6. **Publish the high-latitude catalogue as the positive deliverable.** The README's own framing is
   that the result is valuable either way — "a quantified null on the method's yield, or a
   defensibly clean extreme-IR-excess catalog (debris disks, WD pollution)". §4.3 says which one is
   in hand: at |b| > 30° the screen reproduces the paper's rates and the survivors are not
   plane-contaminated. That subsample, vetted with V1–V4 and carrying the release-consistency and
   single-exposure axes M2 invented, is a real catalogue of extreme mid-IR-excess dwarfs within
   300 pc. It is astrophysics regardless of the technosignature framing, and it does not depend on
   the irreproducible stage.

7. **Two small route items, both cheap.** (a) Keep ESAC's own pull in the manifest but stop
   depending on it — its join tables were still dead on 2026-08-21 and the AIP route now supersedes
   it, while its *single-table* PK lookups are load-bearing for the exact distance cut (§1.6).
   (b) The `~5%` parent residual (§2.3) is the last unexplained number in the funnel and is worth one
   measurement: re-run the parent with a numerical S/N floor in place of `ph_qual ≠ 'U'` and see
   whether it closes.

8. **Matthew's calls, unchanged and still waiting** (M2 §5.5, restated in M3 §7.6): (a) whether the
   Ren+24 unit-error note is worth submitting given Blain's prior "(sic)", and if so the three manual
   browser checks first (IOP page, PubPeer, ADS); (b) whether the candidate-I dossier becomes a JWST
   DDT/small-GO proposal, an RNAAS note, or stays internal. **Nothing in M4 changes either gate.**
   M4 adds no new Matthew-gated item: no object reached STILL-CLEAN.

---

## 8. File index (new in M4)

**Document:** `M4-sky-parent-gvar-jwst.md` (this).

**Scripts:**

- `scripts/m4_aip_screen.py` — the AIP route: `probe` (PR-1's five verification checks), `pull`
  (HEALPix-cell harvest with the ported outage breaker and instant-failure classifier), `status`,
  `distances` (exact EDR3 Bailer-Jones `r_med_geo` via ESAC single-table PK lookups), `purity`
  (PR-2's proxy purity on a sample containing the complement), `accept` (PR-1's V-e acceptance
  test), `select` (the combined ESAC + AIP funnel, with `--jobs` parallel fitting verified
  bit-identical to serial)
- `scripts/m4_funnel_reconcile.py` — §2's parent reconciliation, §3's Gvar reference variants and
  reference-free bound, §4's stage realignment and Galactic-latitude split
- `scripts/m4_jwstD_*.py` — the candidate-D JWST chain (`mast`, `fetch`, `dl`, `look`, `wcscheck`,
  `measure`, `phot`, `fit`, `epsf`, `final`, `morph`, `calib`, `q4fig`)

**Artifacts** (M3's are untouched; M4's carry the `m4_` tag):

- `out/m4_aip_route_probe.json`, `out/m4_aip_acceptance.json`, `out/m4_proxy_purity.json`
- `out/m4_funnel_reconcile_m4full.json` (the full-sky reconciliation quoted in §2–§4) and
  `out/m4_funnel_reconcile_m4.json` (the same analysis on M3's 48.18%, kept as the cross-check)
- `out/m4_jwstD_photometry.csv`, `out/m4_jwstD_summary.json`,
  `out/m4_jwstD_centroid_threshold.csv`, `out/m4_jwstD_cutouts.png`,
  `out/m4_jwstD_centroid_threshold.png`
- `out/w4_funnel_m4_g0.1.json`, `out/w4_rmse_survivors_m4_g0.1.csv`,
  `out/w4_previsual_candidates_m4_g0.1.csv` — the delivered full-sky funnel
- `out/m3_survivor_table_m4_g0.1.csv`, `out/m3_verdict_counts_m4_g0.1.json`,
  `out/m3_vet_cache_m4_g0.1.csv` — the vetting outputs. *(They keep the `m3_` prefix because
  `scripts/m3_vet_survivors.py` is reused unmodified; the `m4_g0.1` tag is what distinguishes them
  from M3's.)*
- `data/w4/aip/manifest_aip.json`, `data/w4/aip/cells/` (the harvest),
  `data/w4/aip/distances/` (the exact `r_med_geo` lookups), `data/w4/aip/pull.log`
- `data/w4/aip/cells_BAD_oidjoin/` + `manifest_aip.BAD_oidjoin.json` — **kept deliberately**: the
  42 cells harvested through the wrong 2MASS join (§1.3), so the failure and its detection are
  auditable rather than erased
- `data/jwst/` — the public GO 7199 MIRI L3 mosaics and working files (131 MB, gitignored)

**Scripts changed:** none. `scripts/w4_screen.py`, `scripts/w1_selection.py`,
`scripts/w2_centroids.py` and `scripts/m3_*.py` are as M3 left them; the M4 driver imports
`w1_selection.fit_ds` / `use_locus` unmodified so the funnel stays stage-for-stage comparable.

**Nothing in this milestone has been submitted, posted, or sent anywhere. No account was created at
AIP, MAST or anywhere else; every service was used anonymously.**
