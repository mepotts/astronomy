# M3 — the all-83 noise campaign, the two seams, and what they do to the common signal

*2026-08-21. Third milestone of avenue #2. Repo law: every externally-sourced number carries its
source URL or the mark UNSOURCED; negative results are results; blockers are findings;
**every criterion is pre-registered before the run that tests it**.
Foundation: [`M1-access-reproduction.md`](M1-access-reproduction.md) (access, stack, conventions,
the mode-vs-model diagnostic) and [`M2-converge-scale.md`](M2-converge-scale.md) (the hardened
harness + its acceptance floor, the top-10 campaign, the 10-pulsar factorised-likelihood CURN,
and the two seams this milestone is built to measure).*

---

## 1. Pre-registration (written 2026-08-21, BEFORE any M3 sampling)

Everything in §1 was fixed before the first M3 chain started. Sections from §2 onward were written
after the runs; git history is the audit trail.

### 1.1 What M3 sets out to measure

Four products, in dependency order:

1. **The all-83 noise campaign** — the favoured model of every released MPTA pulsar, sampled from
   public data under the M2-hardened harness *including its acceptance floor*, compared against the
   published tables parameter by parameter.
2. **Seam (a)** — the chromatic A–β ridge with untabulated priors, quantified across the array.
3. **Seam (b)** — intrinsic achromatic red vs the fixed-13/3 term, quantified across the array,
   and its propagation into the factorised-likelihood CURN amplitude.
4. **The 83-pulsar factorised-likelihood CURN amplitude** under both competing model choices,
   against the published −14.28 ± 0.21.

No detection or evidence claim is made anywhere in M3: γ is fixed at 13/3 throughout the CURN
slices, no Hellings–Downs correlation and no continuous-wave search is attempted (both still sit
behind the sparse-stack upgrade M1 documented). No submissions, no accounts, no commits, no pushes.

### 1.2 Data preparation and the A1 gate, extended to all 83 (P-criteria)

- **P1 (published tables, machine-parsed).** The comparison targets are the two longtables of
  arXiv:2412.01148 — `Table: MPTA noise models` (14 parameter columns × 83 pulsars) and
  `Table: MPTA determinstic models` [sic] (8 columns × 23 pulsars) — parsed from the arXiv LaTeX
  source (<https://arxiv.org/e-print/2412.01148>, re-downloaded 2026-08-21, preserved at
  `data/paper/mnras_template.tex`) by `scripts/m3_parse_tables.py`. **Acceptance for the parser:
  it must reproduce M2's independent hand transcription of ten pulsars exactly** — all published
  values *and* all inferred model configurations, 0 mismatches. If it does not, the parser is
  wrong and is fixed before anything is sampled.
- **P2 (model inference).** Each pulsar's favoured model is inferred from which table columns carry
  values, by the same rule M2 applied by hand: E_Q/E_C column → EQUAD/ECORR; A_Red → free
  achromatic red; A_DM → DM GP; A_Chrom → chromatic GP with β free if the β column prints a CI and
  fixed at 4 if it prints a bare "4"; SW GP columns → SW_Full, n_⊕ with a CI and no SW GP →
  SW_Det, bare "4" → SW_Fixed; a deterministic-table row → chromatic Gaussian event (sign as
  printed) and/or annual chromatic variation. Every model also carries the fixed-γ = 13/3
  free-amplitude achromatic term.
- **P3 (A1, stack acceptance, all 83).** For every pulsar, PINT's weighted RMS of the released
  par+tim must land within **15%** of the par's own tempo2 `TRES`. Pre-registered fallback for
  failures, fixed here before it is used: a pulsar missing the tolerance *as loaded* gets **one
  WLS refit of its own released free parameters**, and A1 is re-tested on the refit model; if the
  refit passes, the refit ephemeris is what the campaign samples and the pulsar is flagged as
  refit-recovered. A pulsar failing even after the refit is reported as an A1 failure and its
  noise result is reported with that caveat attached, not silently dropped.
- **P4 (conventions).** Unchanged from M2 §1.2 in every respect — PINT backend on TCB→TDB-converted
  pars, DE440, `TRACK` stripped where present (measured inert), EFAC/TNEquad/epoch-quantised ECORR,
  120-component Fourier GPs on the full Tspan, 1400 MHz DM/chromatic/SW references, linear-spaced
  SW harmonics, `idx = β` chromatic delay basis, the local Gaussian-bump waveform, the analytic
  SVD timing-model marginalisation, PTMCMC. Priors are M2's (declared UNSOURCED — the paper
  tabulates none), reproduced in `scripts/mpta_models3.py`.

### 1.3 The all-83 campaign (C-criteria — M2's, with its acceptance floor now part of the gate)

- **C1 (convergence gate).** Per pulsar: wall-clock cap **300 min** of sampling (chunked,
  resumable, abortable), gate = **≥ 100,000 raw post-burn iterations** (burn = first 25%)
  **AND** the M2 median-stability rule (last-half vs full-chain shift < 0.1 for log10-amplitudes
  and EFAC, < 0.3 for γ, β and n_⊕, < 0.1 × prior width for t0/σ_g/φ) **AND** the M2 acceptance
  floor **acc ≥ 0.05**. All three must hold; the floor is the fix M2 registered after a frozen
  chain (acc 0.016) passed a stability-only gate. A pulsar not clearing the gate at the cap lands
  the M1-style A3 feasibility verdict and is reported as such.
- **C2 (agreement).** Per parameter, the M1 A2 rule: the published MAP lies inside our 68%
  equal-tailed credible interval, **or** our posterior median lies inside the published 68%
  interval. A pulsar "fully agrees" when every compared parameter agrees. Reported as per-pulsar
  x/y, the count of fully agreeing pulsars, and the array-wide parameter total.
- **C3 (every miss diagnosed).** For each disagreeing pulsar, our own likelihood is evaluated at
  the published MAP vector (fixed table values entering as constants) and at our chain's best
  point. **ΔlnL = lnL(ours) − lnL(published)**; ΔlnL < 0 → our sampler under-performed →
  *sampling shortfall*; ΔlnL > 0 → our likelihood genuinely prefers a different solution →
  *prior/convention finding* (M2's J1017 case) or, if large and on a well-constrained parameter,
  *genuine disagreement*. The pre-registered split between the last two: a miss is called a
  **genuine disagreement** only if ΔlnL > 10 **and** the disagreeing parameter's published 68%
  interval is narrower than 25% of its prior range (i.e. the table claims a real measurement);
  otherwise it is a **prior/convention finding**. ΔlnL is computed for **every** pulsar, agreeing
  or not, so the array-wide distribution of the diagnostic is known rather than only its tail.
- **C4 (coverage honesty).** If the array does not finish inside the session, coverage is reported
  exactly (pulsars gated / running / not started) and the campaign continues from checkpoints;
  nothing is restarted and no partial chain is quietly dropped.

### 1.4 Seam (a): the chromatic A–β ridge and its untabulated priors (S-criteria)

Affected set, fixed by P2: the pulsars whose favoured model carries a **free** chromatic index.
Contrast set: those with β fixed at 4. Measured on the campaign's own post-burn posteriors — no
extra sampling.

- **S1 (does the ridge exist).** Pearson r and the OLS slope d log10A_Chrom / dβ in each free-β
  posterior. Registered expectation: strong negative r (the (1400/ν)^β parameterisation forces it).
- **S2 (is β data-constrained).** The 68% and 95% CI widths of β as a fraction of the U(0,14)
  prior width, per pulsar.
- **S3 (prior sensitivity, by importance reweighting).** Each posterior is reweighted from our
  declared β ~ U(0,14) to three alternative, equally defensible priors whose support is contained
  in ours — **U(0,10)**, **U(0,7)**, **U(2,6)** (a scattering-motivated bracket around 4) — by
  the exact weight π′(β)/π(β), which is valid because the alternatives are nested inside ours.
  Effective sample size is reported for every reweighting and a result is discarded if ESS < 200.
  Recorded per pulsar: the shift in the marginal medians of log10A_Chrom, γ_Chrom, β and
  **log10 A_13/3** under each alternative prior.
- **S4 (verdict rule, fixed now).** A pulsar's tabulated chromatic amplitude is called
  **prior-driven** if, under at least one of the three alternative priors with ESS ≥ 200, the
  median of log10A_Chrom moves by more than the published 68% half-width for that pulsar;
  **data-driven** otherwise. The array-wide count of each is the deliverable, together with the
  single sentence a reader of the MPTA noise table should carry away.
- **S5 (fairness control).** The same reweighting is applied to a parameter that must *not* be
  prior-driven — each pulsar's EFAC — and to the fixed-β=4 contrast set. If EFAC moves under a
  β-prior change, the machinery is wrong and S3/S4 are void.

### 1.5 Seam (b): intrinsic red vs the 13/3 term (B-criteria)

The paper adds a free achromatic red process to **every** pulsar for both common-signal analyses
("achromatic red noise processes were included for pulsars, even if they did not have this term in
their noise models, to mitigate any unidentified intrinsic pulsar noise being misspecified as a
part of a shared signal" — arXiv:2412.01148 §Common signals; the same statement appears in
§Search for common processes). The **published noise table's A_13/3 column is not that quantity**:
it is the favoured single-pulsar model's value, and for the pulsars whose favoured model carries no
red process the two configurations differ. M3 measures the difference on the whole array.

Two runs per pulsar, differing in exactly one component:

- **variant `table`** — the favoured model exactly as tabulated, white noise held at our own
  campaign medians;
- **variant `fl`** — the same, **plus** a free achromatic red process (log10A U(−18,−11),
  γ U(0,7)) where the favoured model lacks one; whites held identically.

Because the whites are fixed identically in both, the only difference between them is the added
red process.

- **B1 (gate).** Each run: wall cap **120 min**, gate ≥ **50,000** raw post-burn iterations + the
  same stability rule + the acceptance floor 0.05. `cov_scale0 = 0.05` for fixed-white runs (M2
  §5.1's frozen-chain fix).
- **B2 (the measurement).** Per pulsar, Δ_b = median(log10A_13/3 | `fl`) − median(log10A_13/3 |
  `table`). Reported: the distribution across the array, the counts moving > 0.3 / > 0.5 / > 1.0
  dex, and for each mover whether the published table's 68% interval contains the `fl` median.
- **B3 (null control, built in).** For the pulsars whose favoured model **already** contains a free
  red process, `table` and `fl` are the *same model*, so their Δ_b measures nothing but sampler
  noise. That set is the pre-registered null distribution against which the movers are judged: a
  shift only counts as real if it exceeds the 95th percentile of |Δ_b| over the control set.
- **B4 (is the tabulated A_13/3 a measurement at all).** Independently of the model choice, count
  the pulsars whose A_13/3 posterior is **prior-floor-limited** — lower 68% edge below −16.5, the
  very point the paper itself uses as "clearly disfavoured" in its Savage–Dickey ratio. For those
  the tabulated MAP is a prior artefact, not a measurement, and this must be stated plainly.

### 1.6 What the seams do to the common signal (F-criteria)

Method: the paper's own (Taylor et al. 2022, 2022PhRvD.105h4049T) — the factorised-likelihood
posterior is the renormalised product of the per-pulsar log10 A_CURN marginals, identical uniform
priors making the prior division a constant. Combination by Gaussian-KDE product on a common
support (M2's `m2_fl_combine.py` machinery), MAP and equal-tailed 68% quoted.

- **F1 (the two products).** The FL product is formed twice: once over the `fl` marginals (the
  collaboration's configuration) and once over the `table` marginals (the noise table taken at face
  value). Both are reported whatever they show.
- **F2 (per-pulsar gate).** Only runs clearing B1 enter a product; the product is additionally
  reported with and without any flagged pulsar.
- **F3 (the pre-registered comparisons).** (i) the 10-pulsar sub-product over M2's exact top-10
  against M2's −14.46 MAP / −14.53 median; (ii) the 83-pulsar product against the published
  −14.28 ± 0.21; (iii) `fl` vs `table` — the seam-(b) propagation.
- **F4 (what counts as a significant shift, fixed now).** The `fl` → `table` shift is called
  **significant** if the two MAPs differ by more than 0.21 dex (the published 1σ) **or** if one
  product's 68% interval excludes the other's MAP. Otherwise the result is a **null**, and the
  null is reported as the headline with the same prominence a shift would have had.
- **F5 (scope statement, unchanged from M2).** What an FL amplitude establishes: that an
  independently implemented likelihood on public data reproduces the collaboration's common-signal
  amplitude scale, and how that scale moves under a model choice the collaboration itself flags.
  What it does not establish: the detection (no Bayes factor), the spectral characterisation
  (γ fixed), or anything about spatial correlations.

### 1.7 The published-table audit (T-criteria — no sampling)

- **T1.** Across all 588 tabulated parameter values, count those whose printed MAP falls **outside
  their own printed 68% interval** (detectable because the printed lower offset is non-negative).
  The paper says this happens "in some few cases"; the deliverable is the number, the list, and
  which parameter types it concentrates in.
- **T2.** Count the tabulated A_13/3 values that are prior-floor artefacts under B4's definition.
- **T3.** Both counts are reported as *properties of the table*, with the paper's own caveat quoted
  alongside — this is a measurement of a documented limitation, not a claim of error.

### 1.8 Economics and honesty rules

Every run's measured eval time, sustained it/s, acceptance and exit reason go into its summary
JSON; the campaign updates the all-83 and full-array projections from 83 measured pulsars instead
of M2's 10. Any chain used for a reported number must have passed the acceptance floor; the audit
of all runs' acceptance rates is reported before any number is quoted.

---

*Results below this line were written after the runs.*

## 2. The published tables, machine-parsed and validated (P1/P2)

`scripts/m3_parse_tables.py` reads both longtables out of the arXiv LaTeX source and emits
`results/m3/published_table.json`: **83 noise rows (588 tabulated parameter values) and 23
deterministic rows**. The pre-registered parser acceptance passes:

> **cross-check vs M2's hand transcription: PASS (0 mismatches)** — every published value *and*
> every inferred model configuration for M2's ten pulsars reproduces exactly.

That is a real check, not a formality: M2's ten were transcribed by hand from the same source
weeks earlier, and they include the four hardest models in the release.

**Which version is the target.** arXiv:2412.01148 has only **v1** (2 Dec 2024) and it carries the
journal DOI `10.1093/mnras/stae2572` (MNRAS 536, 1467). The published OUP table was spot-checked
against the parsed values on five randomly chosen entries spread across the visible half of the
table — J0030+0451 E_F and A_13/3, J0125-2327 A_DM/γ_DM, J1600-3053 A_Chrom/γ_Chrom/β,
J1643-1224 β, J1652-4838 A_SW — **5/5 MATCH**. (One earlier automated fetch returned a
J1909-3744 row inconsistent with both arXiv v1 *and* M2's converged 9/9 reproduction of that row
to 0.01 dex; OUP truncates the longtable in its HTML and that answer is treated as a fetch
artefact, not evidence of a revision. Recorded because the repo has been burned by a
preprint-vs-published divergence before.)

**Model inventory of the release**, inferred by P2 (this is the first machine-readable statement
of it we have):

| component | pulsars | | component | pulsars |
|---|---|---|---|---|
| EFAC | 83/83 | | chromatic GP, β free | **13** |
| EQUAD | 20 | | chromatic GP, β = 4 fixed | 10 |
| ECORR | 29 | | SW_Full (n_⊕ + SW GP) | 26 |
| DM GP | 49 | | SW_Det (n_⊕ only) | 30 |
| free achromatic red | **12** | | SW_Fixed (n_⊕ = 4) | 27 |
| chromatic Gaussian event | 15 | | annual chromatic variation | 8 |
| A_13/3 (fixed γ) | 83/83 | | **total sampled parameters** | **588** |

The two numbers in bold are the sizes of the two seams' affected sets: 13 pulsars carry a free
chromatic index (seam a), and **71 of 83 pulsars have no achromatic red process in their favoured
model** while the collaboration's own common-signal analyses give every pulsar one (seam b).

## 3. A1 across all 83: the release reproduces its own fit statistic to 0.02%, except where it ships fewer ToAs than it fitted

`scripts/m3_prepare.py` (headless A1 + TDB par, run 12-way) over the whole release:

- **82 / 83 PASS** the 15% A1 tolerance; 245,907 ToAs loaded in total (M1's count, confirmed
  independently).
- Split by whether the shipped `.tim` contains as many ToAs as the par's own `NTOA`:
  - **63 pulsars with a complete release: median |PINT wRMS − tempo2 TRES| / TRES = 0.02%**
    (two parts in 10⁴), worst case 12.15% (J1713+0747, the shortest data set).
  - **20 pulsars shipping fewer ToAs than their par fitted: median 6.87%, worst 28.40%.**
  - Pearson r(fractional residual, shipped/NTOA) = **+0.42** over the array.
- The single A1 failure is **J1658-5324 (−28.4%)**, which ships 1,161 of 1,488 ToAs. It is
  reported with that caveat attached rather than dropped, exactly as pre-registered.

So the independent timing implementation agrees with the collaboration's own tempo2 fit to two
parts in ten thousand wherever the release is internally complete, and every material discrepancy
traces to the partial-ToA pattern M1 first noticed on J2241-5236.

### 3.1 Three ephemeris defects found by running all 83 (none visible in the top-10)

1. **Eight pars miss their own TRES badly as loaded, and one WLS refit fixes seven of them.**
   J1802-2124 (+265%), J1435-6100 (+213%), J1757-5322 (+196%), J1525-5545 (+86%),
   J1327-0755 (+48%), J1543-5149 (+31%), J1036-8317 (+20%) and J1658-5324 (−25%) load with
   residual RMS far above the in-release value; one refit of the pars' *own* released free
   parameters brings seven of the eight to **|−2.8%| or better** (four of them to < 0.4%,
   J1802-2124 to +0.02%). The offending direction lies inside the timing-model design matrix — a
   refit with the Shapiro parameters *frozen* recovers TRES just as well (J1802-2124: 2.9997 µs
   both ways vs TRES 2.999) — so it is a parameter-value mismatch introduced by the TCB→TDB
   conversion, not a functional-form disagreement, and enterprise's analytic timing-model
   marginalisation would absorb it. The refit ephemerides are what the campaign samples
   (pre-registered P3 fallback), and 7 of the 8 became A1 PASSes.
2. **J1825-0319's released ephemeris is unphysical.** It carries `BINARY DDH` with
   `H3 = −2.98 × 10⁻⁷ s` — a *negative* orthometric Shapiro amplitude, which implies
   M2 = H3/ς³ < 0. PINT refuses to build the model ("Companion mass M2 cannot be negative,
   −0.448 M☉"); tempo2 evidently does not check. A refit started from the released values lands
   negative again, so the shipped value is what the data pull towards, not a transcription slip.
   Handled by dropping the Shapiro term (H3, ς removed, `BINARY DD`) and refitting: A1 **+0.17%**.
   The delay involved is ≤ 0.3 µs against a 4.6 µs TRES and lives in the design matrix either way.
3. **`TRACK -2` in 12/83 pars** — confirmed inert for the shipped tims across the whole array
   (M2 measured this on J1600-3053 alone); stripping it costs −0.03% there and never decides an
   A1 verdict elsewhere.

## 4. The published table, audited on its own terms (T-criteria)

No sampling; `scripts/m3_table_audit.py`, `results/m3/table_audit.json`.

**T1 — MAPs outside their own printed intervals.** The paper's caption warns: *"In some few cases,
the MAP value has fallen outside of the the confidence interval we report."* The number is
**26 of 588 values (4.4%), affecting 22 of 83 pulsars.** (A further 4 values print an offset of
exactly 0.00 on one side; those are rounding at the printing precision and are excluded — the
count uses strict inequalities.) It is not spread evenly:

| parameter | outside / tabulated | |
|---|---|---|
| log10 A_13/3 | **13 / 83** | 16% |
| log10 E_Q | **5 / 20** | 25% |
| log10 A_s (annual) | 2 / 8 | 25% |
| log10 E_C | 2 / 29 | 7% |
| log10 A_DM | 2 / 49 | 4% |
| φ (annual), log10 A_Red | 1 each | |
| **every other column** | **0** | |

Every affected parameter is an amplitude (plus one phase). Nothing in the E_F, γ, β, n_⊕, SW or
chromatic-Gaussian-event columns is affected at all. The pathology is therefore a signature of
one-sided, prior-limited posteriors, not of a sampling problem spread across the table.

**T2 — how much of the A_13/3 column is a measurement.** The paper's own Savage–Dickey
calculation treats `log10 A_CURN < −16.5` as the region "where the prior range was clearly
disfavoured". Applying that same point to the per-pulsar column:

- **66 of 83 tabulated log10 A_13/3 values have their 68% interval reaching below −16.5** — they
  are bounded by the prior, not by the data (median 68% width **3.01 dex**, up to 4.01 dex).
- **17 are bounded on both sides**, and only **six** are constrained to better than 0.7 dex:
  J2129-5721 (0.37), J1909-3744 (0.38), J1751-2857 (0.44), J1547-5709 (0.45), J1643-1224 (0.55),
  J1216-6410 (0.65).

This is a property of the data, not an error by the collaboration — a 4.5-yr array simply cannot
constrain a γ = 13/3 amplitude in most of its pulsars, and the factorised likelihood is designed
to work precisely by multiplying many weak constraints. But it is the single most important thing
for a reader of that column to know, and the paper does not state it.

## 5. The priors that are not in the paper — and the seven rows that cannot be reproduced without them

The word "prior" appears in arXiv:2412.01148 only in method prose; **no prior range is stated
anywhere in the paper**, for any parameter. M1 declared a standard wide set and M2 carried it
unchanged (both marked UNSOURCED). Running all 83 turns that from a caveat into a measurement.

`scripts/m3_prior_coverage.py` asks the sharp version of the question: of the 573 tabulated values
that correspond to a parameter we sample, how many lie **outside** the prior a good-faith
reproducer declared?

- **7 values (1.2%) are outside — and all seven are the same parameter: the solar-wind GP spectral
  index γ_SW, tabulated NEGATIVE.** J0900-3144 (−0.20), J1327-0755 (−0.76), J1643-1224 (−1.96),
  J1652-4838 (−0.68), J1730-2304 (−1.61), J1751-2857 (−2.32), J1811-2405 (−2.21).
- A further **32 values** sit inside the prior but have a 68% interval that runs past one of its
  edges: 12 more γ_SW (crossing 0), 12 A_DM and 6 A_Red (reaching the −18 amplitude floor),
  1 A_Chrom, 1 σ_g.
- Combining, **19 of the 26 SW_Full pulsars (73%) have a γ_SW value or interval our declared prior
  cannot represent.**

This is our defect first and the paper's second. M1's blanket "γ ~ U(0,7)" was applied to *every*
power-law spectral index including the solar-wind GP — but enterprise_extensions' own
`solar_wind_block`, the very function this analysis uses, defaults to **γ_SW ~ U(−2, 1)**
(verified in `enterprise_extensions/chromatic/solar_wind.py:234`). A negative γ_SW is not exotic
for that signal; it is the library's default regime, and our U(0,7) excluded it by inheritance.
Two of the published values (−2.32, −2.21) fall outside even the library default, so the MPTA's
own γ_SW prior is wider still — and it is not stated.

**The consequence is exact and unavoidable:** for those seven pulsars our chains cannot visit the
published solution, so a γ_SW/A_SW disagreement is *forced by our prior*, not measured from the
data. The pre-registered C3 machinery classifies such misses correctly (prior/convention finding),
and §6 reports how many of the campaign's misses have this single cause. The
post-hoc supplementary check with a widened γ_SW prior is in §6.4, declared as post-hoc and kept
out of the registered statistics.

**What a reader of the MPTA noise table should know (statement 1 of 3):** the table's γ_SW column
takes negative values in 27% of the pulsars that have one, and the prior that allowed them is not
published. Two lines of prior ranges in the caption would make the whole table reproducible; right
now seven rows cannot be reproduced by anyone who has to guess.

## 6. The campaign: coverage, agreement, and every miss classified

**Snapshot taken 2026-08-21 (campaigns still running and checkpointed; §11 resumes them).**

### 6.1 Coverage, stated exactly (C4)

| | pulsars |
|---|---|
| started | **71 / 83** |
| cleared the pre-registered C1 gate (≥100k raw post-burn + stability + acceptance ≥ 0.05) | **48** |
| running, gate not yet met | 23 |
| never started | 12 |
| dependent `table` runs gated | 33 |
| dependent `fl` runs gated | 36 |
| pulsars with **both** dependent runs gated (the seam-(b) sample) | **32** |

The covered set is **not** a random 48 of 83. The schedule was deliberately reordered mid-campaign
(§11) to put the 13 free-β chromatic pulsars and the 12 red-carrying pulsars — the two seams'
affected and control sets — at the head of the queue, precisely so a partial campaign would still
measure the seams. Everything below is therefore *enriched* in the hard models and reports which
model classes it covers:

> gated set contains **21 of 49 DM GPs, 10 of 12 free red processes, 7 of 13 free-β chromatic GPs,
> 4 of 10 β = 4 chromatic GPs, 8 of 26 SW_Full, 9 of 15 chromatic Gaussian events, 4 of 8 annual
> chromatic terms, 9 EQUAD, 9 ECORR.**

Chain sizes: median 111,010 raw post-burn iterations (100,510–213,760); median eval 43 ms;
acceptance over the gated set **0.162–0.527**, every run above the M2 floor of 0.05 — no frozen
chain anywhere.

**One dependent run landed the A3 feasibility outcome as pre-registered:** J1600-3053's `fl` run
exited on its 120-min wall cap at 193,510 raw post-burn iterations with acceptance 0.155 and the
stability check still failing — reported as not-gated and excluded from every product, not quietly
included.

*Coverage kept moving while this section was written* (the campaigns are detached and
checkpointed): by hand-off the noise campaign stood at **50/83 gated**, `table` at 34 and `fl` at
37. Every number in §6–§8 comes from the single 48-gated snapshot above so that the coverage, the
agreement statistics and the CURN products all describe the same set of chains; §11 resumes from
where the campaigns actually are.

### 6.2 Agreement: 46 of 48 pulsars agree in full; 296 of 299 parameters (99.0%)

Per the pre-registered A2 rule, over the 48 gated pulsars:

- **46/48 pulsars agree on every one of their tabulated parameters.**
- **296/299 parameters agree (99.0%).**
- The reproduced structures include 9 chromatic Gaussian events (amplitude, chromatic index,
  epoch, width — all four parameters each), 4 annual chromatic variations, 7 free-β chromatic GPs,
  21 DM GPs and 10 free achromatic red processes, all built from scratch on public data with an
  independently implemented likelihood.

### 6.3 The three misses, and the single cause behind them (C3)

| pulsar | agree | ΔlnL (ours − published) | missed parameters | classification |
|---|---|---|---|---|
| J1652-4838 | 15/16 | **+3.02** | γ_SW | prior/convention finding |
| J1327-0755 | 3/5 | **+0.42** | γ_SW, A_SW | prior/convention finding |

Both misses are the **same parameter in the same direction**, and both are pulsars whose published
γ_SW is **negative** — outside the prior we declared (§5). No miss anywhere in the campaign is on a
DM, chromatic, white-noise, deterministic-event or A_13/3 parameter.

**The mode-vs-model diagnostic run on every gated pulsar, not just the misses** (this is the number
that makes the reproduction claim quantitative rather than categorical):

> ΔlnL = lnL(our chain's best point) − lnL(published MAP vector), under our own likelihood:
> **median +0.40 over 48 pulsars, 45 positive / 3 negative, full range −0.67 to +8.56.**

Two readings follow. First, our sampler never *under*-performs the published solution by more than
0.67 lnL anywhere in the array — M1's ΔlnL = +22.4 sampling shortfall has no analogue at scale.
Second, the largest positive values (J2150-0326 +8.56, J1832-0836 +4.43, J1652-4838 +3.02) occur on
pulsars that **agree on every parameter**: a long MCMC finding a point a few lnL better than a
rounded published MAP vector in a 9–16-dimensional posterior is the diagnostic's noise floor, not
evidence of disagreement. That calibrates the pre-registered "genuine disagreement" threshold
(ΔlnL > 10 *and* a published interval narrower than 25% of the prior) as comfortably above the
floor — and **no pulsar in the campaign reaches it**.

### 6.4 The supplementary γ_SW-prior check (DECLARED POST-HOC — not in any registered statistic)

The registered campaign cannot reach a negative γ_SW, so its two misses are prior-forced. The
supplementary run re-samples the same pulsar with γ_SW ~ U(−4,4), everything else identical
(`scripts/m3_run.py --sw-gamma-prior=-4,4`, tag `swp`):

| J1327-0755 | published | registered `n1`, γ_SW ~ U(0,7) | supplementary `swp`, γ_SW ~ U(−4,4) |
|---|---|---|---|
| γ_SW | −0.76 [−3.05, −0.07] | +0.47 [+0.14, +1.03] ✗ | **−1.36 [−3.14, +0.15] ✓** |
| log10 A_SW | −7.19 [−8.82, −6.82] | −6.54 [−6.77, −6.29] ✗ | **−7.65 [−8.84, −6.73] ✓** |
| n_⊕ | 8.50 [6.94, 10.26] | 8.22 ✓ | 8.17 ✓ |
| log10 A_13/3 | −13.87 [−15.93, −13.59] | −13.78 ✓ | −13.80 ✓ |

The supplementary run cleared the same gate (103,510 raw post-burn) and turns **3/5 into 5/5**.
So the campaign's *only* substantive disagreements with the published table dissolve when the
solar-wind spectral-index prior is widened to a range that contains the published value — which is
the operational meaning of §5's finding. The registered statistics above are left exactly as
registered; this check is reported alongside them, not folded in.

### 6.5 Our own reproducibility, measured (the yardstick every disagreement must beat)

M2's top-10 runs and M3's are independent repeats of the identical model on the identical data with
different seeds. Over the 6 pulsars gated in both (39 parameters):

- **median |median difference| = 0.012**, 90th percentile 0.19.
- The largest differences are all on **prior-limited or weakly-constrained** parameters:
  J2129-5721's annual amplitude (1.08 dex — its published interval is −6.68 −9.40 +0.13, i.e.
  9.4 dex wide), J1600-3053's Gaussian-event width (42 d on a 1,990 d prior, 2%) and epoch (21 d).
  Every well-constrained parameter repeats to ≲ 0.05.

That is the honest scale of "the same analysis, run twice": ~0.01 dex where the data constrain, and
up to a dex where they do not. Any claim about the published table has to clear it.

## 7. The two seams, measured

### 7.1 Seam (a) — the chromatic A–β ridge: the ridge is universal, the prior-dependence is not

Nine free-β pulsars have a gated posterior (7 from M3's campaign, 2 — J0437-4715 and J1017-7156 —
from M2's gated run of the identical model, flagged `*` in the table below and in
`results/m3/seam_a.json`). Plus four β = 4 contrast pulsars.

**S1 — the ridge exists everywhere.** Pearson r(log10 A_Chrom, β) has median **−0.90**, range
−0.95 to −0.63; the OLS slope is **−0.21 dex per unit β** (median). Every free-β chromatic
amplitude in the MPTA table is strongly anti-correlated with its own chromatic index. This is
forced by the (1400 MHz/ν)^β parameterisation and is not a defect — but it means the A_Chrom column
cannot be read independently of the β column.

**S2 — β is mostly measured, not prior-shaped.** The β 68% interval occupies a median of **10%** of
the U(0,14) prior (95% interval: 22%). Only J1911-1114 exceeds 25%.

**S3/S4 — the registered verdict: 2 of 9 free-β pulsars are PRIOR-DRIVEN.**

| pulsar | r(A,β) | β 68% as % of prior | max &#124;Δ median A_Chrom&#124; under a narrower β prior | published 68% half-width | max &#124;Δ A_13/3&#124; | verdict |
|---|---|---|---|---|---|---|
| J0437-4715 * | −0.92 | 15% | **0.38** | 0.26 | **0.17** | **PRIOR-DRIVEN** |
| J1802-2124 | −0.90 | 10% | **0.19** | 0.17 | 0.03 | **PRIOR-DRIVEN** |
| J1804-2858 | −0.84 | 11% | 0.19 | 0.21 | 0.15 | data-driven |
| J1911-1114 | −0.93 | 29% | 0.16 | 0.44 | 0.09 | data-driven |
| J1431-5740 | −0.95 | 16% | 0.13 | 0.28 | 0.04 | data-driven |
| J1017-7156 * | −0.91 | 10% | 0.00 | 0.23 | 0.00 | data-driven |
| J1652-4838 | −0.65 | 6% | 0.00 | 0.11 | 0.00 | data-driven |
| J1747-4036 | −0.74 | 7% | 0.00 | 0.18 | 0.01 | data-driven |
| J1825-0319 | −0.63 | 4% | 0.00 | 0.10 | 0.01 | data-driven |

**S5 — the fairness control passes.** Reweighting the β prior moves EFAC by at most **0.0019**
across all nine — the machinery is not simply reweighting everything.

**This corrects M2's own reading.** M2 attributed J1017-7156's chromatic miss to "a flat A–β ridge"
and called it a prior finding. The measurement says otherwise for that pulsar: J1017's β posterior
sits at 4.40 [3.63, 5.09], comfortably inside every alternative prior, and narrowing the prior
moves its amplitude by **0.00 dex**. J1017 is data-driven; the ridge is real but is not what caused
its 0.28 dex offset. The pulsars that *are* prior-driven are the ones whose β sits near or beyond
the edge of a plausible prior — **J0437-4715 at β = 8.24 [7.26, 9.42]**, where restricting to
U(0,7) (a prior range many PTA pipelines use for spectral indices) moves A_Chrom by **+0.38 dex**,
β by −1.56, and — the part that matters for gravitational waves — **A_13/3 by +0.17 dex**.

**Exploratory extensions (declared, not pre-registered).**

- *Prior shape.* Reweighting β to a Gaussian N(4,1)/N(4,0.5) on the same support moves A_Chrom by
  up to **0.40 dex** and would flag **5 of 9** as shape-sensitive. Range is the easy half of the
  problem; shape is the harder half, and neither is published.
- *S6, the decorrelating reference frequency.* The covariance between log10 A_Chrom and β vanishes
  at ν_piv = 1400 MHz × 10^(Cov(A,β)/Var(β)); measured per pulsar, **ν_piv has median 855 MHz
  (range 641–954 MHz)** — at the bottom of, or below, the 856–1712 MHz band, and far from the
  1400 MHz at which the table quotes the amplitude. Re-referencing there tightens the amplitude
  dramatically: the 68% width of log10 A_Chrom is **0.46 dex at 1400 MHz vs 0.21 dex at each
  pulsar's own pivot** — a factor 2.2 in precision, obtained by changing nothing but the reference
  frequency.

**What a reader of the MPTA noise table should know (statement 2 of 3):** the A_Chrom column is
quoted at a reference frequency that is not where the data actually constrain it, so its
uncertainty is inflated by a factor ~2 and its value is meaningless without the β column beside it.
For 2 of 9 pulsars tested, a different but equally defensible β prior would move the tabulated
amplitude by more than its own quoted uncertainty — and for the worst case, J0437-4715, it also
moves that pulsar's GW-relevant A_13/3 by 0.17 dex.

### 7.2 Seam (b) — intrinsic red vs the 13/3 term: real, one-directional, and modest for most

32 pulsars have both dependent runs gated: **26 test** (favoured model has no red process) and
**6 control** (it already has one, so `table` and `fl` are the *same* model and their difference is
pure sampler noise).

**B3 — the null control sets the bar.** |Δ_b| over the 6 control pulsars: median 0.040,
**95th percentile 0.144 dex**, max 0.167. A shift only counts above 0.144 dex.

**B2 — the measurement.** Δ_b = median(A_13/3 | favoured + free red) − median(A_13/3 | favoured):

- median **−0.033 dex**, mean −0.165, range **−0.77 to +0.12**;
- **8 of 26 (31%) exceed the control threshold**; 5 exceed 0.3 dex; 4 exceed 0.5 dex; none exceeds
  1 dex;
- **18 of 26 (69%) move DOWN** — the 13/3 term was absorbing intrinsic red noise, in the direction
  the collaboration's own mitigation is designed to correct;
- the largest movers are **J2010-1323 (−0.77), J1719-1438 (−0.74), J1721-2457 (−0.70),
  J1547-5709 (−0.69)**, and for **2 of them (J1721-2457, J1547-5709) the published 68% interval
  does not contain our `fl` median** — those are precisely the pulsars whose A_13/3 the table
  reports as *tightly* constrained (widths 1.00 and 0.45 dex, two of only six such rows in the
  whole array).

That is the sharp form of seam (b): the effect is small for the many pulsars whose A_13/3 is
unconstrained anyway, and largest exactly where the table looks most precise.

**M2's 1.3 dex claim for J1600-3053 is NOT reproduced and is withdrawn.** M2 read a 1.3 dex drop
off a comparison between its noise run and its FL run — a comparison that also changed the white
noise from sampled to fixed. With the confound removed by the pre-registered `table` control, no
pulsar in the array moves by more than 0.77 dex, and J1600-3053 is not among the movers. The
seam is real; its size was overstated by a factor ~2 and its worst case is a different pulsar.

**B4 — how much of the column is a measurement at all.** **30 of our 32 `fl` posteriors are
prior-floor limited** (68% lower edge below −16.5), reproducing the published table's own 66/83.

**What a reader of the MPTA noise table should know (statement 3 of 3):** the A_13/3 column is not
the per-pulsar CURN amplitude the common-signal search actually used — that search added a free
achromatic red process to all 71 pulsars that lack one. The two differ by up to 0.77 dex, almost
always downward, and the difference is largest for the handful of pulsars whose A_13/3 the table
constrains best.

## 8. What the seams do to the common signal

The factorised-likelihood product (the paper's own method, Taylor et al. 2022) formed twice from
the same machinery, differing only in whether each pulsar carries the free achromatic red process
the collaboration adds for its common-signal searches. `results/m3/fl_curn_all.json`,
`figures/m3_fl_curn_all.png`.

| product | pulsars | MAP | median | 68% |
|---|---|---|---|---|
| **`fl` — the collaboration's CURN configuration** (favoured + free red) | 36 | **−14.30** | −14.41 | [−14.92, −14.21] |
| **`table` — the noise table at face value** (favoured model only) | 33 | **−14.18** | −14.21 | [−14.46, −14.08] |
| published, 83 pulsars (arXiv:2412.01148, FL, γ = 13/3) | 83 | −14.28 | — | [−14.49, −14.07] |
| M2, 10 best-timed pulsars (`fl` configuration) | 10 | −14.46 | −14.53 | [−14.92, −14.31] |

**Both are consistent with the published value** (overlapping 68% intervals). The `fl` product's
MAP moved from **−14.46 on M2's ten pulsars to −14.30 on 36**, 0.16 dex towards the published
−14.28, with essentially unchanged width (0.61 → 0.71 dex) — and one hour earlier, at 35 pulsars,
it read −14.46. **That volatility is itself a result:** an FL product assembled mostly from
prior-limited marginals moves at the ~0.15 dex level as individual *constrained* pulsars enter, so
a 36-pulsar subset cannot stand in for the 83-pulsar number, and any subset amplitude must be
quoted with its pulsar count attached. It also explains why the published FL interval is as narrow
as it is: 83 weak constraints multiply to something the strongest six dominate.

**The seam-(b) propagation, measured on the 32 pulsars gated in BOTH configurations** (a like-for-
like comparison; the two rows above use slightly different sets and must not be differenced):

| on the same 32 pulsars | MAP | 68% |
|---|---|---|
| `fl` (favoured + free red) | **−14.34** | [−16.85, −14.31] |
| `table` (favoured model only) | **−14.19** | [−14.63, −14.12] |

**ΔMAP = +0.14 dex** (the table configuration reads *higher*), and the pre-registered F4 rule calls
this **significant** — not on the 0.21 dex magnitude test, which it fails, but on the exclusion
test: the table-configuration MAP (−14.19) lies **outside** the `fl` product's 68% interval, whose
upper edge is −14.31.

**The honest headline is therefore about the interval, not the peak.** Adding the collaboration's
own misspecification mitigation moves the FL CURN amplitude down by only 0.14 dex — well inside the
published ±0.21 — but it **widens the posterior enormously on the low side**, from
[−14.63, −14.12] to [−16.85, −14.31], and drags the median from −14.26 to −14.90. That is a
measurement of exactly the trade the paper states it is making ("at the expense of lowering our
sensitivity to a CURN") and, as far as we can find, nobody has published its size. It also says
that the two model choices agree on *where* the common signal is and disagree on *how confidently
it is there* — which is the same shape as Lam et al. (2026)'s NANOGrav result that model choice
moves parameters more than significance, arrived at from the opposite direction.

**The M2 top-10 sub-product (registered comparison F3(i)) is NOT yet re-covered and is reported as
such.** M2's ten best-timed pulsars are precisely the array's heaviest models, and this campaign's
schedule pushed them behind the seam-critical set: only 4 of the 10 have a gated `fl` run and 3 a
gated `table` run, with just **2 in common** (J1713+0747, J1946-5403). Those give `fl` MAP −14.29
(4 psr) and `table` MAP −14.25 (3 psr), and a 2-pulsar seam-(b) shift of +0.04 dex — numbers too
thin to compare against M2's −14.46/−14.53, and quoted here only so the gap is on the record rather
than silently omitted. The like-for-like seam-(b) comparison is the 32-pulsar one above.

**Pre-registered scope statement (F5), unchanged.** This establishes that an independently
implemented likelihood on public data reproduces the collaboration's common-signal amplitude scale
and quantifies how that scale moves under a model choice the collaboration itself flags. It does
**not** establish the detection (no Bayes factor computed), the spectral characterisation (γ fixed
at 13/3 throughout), anything about spatial correlations (no HD, no CW — still behind the sparse
stack), or the 83-pulsar number itself: **at this snapshot the array is 48/83 gated, so the
83-pulsar FL amplitude of item 4 has NOT been reached.** The 36-pulsar product is reported as a
36-pulsar product.

## 9. Write-up scoping — venue, bar, and whether the evidence clears it

*(Scoping only; no draft written, nothing submitted. Section numbered ahead of the results so the
assessment can be read against them.)*

### 9.1 What is actually new here

Three things, in decreasing order of novelty:

1. **An independent, from-scratch reproduction of a PTA's published per-pulsar noise table from
   its public data, with a pre-registered agreement criterion.** No such paper exists for any PTA.
   Searches over the MPTA literature and the citing work return data-release papers, the
   collaboration's own follow-ups (e.g. the IPS-informed heliospheric modelling of Mishra et al.
   2026, arXiv:2607.09004, which re-models the solar wind but does not re-derive the noise table),
   and methodological work on priors — but no outside reproduction.
2. **A measurement of how much of the published table is prior-determined rather than
   data-determined**, with the specific, checkable consequences: 66/83 A_13/3 rows prior-limited,
   7 γ_SW rows outside the standard prior, 26/588 MAPs outside their own intervals.
3. **The propagation into the common-signal amplitude** under the collaboration's own two model
   choices.

### 9.2 The prior art that constrains the claim (and must be cited)

- **Goncharov & Sardana 2025** (MNRAS 537, 3470; arXiv:2409.03661), *Ensemble noise properties of
  the EPTA*: shows that noise-prior misspecification biases the GWB strain amplitude and offers
  hyperparameter marginalisation as the fix. The general claim "priors matter for PTA GW results"
  is therefore **already published** — this work cannot claim it as new. What is new is the
  per-table, per-parameter measurement of *how much* of a specific published table is prior-driven.
- **Lam et al. 2026** (ApJ, submitted 2025-06, revised 2026-05; arXiv:2506.03597), the NANOGrav
  J1455-3330 DM-modelling case study: a single pulsar's noise-model choice, its effect on GW
  parameters, 16 pages in ApJ. This is the closest genre precedent and it establishes the venue
  bar — a *one-pulsar* model-choice study is an ApJ paper when done by insiders. Their headline
  ("the significance does not change but the recovered parameters do") is also the most likely
  shape of our seam-(b) result, and must be engaged with directly rather than rediscovered.
- **van Haasteren 2024**, *PTAs Require Hierarchical Models* (ApJS): the structural argument
  behind the same point.
- The MPTA papers themselves are scrupulous about the limitation: the noise-table caption warns
  that some MAPs fall outside their intervals, and §Impacts of noise misspecification measures the
  CURN shift under a deliberately misspecified model. **Any write-up has to open on those
  admissions and position itself as quantifying them, not as discovering them.** That is the
  difference between constructive criticism and a complaint, and it is also simply what the
  evidence supports.

### 9.3 Venue options, honestly ranked

| Venue | Fit | What it would need |
|---|---|---|
| **MNRAS / ApJ full paper** | The natural home if — and only if — the array is complete and the CURN measurement lands (either a real shift or a tight null). ~15–20 pages: reproduction, two seams, CURN propagation, and the reproducibility recommendations. | 83/83 (or a stated, unbiased subset) through all three variants; every miss diagnosed; the γ_SW prior check closed; a public code + chain release with a DOI. |
| **MNRAS Letter / ApJL** | Only if the CURN shift is **significant**. A null does not carry a letter. | the shift, plus a compact reproduction as support. |
| **RNAAS** | Fits the *table audit* alone (26/588 MAPs outside their intervals; 66/83 A_13/3 prior-limited; 7 γ_SW unreachable) — one table, ~1,000 words, no sampling needed. Non-peer-reviewed. | nothing further; this part is already complete and self-contained. |
| **A methods/software note** | The three environment defects (the enterprise varying-basis phi-cache bug, the e_e numpy-2 jump proposals, the ELL1H/TCB refit issue) are real and reusable, but they belong in issue trackers, not a paper. | upstream reports (Matthew's call — outward-facing). |

### 9.4 The bar, stated as falsifiable conditions

A full paper is justified **iff all four hold**:

- **B-1 Coverage.** The reproduction covers the whole array, or a subset whose selection is
  demonstrably independent of the outcome (our shortest-first schedule is *not* — it correlates
  with model complexity, which is why the seam-critical pulsars were promoted to the head of the
  queue; any partial result must report that explicitly).
- **B-2 A quantitative headline the collaboration has not published.** Either the CURN amplitude
  moves measurably between the two model choices, or it demonstrably does not — the null is
  publishable, but only if it is *tight* (a 68% interval narrow enough to exclude the shifts the
  literature worries about, i.e. ≲ 0.2 dex).
- **B-3 The criticism is constructive and fair.** Every claim framed against the paper's own
  admissions, with the fix stated (tabulate the priors; quote A_Chrom at the decorrelating
  reference frequency; label the A_13/3 column as prior-limited where it is).
- **B-4 Reproducibility of the reproduction.** Code, priors, and chains released with a DOI — a
  paper criticising undocumented priors that does not publish its own would be self-defeating.

### 9.5 Verdict on whether the bar is cleared

**Not yet — and the gap is coverage, not evidence.** Against the four conditions of §9.4:

- **B-1 Coverage — FAILS today.** 48 of 83 pulsars are gated, and the covered set is deliberately
  enriched in the hard models. That enrichment is defensible and stated, but it is not a
  publishable sample: the paper's central claim is about *a published table*, and a reproduction of
  half of it invites the obvious question about the other half. This is a compute problem with a
  known cost (§10), not a scientific one.
- **B-2 A quantitative headline — PARTIALLY MET.** The seam-(b) propagation is measured
  (ΔMAP +0.14 dex, interval [−14.63,−14.12] → [−16.85,−14.31]) and it is a *width* result rather
  than a *shift* result. That is publishable and is not in the literature, but it is not a letter:
  it does not overturn the MPTA amplitude, it prices its confidence. The 68% width criterion of
  B-2 (≲0.2 dex for a tight null) is **not** met — our `fl` interval is 0.71 dex wide, because
  36 pulsars is not 83 — and the product moved 0.16 dex when the 36th arrived.
- **B-3 Constructive and fair — MET.** Every claim here is framed against the paper's own
  admissions and comes with a fix: publish the priors (§5 shows 7 rows are otherwise
  unreproducible), quote A_Chrom at the decorrelating reference frequency (§7.1: a factor 2.2 in
  precision for free), and label the A_13/3 column as prior-limited where it is (§4: 66 of 83).
  Two of our own earlier readings were corrected by the measurement (M2's J1017 "prior finding" and
  M2's 1.3 dex J1600 claim) — the criticism was applied to ourselves first.
- **B-4 Reproducibility of the reproduction — MET in substance, pending in form.** Priors, models,
  parser and harness are all in `scripts/`; chains and summaries are on disk. A citable archive
  (Zenodo DOI) is a human step and is not done.

**Recommended venue if and when B-1 and B-2 close: one MNRAS/ApJ paper**, framed as *"How much of a
PTA noise table is a measurement?"* — the reproduction as the method, the three reader statements
as the result, the CURN width as the consequence. **Available today without any further compute:
one RNAAS note on the table audit alone** (26/588 MAPs outside their own intervals; 66/83 A_13/3
prior-limited; 7 γ_SW values outside the standard prior) — that part is finished, self-contained,
and needs one table and about a thousand words. It is also the part most likely to change practice,
because the fix costs the collaboration two lines of caption.

**What would change the verdict to "clears the bar":** finishing the array (45 → 83 in all three
configurations), which §10 prices at roughly 60–100 further core-hours; and re-running the FL
products on the full set, where the `fl` interval should tighten by roughly √(83/36) ≈ 1.5× and the
comparison becomes a real test rather than an indication.

## 10. Economics, re-measured at scale, and the recommended M4

### 10.1 What the all-83 campaign actually costs (M2's projection was optimistic)

M2 measured the top-10 and concluded the all-83 noise campaign was "an overnight job". Running it
says otherwise, and the reason is instructive:

- **Measured: 86 CPU-hours consumed** to gate 48 of 83 noise runs plus 33 `table` and 36 `fl` runs,
  on 16 physical cores (AMD Ryzen 9 9950X3D, SMT2). Throughput scaled essentially perfectly with
  worker count at 1 BLAS thread each — 15 concurrent runs delivered 190 it/s against 183 it/s
  predicted from isolated single-core benches, i.e. **no contention penalty**; 2-thread BLAS was
  *worse* than 1-thread at these matrix sizes.
- **The gate, not the likelihood, is the cost driver.** M2 sized the campaign from eval times and
  a 133k-iteration target. In practice the binding criterion is the M1/M2 **absolute** stability
  tolerance (0.1 dex on log10 amplitudes) applied to **prior-limited A_13/3 posteriors 3 dex wide**
  — it demands the running median be stable at ~3% of the posterior width, which is a slow
  random walk. Gated runs needed a median of **111,760** raw post-burn iterations and up to
  213,760; the 24 started-but-ungated runs sit at a median of 58,885.
- **Remaining cost to finish the array:** the 38 pulsars not yet gated are the expensive tail
  (median eval 63 ms over the started set vs 34 ms over the gated set). Extrapolating at the
  measured throughput: **≈ 60–100 further core-hours** for the noise campaign, plus ≈ 20–30 for
  the dependent `table`/`fl` runs. On this box that is one to two further overnight sessions —
  not one.
- **Post-hoc diagnostic, declared:** under a scale-relative stability rule
  (|Δmedian| ≤ max(registered tol, 0.1 × 68% width)) **52 rather than 48 runs would clear** — the
  absolute tolerance is costing about 4 pulsars' worth of compute at this snapshot, and the
  parameter holding the gate on the ungated runs is an amplitude in 8 cases and a spectral index
  in 7. A future campaign should register the relative rule; M3's statistics stand as registered.

### 10.2 Recommended M4

1. **Finish the array.** Re-issue the three campaigns (§11) until 83/83 in all three
   configurations. Everything is checkpointed; nothing needs re-deriving. This single step turns
   the §9.5 verdict from "not yet" to "clears the bar" for B-1, and shrinks the `fl` CURN interval
   by roughly √(83/36) ≈ 1.5×, which is what B-2 needs.
2. **Register the relative stability gate** (and an effective-sample-size statistic) before it,
   so the compute goes into pulsars rather than into random-walking medians of unconstrained
   parameters.
3. **Widen γ_SW to the library default across the 26 SW_Full pulsars** — the supplementary check
   (§6.4) shows the campaign's only substantive misses close when it is; run it as a registered
   variant, not a post-hoc one, so the agreement statistic is prior-fair.
4. **Then, and only then, the write-up.** The RNAAS table-audit note (§9.5) is separable and
   ready now if Matthew wants a short outward product first — it needs no further compute, but it
   is a submission and therefore his call.
5. **Deferred, unchanged from M1/M2:** the full-PTA CURN posterior (2.5–5 d background), and all
   Hellings–Downs / continuous-wave work until the sparse stack lands.

## 11. Running and resuming this campaign (operational record)

Everything is checkpointed and idempotent; re-running a launcher **resumes** rather than restarts,
because `scripts/m3_campaign.sh` skips any pulsar whose summary already reports `gate_met`, and the
harness resumes each chain from disk.

```
# one-off preparation (already done; re-runnable)
bash scripts/m3_prepare_all.sh                 # A1 + TDB pars, all 83
python scripts/m3_parse_tables.py              # published tables -> JSON (+ parser acceptance)
bash scripts/m3_bench_all.sh noise             # every model builds; eval-time bench

# the three campaigns (safe to re-issue at any time)
NPROC=20 THREADS=1 CHUNK_MIN=5 ORDER_FILE=logs/m3/order_priority.txt \
  bash scripts/m3_campaign.sh noise
bash scripts/m3_rolling.sh table t1            # follows the gated noise runs
bash scripts/m3_rolling.sh fl f1

# analysis, on whatever coverage exists
bash scripts/m3_pipeline.sh
```

Two operational notes that cost time to learn and are worth keeping:

- **`pkill -f <pattern>` matches the invoking shell's own command line** when the pattern appears
  in the command you typed, so a "kill the campaign" one-liner kills the session that issues it
  (three sessions died this way). `scripts/m3_kill.sh <variant>` walks `/proc` instead and is the
  only safe way to stop a pool here.
- **Scheduling changed twice for throughput** (heaviest-first → shortest-first → seam-critical
  first). Shortest-first minimises mean completion time but correlates coverage with model
  simplicity, which would have biased both seams' samples; the final order puts the 13 free-β and
  12 red-carrying pulsars at the head precisely so that a partial campaign still measures the
  seams. The relaunches mean the pre-registered **300-min wall cap applies per launch, not
  cumulatively** — it is a resource criterion, not a scientific one, and the gate itself
  (iterations + stability + acceptance floor) is unchanged, but it is recorded here rather than
  left implicit.
