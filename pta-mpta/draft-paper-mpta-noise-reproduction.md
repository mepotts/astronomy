# DRAFT — NOT SUBMITTED

*Full-paper draft (A&A / MNRAS short-paper shape). Nothing here has been sent to any journal, any
collaboration, or any person. Author, affiliation and ORCID are placeholders and are Matthew's to
fill or delete. Pre-registration for this draft:
[`M5-ess-floor-sw-census-and-the-paper.md`](M5-ess-floor-sw-census-and-the-paper.md) §1.3 (P1–P7).
**Every number in the text is re-derived from a committed artifact by
`scripts/m5_paper_numbers.py` (105 numbers, audit table in Appendix A) and the drafted text is
checked back against that artifact by `scripts/m5_paper_check.py`.**
The separate, shorter Research Note —
[`draft-rnaas-mpta-table-audit.md`](draft-rnaas-mpta-table-audit.md) — is its own finished
deliverable and is not superseded by this. §11 lists exactly what remains before this could be
submitted.*

---

**Title:** How much of a pulsar timing array noise table is a measurement? An independent
reproduction of the MeerKAT PTA 4.5-year single-pulsar noise models

**Authors:** [PLACEHOLDER — Independent Researcher]¹, ORCID [PLACEHOLDER]

¹ [PLACEHOLDER]

---

## Abstract

The MeerKAT Pulsar Timing Array (MPTA) 4.5-year release publishes noise models for 83 millisecond
pulsars — 588 tabulated parameter values — together with the 245,907 sub-banded times of arrival and
the ephemerides needed to rebuild them. We rebuild all 83 from that public data with an
independently implemented likelihood and a different sampler family, under criteria fixed before
each run. **The reproduction agrees with 576 of the 588 published values (98.0%) and with 73 of 83
pulsars on every value.** All twelve disagreements have one of two named causes, and neither is the
data or the implementation: **ten are the solar-wind spectral index γ_SW, or the amplitude coupled
to it, on pulsars whose published value lies outside the prior range a reproducer must guess** — the
paper tabulates no prior range for any of the 588 values — and two are one deterministic-event width
on exactly the two rows the paper itself flags as coming from a different analysis. A registered
variant with γ_SW ~ U(−4,4) resolves all ten and creates none. Widening that prior also grades the
column: **of all 26 rows, only five are measurements of γ_SW** — five more have an apparent
constraint that is the prior edge, fifteen are unconstrained under either prior — and a reader can
identify all but two of the non-measurements from the printed table alone. The same
prior-dominance appears elsewhere: 66 of 83 tabulated log₁₀A₁₃/₃ intervals reach below the paper's
own "clearly disfavoured" point. Our 83-pulsar factorised amplitude, log₁₀A_CURN = −14.44,
68% [−14.64, −14.35], agrees with the published −14.28 ± 0.21, but both depend on *which* pulsars
enter the product more than their intervals suggest. Adding the collaboration's own misspecification
mitigation moves the inferred amplitude down in 49 of 70 pulsars (p = 6 × 10⁻⁶ against a null
control), though its array-level effect is not resolved by this data set. None of this is an error,
and all of it is checkable only because the release is complete and open.

---

## 1. Introduction

A pulsar timing array measures a gravitational-wave background against a per-pulsar noise model,
and the noise model is not a nuisance: the amplitude, spectral index and even the existence of the
common signal depend on what each pulsar's chromatic, dispersive and achromatic processes are
allowed to absorb. That prior choices in these models propagate into gravitational-wave inference
is established — Goncharov & Sardana (2025) and van Haasteren (2024) demonstrate it directly, and
Hazboun et al. (2020) showed earlier how strongly Bayesian PTA statistics depend on the assumed
model. **This paper claims none of that.** What it adds is narrower and, as far as we can find,
unpublished: a value-by-value measurement of one specific published noise table against an
independent reproduction from that collaboration's own public data, and a per-row answer to the
question *which entries in this table are measurements?*

We work on the MPTA 4.5-year data release (Miles et al. 2025). We chose it for one reason: it is
complete. The 83 ephemerides, the 83 arrival-time files containing 245,907 sub-banded times of
arrival, and the epoch-resolved archives are all public, account-free, and carry a DOI. There are no
posterior chains, but a likelihood-level reproduction does not need them, and the release contains
everything a likelihood-level reproduction does need. **That openness is the entire reason this
paper exists, and we say so first rather than in an acknowledgement:** the great majority of
published noise tables cannot be checked this way at all, and the fact that this one can is a
service, not an exposure.

There is one thing the release does not contain, and it turns out to matter. The paper tabulates no
prior range for any of the 588 values, and no prior or configuration file ships with the data. For
almost every column that is harmless — the published posteriors sit far inside any reasonable
choice. For one column it is not, and the consequences of that single gap organise most of this
paper.

We state our scope once, and hold to it. We reproduce single-pulsar noise models and a factorised
common-signal amplitude. We make **no detection claim, no evidence claim, no spectral
characterisation** (the common-process spectral index is fixed at 13/3 throughout), and **no
statement about spatial correlations** — no Hellings–Downs analysis and no continuous-wave search
appears anywhere below.

## 2. Data, model and method

### 2.1 The public release

All input comes from the MPTA 4.5-year release at Data Central (doi:10.57891/j0vh-5g31): 83 `.par`
ephemerides and 83 `.tim` arrival-time files, 245,907 sub-banded ToAs in 32 frequency channels. We
inspected the release tarballs directly rather than assuming their contents: `partim.tar.gz` holds
exactly 83 ephemerides and 83 arrival-time files and nothing else, and the "anisotropy supplement"
is nine video files. **No prior specification, configuration or chain ships with the release.**

Before modelling anything we verified that our timing residuals reproduce the release's own. Our
weighted residual RMS matches the `TRES` value recorded in each published ephemeris to a median of
**0.015%** over the 63 pulsars whose release is internally complete; every material discrepancy
traces to the 20 pulsars that ship fewer ToAs than their ephemeris was fitted to. Three
ephemeris-level defects surfaced along the way and are reported for completeness in §7.

### 2.2 An independent implementation

Noise models were rebuilt with `enterprise` and `enterprise_extensions`, driven by our own model
constructor and sampled with `PTMCMCSampler` at a single temperature, using its adaptive-Metropolis,
single-component adaptive-Metropolis and differential-evolution proposals together with per-signal
prior-draw proposals of our own (the library's own prior-draw proposals fail under NumPy 2; see §7).
Timing models were built with `PINT`, independently of the `tempo2` fits the release ships.

**The sampler family is different from theirs, and that matters.** The MPTA paper's single-pulsar
posteriors come from **nested sampling** — `parallel-bilby`, driven through the `enterprise_warp`
framework — with `PTMCMC` reserved for the full-PTA common-signal analysis. Ours are Markov-chain
posteriors throughout. A reproduction that agrees across that gap is a stronger check than one that
re-runs the same sampler on the same code. Beyond the shared `enterprise` model layer, no
collaboration code is reused.

The same sentence of their methods carries a constructive implication for §4: the paper states that
`enterprise_warp` was "used to pass the prior and likelihood information from `Enterprise` to
`Bilby`", so the prior ranges exist in machine-readable form somewhere in that pipeline. Printing
them — or releasing that one configuration file — is a smaller step than it might appear.

Model *structure* per pulsar was taken from the published tables:
whether each pulsar carries a DM Gaussian process, a chromatic Gaussian process (with the index free
or fixed at 4), a chromatic Gaussian event, an annual chromatic term, a solar-wind Gaussian process,
a free achromatic red process, and EQUAD/ECORR terms. The common achromatic process is present in
all 83 pulsars at fixed γ = 13/3. Across the array this is 15 chromatic Gaussian events, 8 annual
chromatic variations, 13 free-index chromatic Gaussian processes, 10 fixed-index ones, 49 DM
Gaussian processes, 26 solar-wind Gaussian processes, 12 free achromatic red processes, and 20 EQUAD
and 29 ECORR terms.

### 2.3 Priors, and the one we had to guess

Because no prior ranges are published we declared our own before running anything, using the ranges
conventional in the PTA literature: log-uniform amplitudes over wide ranges, uniform spectral
indices on [0, 7], uniform chromatic index, uniform EFAC, and so on. **The declared range for
power-law spectral indices, γ ∈ [0, 7], was applied to the solar-wind Gaussian process as well.**
That was our decision and it was wrong for that signal — §4 is the measurement of how wrong, and why
the mistake is instructive rather than embarrassing. We note here only that it is not an eccentric
choice: the same [0, 7] range is applied to red and DM spectral indices throughout the PTA
literature, and a reproducer with no published range to follow will reach for it.

### 2.4 Sampling, the gate, and pre-registration

Every criterion in this work was fixed in a written registration before the run that tests it, and
each registration, including the ones that failed, is preserved. A run is accepted when it has at
least 100,000 post-burn iterations (50,000 for the fixed-white variants), a Metropolis acceptance
rate of at least 0.05, and a stability condition on every sampled parameter: the median of the last
half of the post-burn chain must lie within `max(t_abs, 0.1 × W68)` of the full-chain median, where
`t_abs` is a fixed absolute tolerance and `W68` is that parameter's own 68% interval width.

That last rule replaced a purely absolute tolerance partway through the campaign, and because it is
a **relaxation** we report both outcomes everywhere: **83 of 83 pulsars clear the registered gate;
76 of 83 clear the stricter absolute one.** The agreement statistics under the two are 98.0% and
97.9% respectively — indistinguishable — and the pulsars admitted only by the relaxation agree on 61
of 62 parameters, better than the array as a whole. The relaxation exists because the absolute
tolerance, applied to an amplitude posterior 3.01 dex wide *because it is bounded by the prior*,
demands that a near-flat distribution's running median be stable to 3% of its own width; that is a
requirement on the prior, not on the data.

We also registered and applied an effective-sample-size floor (run-level minimum ESS ≥ 100, chosen
so that each 68% interval edge is determined to better than 15% of the interval's own half-width)
and report the result honestly, because it is a negative one: **the runs the floor rejects agree
with the published table slightly *better* (98.4%) than the runs it admits (97.7%)**, so ESS is not
diagnostic of fidelity to the published table in this problem. We therefore keep the floor only as a
bound on our own Monte-Carlo error, quote all headline numbers under the registered gate, and give
the ESS-floored subset alongside wherever it changes a conclusion (§6.3 is the one place it does).

Acceptance rates over the accepted runs span 0.158–0.527; none is near the floor, and no frozen
chain enters any number below. Total recorded cost is at least 192.4 core-hours over 277 runs, a
firm lower bound because the elapsed-time counter resets on resume and most runs were resumed.

### 2.5 The comparison rule

A published value and our posterior **agree** when the published maximum-a-posteriori value lies
inside our 68% interval, **or** our posterior median lies inside the published 68% interval. This
was fixed in advance, is symmetric, and is deliberately generous: the question of this paper is not
whether the published numbers are right to the last digit but whether an independent reproduction
lands in the same place. Where it does not, we run a further diagnostic (§3.3) that distinguishes a
sampling failure from a model or prior difference.

## 3. The reproduction

### 3.1 Agreement

**576 of 588 tabulated values agree (98.0%), and 73 of 83 pulsars agree on every value** (Table 1).
Every DM Gaussian process, chromatic Gaussian process, chromatic Gaussian event amplitude and
timescale, annual chromatic term, achromatic red process, white-noise term, chromatic index, solar
electron density and log₁₀A₁₃/₃ value in the release is reproduced within the rule of §2.5. The
disagreements are confined to two parameters.

### 3.2 The twelve disagreements, and their two causes

| cause | parameters | pulsars |
|---|---|---|
| published γ_SW outside our declared prior, or its interval crossing zero | 8 × γ_SW + 2 × log₁₀A_SW | J0900−3144, J1327−0755, J1643−1224, J1652−4838, J1730−2304, J1751−2857, J1811−2405, J2124−3358 |
| Gaussian-event width on rows the paper prints in bold, whose values it states are taken from a different (CURN) analysis | 2 × σ_g | J0610−2100, J1902−5105 |

**Ten of the twelve are the solar-wind spectral index or the amplitude coupled to it**, on pulsars
whose published γ_SW is negative or whose interval crosses zero — values our declared prior cannot
visit, so the disagreement is forced by our own choice and measures nothing about the data. The
other two are the same parameter on exactly the two rows the paper's own caption excludes from
like-for-like comparison: *"Where the pulsar name is displayed in bold, the parameter values we
report are taken from the CURN Bayesian analysis"* — a different model from the favoured
single-pulsar one we sampled. **No parameter of any other kind disagrees anywhere in 83 pulsars.**

### 3.3 Mode versus model

For every pulsar we evaluate our own likelihood at the published parameter vector and at our
chain's best point, and record the difference. Over all 83 pulsars the median is **+0.70**, with 79
positive and 4 negative, and the most negative value anywhere in the array is **−0.67**. Our sampler
therefore never materially under-performs the published solution: where we disagree, our likelihood
prefers our answer, which points at a prior or convention difference rather than a failure to find
the mode. (The single negative case among the disagreements, J1811−2405, is a pulsar whose published
γ_SW our prior excludes by construction, so its best point is constrained away from the published
one.)

## 4. The solar-wind spectral index

### 4.1 Seven published values cannot be reached

The stochastic solar-wind model is a power law in the plasma density fluctuation spectrum (Hazboun
et al. 2022), and the MPTA paper says explicitly that its index "is allowed to have a red or blue
spectrum" — so a negative index is intended, and nothing here suggests otherwise. What is missing
is the *range*. Of the 26 pulsars whose favoured model samples γ_SW, **seven have a negative
published value** and **twelve more have a 68% interval crossing zero**: **19 of 26** cannot be
fully represented under γ ∈ [0, 7].

Nor does the obvious library default rescue a reproducer. The `powerlaw` branch of
`enterprise_extensions`' own `solar_wind_block` hard-coded γ_SW ~ U(−2, 1) at the version current
when the paper was submitted and still at the version we ran; two published values (−2.21, −2.32)
and interval edges reaching **−3.21** (J1811−2405) lie outside it. That default was later widened to
U(−6, 5), citing Susarla et al. (2024) — a range that does contain all seven. So the answer to
"which prior reproduces this column?" changed after publication and depends on a package version,
while the table's own range remains unstated. This is the single documentation gap from which every
disagreement in §3.2 follows.

### 4.2 A registered wide-prior variant resolves all ten disagreements

We re-ran the identical model, data and machinery for every solar-wind pulsar with γ_SW ~ U(−4, 4)
and nothing else changed. The range was chosen to contain every tabulated γ_SW value and every
tabulated interval edge in the column, which is selection from the answer; we state that plainly,
because it fixes what the variant can establish. It answers *"does a prior wide enough to contain
the published column recover the published column?"* — a reproducibility question — and **not**
*"is U(−4,4) the right prior"*, which is the collaboration's to answer.

**Over all 26 solar-wind pulsars, each with both runs gated, the registered campaign misses ten
solar-wind parameters and the variant misses none: all ten are resolved and none is created.** Eight pulsars go
from partial to complete agreement. Our headline 98.0% is quoted under the *registered* prior and is
never recomputed with the variant substituted in; the variant is reported as its own measurement.

We also record the failure this variant first produced, because it changed what we measured. Our
original control for the variant was defined by the **sign** of the published γ_SW: pulsars with a
comfortably positive published value should not move when the prior is widened downward. That
control failed — and it failed because the sign of a published value is not a proxy for whether the
value was measured. J1744−1134 has a published γ_SW of +0.91 and its 68% width still goes from 1.52
to 4.42 when the prior widens, because the narrow posterior *was the prior edge*. The right control
is the one in §4.3, and re-specified that way it passes.

### 4.3 Which rows of the published γ_SW column are measurements?

Define a row's **prior occupancy** as the ratio of its 68% posterior width to the prior width, under
each of the two priors, and its **widening ratio** R as the wide-prior width divided by the
narrow-prior width. A row is a **measurement** when it occupies less than a quarter of the prior
under *both*; **prior-propped** when it does not, but R ≥ 2 — an apparent constraint that is the
prior edge; and **unconstrained under both** when it occupies more than a quarter of both priors.
Thresholds were fixed before the classification was run, and the result is stable enough to quote
under a registered sensitivity grid.

| class | rows | median 68% width of log₁₀A_SW, U(0,7) → U(−4,4) |
|---|---|---|
| **measurement** | **5** | 0.29 → 0.30 dex |
| **prior-propped** | **5** | 0.47 → **2.14** dex |
| **unconstrained under both priors** | **15** | 2.75 → 3.04 dex |
| other (J1125−5825, which *narrows* under the wider prior) | 1 | 2.38 → 2.12 dex |

> **Of the 26 published γ_SW rows, five are measurements of γ_SW. Twenty are not** — five because
> their apparent constraint is the prior edge, fifteen because they were never constrained under
> either prior. Across the registered sensitivity grid the count of non-measurements ranges 16–20
> and the count of measurements 4–7, so we quote the former as a range and the latter as *at most
> seven*.

The five prior-propped rows are **J1327−0755, J1614−2230, J1744−1134, J1811−2405 and J2145−0750**.
Their log₁₀A_SW intervals widen from 0.34–0.52 dex to 1.4–2.4 dex when the index prior is widened —
so it is not only the index that was prior-supported, but the solar-wind amplitude the column is
usually read for.

Two consequences are worth separating, because they land differently on a reader.

1. **Most of this is visible from the printed table alone.** Classifying the *published* 68% widths
   by their occupancy of a candidate prior agrees with our chain-based classification on **24 of
   26** rows. A reader with the paper and nothing else can identify 18 of the 20 non-measurements.
2. **Two cannot be.** **J1614−2230 and J1744−1134** print narrow γ_SW intervals — 1.73 and 1.47 —
   that look like measurements and are not. Recognising those two requires re-running the chains
   under a wider prior, which requires knowing what the original prior was.

With the control re-specified this way — the five measured rows, which by construction are the rows
where the data speak — widening the prior moves the γ_SW median by at most **0.135** and the
log₁₀A_SW median by at most 0.035, both inside our own run-to-run repeatability of 0.19, and no
parameter that agreed under the narrow prior disagrees under the wide one. **The control passes.**
The machinery is not perturbing measured parameters; our first control simply was not made of
measured parameters.

### 4.4 What this does and does not say

It says: *under a reproduction that has to guess the prior, most of the published γ_SW column
carries no information about γ_SW, and two rows that look informative are not.* It does **not** say
that any published value is wrong, and it cannot: the collaboration's own prior is unpublished, so
we cannot state what their posterior occupied. That is the same gap as §4.1, seen from the other
side, and it is why the fix in §9 is one line of a caption.

## 5. How much of the rest of the table is prior?

**The achromatic amplitude column.** Every model carries a free-amplitude achromatic process at
fixed γ = 13/3, described in the paper as "allowed to vary across the entire amplitude prior range".
Taking the paper's own reference point — p(log₁₀A < −16.5), "a point where the prior range was
clearly disfavoured" — **66 of the 83 tabulated log₁₀A₁₃/₃ intervals reach below it**, with a median
68% width of **3.01 dex**, and only **six** rows are constrained better than 0.7 dex. This is a
property of a 4.5-year array rather than a defect — a factorised-likelihood search works precisely
by multiplying individually uninformative constraints — but the column should not be read
pulsar-by-pulsar as a set of measured intrinsic amplitudes.

**A visible symptom of the same thing.** The noise-table caption warns that in a few cases the
tabulated MAP falls outside the tabulated interval. It happens in **26 of 588 values (4.4%),
affecting 22 pulsars**, and the pattern is diagnostic: every affected value is an amplitude except a
single annual phase. A MAP outside its interval is not a typographical accident; it is what a
one-sided, rail-anchored posterior looks like when summarised by a mode and equal-tailed quantiles,
and it is a **flag that the row is prior-limited**.

**A free improvement in the chromatic column.** For the 13 pulsars with a free chromatic index the
amplitude–index posterior is a tight ridge, and the amplitude is tabulated at a reference frequency
of 1400 MHz where that covariance is near-maximal. The frequency at which it vanishes is
**857 MHz** (median over those pulsars) — at or below the bottom of the observing band. Re-quoting
the same posteriors there takes the median log₁₀A_Chrom 68% width from **0.46 dex to 0.19 dex**, a
factor 2.4 in precision for nothing but a change of reference frequency. Two of the 13 are
prior-driven in the sense that their amplitude moves further than the published uncertainty under a
different index prior.

## 6. Consequences for the common signal

### 6.1 The array-scale factorised amplitude reproduces

Using the collaboration's own factorised likelihood (Taylor et al. 2022) — the renormalised product
of the per-pulsar marginal posteriors for the common amplitude at fixed γ = 13/3 — we obtain, over
**all 83 pulsars**, **log₁₀A_CURN = −14.44 with a 68% interval of [−14.64, −14.35]**, against the
published 83-pulsar **−14.28 ± 0.21**. The intervals overlap; the modes differ by 0.16 dex, inside
the published 1σ. To our knowledge this is the first independent reproduction of an MPTA
common-signal amplitude at full array scale, and it agrees. We attach no Bayes factor and make no
detection claim.

### 6.2 These products are more composition-sensitive than their intervals suggest

Two measurements, both new, say the same thing.

**A leave-one-out jackknife over pulsars.** The 83-pulsar product above has a 68% width of 0.29 dex
and a jackknife standard error over pulsar composition of **0.137 dex**. The corresponding product
built from the noise table at face value is tighter still — 68% width **0.149 dex** — but its
composition jackknife is **0.256 dex**, *larger than its own credible interval*. A reader who takes
the width of such a product as its uncertainty will understate how much it depends on which pulsars
are in it.

**A growth curve.** Adding pulsars to the product in a pre-registered random order, the 68% interval
stays 1.9–2.2 dex wide and its lower edge stays pinned near the prior floor for the first 57
additions, while the mode lurches between −16.7 and −14.5. At the **58th** addition the width
collapses from **1.92 to 0.37 dex** in a single step and never returns; over the final ten additions
the mode moves by 0.030 dex. **The 58th pulsar is J1909−3744.** The transition is not √N
accumulation; it is the array's single most informative pulsar arriving and detaching the product
from the prior rail on its own.

The operational consequence is a rule any PTA can apply: **a factorised amplitude built on a subset
is not an amplitude until the informative pulsars are in it**, and every subset product should be
quoted with its pulsar count *and* with whether it contains the strongest constraints.

### 6.3 The cost of the collaboration's own misspecification mitigation

The MPTA paper's common-signal analysis adds a free achromatic red process to every pulsar that
lacks one in its favoured model, and states the trade-off in the same sentence: it was done *"to
minimize the risk of misspecifying the intrinsic pulsar noise as a potential shared signal **at the
expense of lowering our sensitivity to a CURN**"*. **The collaboration therefore names this cost
itself; what has not been published is its size.** That is what we measure here. We are not arguing
against the choice, which is defensible and which we would make too.

**The per-pulsar effect is established.** For each of the 70 pulsars where the two configurations
genuinely differ, we take the difference in the median common amplitude, with the white noise held
fixed at the same values in both so the comparison isolates the added process. The shift is
**downward in 49 of 70 pulsars** with a median of **−0.073 dex** (sign test p = 0.0011; Wilcoxon
signed-rank p = 6 × 10⁻⁶). The 12 pulsars that already carry a free red process act as a control —
for them the two runs are the same model and any difference is sampler noise — and over that control
set the shift is consistent with zero (median +0.0004, Wilcoxon p = 0.68). **Adding the mitigation
moves individual pulsars' inferred common amplitude down.**

**The product-level magnitude is not established, and this is a correction to our own earlier
work.** Propagating that per-pulsar shift into the factorised amplitude gives a difference between
the two configurations of **+0.257 dex** over the 83 pulsars gated in both — which we previously
reported as a significant shift against a pre-registered 0.21 dex threshold. That threshold was
never given an uncertainty. Supplied now, by the same leave-one-out jackknife as §6.2, it is
**+0.257 ± 0.212 dex — a 1.2σ result**, and removing the single most influential pulsar
(J2129−5721) takes it to +0.075. On the subset of pulsars that additionally clear our ESS floor it
reads +0.04, and random equal-sized thinnings of the full set span a 0.34 dex standard deviation, so
neither number distinguishes itself from the other. **We therefore withdraw the product-level
magnitude as a claim.** What survives — and it is the part that matters physically —
is the paired per-pulsar result above, which does not pass through a product and does not inherit
the product's composition sensitivity.

We report this at length rather than quietly restating it because the mechanism is general: an F-test
style threshold on the difference of two modes of two factorised products is not a significance test
unless the composition sensitivity of those products has been measured. §6.2 measures it here, and
it is comparable to the effect.

### 6.4 Scope, restated

This establishes that an independently implemented likelihood on public data reproduces the MPTA's
common-signal amplitude scale at full array size, and quantifies how that scale responds to a model
choice the collaboration itself flags. It does not establish the detection (no Bayes factor is
computed anywhere), the spectral characterisation (γ is fixed at 13/3 throughout), or anything about
spatial correlations.

## 7. Corrections to our own earlier analysis

The standard applied to the published table above was applied inward first, and this section is the
record. Every claim below was made by us at an earlier stage of this analysis and later withdrawn,
narrowed or reinstated. None of them was ever published outside this work; they are stated here
because the staged records in which they were made — including the pre-registrations whose criteria
failed — are archived with the code (§10), so a reader can check what we said before as easily as
what we say now. **A paper that hides its own retractions is worth less than one that shows them.**

| # | what we claimed | what replaced it |
|---|---|---|
| 1 | The blanket γ ∈ [0,7] prior applies to the solar-wind index. | **Our error, and the origin of §4.** It cannot reach seven published values. Corrected before any of §4 was measured. |
| 2 | J1017−7156's chromatic amplitude was "a prior finding". | **Withdrawn.** It is data-driven: the amplitude moves by 0.00 dex under every alternative index prior tested. |
| 3 | Adding a free red process drops J1600−3053's common amplitude by 1.3 dex. | **Withdrawn** (the comparison also changed the white noise), then **partly reinstated** with the confound removed at **−1.22 dex** — with the caveat that that pulsar's run clears only the relaxed stability rule and falls below our own ESS floor. |
| 4 | "The interesting effect of the mitigation is the interval width, not the central shift." | **Withdrawn.** At full coverage the width blow-up is gone (2.54 → 0.29 dex); it was coverage, not physics, and §6.2 explains exactly how. |
| 5 | The per-pulsar control bar for §6.3 is 0.144 dex (6 controls), then 0.463 dex (12 controls). | **Both are conditional.** Over the six controls that clear our ESS floor the bar is 0.144 again — the tripling was itself a mixing artefact, and the bar is quoted with its control set attached. |
| 6 | A released ephemeris carries an "unphysical" negative Shapiro amplitude. | **Narrowed.** A negative central value for a weakly detected orthometric H₃ is expected behaviour of that parameterisation (Freire & Wex 2010). The surviving claim is only that the file as released will not build in `PINT`. |
| 7 | The lowest printed γ_SW interval edge is −3.14 (J1327−0755). | **Corrected** to **−3.21 (J1811−2405)** by our own re-derivation, which caught an error in our own pre-registration. |
| 8 | The solar-wind variant's control failed, voiding its result. | **Re-specified and passed** (§4.2, §4.3): the control had been defined by the sign of the published value rather than by whether the value was measured. |
| 9 | The product-level mitigation shift is +0.259 dex (82 pulsars) and significant. | **Withdrawn as a magnitude claim** (§6.3): at full coverage +0.257 ± 0.212 dex, 1.2σ. The paired per-pulsar result stands. |
| 10 | Our earlier text named four pulsars in the §4.3 control set. | **Five.** Our own artifact listed five (it also holds J1909−3744, the most tightly measured γ_SW row in the column); the prose dropped one. Found by re-deriving rather than re-reading, which is the whole point of §10. |

Two further defects found and fixed in the software stack are recorded because they would silently
affect anyone reproducing this table: a bug in the released `enterprise` version that zeroes the
Gaussian-process prior matrix whenever a chromatic index is sampled (a guaranteed crash, not a
silent error), and jump proposals in `enterprise_extensions` that fail under NumPy 2.

Three properties of the released ephemerides are recorded for the same reason, none of them a
result: eight ephemerides do not reproduce their own recorded `TRES` until one weighted-least-squares
refit is applied (seven then do); the `TRACK -2` directive present in twelve files is inert for this
data set, which we checked rather than assumed; and one file (J1825−0319) will not build in `PINT` as
released, for the reason in row 6 above.

## 8. Threats to validity

- **The wide-prior range is selected from the answer** (§4.2). It establishes reproducibility, not
  correctness of the prior.
- **The census measures our posteriors under two priors we chose** (§4.3). It states what a
  reproducer can determine from public data. It cannot state what the collaboration's chains did,
  because their prior is unpublished — which is the point.
- **Our stability rule was relaxed mid-campaign.** Both outcomes are reported throughout; the
  relaxation is a strict weakening, so nothing already accepted was lost, and the pulsars it admits
  agree better than the array as a whole.
- **Our ESS floor is a negative result about itself** (§2.4): it does not improve agreement with the
  published table, and we do not claim it does.
- **The census is complete at 26 of 26, but its last row leans on the relaxed rule.** J1525−5545,
  the array's slowest model, clears only the scale-relative stability rule and not the absolute one,
  and its minimum effective sample size is 86 — below our own floor. It classifies as unconstrained
  under both priors, which is also what its printed interval (width 3.44) says on its own, so no
  count turns on it; but a reader should know which row it is.
- **The prior-art sweep is not exhaustive.** It rests on a citation graph from one provider plus a
  count from another, because two citation services refused automated access.

## 9. What would fix it

Three changes, each the size of a caption, would make this table self-contained.

1. **Print the prior range beside each parameter column.** This is the one that matters. Without it,
   seven published rows cannot be reproduced by anyone who has to guess, and two more look
   constrained when they are not.
2. **Mark the rows whose 68% interval reaches the prior floor.** 66 of 83 in one column, 19 of 26 in
   another; the marking costs a symbol and tells a reader which entries are measurements.
3. **State in the caption that a MAP outside its interval indicates a prior-limited posterior**
   rather than an error, since the caption already flags that it happens.

We would add one recommendation to ourselves and to the field: quote a factorised-likelihood
amplitude with its pulsar count and a composition jackknife, not only its credible interval (§6.2).

## 10. Data availability and reproducibility

All input data are public (doi:10.57891/j0vh-5g31). All model definitions, declared priors, sampler
configuration, per-run summaries with per-parameter medians, intervals, acceptance rates and
effective sample sizes, the parsed published table, the per-pulsar marginal posteriors entering the
factorised products, and every analysis script that produced a number in this paper are deterministic
and are archived at **[PLACEHOLDER — Zenodo DOI]**. The pre-registrations, including the ones whose
criteria failed, are archived with them.

**This is a hard requirement on ourselves, not a courtesy.** A paper whose central observation is
that a published table does not state its priors would be self-defeating if it did not publish its
own.

## Acknowledgements

We thank the MPTA collaboration for a data release complete enough that this work was possible
without asking them for anything. [PLACEHOLDER — software and facility acknowledgements.]

## References

- Freire, P. C. C. & Wex, N. 2010, MNRAS 409, 199 — arXiv:1007.0933
- Goncharov, B. & Sardana, S. 2025, MNRAS 537, 3470 — arXiv:2409.03661
- Hazboun, J. S., Simon, J., Siemens, X. & Romano, J. D. 2020, ApJL 905, L6 — arXiv:2009.05143,
  doi:10.3847/2041-8213/abca92
- Hazboun, J. S., Simon, J., Madison, D. R., et al. 2022, ApJ 929, 39 — arXiv:2111.09361
- Miles, M. T., Shannon, R. M., Reardon, D. J., et al. 2025, MNRAS 536, 1467 — arXiv:2412.01148,
  doi:10.1093/mnras/stae2572
- Miles, M. T., Shannon, R. M., Reardon, D. J., et al. 2025 (companion GW paper) — arXiv:2412.01153
- Susarla, S. C., Chalumeau, A., Tiburzi, C., et al. 2024, A&A 692, A18
- Taylor, S. R., van Haasteren, R. & Wang, Y. 2022, PhRvD 105, 084049 — 2022PhRvD.105h4049T
- van Haasteren, R. 2024, ApJS 273, 23 — arXiv:2406.05081
- [PLACEHOLDER — software citations: `enterprise`, `enterprise_extensions`, `PINT`, `tempo2`,
  `PTMCMCSampler`, and the ESS estimator (Geyer 1992). See §11.]

---

## Appendix A — number provenance

Every number in the text is re-derived from a committed artifact by `scripts/m5_paper_numbers.py`,
which emits an audit table of 105 rows in the form *claim → value → artifact → field*, and
`scripts/m5_paper_check.py` verifies the drafted text against it. The audit table is reproduced in
[`M5-ess-floor-sw-census-and-the-paper.md`](M5-ess-floor-sw-census-and-the-paper.md) §6. No number in
this paper was transcribed from prose, including our own.

## Appendix B — figures and tables intended for the paper

| # | content | file |
|---|---|---|
| Fig. 1 | agreement per pulsar, published vs reproduced, all 588 values | `figures/m3_agreement.png` |
| Fig. 2 | the solar-wind census: γ_SW and log₁₀A_SW 68% widths under both priors, classified | `figures/m5_sw_census.png` |
| Fig. 3 | the factorised product's growth curve and its one-pulsar transition | `figures/m4_fl_growth_fl.png` |
| Fig. 4 | the seam-(b) product-level shift against its jackknife and subset spread | `figures/m5_seamb_null.png` |
| Table 1 | agreement summary and the twelve disagreements | §3 |
| Table 2 | the census classes | §4.3 |
| Table 3 | corrections to our own earlier analysis | §7 |
| (supp.) | all 83 published log₁₀A₁₃/₃ rows sorted by interval width | `figures/m4_table_audit_a13.png` |

---

# NOT PART OF THE PAPER

## 11. What remains before this could be submitted

**State: DRAFT — NOT SUBMITTED. Nothing has been sent to anyone.** In rough order of who must do it:

**Human steps (Matthew's, and only his):**

1. **Author, affiliation, ORCID.** Every author field is a placeholder.
2. **The archive DOI (§10).** This is the one blocking item that is not a measurement. Everything
   §10 promises exists on disk and is deterministic; depositing it under a DOI requires an account
   and a publish action, and a paper making this argument cannot go out without it.
3. **Choice of venue.** The draft is written to A&A/MNRAS short-paper length. MNRAS is the venue of
   the paper being reproduced, which is an argument for it.
4. **Whether to contact the collaboration first.** A short, plainly worded paragraph about the γ_SW
   prior is drafted inside the companion Research Note, marked DRAFTED — NOT SENT. Sending it before
   submission would be the courteous order and is entirely his call.
5. **Whether the companion Research Note goes out first**, in which case this paper cites it.

**Work still owed by the analysis, all of it small:**

6. **Software and facility citations.** The reference list carries a placeholder for
   `enterprise`, `enterprise_extensions`, `PINT`, `tempo2`, `PTMCMCSampler` and the ESS estimator.
   Each needs a verified bibliographic record before submission; the versions used are recorded in
   the archive but the citations are currently UNSOURCED in this draft.
7. **A prior-art re-check at submission time.** The last sweep found no work re-analysing or
   auditing this table among the 44 citing works, no erratum, and no prior file anywhere in the
   release, but it is dated and two citation services refused automated access. It should be redone
   the week of submission.
8. **§2.2's software description** should name exact versions inline once the archive is minted, so
   that the version-dependent claim in §4.1 is anchored on both sides.
9. **Trim the abstract to the venue's limit.** It is 333 words as drafted; MNRAS caps abstracts at
    250 and A&A at 250. Nothing in it is decoration, so the trim is a real editorial choice about
    which of the four results leads.
10. **A final read for tone.** The paper's argument only works if it is unmistakably a contribution
    rather than a complaint. §1, §4.4 and §9 carry that load; they should be re-read cold before
    anything is sent.

## 12. What this draft deliberately does not contain

No Bayes factor, no detection or evidence claim, no Hellings–Downs analysis, no continuous-wave
search, no anisotropy result, and no statement about any other PTA's noise models. No claim that any
published value is wrong. No submission, no account, no upload, nothing sent.
