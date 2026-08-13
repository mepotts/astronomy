# M28 — the audit: three new tests, one real defect, and what survives

Asked for: the primary-star null control, a common-mode check, and a full scrutiny of
the code, logic and methods "as a true astronomer would". This is what came back.

Headline: **no published conclusion is retracted.** Two of the three new tests
*strengthen* the CD-35 2722 B detection with numbers it did not previously have. One
real defect was found — in the error bars on the second-satellite refutation, not in
its sign. Six smaller issues are logged with their blast radius.

New machinery, all committed: [`m28_nullcal.py`](scripts/injection/m28_nullcal.py),
[`m28_limitcal.py`](scripts/injection/m28_limitcal.py),
[`m28_jackknife.py`](scripts/injection/m28_jackknife.py),
[`m28_contam.py`](scripts/injection/m28_contam.py).

---

## 1. The common-mode test — the 171 d signal is unique to CD-35 2722 B

The worry: the archival sampling puts BERV power 0.66 at the signal period, and 171 d
sits near half a year. If ~171 d were a property of the CRIRES+ companion-programme
cadence or the telluric season rather than of CD-35 2722 B, it should appear in other
targets reduced by the identical pipeline.

Every reduced series was pushed through the same recipe (per-order median/clipped
combine, per-night binning, internal 3x-spread screen, dBIC landscape over 5–460 d,
with and without the BERV covariate). Targets with >= 6 epochs:

| target | n | span (d) | dBIC near 171 d (+BERV) | p |
|---|---:|---:|---:|---:|
| **CD-35 2722 B** (per-nodding) | 17 | 466 | **+27.94** | **0.0005** |
| **CD-35 2722 B** (combined route) | 17 | 466 | **+23.80** | **0.0005** |
| eta Tel B | 17 | 815 | −3.06 | 0.61 |
| beta Pic b (v2 template) | 11 | 813 | −1.76 | 0.54 |
| beta Pic b (v3, masked orders) | 11 | 813 | −1.68 | 0.55 |
| HD 1160 B | 8 | **41** | +9.27 | 0.045 |

**eta Tel B is the ideal control** — same H1567 setting, same eleven-order recipe, same
pipeline, same observing seasons, *longer* baseline, same number of epochs — and it
carries **negative** dBIC at 171 d. beta Pic b agrees on two independent reductions.

The HD 1160 B entry is not a counterexample: its baseline is **41 days**, so a 171–182 d
period is an extrapolation 4x beyond the data, and the power appears only when the BERV
column is added. It supports no claim (HD 1160 B never carried one) but it does expose a
code defect — see §6.3.

**Verdict: the 171 d signal does not reproduce anywhere else. It is a property of
CD-35 2722 B, not of the cadence.** This is a new result and belongs in the paper.

## 2. The detection's significance, calibrated for the first time

dBIC = +43 was quoted as a maximum over a 4000-period search. The BIC penalty charges
for parameters, not for the search, so that number was never a significance. Permutation
null (epoch times, BERV column and value distribution held fixed; base-model residuals
shuffled; 2000 realizations):

| combine | variant | observed dBIC | permutation p | noise-only max dBIC (95th pct) |
|---|---|---:|---:|---:|
| median | plain | +43.16 | **0.0005** | +18.90 |
| median | +BERV | +27.94 | **0.0025** | +17.77 |
| clip | plain | +39.91 | **0.0010** | +18.11 |
| clip | +BERV | +26.85 | **0.0055** | +19.70 |

Two things follow:

1. **The detection survives its own search space** at p <= 0.006 in every combine, and
   p = 0.0005 (the 2000-permutation floor) without the BERV term.
2. **A signal-free series with this sampling reaches dBIC ~ 19 as its best peak 5% of
   the time.** Any dBIC in the teens is not evidence. This retroactively justifies —
   with a number rather than a judgement — the project's refusal to claim eta Tel B's
   "+14.9 at 5.7 d" comb (M15 §4) and beta Pic b's long-period structure.

## 3. Leave-one-out: no single night carries the detection

The standard referee question at n=17. Dropping each epoch in turn:

- **plain:** peak within 6% of 171 d in **17/17**, dBIC +38.5 to +45.7
- **+BERV:** peak within 6% of 171 d in **17/17**, dBIC +23.9 to +29.8

No epoch is load-bearing. The largest single-epoch effect is *positive* (dropping
BJD 2460666.79 raises dBIC to +45.7).

## 4. The eta Tel B limit re-derived — it holds

M15 defines detection as `dBIC >= 10 AND the peak ranks first`. The bar of 10 sits well
inside the noise (§2), which looked like a problem. Measuring the false-alarm rate of
the criterion **as written** shows the rank-1 clause carries the protection:

| P_inj (d) | FAP at bar=10 | bar=15 | bar=20 |
|---:|---:|---:|---:|
| 20 | 0.0085 | 0.0000 | 0.0000 |
| 60 | 0.0025 | 0.0000 | 0.0000 |
| 120 | 0.0010 | 0.0000 | 0.0000 |
| 200 | 0.0020 | 0.0000 | 0.0000 |
| 300 | 0.0015 | 0.0000 | 0.0000 |

FAP <= 0.85% everywhere — a noise peak must both clear the bar *and* land inside the
narrow window around the specified period. Re-deriving K90 on a **3x finer grid**
(36 phases vs 12, 19 amplitudes vs 8) reproduces the published limit exactly:

| P (d) | K90 published | K90 recomputed | m sin i (M_Jup) |
|---:|---:|---:|---:|
| 20 | 300 | 300 | 0.51 |
| 60 | 250 | 250 | 0.61 |
| 120 | 250 | 250 | 0.77 |
| 200 | 300 | 300 | 1.09 |
| 300 | 300 | 250 at a stricter bar | 1.25 -> 1.04 |

**The limit stands, and is mildly conservative at P = 300 d.** Leave it as published.

## 5. The primary-star control — reframed by the archive, then done a better way

BUILD-PLAN §M2 planned CD-35 2722 A as a null control ("300 public CRIRES+ frames").
The archive says that control cannot be built as designed:

| OBJECT | programme | frames | **nights** | slit | note |
|---|---|---:|---:|---|---|
| CD-35 2722 (primary) | 114.27LL.002 | 300 | **2** | w_0.2 | Oct 2024; the M26 "deep pair", thermal-IR |
| CD-35 2722 (primary) | 110.23RW.002 | 8 | **1** | w_0.4 | Hoy pilot, 2023-01-01 |

**Three nights total across two settings — no periodicity control is possible.** The
common-mode question §1 answers is the one that control was meant to answer, and §1
answers it better (17 epochs over 815 d on a same-setting target).

What the primary *can* be measured for was done instead, and it fills the one blank in
the figure-by-figure appendix. H26's Fig. 3 estimates stellar contamination from
slit-viewer PSF fits; the draft currently says "not attempted". The nodding **slit
function** measures the same thing directly: the extraction swath spans the full slit
(order height 179.8 px x 0.056"/px = **10.07"**, sampled at 0.0197"/point), the slit
PA is pinned at **POSANG = 153.1 deg on all 18 nights** with a 6" nod throw, so the
primary at 3.17" lands **161 points** from the companion trace.

**Result: no primary peak is detected on any night.** Ratio at the primary position to
the companion peak: median **0.0006**, versus a profile noise of 0.0072 — 0.1 sigma.
Per-night 3-sigma upper bounds run 1–11% (median 2.5%), i.e. **tighter than, and
consistent with, H26's ~15% worst-night estimate**. The primary's core is outside the
0.2" slit, as the geometry implies.

Caveat to state when publishing this: the profile median is subtracted, so this bounds a
*resolved* second trace, not a smooth halo pedestal. It is complementary to the
slit-viewer method, not a replacement.

One loose end, reported because it did not work out: BJD 2460604.814 — the single epoch
both this project's internal screen and H26's table reject — has the **highest**
measured ratio of the 18 nights (0.0187), but only at 2.0 sigma, and its seeing was the
**best** of the campaign (IA FWHM 0.60"). Contamination does not explain why that night
is bad. Recorded as unexplained.

## 6. Code and method audit

### 6.1 REAL DEFECT — the second-satellite evidence errors are underestimated

`nested_orbits.py` quotes dynesty's internal `logzerr` (~0.24–0.27 everywhere). The
**seed-to-seed scatter is much larger**:

| configuration | seed 0 | seed 1 | spread | quoted error | ratio |
|---|---:|---:|---:|---:|---:|
| linjit / eccP | −4.64 | −2.23 | 2.42 | 0.27 | **9x** |
| linjit / freeP | −4.35 | −2.88 | 1.47 | 0.27 | 5x |
| default / eccP | −5.41 | −6.63 | 1.23 | 0.27 | 5x |
| default / fixP | −1.42 | −1.96 | 0.55 | 0.24 | 2x |
| default / freeP | −3.23 | −3.65 | 0.42 | 0.27 | 2x |
| logK / freeP | −2.32 | −2.30 | 0.02 | 0.27 | ok |
| logK / eccP | −0.83 | −0.79 | 0.04 | 0.27 | ok |

Two seeds per cell cannot estimate this. **Table 3 of the draft, as written, is not
defensible** — a referee will notice that two seeds differing by 0.55 carry quoted
errors of 0.24. The sign is unaffected (10/10 negative), but the error bars must be the
empirical scatter over seeds, not dynesty's internal estimate. Rerun at 10 seeds per
configuration plus an nlive=2000 convergence check: results in §7.

### 6.2 The injection gate validates the fitter, not template absorption

`mktpl.py` shifts the **already-built** template per epoch. That is the right call —
shifting the observation moves the tellurics too, which a real Doppler shift does not do
(and viper's telluric-anchored solution absorbs ~92% of it). But it means the gate
measures *"given this template, does the fitter transmit a velocity?"* — not *"if a real
signal were present, would the self-built template have absorbed part of it?"*

This is a caveat, not an error, and it is bounded: M11 measured 41% absorption with a
*different* recipe on GJ 229 B, and M14's external check on CD-35 (slope 1.19–1.34
against the published RVs) shows the adopted recipe absorbs nothing. **Every limit in
the project should state that its transmission is validated at the fitter stage and
externally verified only on CD-35.** The PDS 70 nine-night rejection shows the gate does
catch template pathology when it is severe.

### 6.3 The period grid is not bounded by the baseline

`blind_search.py` searches 5–460 d regardless of the series' span. On HD 1160 B (span
41 d) that extrapolates 11x beyond the data and manufactures the +9.3 entry in §1. No
published claim depends on it — every claim-bearing series spans >= 466 d — but the grid
should be capped near the baseline, and the affected entry annotated.

### 6.4 Unweighted least squares throughout the search

`bic_landscape` and `bic_peak` use `np.linalg.lstsq` with no per-epoch weights, so a
70 m/s night and a 700 m/s night count equally. Harmless where epoch quality is uniform
(CD-35, eta Tel), potentially lossy where it varies 70x (HD 1160). Worth a weighted
variant as a robustness column; not a correction.

### 6.5 Small-n error bars are quoted too precisely

`m17_score.py` reports the epoch-to-epoch scatter of the recovery ratio as the gate
uncertainty. At n=2 (2M0103AB b, HD 19467 B, AB Pic b, AF Lep b) "gates 100 +- 0%" is
two numbers that happened to agree. Quote the range, or a bootstrap, not a std at n=2.

### 6.6 A numerical inconsistency in the draft

§4 reads "K = 380–470 m/s against the published 306, a **20–40%** overshoot". 470/306
is **+54%**, and 380/306 is +24%. Either the amplitude range or the percentage is wrong.
The regression slope re-measures cleanly at **1.19–1.34** across all six combines (the
draft quotes 1.19–1.24, which is the adopted-combine subset). Fix before submission.

### 6.7 Verified clean

- Eq. (1) in `score.py` matches the published formula, including the weighted mean.
- The nested-sampling likelihood (`s2 = erv^2 + jit^2`) is a correct Gaussian-with-jitter.
- Priors are shared between the one- and two-satellite models wherever a parameter is
  shared, and the model pairs are dimension-matched (6 vs 6 in `fixP`).
- The eccentric one-satellite model carries an omega/tp degeneracy at low e that
  *penalizes* it — the model that wins does so despite a handicap. Conservative.
- Order-combine broadcasting in `blind_search.py` and `m15_limit.py` is equivalent.
- The headline table re-runs exactly: rms_pub 90 (mean), 70–76 (centred robust),
  r = 0.93–0.98, n = 17.

## 7. The second satellite at honest error bars

82 independent sampler runs: 10 seeds per configuration at nlive = 500, plus 4 seeds per
configuration at nlive = 2000 as a convergence check.

| priors | pairing | nlive | ΔlnZ (mean ± s.e.) | run-to-run σ | quoted | ratio |
|---|---|---:|---:|---:|---:|---:|
| uniform | periods fixed | 500 | −1.83 ± 0.08 | 0.25 | 0.24 | 1.1x |
| uniform | periods in windows | 500 | −4.60 ± 0.27 | 0.87 | 0.27 | **3.3x** |
| uniform | both eccentric | 500 | −5.51 ± 0.69 | 2.18 | 0.27 | **8.1x** |
| jitter U(0,300) | free periods | 500 | −3.82 ± 0.20 | 0.62 | 0.27 | 2.3x |
| jitter U(0,300) | both eccentric | 500 | −3.37 ± 0.38 | 1.19 | 0.27 | **4.4x** |
| K log-uniform | free periods | 500 | −3.77 ± 0.30 | 0.96 | 0.27 | 3.5x |
| K log-uniform | both eccentric | 500 | −1.42 ± 0.44 | 1.40 | 0.27 | **5.3x** |
| uniform | periods fixed | 2000 | −1.50 ± 0.24 | 0.49 | 0.12 | **4.1x** |
| uniform | periods in windows | 2000 | −4.46 ± 0.31 | 0.62 | 0.13 | **4.7x** |
| uniform | both eccentric | 2000 | −3.49 ± 0.27 | 0.54 | 0.13 | **4.1x** |

**Three findings.**

1. **The conclusion holds and is now properly bounded.** Every configuration's mean is
   negative, from −1.42 to −5.51. Of 82 individual runs, **81 are below zero**; the
   single exception reaches **+0.91**, still far short of the claimed +2.62. The old
   "10/10 negative" phrasing was true of the runs then in hand but is superseded — the
   draft now states the 81/82 figure.

2. **More live points do not fix it — they make the understatement worse.** At nlive =
   2000 the internal estimate shrinks to ±0.12–0.13 exactly as its N^(−1/2) scaling
   demands, while the empirical scatter stays at 0.49–0.62. The ratio therefore *rises*
   to 4–5x. The internal number measures the sampler's accounting of its own
   integration, not the dispersion of answers the procedure returns.

3. **The nlive = 500 `eccP` row was partly unconverged.** Its scatter of 2.18 and mean of
   −5.51 tighten to 0.54 and −3.49 at 4x live points, so the original −5.41/−6.63 pair
   sat in the tail. The direction is unchanged; the magnitude was overstated. This is
   the one place where the previously published numbers were not merely
   under-uncertain but off-centre, and the draft now carries the converged values
   alongside.

**What this does to the disagreement with H26** — and it is more collegial than it
sounds. Their +2.62 rests on lnZ uncertainties of ±0.70 and ±0.69, the same class of
internal estimate, plausibly understated by a similar factor. If so, **+2.62 is not
significant on its own terms**, before any argument about priors, and consistent with
their own word "tentative". We cannot test their sampler and do not claim to. The
falsifiable version is a question they can answer in an afternoon: how many independent
runs stand behind +2.62, and what is the scatter among them? That is now the lead ask in
`docs/author-query-draft.md`.

Drafted into the manuscript as Table 3 (rebuilt with mean ± s.e. and run-to-run σ as
separate columns) and a new §5.1.
