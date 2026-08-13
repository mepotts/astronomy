# Where this project goes next

The existing queue (`docs/target-queue.md`) answers "where else do we point the
pipeline". This file answers a different question: **what else does the work we have
already done make possible** — including things that are not exomoon searches at all.

Ordered by (novelty x feasibility x reach), not by difficulty.

---

## A. New science from data already on disk

These need no new observations, no new downloads, and in two cases no new reduction.
They are the highest-value-per-hour ideas in this file.

### A1. The RV jitter floor of directly imaged companions — **ATTEMPTED, NOT ACHIEVABLE YET**

> **Result (2026-08-13, `scripts/injection/m29_jitter.py`): the idea is sound and the
> data cannot support it. Documented here rather than quietly dropped.**
>
> The measurement needs the epoch-to-epoch scatter split into measurement noise and
> astrophysical variability. Two noise channels were tried and both fail:
>
> - **Within-night frame scatter.** Frames of one night are minutes apart, so a
>   satellite orbit cannot move between them — pure noise, in principle ideal. But the
>   campaigns take only **~2 frames per night**, giving too few degrees of freedom. The
>   built-in control settles it: CD-35 2722 B, which carries a real signal (published K = 306 m/s, fitted here at 426-472),
>   resolves its excess at only **1.4σ**. A method that cannot recover a known signal
>   cannot certify a null, so every other object's "no excess" is a power failure, not
>   a physical result.
> - **Across-order dispersion.** Far more degrees of freedom, and invariant to
>   common-mode signal by construction — but on CD-35 it reads **1333 m/s** against a
>   272 m/s epoch-to-epoch scatter of the median, even after per-order centering. The
>   per-epoch order distribution is heavy-tailed, so a Gaussian σ/√N conversion
>   overestimates the error on the combined RV several-fold and drives every
>   significance negative.
>
> The machinery is not broken: β Pic b's known starlight contamination is resolved at
> 2.1–2.2σ in both channels. The excesses being sought elsewhere are simply smaller
> than the available power.
>
> **What it turned into — an observing-strategy result worth stating.** The binding
> constraint on measuring companion RV jitter is **frames per night, not nights**.
> Current campaigns take ~2; a decomposition needs ~6–10. That is a concrete, cheap
> change to any future OB and belongs in the proposal case (D1) and the methods paper
> (C1). Also banked: **η Tel B's 116–130 m/s epoch scatter is fully accounted for by
> its own within-night measurement noise**, needing no astrophysical jitter — which is
> a clean supporting sentence for the limit in Paper I.
>
> **To revive it:** a robust (heavy-tail-aware) per-order error model, or one campaign
> with 6+ frames per night.

*Original statement of the idea, kept for the record:*

**The gap.** Every proposal in this genre — including this project's own — guesses the
astrophysical RV noise floor of a young self-luminous giant. Nobody has measured it,
because nobody has a homogeneous multi-epoch RV sample of imaged companions.

**We do.** Per-epoch scatter is in hand for ~11 companions spanning M7 → L → T, at
known ages, masses, spectral types and rotation regimes, all through one pipeline whose
velocity transmission is injection-verified per target:

| object | per-epoch scatter | note |
|---|---:|---|
| YSES 1 b | 34 m/s | best of the campaign |
| HD 19467 B | 45 m/s | benchmark T dwarf |
| 2M0103AB b | 53 m/s | within-night |
| CD-35 2722 B | 70–90 m/s | has a real signal — the calibrator |
| HIP 81208 B | 124 m/s | |
| eta Tel B | 127–129 m/s | |
| PDS 70 (star) | 130 m/s | accreting transition-disk host |
| HIP 65426 b | 131 m/s | |
| AB Pic b | 120–190 m/s | |
| HD 1160 B | 725 m/s | quality-limited, the outlier |

**The result.** Decompose scatter into photon noise (measurable), instrumental floor
(measurable from the injections), and the residual — which *is* the astrophysical
jitter. Regress the residual against spectral type, T_eff, log g, age and v sin i.

**Why it matters.** This converts a pile of null results into the single number that
decides whether companion-side exomoon RV is feasible at all, for anyone, ever. It is
the reference table the next decade of proposals will cite. And every input already
exists — this is analysis, not observation.

### A2. Companion–host relative radial velocities → orbital dynamics

Direct imaging gives sky-plane position; it cannot give the line-of-sight velocity that
breaks the orbit-orientation degeneracy. A single precise companion RV does (this is
how Ruffio et al. constrained HR 8799). **We have absolute RVs for ~11 companions** and
have never used them for this — the whole project treats RV as a satellite probe and
throws the systemic value away.

Deliverable: a table of companion-minus-host radial velocities with uncertainties, and
per system what it does to the orbit posterior when combined with published astrometry.
Different science case, different audience (dynamics, not exomoons), same data.

### A3. A homogeneous v sin i catalog

The same H- and K-band spectra carry rotational broadening, and viper already forward-
models line profiles. Companion spin is an active formation diagnostic (spin–mass and
spin–age relations test accretion history). No homogeneous multi-object set exists —
published v sin i values are one-object-per-paper with inconsistent methods. Moderate
new work (a broadening fit alongside the RV fit), high citation surface.

### A4. CT Cha B's accretion variability

A 3.3σ deviant epoch on an accreting ~2 Myr companion, undecidable at n=3. Accreting
companions are rare and variable-accretion RV signatures are almost unstudied. Two more
epochs decide it — this is the one item here that needs telescope time, and it is a
cheap ask.

## B. Cheap external checks that strengthen the paper now

### B1. Photometric cross-check of the 171 d period ⭐ *do this before submitting*

If CD-35 2722 shows a ~171 d **photometric** periodicity, the satellite has an activity
explanation and the paper's central claim is in trouble. If it does not, that is another
independent systematics defence. ASAS-SN, ATLAS and TESS are public and account-free,
and the primary is bright. Half a day of work, and a referee will ask for it.

### B2. Gaia astrometric cross-check

RUWE, astrometric excess noise, and any non-single-star solution for CD-35 2722 A and
for every target carrying a limit. Independent constraint on unseen companions,
essentially free, and it strengthens the null results as well as the detection.

## C. Method contributions with reach beyond this subfield

### C1. The methods paper — four ways this measurement goes wrong

Written entirely from milestones already banked, each with a worked example from real
data:

1. **A flat series is not a quiet series.** PDS 70's nine-night template returned −62%
   injection recovery: a template that lost its stellar lever produces beautiful,
   meaningless upper limits. Caught only by gating.
2. **A precision statistic invariant to its own signal.** The field's per-epoch
   dispersion (Eq. 1) is invariant to common-mode velocity by construction, and moved
   *against* this project's two largest real improvements.
3. **A search maximum is not a significance.** ΔBIC quoted as the peak of a 4000-period
   search, when a signal-free series with the same cadence reaches ΔBIC ≈ 19 five
   percent of the time.
4. **Sampler-internal evidence errors are not reproducibility.** Measured 2–8x
   understatement on a real published RV table (§C2).

### C2. Sampler reproducibility as a standalone note

Evidence ratios across the exoplanet literature are quoted with the sampler's internal
logZ uncertainty. Measured here on the published Nature table: empirical seed-to-seed
scatter is 1.1x, 3.3x and 8.1x the quoted error depending on prior family, with single
runs spanning −1.7 to −8.9 where the internal error claims ±0.27. Short, sharp, wide
audience, code included. RNAAS-length.

### C3. A public "does your detection survive?" service

`m28_nullcal.py` generalized: upload an RV table, get back permutation-calibrated
significance, a leave-one-out panel, window-function/alias structure, and a
nuisance-covariate test. This is exactly the portfolio's stated thesis — the usability
layer between public archives and the people using them — and it turns the methods paper
from a lecture into a tool.

## D. Less adjacent

### D1. Isolated planetary-mass objects: where the contrast wall does not exist

This project measured the wall at four points and concluded that inside ~0.8″/2000x you
need fiber suppression. **Free-floating planetary-mass objects have no host at all** —
no contrast wall, no starlight, no slit contamination, and the same bright young IR
spectra. They are the ideal targets for companion-side RV and nobody frames them that
way. ESO's archive is swept negative, so this is a proposal case rather than an archival
one — but it is the strongest proposal case the project has, and it is the natural
ELT/ANDES argument.

### D2. The contrast wall as an instrument-design curve

The separation–contrast–precision surface, measured rather than forecast, is directly
actionable for HiRISE/KPIC/RISTRETTO and for ELT instrument teams. Small paper,
specific and useful audience.

### D3. Systematic significance audit of published periodic detections

The machinery in C3 applied to a defined sample of published RV claims: how many quote a
search maximum as a significance? This is `IDEAS/reproduction-audit-fleet.md` with
working code and a demonstrated finding behind it. Provocative — needs care, and needs
the methods paper published first so it reads as method rather than accusation.

---

## Suggested execution order

1. **B1, B2** — cheap, and they belong in Paper I before it goes out.
2. **C2** — the data is already computed.
3. **A1** — the highest-value new result available without new observations.
4. **C1** — writes from banked milestones.
5. **A2, A3** — new science, moderate new analysis.
6. Then the existing queue: YSES 1 b's blocked 2022 pair, beta Pic b's HiRISE nights,
   Keck/KOA (DH Tau B, HR 8799).
