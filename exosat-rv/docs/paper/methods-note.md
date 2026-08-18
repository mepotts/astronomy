# Flat is not quiet: four silent failure modes in companion-side radial velocimetry

*Matthew Potts · independent analysis · draft 2026-08-13*

*Methods note. Target venue: A&A or MNRAS methods section. Written from milestones M9–M29 of the exosat-rv archival reproduction project; every number below traces to a document in that repository, cited inline as (M-n §s).*

---

## Abstract

Companion-side radial velocimetry — measuring the reflex motion of a directly imaged
brown dwarf or giant planet from its own spectrum — now has one claimed detection and a
growing set of upper limits. It is an unforgiving regime: the signal sits well below the
per-spectrum noise, the wavelength reference is telluric, and the stellar template is
usually built from the target's own data. We describe four ways a measurement of this
class goes wrong without leaving a visible trace, each with a worked example from a
from-raw reproduction of a published CRIRES+ detection and from an eleven-system
archival survey run through a single pipeline.

**(1) A flat series is not a quiet series.** A template that has lost its stellar lever
returns a tighter, better-looking and entirely meaningless upper limit. Ours did: a
rebuilt nine-night template on PDS 70 improved every visible diagnostic and transmitted
**−62% ± 197%** of an injected Keplerian.

**(2) A precision statistic can be invariant to its own signal.** The per-epoch
dispersion statistic in use in this subfield is an error-weighted dispersion of
per-order velocities *within* an epoch. A common-mode Doppler shift cancels from it
exactly. That makes it safe to optimise, and unsafe to quote as accuracy: it moved
against our two largest genuine improvements while agreement with an external reference
series improved by ~40%.

**(3) A search maximum is not a significance.** ΔBIC charges for parameters, not for the
size of the search. Permutation-calibrated on the true cadence, our detection survives
at *p* = 5×10⁻⁴ — and the same null shows that a *signal-free* series with this sampling
reaches ΔBIC ≈ 19 as its best peak 5% of the time.

**(4) A sampler's internal evidence error is not its reproducibility.** Measured over 82
nested-sampling runs on a real published RV table, run-to-run scatter in ΔlnZ is
**1.1–8.1×** the sampler's internal estimate, and quadrupling the live points makes the
understatement *worse*, not better.

The four have one structure in common: each makes a result look better than it is, so
none of them self-report. We give the checks that catch them, and the observing-strategy
change the last of them implies.

---

## 1. Introduction

Doppler monitoring of a directly imaged companion — using the companion's own spectrum to
detect a satellite or a second companion orbiting it — was proposed by Vanderburg et al.
(2018), applied to HR 8799 by Vanderburg & Rodriguez (2021) and to HR 7672 B by Ruffio et
al. (2023), forecast in the CRIRES+ era by Lazzoni et al. (2022), and pursued by Horstman
et al. (2024) on GQ Lup B and by Kral et al. (2026) with VLTI/GRAVITY on HD 206893 B. Hoy
et al. (2026, hereafter H26) reported the first detection: a *P* ≈ 171 d,
*K* ≈ 306 m s⁻¹ signal in CD-35 2722 B, interpreted as a ~0.92 M_Jup satellite, with
tentative evidence for a second, smaller companion.

This note is not about any one of those results. It is about the class. We reproduced H26
from the raw CRIRES+ frames with an independently configured extraction, then applied the
validated pipeline to every other companion with usable public CRIRES+ data — eleven
systems, yielding one confirmation, one contradiction, four limits, one contamination case
and four honestly data-limited entries (M23 §5). H26's primary result reproduces: a blind
period search with no reference to the published values recovers *P* ≈ 169–171 d as the
rank-1 peak, and it survives a barycentric-velocity (BERV) nuisance term (M14 §6). We use
that work as the motivating case throughout, and where our conclusions differ from H26's we
say so with the arithmetic attached; but none of what follows is an argument about that
paper.

What the work produced over and above the science is a catalogue of ways this measurement
fails *quietly*, and in every case the failure improved the appearance of the result. Six
separate times an internal statistic moved the wrong way against an external check
(M14 §6). Three times a change that improved the science target was caught only because a
positive control collapsed (M11 §4). Once, a template rebuild tightened an upper limit by
deleting the pipeline's ability to measure velocity at all.

The four sections below are ordered by how expensive each failure is to discover after
publication.

---

## 2. The measurements these lessons come from

All spectra are public ESO archive holdings. RVs are extracted with `viper` (Köhler et al.
2025) in gas-cell-free CRIRES+ mode, forward-modelling each spectral order against a
telluric-free stellar template built from the observations themselves; reductions use
`cr2res` 1.6.10 from raw frames, and reproduce ESO's own archived products to 42 m s⁻¹ in
the final RV (M12 §9b). The CD-35 2722 B series is 18 archival H1567 nights over 466 d;
η Tel B is the same instrument setting over 815 d; the remaining systems span H- and K-band
settings (M20, M23).

Two properties of the regime matter for everything below.

**The wavelength reference is the sky.** With no gas cell in the beam, telluric lines are
the only absolute wavelength anchor. Deliberately weakening that anchor — masking the
tellurics, downweighting them, or fitting water alone — multiplies the per-frame velocity
error by ~9× (M12 §9b.3). Any operation that moves the tellurics relative to the stellar
spectrum, including a naively implemented signal injection (§3.3), is therefore an
operation on the reference frame itself.

**The template is built from the target.** There is no external standard star at the right
spectral type, brightness and slit geometry. Self-templating is not a choice but a
constraint, and it couples the thing being measured to the thing measuring it in a way that
has no clean analogue in stellar RV work.

---

## 3. Failure I — A flat series is not a quiet series

### 3.1 The worked example: PDS 70

Six CRIRES+ K2166 nights over 426 d on PDS 70 gave a flat series: night-to-night scatter
130 m s⁻¹, χ² = 3.5/5 against a constant, injection gates at 99% ± 1–2, and a variance
exclusion of *K*₉₀ ≈ 150 m s⁻¹ for *P* ≤ 200 d, i.e. ~3 M_Jup on close companions of the
star (M20 §3). Six further archival products were then recovered, growing the series to
nine nights over 483 d, and the template was rebuilt over all fourteen files. The rebuild
looked like the better result: 150 m s⁻¹ night-to-night over a baseline 13% longer, and a
tighter 90% amplitude limit than the six-night state it replaced (M23 §4).

The injection arm returned **−62% ± 197%** recovery, with systematically *negative*
per-order recoveries. The enlarged template had converged on a solution with no stellar
lever: velocity information was no longer being transmitted through the fit at all. A
series that measures nothing is, necessarily, flat — and a flat series with a long baseline
and small formal errors produces the tightest upper limit in the table.

The rebuild was rejected on the gate and the validated six-night state was re-staged and
reproduced bit for bit (`m21_restore.sh`). Nothing about the nine-night series looked
wrong. It looked like the best result the target had ever produced.

**Rule.** Gate *every* template iteration against injection recovery, not just the final
one, and keep a bit-for-bit restore path to the last validated state. An upper limit is a
statement about the pipeline's sensitivity as much as about the sky, and it is only as
good as the most recent measurement of that sensitivity.

### 3.2 The same failure, twice more, with different mechanisms

The PDS 70 case is the cleanest instance but not the first. Two earlier ones are worth
recording because the mechanisms differ and the symptom does not.

**Weighting orders by their empirical scatter.** Weighting each spectral order by 1/rms²
measured from the data gave the best number this project had seen on the science target:
combined scatter 823 → 514 m s⁻¹, a 1.6× improvement. On a known 12.1-day binary used as a
positive control, the same weighting took Δχ² from 63.8 to 5.8 and the recovered
semi-amplitude from 6165 to 1825 m s⁻¹ (M9 §5). The reason is circular: *for a target with
a real signal, an order's scatter partly is the signal*, so inverse-scatter weighting
downweights exactly the orders carrying it. On a target with no detection that pathology is
invisible; it presents as clean noise suppression.

Weighting by the pipeline's *formal* errors instead fails in the opposite direction —
823 → 2620 m s⁻¹ — because the most pathological order in the set carried both the largest
scatter (4130 m s⁻¹) and the smallest formal error (101 m s⁻¹), and so received ~20× the
weight of a well-behaved order (M9 §4). Anyone reaching for
`np.average(rv, weights=1/err**2)` here will make the result worse and have no way to
notice.

**Iterating a self-built template.** Rebuilding the template by co-adding the target's own
RV-aligned spectra improved the science target from 776 to 620 m s⁻¹ and collapsed the
control: recovered amplitude 5948 → 2452 m s⁻¹ after one iteration (41% of correct), 2360
after two (M11 §3). The alignment velocities had been measured against a template that
already contained the signal, so the residual is baked into the next template and
velocities measured against it are partly the target measured against itself.

That verdict then needed a correction of its own, which is the instructive part. The control
moves by ±6–18 km s⁻¹ across its six nights; CD-35 2722 B moves by ±250 m s⁻¹ across
eighteen. Self-template absorption scales with the signal amplitude relative to the
template's epoch spread, so the control over-predicts absorption on the science target by
nearly two orders of magnitude. Measured directly on the target by injection, the corrected
configuration transmits **95% ± 7%** where the control had predicted 46% — a 7σ
disagreement (M12 §7.1, §8.3). **A positive control tells you the extraction works; it does
not transfer a quantitative bias across a 70× difference in amplitude.** Only injection into
the target's own spectra does that.

### 3.3 Two rules that the injection test itself needs

The gate is only as good as its implementation, and there are two ways to build it wrong.

**Inject by shifting the template, never the observation.** The obvious implementation —
multiply each observation's wavelength column by (1 + *v*/*c*) — moves the star *and the
tellurics* together. A real Doppler shift does not do that; the tellurics stand still.
Because the tellurics are the wavelength reference, the fit simply recalibrates the
injection away. Measured on one epoch with 1000 m s⁻¹ injected: shifting the observation
returns **+83 m s⁻¹** (92% absorbed); shifting the template by −*v* returns
**+1175 m s⁻¹** (M12 §8.1). Anyone building the harness the obvious way would measure a
pipeline 92% blind to radial velocity and conclude the extraction was broken.

**Never build a template from a single night.** A template built from one night's frames
has no barycentric lever with which to separate target lines from telluric residue, so it
drags a fraction of Earth's motion into every epoch. On β Pic b this produced a
**4712 m s⁻¹** night-to-night scatter locked to the barycentric velocity at *r* = +0.94,
with blind period peaks that collapsed under a BERV covariate. Rebuilding across all 28
frames over 813 d halved the scatter to 2466 m s⁻¹ and left *r* = +0.88 intact — which is
how we established that the residual was host starlight rather than the template (M20 §2).
The artifact and the real contamination were separable only because the template was
rebuilt.

### 3.4 What the gate does not cover — stated because it matters

Our injection harness shifts the *already-built* template per epoch. That is the correct
choice for the reason just given, but it means the gate measures *"given this template, does
the fitter transmit a velocity?"* — not *"if a real signal were present, would the self-built
template have absorbed part of it?"* (M28 §6.2). The exposure is bounded rather than
eliminated: one recipe measurably absorbed 59% on a control (M11 §3), while the adopted
recipe shows no absorption against an external reference series (regression slope 1.19–1.34
against the published RVs; M28 §6.6). Any limit derived this way should state that its
velocity transmission is validated at the fitter stage and externally verified only where
published RVs exist. Closing the gap — an injection performed *before* template construction
and propagated through the full template ladder — is in our view the most valuable single
upgrade available to this method. It has not been built here.

---

## 4. Failure II — A precision statistic invariant to its own signal

The per-epoch precision statistic in use for CRIRES+ companion RVs (Köhler et al. 2025,
Eq. 1; adopted as Eq. 1 of H26) is an error-weighted dispersion of the per-order velocities
*within a single epoch*:

```
eps_RV = sqrt[ (1/(N_o - 1)) · Σ_o eps_o⁻² (RV_o − RV̄)² / Σ_o eps_o⁻² ]
```

This is a genuinely useful statistic, and this project adopted it as an optimisation
objective for a specific and good reason. But it must not be read as an accuracy.

**The invariance.** A real radial-velocity signal is *common-mode across orders*: it shifts
every RV_o by the same amount, shifts RV̄ with them, and cancels exactly in (RV_o − RV̄).

> **The statistic is mathematically invariant to the signal it is being used to certify.**

The consequence cuts both ways.

**In its favour.** A configuration cannot improve this statistic by suppressing the
Keplerian. It can improve it only by making the orders agree, which is what a correct
forward model does. That closes, by construction, the specific trap of §3.2 — the trap that
epoch-to-epoch rms walked straight into twice. Where a signal-invariant objective exists, it
is the right thing to run a configuration sweep against, and this project's sweeps were
scored on it for exactly that reason (M12 §3).

**Against it.** Because it is computed *within* an epoch, it is blind to anything static
across the orders of one exposure and variable between exposures — per-order zero points
that drift between nights, calibration ageing, night-level systematics. Those are precisely
what limit a multi-epoch campaign. In this project the statistic moved the *wrong way*
against both of the two largest genuine improvements: 331 → 347 m s⁻¹ when template
oversampling was fixed, and 331 → 429 m s⁻¹ when the decisive second template iteration was
adopted, while the rms against the published reference series fell from 147 to 133 and then
to 85 m s⁻¹ — a ~40% improvement in external agreement (M14 §4, §6). Both changes were
adopted on the external metric and both passed injection recovery; the internal statistic
would have rejected them.

### 4.1 The ten-minute repeatability test that nearly produced a false reproduction

A related and more dangerous version of the same error is worth recording in full, because
it produced a result we briefly believed.

Nodding pairs A and B are the same object observed ~10.6 minutes apart. A 171-day orbit
moves under 1 m s⁻¹ in that time, so the true A − B difference is zero by construction and
the astrophysical signal cancels exactly — apparently an ideal signal-free noise estimator.
Swept over configurations, with an order screen on telluric-anchor strength, rms(A − B)
fell to 132 m s⁻¹, implying a per-night error of **66 ± 23 m s⁻¹** against the published
57.68 — agreement at 0.36σ (M12 §9b.4).

It was wrong. A − B probes only ten minutes. The within-epoch dispersion statistic computed
on the *same* screened frames said 563 m s⁻¹ per frame → 398 m s⁻¹ per night, six times
worse. The two can only disagree if most of the per-order spread is a static offset that
cancels in a ten-minute difference — and it is. The decisive test, comparing our from-raw
RVs night by night against the published table, measured **387 m s⁻¹**. The within-epoch
statistic had predicted 398; agreement to 3%. The 66 m s⁻¹ figure was withdrawn before it
propagated anywhere.

**Rule.** Every noise estimator is invariant to something. State what — signal, timescale,
or both — before quoting it as a precision. And where an external reference series exists it
outranks every internal proxy: every internal proxy tried in this project has been wrong by
a factor of at least six at least once.

---

## 5. Failure III — A search maximum is not a significance

Our blind period search evaluates a sinusoid-plus-covariates model on a grid of 4000
periods log-spaced over 5–460 d and reports ΔBIC at the best period. The CD-35 detection
peaked at ΔBIC = +43.16.

**That number was never a significance.** The BIC penalty charges for the number of free
parameters; it does not charge for the size of the search. A ΔBIC read off the maximum of a
4000-period grid is the maximum of 4000 correlated trials, and the correlation structure is
set by the window function of the actual epoch sampling — which, for archival companion
campaigns, is seasonal, sparse and strongly aliased.

### 5.1 Calibrating the null on the true cadence

The calibration is cheap and there is no excuse for omitting it. Hold the epoch times, the
nuisance-covariate column and the value distribution fixed; shuffle the residuals of the
base model, which is signal-free by construction and preserves the true window function;
re-run the identical search. 2000 realisations (M28 §2):

| order combine | model | observed ΔBIC | permutation *p* | noise-only best peak, 95th pct |
|---|---|---:|---:|---:|
| median | plain | +43.16 | **0.0005** | +18.90 |
| median | + BERV covariate | +27.94 | **0.0025** | +17.77 |
| clip | plain | +39.91 | **0.0010** | +18.11 |
| clip | + BERV covariate | +26.85 | **0.0055** | +19.70 |

Two things follow, and the second is the transferable one.

1. The detection survives its own search space, at *p* ≤ 0.006 in every combine and at the
   2000-permutation floor of *p* = 5×10⁻⁴ without the covariate. Supporting this, all 17
   leave-one-out subsets return the peak within 6% of 171 d, at ΔBIC +38.5 to +45.7 (plain)
   and +23.9 to +29.8 (with covariate), and the largest single-epoch effect is to *raise*
   the significance (M28 §3).

2. **A signal-free series with this sampling reaches ΔBIC ≈ 19 as its best peak 5% of the
   time.** Any ΔBIC in the teens, on a cadence of this class, is not evidence. This is a
   number rather than a judgement, and it retroactively justified this project's refusal to
   claim a +14.9 short-period feature in the η Tel B residuals and long-period structure in
   β Pic b (M15 §4, M20 §2).

Note that the calibration is specific to the sampling. It is not a universal threshold, and
a series with a different window function will have a different noise-only distribution. It
costs one shuffle loop around the search you have already written.

### 5.2 The same calibration applies to upper limits

An upper limit is defined by a detection criterion, so the criterion's false-alarm rate is
part of the limit's meaning. Our η Tel B limit uses "ΔBIC ≥ 10 **and** the peak ranks first
at the injected period" (M15 §5). A bar of 10 sits well inside the noise distribution of
§5.1, which looked like a problem. Measuring the false-alarm rate of the criterion *as
written* shows that the rank-1 clause carries the protection: FAP ≤ 0.85% at every injected
period tested from 20 to 300 d, and identically zero at bars of 15 or 20 (M28 §4). A noise
peak must both clear the bar and land inside a narrow window around the specified period.

Re-deriving the 90% amplitude limits on a 3× finer phase and amplitude grid reproduced the
published values, one period bin coming out mildly conservative. The general point:
**measure the FAP of the composite criterion you actually used, not of the test statistic in
isolation.**

### 5.3 Bound the grid by the baseline

One real defect this audit found in our own code: the search grid ran 5–460 d regardless of
the series' span. On a nine-night HD 1160 B series spanning **41 days**, that is an
extrapolation 11× beyond the data, and it manufactured a ΔBIC = +9.3 entry (*p* = 0.045) at
~171 d that appears only when the nuisance covariate is added (M28 §1, §6.3). No claim in
this project rests on it — every claim-bearing series spans ≥ 466 d — but the entry exists
in a table, and in a less careful project it would have become a result.

Two smaller items from the same audit: the search uses unweighted least squares, harmless
where epoch quality is uniform and potentially lossy where it varies by 70× (M28 §6.4); and
an injection-gate uncertainty quoted as an epoch-to-epoch standard deviation is meaningless
at *n* = 2, where "100 ± 0%" is two numbers that happened to agree (M28 §6.5).

---

## 6. Failure IV — A sampler's internal evidence error is not its reproducibility

Model comparison in this subfield is usually decided by a Bayesian evidence ratio, quoted
with the uncertainty the sampler reports internally. For nested sampling that uncertainty
derives from the information content of the run and scales as *N*^(−1/2) in the live-point count.
**It is the sampler's accounting of its own integration. It is not the dispersion of answers
the procedure returns.**

We measured the difference on a real published RV table — the 23-epoch table of H26 —
comparing a one-companion against a two-companion model with `dynesty` (Speagle 2020),
priors symmetric between models, over 82 independent runs varying only the random seed, the
prior family and the live-point count (M28 §7). At nlive = 500 the run-to-run scatter in
ΔlnZ is **1.1× to 8.1×** the internal estimate of ±0.24–0.27, worst where the model pairing is
least constrained: a single run reporting −5.5 ± 0.27 is one draw from a distribution with
σ = 2.18.

The counterintuitive part is what happens when the standard remedy is applied. Raising the
live points fourfold shrinks the internal estimate to ±0.12–0.13, exactly as its
*N*^(−1/2) scaling demands, while the empirical scatter stays at 0.49–0.62 — so the ratio
*rises*, to 4–5×. More live points tighten the number you quote without tightening the number
you would get if you ran it again. They do fix something real — the *location* of one partly
unconverged configuration moved from −5.51 to −3.49 — which is why a convergence check is
worth reporting, as a separate claim from the uncertainty.

**Rule.** Quote the run-to-run scatter over ≥ 10 independent seeds as the uncertainty on a
ΔlnZ, and report the convergence check separately. Both are cheap; the full matrix here is
minutes of CPU. The per-configuration table and the complete 82-run analysis are given in a
companion note (`docs/paper/sampler-reproducibility-note.md`, in preparation), which
independently re-derives them; they are not repeated here.

**What this does and does not say about a published result.** In our comparison every
configuration's mean is negative (−1.42 to −5.51) and 81 of 82 runs land below zero, the
single exception reaching +0.90 — against a published ΔlnZ = +2.62 ± ~1.0 favouring the
two-companion model. The sign disagreement is a scientific matter argued elsewhere. The
*methodological* point is narrower: +2.62 rests on lnZ uncertainties of ±0.70 and ±0.69,
internal estimates of the same class, and if their reproducibility resembles what we measure
for ours then +2.62 is not significant on its own terms — before any argument about priors,
and consistent with the authors' own description of that result as tentative. We cannot test
another group's sampler and do not claim to have. The falsifiable version is a question any
author can answer in an afternoon, and one we would like to see asked routinely in review:
*how many independent runs stand behind this evidence ratio, and what is the scatter among
them?*

---

## 7. What follows for observing strategy: frames per night, not nights

One further result belongs here, because it is the practical consequence of taking the
above seriously.

Every proposal in this genre, including our own, *guesses* the astrophysical RV noise floor
of a young self-luminous giant. We attempted to measure it from a homogeneous multi-epoch
sample of ~11 companions and could not, and the reason is a scheduling parameter rather
than a physical one (M29, recorded in `NEXT-DIRECTIONS.md` §A1).

The measurement requires splitting the epoch-to-epoch scatter into measurement noise and
astrophysical variability. Two noise channels were tried. **Within-night frame scatter** is
in principle ideal — frames minutes apart, across which no plausible satellite orbit moves —
but current campaigns take only **~2 frames per night**, leaving too few degrees of freedom.
The built-in control settles it: CD-35 2722 B, which carries a known signal of several
hundred m s⁻¹, resolves its own excess at only **1.4σ**. A method that cannot recover a
known signal cannot certify a null, so every other object's "no excess" is a power failure
rather than a physical result. **Across-order dispersion**, the other channel, has far more
degrees of freedom and is invariant to common-mode signal by construction (§4) — but the
per-epoch order distribution is heavy-tailed, so a Gaussian σ/√N conversion overestimates
the error on the combined RV several-fold: on CD-35 it reads 1333 m s⁻¹ against a
272 m s⁻¹ epoch-to-epoch scatter of the median, and drives every significance negative.

The machinery is not broken. β Pic b's known starlight contamination is resolved at 2.1–2.2σ
in both channels, and η Tel B's 116–130 m s⁻¹ epoch scatter is fully accounted for by its
own within-night measurement noise, requiring no astrophysical jitter — a clean supporting
statement for that target's limit. The effects being sought elsewhere are simply smaller
than the available power.

**The observing-strategy result: the binding constraint on measuring companion RV jitter is
frames per night, not nights.** Current campaigns take ~2; a variance decomposition needs
~6–10. That is a cheap and concrete change to any future observing block, it costs no extra
nights, and it converts a survey of upper limits into a measurement of the noise floor that
decides whether this technique is feasible at all.

---

## 8. The checklist

Compressed, in the order we would apply it.

1. **Gate every template iteration** by injection recovery, not just the last. Keep a
   bit-for-bit restore path to the last validated state.
2. **Inject by shifting the template, never the observation.** Shifting the observation
   moves the tellurics, which a real Doppler shift does not, and the fit recalibrates the
   injection away.
3. **Never build a template from a single night.** Without a barycentric lever the template
   cannot separate target lines from telluric residue.
4. **Report per-order injection recovery, not just the combined figure.** A combined ~100%
   can hide orders running from −4% to +493% (M12 §8.4). Per-order recovery is also a
   non-circular order screen: a screen on recovery fraction cannot delete signal, because
   deleting signal is exactly what it measures.
5. **Say what your precision statistic is invariant to** — signal, timescale, or both — and
   never quote a within-epoch dispersion as a night-level accuracy.
6. **Prefer an external reference** (published RVs, a second instrument, a positive control)
   over any internal proxy. Where none exists, the injection harness carries the entire
   validation burden and should be stated as doing so.
7. **Calibrate every search maximum by permutation on the true cadence**, holding times,
   covariates and the value distribution fixed. Report the noise-only 95th-percentile peak
   alongside the observed one.
8. **Bound the period grid by the baseline.** Do not search to 460 d on a 41-day series.
9. **Measure the FAP of the composite detection criterion** used to define an upper limit,
   not of the test statistic alone.
10. **Quote evidence uncertainties as run-to-run scatter over ≥ 10 seeds**, and report a
    live-point convergence check separately. Do not treat more live points as a fix.
11. **Do not quote a standard deviation at *n* = 2.** Give the range or a bootstrap.
12. **Ask for 6–10 frames per night** in any new campaign, so the noise decomposition is
    possible at all.

---

## 9. Discussion: the asymmetry

The four failures have different mechanisms — a template collapse, an algebraic invariance,
a multiple-comparisons omission, and a misread uncertainty — and one structural property in
common.

**Every one of them makes the result look better.** The collapsed template gives a tighter
limit. The invariant statistic rewards configurations that make orders agree, including
configurations that make them agree on nothing. The uncalibrated search maximum reports a
larger significance than the data support. The internal evidence error reports a smaller
uncertainty than the procedure delivers, and shrinks further the harder you try to fix it.

That asymmetry is why none of them self-report, and it is why the usual defences do not
work. Re-running the analysis reproduces the failure. Reading the code does not reveal it —
in three of the four cases here the code was correct and the interpretation was not.
Internal consistency checks pass, because the failures are internally consistent. What
catches them is *external*: a signal you put in yourself and demand back; a reference series
you did not produce; a null you generated from your own cadence; a second run with a
different seed.

The corollary for a field at this stage of maturity is uncomfortable but simple.
Companion-side RV currently consists of a small number of nulls and one detection. Nulls are
the easiest results in the world to produce accidentally, and a survey of upper limits from
un-gated pipelines would be indistinguishable from a survey of upper limits from working
ones — except that the broken pipeline's limits would be *deeper*. The first thing to
publish alongside a limit in this field should be the measured velocity transmission of the
pipeline that produced it.

None of this is an argument against the measurement. Our own reproduction found the
motivating detection to be real, blind, robust to leaving out any single night, and absent
from every other target reduced identically — including one on the same instrument setting
with a longer baseline (M28 §1). The technique works. It simply does not tell you when it
has stopped working, and that is the gap these checks fill.

---

## Acknowledgements and statement of AI involvement

The analyses summarised here — archive census, reduction, pipeline development, statistical
calibration, and the drafting of this note — were carried out by AI agents (Claude,
Anthropic, running in Claude Code), directed and reviewed by the human author, who set the
research questions, challenged the agents' claims, made every decision with external
consequences, and takes sole responsibility for all content. Verification is primarily
mechanical rather than expert-audited: every adopted pipeline change was scored against an
external reference and required signal-injection recovery; positive controls preceded every
null; dead ends and retractions remain in the public record. Based on data obtained from the
ESO Science Archive Facility. This document reports an independent analysis and is not
affiliated with or endorsed by the authors of any work discussed.

---

## References

- Hoy, K., Zurlo, A., Peña R., P. A., Köhler, J., et al. 2026, *Nature*, "Satellite detected around a star's substellar companion" (published version; supersedes arXiv:2607.05193v1).
- Horstman, K., Ruffio, J.-B., Batygin, K., et al. 2024, "RV measurements of directly imaged brown dwarf GQ Lup B to search for exo-satellites", arXiv:2408.10299.
- Köhler, J., Zechmeister, M., Hatzes, A., et al. 2025, A&A, "viper: High-precision radial velocities from the optical to the infrared", arXiv:2505.08315.
- Kral, Q., Wang, J., Kammerer, J., et al. 2026, A&A, "Exomoon search with VLTI/GRAVITY around the substellar companion HD 206893 B", arXiv:2511.20091.
- Lazzoni, C., Desidera, S., Gratton, R., Zurlo, A., Mesa, D., & Ray, S. 2022, MNRAS, "Detectability of satellites around directly imaged exoplanets and brown dwarfs", arXiv:2207.07569.
- Ruffio, J.-B., Horstman, K., Mawet, D., et al. 2023, "Detecting exomoons from radial velocity measurements of self-luminous planets: application to observations of HR 7672 B and future prospects", arXiv:2301.04206.
- Speagle, J. S. 2020, MNRAS 493, 3132, "dynesty: a dynamic nested sampling package for estimating Bayesian posteriors and evidences".
- Vanderburg, A., Rappaport, S. A., & Mayo, A. W. 2018, "Detecting exomoons via Doppler monitoring of directly imaged exoplanets", arXiv:1805.01903.
- Vanderburg, A., & Rodriguez, J. E. 2021, "First Doppler limits on binary planets and exomoons in the HR 8799 system", arXiv:2110.14650.

---

## What to verify before submission

> **M29 resolution pass (2026-08-13).** Items 1, 2, 5, 8 and 12 have been checked
> against the milestone documents and the source PDFs. Results below, in place.
> **Item 2 turned out to be a real defect and has been corrected in the manuscript.**
>
> - **1 — RESOLVED, no change needed.** M14 §4 (`331→347`) and §6 (`331→429`) both start
>   from the same M13 baseline of 331; they are *not* sequential. The non-sequential
>   phrasing here is correct.
> - **2 — DEFECT, FIXED.** The "~40% external improvement" compared **different order
>   combines**: 147 m/s is the M13_G *median*-combine baseline, 85 m/s is the final
>   *mean*-combine result. The like-for-like pair in M14 §6 is **133 → 85 m/s = 36%**.
>   The manuscript now states 36% and names the combine; this note should too.
> - **5 — RESOLVED.** Both counts are right for their own treatment: M15 works from
>   **18 nights** with **n = 19** in the blind search (two nights carry double visits),
>   while M28 §1 reports **n = 17** after per-night binning plus the internal spread
>   screen. Quote the treatment alongside the count.
> - **8 — FIXED.** The HTML draft now reads Köhler, **J.**, confirmed twice: the viper
>   paper's own text, and the Hoy et al. author list (Jana Köhler).
> - **12 — FIXED.** The draft cited a title matching *neither* version. It now carries
>   the published title, the preprint title, and the note that both changed.
>
> Items 3, 4, 6, 7 stand as written — they are caveats to travel with the numbers, not
> ambiguities to resolve. Items 9, 10, 11 are covered by the repository-wide reference
> audit in `docs/REFERENCE-AUDIT.md`.


Items the author should check personally. Everything else in this note traces to a numbered
milestone document in the repository.

**Numbers with a documented ambiguity**

1. **The Eq. 1 baselines in §4.** M14 §4 reports 331 → 347 and M14 §6 reports 331 → 429.
   Both appear to be measured against the same M13 baseline of 331 rather than in sequence.
   Confirm before the sentence is read as a two-step progression; the phrasing here is
   deliberately non-sequential.
2. **The "~40% external improvement".** Computed here as 147 → 85 m s⁻¹ = 42%, matching the
   existing HTML draft's "40%". Confirm the two rms values are on the same order combine and
   epoch screen.
3. **"a known signal of several hundred m s⁻¹" on CD-35 (§7).** `NEXT-DIRECTIONS.md` §A1
   uses "~430 m s⁻¹"; the published *K*₁ is 306 and this project's own fitted *K* runs
   380–470. Written vaguely here on purpose; decide which number to state.
4. **The 92%-absorption figure (§3.3)** is measured on **one epoch** at 1000 m s⁻¹ injected
   (M12 §8.1). It is decisive as a direction and should not be read as a calibrated fraction.
5. **η Tel B epoch counts.** M15 uses 18 nights / 815 d with *n* = 19 in the blind search;
   M28 §1 tabulates *n* = 17 over 815 d for the common-mode test. Different screens. If
   η Tel B numbers are quoted more fully than they are here, reconcile them.
6. **HD 1160 B extrapolation factor.** M28 §1 says "4× beyond the data" (171 d against a
   41 d baseline); M28 §6.3 says "11×" (the 460 d grid edge against 41 d). Both are correct
   in context; §5.3 here uses 11× because it is talking about the grid. Keep them distinct.
7. **The 12.1-day binary control (§3.2)** is GJ 229 B, and its "correct" recovered amplitude
   (~6000 m s⁻¹) is a model-dependent expectation for an unresolved double-lined pair, not a
   measured ground truth (M3 §4, M11 §6). The robust statement is the *relative* collapse
   under an unchanged target. Named or not, that caveat should travel with the number.

**Bibliography**

8. **Köhler initial.** The existing HTML draft's reference list reads "Köhler, J.". The
   paper text in `papers/text/kohler2025_viper.txt` gives **J. Köhler**, and the H26 author
   list includes Jana Köhler. This note uses J.; the HTML draft should be corrected.
9. **Journal, volume and year** for Köhler et al. 2025, Lazzoni et al. 2022, Ruffio et al.
    2023, Horstman et al. 2024, Kral et al. 2026, Vanderburg et al. 2018 and Vanderburg &
    Rodriguez 2021 are **not** given here because they are not confirmed anywhere in the
    repository. Fill from ADS before submission.
10. ~~**Kral et al. 2025** filename looks misleading~~ — **RESOLVED (M32).** The archived
    copy is the **arXiv preprint** (ESO 2025, dated 26 November 2025); A&A **published it in
    January 2026**. So the `kral2026_*` filename is correct and the year to cite is **2026**,
    which is what the manuscript and the RNAAS note use. This note previously cited 2025,
    disagreeing with them; all occurrences are now 2026.
11. **Peña R. et al. 2025 (EMPEROR/reddemcee)** and **Wahhaj et al. 2011** appear in the HTML
    draft's reference list but are not cited here. Add only if used.
12. **H26 title.** Taken from `papers/text/hoy2026_nature_published.txt`, which renders it as
    "Satellite Detected Around a Star's Substellar Companion". The existing HTML draft uses a
    different wording ("A satellite orbiting the directly-imaged brown dwarf CD-35 2722 B",
    which is the preprint's). Check against the published article.

**Claims that need a decision rather than a check**

13. **§3.4** proposes an injection performed before template construction as the natural
    upgrade. This has not been built. It is written as a proposal, not a result; confirm that
    framing survives editing.
14. **§6** discusses another group's quoted lnZ uncertainties. The wording is deliberately
    narrow — we cannot test their sampler, and we suggest a question rather than assert a
    fault. Re-read it once with a referee's eye before submission.
15. **§9's** closing recommendation — publish measured velocity transmission alongside every
    limit — is a normative claim about the field. Keep or soften as the venue warrants.
16. **Overlap with the other drafts in `docs/paper/`.** §5 restates calibrations that also
    appear in the CD-35 / η Tel manuscript (`draft.template.html`, §4.1 and §5.1) — cite
    Paper I rather than duplicating its tables if it goes out first. §6 has been cut back to
    headline numbers and now defers to `sampler-reproducibility-note.md` for the
    per-configuration table; check that the cross-reference resolves to a real citation
    before submission, and that the two documents' headline numbers stay in step if either
    is revised.
17. **Venue and length.** §1–§9 run to roughly 4,600 words including the permutation table
    and the twelve-item checklist (continuous prose is about 4,100), excluding abstract,
    references and this list. Confirm section numbering and reference style against the
    chosen template.
