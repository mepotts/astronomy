# M7 — the day-one clock measured, the refit arm built, and December pre-registered

*2026-08-23. Runs M6's own three recommendations, in M6's own priority order. M6 left a
verdict factory whose speed was a band, a headline arm that was a pattern rather than a
pipeline, and one remaining route by which a post-hoc choice could launder a null. M7
closes all three. Repo law: sourced-or-UNSOURCED; negative results are results; rules
pre-registered. Anonymous HTTP only. No accounts, no submissions, no commits, no pushes.*

---

## 0. The one-paragraph answer

The day-one clock has a **measured centre** for the first time, and the half of M6's
125–857 sources/hour band that a better experiment could remove has been removed:
M6's two transport models **were never rivals — they are the two terms of one model**,
and the probe that could not tell them apart was collinear by construction. A
981-source dry run at a *fixed* batch size with payload deliberately varied 4.7× across
batches separates them at 13.5 σ: `t = 2.42 s + 0.215 s/source × n + 0.1424 s/KiB × KiB`
(R² 0.878, 100 requests). At DR4's real 50.9 KiB/source that is **468 sources/hour and the
981-row queue in 2.1 h** — a *measured central value* where M6 had none. A band remains,
**126–803 sources/hour (1.2–7.8 h)**, but it is a different object: every edge of it is a
*measured archive state* rather than a modelling choice, sustained runs vary by only
**±8 %** (the two halves of phase B), and the whole of it is weather that happens on the
day and cannot be measured before it. The **orbital-refit arm**
exists as a pipeline and passed its pre-registered acceptance: Gaia BH3 re-derived through
the production path to **P 11.454 yr, e 0.72782, M₂ 34.684 M☉**, inside M1's printed
precision on all three, with a companion-mass posterior the previous script did not have.
Run over the pre-release trio it reproduces the DR3 catalogue orbits, and on HD 114762 it
lands with **Winn 2022 (0.233 vs 0.215 ± 0.013 M☉)** rather than with Kiefer's 0.10–0.14 —
while its own formal error bars are measurably **too small by a median factor 2.3**. And
`PREREG-2026-08-23-december-discriminators.md` is written and frozen, while zero December
verdicts exist.

---

## 1. Task 1 — the day-one-scale dry run

### 1a. What M6 left, and why a band was the honest answer *then*

M6's DataLink probe swept **batch size**. Source count and payload bytes therefore moved
together, and two models fitted those calls about equally well:

| | model | R² |
|---|---|---|
| **A** transport-limited | `t = 2.3 s + bytes / 1.8 KiB/s` | 0.934 |
| **B** per-source work | `t = 6.0 s + 3.86 s × n_sources` | 0.917 |

They disagree only about DR4's 6.8× larger payload, which is the whole question. Reporting
one number would have been a guess. Reporting a band was correct — and it was also a
design defect that could be fixed by a different experiment.

### 1b. The experiment that fixes it

`scripts/m7_dryrun_ids.py` + `scripts/m7_day1_dryrun.py`, run through the **production
harness** (`scripts/epoch_vet_harness.py`: same batching, same per-source atomic parquet
cache, same append-only ledger and resume, same 6× retry with `Retry-After`, same
per-batch checkpoint, same timings CSV). Four phases, all anonymous, all polite
(≥ 1 s between requests).

**Phase A — the literal ask: all 981 day-one queue members** against DR3
`EPOCH_PHOTOMETRY`, batch 20, 50 requests, **4.5 min**.

> **First finding, and it is the reason phase B had to exist: only 74 of the 981 queue
> members (7.5 %) have DR3 epoch photometry at all.** DR3 publishes it only for its
> variability candidates (`gaiadr3.gaia_source.has_epoch_photometry`, checked over all 981
> — it agrees exactly with `vari_summary` membership). A DR3-photometry dry run over the
> *real* queue therefore cannot be a payload test: 907 of the requests return nothing.

What phase A did measure is the thing M6 could not: **the empty-request floor. 14 requests
that served zero sources cost a median 0.65 s (range 0.51–0.75 s)** — not M6's 2.3–6.0 s.
M6 could not separate overhead from payload because every probe request carried payload.
A DataLink request that serves nothing is nearly free.

**Phase B — the degeneracy-breaker.** 981 DR3 sources drawn from
`nss_two_body_orbit ∩ vari_summary` (astrometric binaries that *do* serve epoch
photometry), arranged into **payload-homogeneous batches of 20 cycling five
`num_selected_g_fov` strata** (20–35, 35–50, 50–70, 70–100, 100–400). At a fixed
n_ids = 20 the served payload varies **4.7×** between batches (529 to 2484 transits) and
the batch time varies **6.0×** (9.6 to 57.4 s) — where a flat model predicts 1.0×. Across
batch seconds the correlation is **0.83 with served transits and 0.26 with source count**.
(48 of the 50 batches served exactly 20; 981 = 49×20 + 1, and quoting the odd partial
batch's range would inflate 4.7× into a meaningless 20.7×.)

Wire bytes were calibrated separately (6 `dump_to_file` requests, the zip weighed — M6
landmine #8: astroquery writes it into the CWD, so `chdir` first):
`zip_bytes = 6189 + 120.6 B per served G-FoV transit`, **R² 1.000**.

| the test, at fixed n = 20 | result |
|---|---|
| **model A form** `t = a + c·KiB` | `t = 6.12 s + 0.1450 s/KiB × KiB`, R² **0.689**, slope **10.3 σ** from zero |
| **model B form** (flat, since n is fixed) | constant 28.0 s, R² **0.000** |

> **Model B is refuted at fixed n.** DataLink's cost tracks **data volume**, not source
> count. M6's "server-work-limited, not bandwidth-limited" survives as a statement about
> the *rate* (6.9 KiB/s is not a network); what M6 could not tell, and this can, is that
> the work is **proportional to the bytes**.

**And then both terms at once.** Phase B holds n_served at 20 and varies bytes; phase A
holds bytes near zero and varies n_served from 0 to 3. Their union is the only place in
this repository where the two predictors have ever been decorrelated:

> **`t = 2.42 (±0.81) s + 0.215 (±0.100) s/source × n + 0.1424 (±0.0105) s/KiB × KiB`**
> — 100 requests, R² **0.878**, per-source term 2.2 σ, per-byte term **13.5 σ**.
>
> At DR4's 50.9 KiB/source the byte term costs **7.25 s/source** against the source term's
> **0.22 s**. **M6's models A and B were not rivals; they were the two terms of one model,
> and the probe's collinearity is what made them look like a choice.**

**Sustained throughput actually achieved** (this is the measurement, not a fit):
400 sources in 9.1 min, then — *after a deliberate stop* — the remaining 581 in 15.6 min.
**981 sources in 24.7 min = 2,379 sources/hour at DR3's 7.7 KiB/source.**

**Resume was exercised at real scale, not in a probe.** The second run reported
`981 queued, 400 already in the ledger, 581 to do` and picked up at batch 20 of 50. The
ledger is append-only, the cache is per-source and atomic, and a kill costs at most the
batch in flight.

**Phase C — the fit half, sustained.** 981 consecutive `gaiasupdate` single-star fits over
the real DR4 pre-release epoch astrometry, from cache:

| | |
|---|---|
| first fit | 4.03 s (import + pandas accessor registration) |
| steady state | mean **0.1231 s**, median 0.1216 s, p90 0.1638 s ⇒ **29,252 fits/hour** |
| drift | first decile 0.1177 s vs last decile 0.1199 s; OLS slope **−0.011 s per 1000 fits** |
| determinism | max distinct f2 per source over 981 fits = **1** |

Slower than M6's 0.036 s (that was an idle machine; this one was running the DataLink
stream at the same time) — and **it does not matter**: the fit is still 60× cheaper than
transport at DR4 payload, it does not drift, and it does not leak. Transport is the whole
clock, and now the whole clock is one equation.

**Phase weather — the same request, over hours.** M6's soak was 5 requests in a few
minutes. This is **60 identical batch-20 requests over 2.0 h**, one every 2 min: **min
15.2 s, median 26.9 s, p90 34.3 s, max 42.2 s — a 2.8× spread, no monotone trend
(−0.04 s/min) and zero failures in 60.** M6 saw 3.2× inside a few minutes and concluded
load rather than throttling; over two hours that holds, and the distribution is tight
enough that a 50-batch run averages most of it away.

### 1c. The number, and what is left of the band

Measured model, DR4 payload 50.9 KiB/source (M6, on the real pre-release file), batch 20:

| branch | wall clock, 981 rows | sources/hour |
|---|---|---|
| best single request observed (0.57× median) | 1.2 h | 803 |
| **MEDIAN — the measured branch** | **2.1 h** | **468** |
| p90 request | 2.6 h | 371 |
| worst single request observed | 3.2 h | 303 |
| M6's bad afternoon (1.8 KiB/s) | 7.8 h | 126 |
| 10× degraded — M6's worst branch | **20.2 h** | 49 |

**A 50-batch wall clock does not see single-request extremes; it sees their mean.** The
honest bracket for a *sustained* run is the spread between the two halves of phase B,
separated by a stop and a restart: **2,626 and 2,236 sources/hour, ± 8 %**. The quantile
rows above are instantaneous conditions; the day-to-day rows (M6's afternoon, the 10×
branch) are what bound a whole run.

> **M6: 125–857 sources/hour, 1.1–7.9 h.** **M7: 468 sources/hour, 2.1 h — measured**,
> with 126–803 (1.2–7.8 h) around it. The two bands are similar in *width*, and saying
> otherwise would be spin. What changed is what the width means: M6's was a **model**
> ambiguity with no defensible centre, spanned by two extrapolations neither of which had
> been observed; M7's is **archive weather**, it has a measured centre, every edge of it is
> an archive state somebody actually measured, and a sustained run varies by ± 8 % rather
> than by the full spread. **The half of M6's uncertainty that a better experiment could
> remove has been removed; the half that only release day can settle has not.**
>
> **M6's 78-h worst branch is superseded.** It was model A extrapolated from a 2.3 s
> overhead; the measured overhead is 2.42 s but the measured rate is 6.9 KiB/s, so the same
> 10× degradation costs **20 h, not 78** — and 72 h now has margin on every branch measured.

**What is still extrapolated, named:** the payload. DR4 epoch astrometry is not on the
service yet, so 50.9 KiB/source comes from the pre-release *file* and the rate from DR3
photometry. M7 removes the **model** half of M6's band. It cannot remove the weather.

---

## 2. Task 2 — the orbital-refit arm

`scripts/orbital_refit_arm.py`. The harness stops at `CONFIRMED (orbit_reality)`;
December's headline is the independent orbit and its companion mass. That existed only as
`scripts/fit_prerelease_orbit_bh3.py`: one hard-coded source, one hard-coded primary mass,
point estimates, a printed text file, no place in the verdict record.

### 2a. What the arm is

The route is M1's, deliberately unchanged (ESA's own notebook, `esa/gaia-bhthree` branch
`gaia-dr4-prerelease`, via kepmodel/spleaf + pystrometry): gaiasupdate prepares the epoch
table → kepmodel `AstroModel` with five linear terms → periodogram of the single-star
residuals → Keplerian at the peak → all seven Campbell elements freed and refitted →
a0 + parallax → `pjGet_m2`. What is new:

1. **it runs from the ledger over any set of sources**, not one id;
2. **a companion-mass posterior.** kepmodel exposes the log-likelihood Hessian, so the
   parameter covariance is `-inv(H)` at the optimum — exactly the matrix its own
   `get_param_error()` takes its error bars from. The arm draws 20,000 samples from that
   multivariate normal, draws M₁ from its own uncertainty, and solves the mass function per
   draw. It is a **Laplace** posterior, it is labelled as one, and it is not an MCMC;
3. **the M1-free observable reported beside it.** The astrometric mass function needs no
   primary mass and is what survives a wrong one;
4. **M₁ from the triage's own three-tier ladder** (`binary_masses` IsocLum → photometric
   MS → evolved bracket), with the rung recorded — not a new chain invented for the arm.
   The candidate list was *ranked* with that ladder;
5. **output as verdict-record v2**, so a refit lands on the same row as the verdict that
   triggered it.

### 2b. Verdict record v2 (`scripts/verdict_schema_v2.py`, `schemas/day1_verdict_record.v2.json`)

v1 is frozen and its `validate()` rejects a foreign `schema_version` by design, so v2 is a
**separate module that imports v1** rather than an edit. **74 columns = v1's 39 + 35
`refit_*` fields.** Every v1 record is a valid v2 record after `upgrade()`; the reverse is
data loss and is not provided (round trip verified identical on the frozen EB26 store).

The `refit_*` prefix is not decoration. `orbit_period_d` / `orbit_a0_mas` are **orbit
provenance** — the catalogue's orbit, the thing being adjudicated. Writing a re-derived
value into them would destroy the only distinction that makes an independent orbit
independent. v2 also declares one new verdict value, `NOT_ADJUDICATED`, for a pass the
harness handled without attempting adjudication; it is declared and unused, because the
transport rehearsal writes its own ledger instead (§4).

**And one rule the v2 store forced into the open: SUPERSEDING.** The refit arm *enriches*
a harness verdict — same `(source_id, solution_type, source, scope)` key, refit block
filled in — so after a refit pass the same orbit exists in the v1 harness ledger and in
the v2 refit store. `load_store('all')` duly raised `12 duplicate key(s)` the first time it
was tried, which is correct: a duplicate key is normally a bug. The declared rule is now
in the module: **a key present in both a v1 and a v2 file is resolved in favour of the v2
row — it is the same verdict plus measurements — and the number superseded is
PRINTED; a key duplicated *within* one schema version still raises.** Verified:
`load_store('all')` returns **88 records** (76 EB26 upgraded + 12 harness superseded by
their refit rows, 3 carrying a mass posterior), and `supersede=False` still raises.

### 2c. Acceptance — PASS

Pre-registered in the arm's docstring before the runs, with the tolerance set from the
**reference's own printed precision** (M6 landmine #10), not a hopeful epsilon:

| | arm | M1 (`out/bh3_orbit_fit.txt`) | \|Δ\| | tol | |
|---|---|---|---|---|---|
| P (yr) | 11.45429 | 11.4540 | 0.000290 | 0.005 | **PASS** |
| e | 0.727816 | 0.7278 | 0.000016 | 0.0005 | **PASS** |
| M₂ (M☉) | 34.68425 | 34.6800 | 0.004250 | 0.005 | **PASS** |

`out/m7_refit_acceptance.json`. And the arm produces what M1 could not: **M₂ = 34.68,
68 % [34.20, 35.17], 90 % [33.89, 35.50] M☉**, 0/20,000 draws rejected as unphysical.

### 2d. The trio, against the DR3 catalogue *and* against the literature

`out/m7_refit_trio.csv`, `out/m7_refit_vs_literature.{csv,txt}`,
`out/verdicts_v2/harness_prerelease_refit.v2.csv` (12 records, 3 with a refit).

| | Gaia BH3 | HD 114762 | Gaia-4 |
|---|---|---|---|
| CCD transits | 558 | 558 | 824 |
| single-star rms | 6.605 mas | 1.263 mas | 0.154 mas |
| periodogram FAP | 0 | 3.3e−260 | 2.8e−151 |
| **P (d)** | 4183.68 ± 72.22 | 83.8376 ± 0.0129 | 578.96 ± 2.99 |
| **e** | 0.72782 ± 0.00354 | 0.30533 ± 0.00980 | 0.41482 ± 0.06175 |
| **a₀ (mas)** | 27.110 ± 0.368 | 1.8512 ± 0.0172 | 0.25509 ± 0.00880 |
| **ϖ (mas)** | 1.65980 ± 0.00652 | 25.3094 ± 0.0114 | 13.6235 ± 0.0065 |
| mass function (M☉) | 33.2128 | 0.0074272 | 0.0000026 |
| M₁ (rung) | 0.76 (literature) | 1.0747 (`binary_masses`) | 0.6392 (`binary_masses`) |
| **M₂ (M☉), 68 %** | **34.68** [34.20, 35.17] | **0.2334** [0.2205, 0.2456] | **0.01033** [0.00898, 0.01159] = **10.8 M_Jup** [9.4, 12.1] |
| refit time | 1.2-1.5 s | 1.0-1.4 s | 1.4-2.2 s |

**Against the DR3 catalogue orbit** (pulled live from `gaiadr3.nss_two_body_orbit`; BH3
**has no DR3 NSS row at all**, which is exactly why Panuzzo needed preliminary DR4
astrometry):

| | HD 114762 | Gaia-4 |
|---|---|---|
| P | +0.12 % | +2.6 % |
| e | −5.7 % | −18.3 % |
| a₀ | +3.0 % | −18.5 % |
| ϖ | −0.19 % | −0.14 % |

**Against the published solutions** (sourced; full citations in the arm and in
`out/m7_refit_vs_literature.txt`):

- **Gaia BH3** — Panuzzo et al. 2024, A&A 686, L2, Table 2 *astrometric-only* column:
  **every Campbell element within 1.1 σ.** P −0.10 σ, e +0.29 σ, a₀ +0.07 σ, i −1.06 σ,
  ω +0.68 σ, Ω +1.09 σ.
- **HD 114762** — the arm gives **M₂ = 0.2334 M☉, 68 % [0.2205, 0.2456], 90 %
  [0.2120, 0.2539]**, i.e. **1.5 σ from Winn 2022's 0.215 ± 0.013** and **7.4 σ / 10.4 σ
  from Kiefer et al. 2021's 0.140 and Kiefer 2019's 0.103**. Inflating the formal error by
  the measured ×2.3 of §2e-i those become **0.6 σ from Winn and 3.2 σ / 4.5 σ from the
  Kiefer values** — so the exclusion survives the caveat. Where the literature disagrees
  by a factor two, the arm lands with the joint Gaia+Doppler solution, not with the
  GASTON excess-noise masses.
- **Gaia-4** — **M₂ = 10.82 M_Jup against Stefánsson et al. 2025's 11.8 +0.73/−0.66
  (−1.39 σ)**, and the M₁ ladder's `binary_masses` value **0.639 M☉ reproduces their
  EXOFASTv2 host mass 0.644 ± 0.024 to −0.20 σ** — an independent validation of the rung
  the whole candidate list is ranked with.

### 2e. Two measured caveats that must ride with every mass the arm produces

**(i) The formal error bars are lower bounds, empirically by a median factor 2.3.**
Across the 11 trio elements that have both a published value and a refit formal error,
|refit − published| / (the refit's own σ) has **median 2.28, max 6.16**, and only **4 of 11
fall inside 1 σ** (expect ~68 %) and **5 of 11 inside 2 σ** (expect ~95 %). HD 114762's
period is 6.2 of its own σ from Winn's Doppler period. A Laplace posterior is a formal
interval and must never be quoted as a total uncertainty.

**(ii) The parallax zero-point, amplified by three.** All three refit parallaxes are
**below** the published value: −14.9, −40.6 and −4.5 µas — the Lindegren+2021 scale. The
photocentre mass function goes as **ϖ⁻³**, so a −0.9 % parallax (BH3) is +2.7 % on the mass.
That, and not a discrepant orbit, is what the arm's **+2.42 σ** offset from Panuzzo's
published M_BH = 32.70 ± 0.82 actually is — and Panuzzo says so first: the published
headline mass comes from the **combined astrometry+RVS** solution via `a1` in AU precisely
to avoid the parallax route, and the Letter states that the Table-2 mass-function
uncertainty is underestimated because the preliminary-NSS parallax bias could not be
quantified. **This is the arm's dominant systematic and it is not reducible by better
fitting.**

---

## 3. Task 3 — the December pre-registration, frozen

**`PREREG-2026-08-23-december-discriminators.md`**, dated, frozen on writing, with a
variant log that is the only place later milestones may append.

**The two decision rules in two sentences.** *Primary analyses are scope-pure — every
discriminator test is run on harness verdicts alone (`orbit_reality`), the EB26-only run
is a byte-identity regression check rather than new evidence, and a pooled analysis is
secondary, always printed with its scope composition, and **interpretable in one direction
only**: because a harness CONFIRMED is weaker than an EB26 CONFIRMED the pooled CONFIRMED
group is heterogeneous, so pooled significance is a conservative positive while pooled
non-significance is dilution and may never be reported as a null.* *Each test then gets
exactly one of six pre-assigned labels — POSITIVE, POSITIVE (conservative, pooled), NULL,
UNDERPOWERED, DIRECTION REVERSAL, NOT TESTABLE — where NULL requires the test to be **decisive** (the
smallest effect detectable at 80 % power at the achieved n is at least as small as the
M4/M5 effect under test), so "not significant" can no longer be reported without saying
which of the two things it means.*

Also frozen: admitted verdict classes (`INCONCLUSIVE` is never folded into `SPURIOUS`);
de-duplication on `(source_id, nss_solution_type)` with EB26 winning a collision; Holm
within each family with the **family sizes fixed now** (D1 m = 3, D2 m = 5, D3 m = 6,
D4 m = 1) and no correction across families, so December's p-values stay comparable with
the frozen ones; the pre-registered *direction* of each effect, so a significant reversal
is reported as a reversal; the negative control `phot_g_n_obs` with a **veto** — if it goes
significant, no D1–D4 positive may be reported as a finding until it is explained; the
exact December commands; and four things the pre-registration deliberately does not cover.

**The sample thresholds** (`scripts/m7_prereg_power.py` → `out/m7_prereg_power.txt`), at
three plausible CONFIRMED:SPURIOUS ratios because the harness's own split is not knowable
in advance:

| test | effect under test | 1:1 | 1.83:1 (EB26) | 0.33:1 (harness) |
|---|---|---|---|---|
| D1 X-ray, in-footprint | 0.154 vs 0.000 | 50 + 50 | 49 + 27 | 32 + 95 |
| D2 ΔAmp_G | AUC 0.659 | 51 + 51 | 71 + 39 | 34 + 103 |
| D3 `astrometric_gof_al` | AUC 0.344 (in-list) | 54 + 54 | 73 + 40 | 35 + 104 |
| D4 flag marking rate | 0.30 vs 0.075 | 52 + 52 | 64 + 35 | 34 + 101 |

One harness pass over 981 rows gives ~490+490, ~633+347 or ~245+735. **D2, D3 and D4 clear
their thresholds at every ratio** — so a non-significant December result is a **NULL**, a
thing this project has never yet been able to claim. **D1 is the exception and cannot be
fixed by throughput**: it is capped by the eROSITA-DE footprint at ~45 % of whatever is
adjudicated.

The power driver **imports M5's own routines** rather than reimplementing them: a fresh
normal-approximation version reproduced M5's published `min_detectable` column only to ~2 %
(0.711 vs 0.725; 0.816 vs 0.800). Two power conventions in one repository is one too many.
The driver's reproduction block re-derives M4's, M5's and M6's published power statements
as a self-check before computing anything new — and it earned its keep on the first run:
`min_detectable_rate(n1, p0, n2)` takes the FIXED-rate group first, and calling it with
the spurious group first returned **0.60** where M6 published **0.55**. All four
statements now reproduce exactly (0.725, 0.800, 0.55, 0.40).

---

## 4. Changes to the production harness, and why they are small

`scripts/epoch_vet_harness.py`, four additions, none of which touch the December path:

1. `DataLinkSource.fetch` split into **`_call_with_retries`** (the polite / backoff /
   `Retry-After` / fail-fast-on-deterministic-500 policy) and **`_frames_from`** (the
   epoch-astrometry parser), so a subclass can transport a *different* DataLink product
   through the *same* retry policy. Behaviour identical: the pre-release run reproduces
   the frozen M6 ledger with **max |Δf2| = 0.000000** on all 12 sources.
2. `run(retrieval_type=…, epoch_source=…)` — inject an already-built fetch layer.
3. `run(transport_only=True)` + `payload_cells()` + a **transport ledger**
   (`TRANSPORT_LEDGER_COLS`, written outside `out/verdicts/`).

> **Why a transport rehearsal writes no verdicts.** DR3 epoch photometry carries no
> astrometric epochs, so there is no f2 and no adjudication is possible. A placeholder
> verdict in the store would be a provenance lie in a schema whose entire purpose is
> provenance. The resume contract is identical — append-only, one row per source, restart
> skips what is in it — which is what makes this a rehearsal of the real thing.

4. `run(progress_every=…)` — a checkpoint line with elapsed rate and ETA.

And two one-line fixes to the **consumers**, forced by landmine #12 (§6): `m4_eb26_erosita_test.py`
and `m5_activity_discriminator.py` no longer hard-code `== 76` on the verdict join. All five
frozen artifacts still reproduce byte-identically through the fixed path.

### Rehearsal — all nine stages green

Re-run end to end **after every M7 change, including the consumer fixes**
(`out/m7_rehearsal.log`):

| stage | s | status | note |
|---|---|---|---|
| A — schema pin | 291.8 | OK | **ESAC's `TAP_SCHEMA` path was unusable again** — four ReadTimeouts; introspection failed over to ARI, as the M5 branch prescribes. Never the data path |
| B — rename patch + live probe | 46.7 | OK | |
| C — plan-B ranged pull | 247.5 | OK | resumed from 94 cached chunks; **169,227 rows, sha256 `b3b099a6…dddd5231` for the FIFTH time**, id-sum match |
| D — triage + BH1/BH2 acceptance | 127.2 | **PASS** | BH1 M₂_min 12.81 M☉ |
| E — corr_vec (measured) | 74 + 10 | OK(measured) | |
| **F — epoch-vet, production harness** | 7.4 | **PASS** | 3/3 kept, 9/9 demoted, max \|Δf2\| vs the M3 prototype **0.0050** — **through the M7-refactored fetch layer** |
| G — bulletin | 0.7 | OK | |
| H — day-one queue | 0.6 | **PASS** | 983 rows, BH1/BH2 top-2 asserted by the builder |
| I — verdict store | 0.2 | **PASS** | 88 records, 2 producers, 2 scopes, schema-validated, consumer contract OK |
| **total** | **722 s** | **COMPLETE** | |

722 s against M6's 82 s is archive weather, not a regression: stage A alone was 291.8 s of
ESAC failover where M6 got 7.3 s, and an earlier M7 run of the same driver took 358 s.
What the rehearsal certifies is the nine **statuses**, and all nine are green in both M7
runs.

---

## 5. Files

| artifact | what |
|---|---|
| `PREREG-2026-08-23-december-discriminators.md` | **the frozen pre-registration** |
| `scripts/m7_dryrun_ids.py` | the two id sets: the 981 queue members, and the 981 payload-stratified serving sources |
| `scripts/m7_day1_dryrun.py` | phases A / B / C / calib / weather through the production harness |
| `scripts/m7_throughput_report.py` | the regressions, the model test, the day-one number → `out/m7_throughput_measured.txt` |
| `scripts/orbital_refit_arm.py` | **the refit arm** — orbit, mass function, mass posterior, M₁ ladder, DR3-catalogue and literature comparison |
| `scripts/verdict_schema_v2.py`, `schemas/day1_verdict_record.v2.json` | verdict record v2 (v1 + 35 `refit_*` fields) |
| `scripts/m7_prereg_power.py` | the pre-registration's thresholds → `out/m7_prereg_power.txt` |
| `out/m7_dryrun/` | id sets, transport ledgers A and B, harness timings, bytes calibration, fit-scale test, archive weather, batch regression |
| `out/m7_refit_acceptance.json`, `out/m7_refit_trio.csv`, `out/m7_refit_vs_literature.{csv,txt}` | the arm's outputs |
| `out/verdicts_v2/harness_prerelease_refit.v2.csv` | the v2 store |
| `out/m7_rehearsal.log`, `out/m7_pooled_m4.log`, `out/m7_pooled_m5.log` | the green rehearsal, and the evidence that the pre-registered pooled commands actually run |
| `scripts/epoch_vet_harness.py` | **modified** (§4) |
| `DR4-DAY-RUNBOOK.md` | **modified**: measured throughput, Phase 3.4 = the refit arm, §3.3 points at the pre-registration, failure branches updated |

Frozen artifacts verified byte-identical at close: configs v1–v5, all M2–M6 CSVs and stats
files, `schemas/day1_verdict_record.v1.json`, `out/verdicts/eb26.v1.csv`,
`out/verdicts/harness_prerelease.v1.csv` — see §7.

---

## 6. Corrections and new landmines

1. **M6's models A and B were not competing hypotheses.** They are the per-source and
   per-byte terms of a single cost model, and the probe made them look like a choice
   because it varied both together. When two models "fit equally well and disagree only in
   extrapolation", the next experiment is the one that decorrelates their predictors — not
   a wider band.
2. **DataLink's per-request overhead is 0.65 s, not 2.3–6.0 s.** M6's estimate absorbed
   payload because every probe request carried some. Measured on 14 requests that served
   nothing.
3. **Only 7.5 % of the day-one queue has DR3 epoch photometry.** Anyone rehearsing DR4
   transport with DR3 `EPOCH_PHOTOMETRY` over the real queue is mostly measuring empty
   requests. Draw a serving population deliberately.
4. **`DataFrame.iloc[0].to_dict()` rounds `source_id` past 2^53.** Taking a row from a
   mixed-dtype frame upcasts every column to float64; Gaia BH3's DR3 id 4318465066420528000
   came back as ...528128, a source that does not exist, and would have been written into
   `source_id_dr3`. This is the pandas twin of M2's ADQL landmine. **Take an int column
   from the COLUMN, never from the row.**
5. **Newton's method on the mass-function cubic diverges from the natural starting guess.**
   `(F·M₁²)^(1/3)` sits left of the turning point of `h(x) = x³ − F(M₁+x)²`, where h′ < 0,
   so the first step walks away and the iteration collapses onto the lower clip — Gaia BH3
   came out as M₂ = 1e−9 instead of 34.68. Caught **only** because every point estimate is
   cross-checked against `pystrometry.pjGet_m2`. Use the monotone fixed-point map
   `M₂ ← (F(M₁+M₂)²)^(1/3)`, then polish.
6. **The astronomical mass function `a₀³/(P_yr²ϖ³)` and pystrometry's SI chain differ by
   ~1e−4** (3.6e−5 in M₂ on BH3) — a units-convention gap, invisible physically, fatal to a
   bit-exactness claim, and it cost a debugging round. The arm computes the mass function
   in pystrometry's own constants and carries the shortcut value in `refit_notes`.
7. **The refit arm's formal errors are too small by a median factor 2.3**, measured against
   three published solutions (§2e-i). Report the posterior as a formal interval.
8. **Refit parallaxes run low by 5–41 µas, and the mass function goes as ϖ⁻³.** The single
   largest systematic on any companion mass this pipeline produces (§2e-ii).
9. **`min_detectable_rate(n1, p0, n2)` takes the FIXED-rate group first.** Passing the
   spurious group first returned 0.60 where M6 published 0.55. Caught only by the driver's
   reproduction block — which is the argument for having one.
10. **A CSV appender that does not align columns corrupts silently.** Phases A/B and C
    report different quantities; the first phase-C `mode='a', header=False` append filed
    `n_fits` under `n_processed`. Obvious nonsense this time; it will not always be.
11. **`gaiadr3.gaia_source.has_epoch_photometry` and `vari_summary` membership agree
    exactly** on all 981 queue members (74 each). Either can be used; say which.
12. **The runbook's own December command crashed.** `--verdicts all` on either
    discriminator test raised the moment the store held a second producer —
    `AssertionError: EB26 join to triage parquet must be 1:1 and complete` (M4) and
    `EB26 join fanned out: 88` (M5) — because both hard-coded `== 76`, the size of the
    only store that existed when they were written. **§3.3 of the runbook told December to
    "run each twice: scope-pure and pooled", and the pooled half would have died on the
    day.** The invariant those assertions were protecting is *no join fan-out*, which is a
    property of the merge and not of the store's size; both now assert `len(t) == len(eb)`
    and **drop unjoinable rows with a printed count** instead of dying. Running the
    pre-registered *primary* (scope-pure, harness-only) command then exposed the second
    half of the same problem: with today's store that selection leaves zero testable rows,
    and both tests died on an `AssertionError` — which reads as "the pipeline broke" when
    the truth is "there is nothing to test". Both now exit cleanly with **NOT TESTABLE and
    the coverage count**, which is the answer M5 family A already gives for the same
    situation. All five frozen M4/M5 artifacts reproduce **byte-identically** through every
    one of these changes, re-verified after each. *A
    pre-registered command nobody has executed is a promise, not a protocol* — which is
    also why M8's third recommendation exists.
13. **A killed background wrapper can leave its python child running.** The weather
    sampler's shell wrapper was reported killed; the sampler itself kept going, a
    replacement was started, and **two processes rewrote the same CSV** — each write a
    complete, self-consistent series, so the file flipped between two different runs and
    looked as though the rep counter had gone backwards. Caught by reading the file twice.
    A globbing consumer would have silently double-counted the overlap; the report now
    reads exactly one file, and the duplicate was stopped by PID rather than by wrapper.
14. **`m5_activity_discriminator.py` announced `out/…` no matter where it wrote.** The
    completion line hard-coded the default directory while the files went to `--out-dir`,
    so the pre-registered *pooled* December run would have reported that it had just
    overwritten the frozen M5 artifacts — when it had not. Fixed to print the real path
    (artifacts re-verified byte-identical afterwards). A log line that lies about a path
    is a log line that will be believed at 3 a.m. on release day.

---

## 7. Frozen-artifact verification

Run at close, `git diff --stat` over `gaia-dr4/`:

- `queries/dr4-triage-config.{json,v2,v3,v4,v5}.json` — **untouched**
- `schemas/day1_verdict_record.v1.json` — **untouched**
- `out/verdicts/eb26.v1.csv`, `out/verdicts/harness_prerelease.v1.csv` — **untouched**
- every M2/M3/M4/M5/M6 result CSV, PNG and stats file — **untouched**, and the five M4/M5
  artifacts additionally re-verified byte-identical by re-running the pre-registered
  regression command through the modified consumers
- modified, all deliberate: `scripts/epoch_vet_harness.py` (§4),
  `scripts/m4_eb26_erosita_test.py` + `scripts/m5_activity_discriminator.py` (one
  assertion each, landmine #12), `DR4-DAY-RUNBOOK.md`, `STATUS.md`, and
  `out/rehearsal_timings.csv` — the last is the rehearsal driver's own log, rewritten by
  every rehearsal since M3 and not an artifact anyone freezes
- added: the M7 scripts, `out/m7_*`, `out/m7_dryrun/`, `out/verdicts_v2/`,
  `schemas/day1_verdict_record.v2.json`, this file and the pre-registration

**No config version was written by M7.** M7 changed nothing about the candidate list, the
screen, the membership or any flag decision, and a config bump that carries no decision is
noise in a version history that has so far meant something. v5 stands.

---

## 8. Recommended M8

1. **Run the refit arm at queue scale, on DR3.** The arm is validated on three sources and
   costs ~1.2 s each; nothing has yet run it over hundreds. The natural rehearsal is the
   DR3 NSS orbits themselves: the arm's own output can be compared against
   `nss_two_body_orbit` for every source with published Campbell elements, which turns
   §2d's three-row table into a distribution and gives the **empirical error-inflation
   factor** (§2e-i, currently n = 11) a real sample. That factor is the number December
   will have to quote next to every companion mass, and 2.3-from-three-objects is not good
   enough to publish.
2. **Close the parallax systematic, or bound it.** §2e-ii is the dominant error on every
   mass the pipeline will produce and it is currently only *named*. Two tractable routes:
   apply the Lindegren+2021 zero-point correction inside the arm (sourced, mechanical) and
   measure what it does to the trio; and check whether DR4's RVS-derived `a1` is available
   for enough candidates to take Panuzzo's own route around the problem.
3. **Rehearse the December analysis end to end against the pre-registration.** Generate a
   synthetic verdict store at plausible December scale and *run the pre-registered
   commands on it*, purely to confirm that every rule in the pre-registration is executable
   and that each test emits its label. A pre-registration nobody has run is a promise, not
   a protocol — and this is the last milestone in which finding an unworkable rule is free.
4. Human TODOs unchanged: Gaia Archive + Data Lab accounts (Matthew). A logged-in DataLink
   quota remains a measured lever; note that at 468 sources/hour the anonymous service now
   clears the queue in one evening, so the account buys **depth beyond the queue**, not the
   queue itself.
