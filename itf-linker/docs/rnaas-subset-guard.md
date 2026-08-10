# RNAAS draft — subset fits and the RMS gate

> **Front matter (not part of the note; excluded from the word count).**
>
> **Word count: 1,499 words** — title through references inclusive, counting the title,
> author line, abstract, section headings, every cell of the table, its caption and
> footnote, and the reference list. The RNAAS limit is 1,500 with 150 reserved for a
> required abstract: this abstract is **146 words** and the rest of the note is **1,353**,
> so both budgets are met, with 1 words spare on the total and 4 on the
> abstract. That is much tighter than the 203 spare of the 2026-08-06 draft: correcting the
> statement of the MPC's criteria and adding the ground-truth result in §4 cost most of the
> margin. Counted by stripping this front-matter
> block, removing Markdown syntax characters (`| * # > _`), and counting whitespace-
> separated tokens containing at least one alphanumeric character; the one-liner that
> produces it is recorded in `rnaas-notes.md`.
>
> **One table, no figure — and why.** RNAAS permits one or the other. The finding is a
> comparison of exact rates across four runs, and every one of those rates needs its
> denominator visible to be worth anything: "84.4%" means nothing without "of 11,113
> converged fits", and the second rate — the guard's effect *restricted to solutions our own
> acceptance gate already accepts* — is the load-bearing number and cannot be read off a
> bar chart. Four rows of five numeric columns gives a reader every count and every
> denominator to check against the archived run reports, which a plot of four rates cannot.
> The alternative considered and rejected was a scatter of
> residual RMS against used-observation fraction, which would show the mechanism vividly but
> would carry no denominators, would need a log axis to be legible, and would answer a
> weaker question ("are these correlated?") than the table answers ("how often does an
> RMS-based filter accept a subset fit?"). Two sentences of prose (§3) recover most of what
> that figure would have shown.
>
> **Status: draft only.** Nothing here has been submitted anywhere, and the bibliographic
> details in the reference list have not been verified against ADS — see `rnaas-notes.md`.

---

# A wrong link need not raise the residuals: subset fits and the limits of an RMS gate in archival minor-planet linking

**Matthew Potts**, Independent Researcher

## Abstract

Pipelines that link archival astrometry propose associations from a hypothesis grid and
filter them on the residual RMS of a fitted orbit. That filter is weakest where it is most
needed. In a HelioLinC-style linker over the Minor Planet Center's Isolated Tracklet File, a
supplementary check — credit a converged fit only if the solver used at least 80% of the
observations and those still span three nights — rejected 6.4% of converged fits from
survey pipelines, 74.2% from a 387-hypothesis main-belt grid, and 84.4% from a
2,555-hypothesis 0.55–50 AU grid. Nothing
about the check changed between those runs. Restricted to solutions already passing this
pipeline's acceptance gate, itself stricter than the MPC's published rule, it rejects 3.0%,
58.0% and 79.5%. A wrong association converges on the subset belonging to one object,
reporting excellent residuals obtained by discarding the rest. Of twenty-six independently
confirmed links, it rejects none.

## 1. The question the published criteria do not ask

The Minor Planet Center's Isolated Tracklet File (ITF) holds roughly 9.3 million astrometric
observations that no pipeline ever linked to an orbit. Recovering orbits from it is a
hypothesis-grid problem: assume a heliocentric distance and radial velocity, propagate every
tracklet to a common epoch, cluster, and fit the clusters. The MPC publishes the criteria an
ITF-to-ITF identification must meet: three distinct nights and a three-day arc before
fitting, and after it, rejection only on non-convergence or when *every* clause of an
arc-length rule holds at once — a short arc **and** RMS > 0.25″ **and** insufficient orbit
quality (σ(a), σ(q) < 0.05 AU, σ(i) < 0.5°, σ(e) < 0.05, e < 0.5).

Because those clauses are conjunctive, a converged fit with RMS ≤ 0.25″ is never
quality-tested: the published filter is *more* permissive than a plain RMS ceiling.
The pipeline here applies a stricter gate — an unconditional 0.25″ ceiling plus the σ limits
on three-night links — and every rate below is measured against it, which understates the
problem rather than overstating it.

Neither rule asks whether the fitted orbit accounts for all of the observations submitted
with it. Least-squares orbit determination is free to reject observations, and a wrong
association gives it every reason to: the solver converges on the subset belonging to one
object, drops the rest, and reports an RMS that is not merely acceptable but frequently
excellent — because it obtained that RMS by discarding the observations that disagreed. The
behaviour is not exotic. It appeared during this pipeline's Find_Orb validation on a single
genuine object: a noisy 49-day arc of (433) Eros yielded a converged solution using 6 of 24
observations, RMS 0.225″, and a semimajor axis wrong by a factor of nine.

The supplementary guard adopted in response is deliberately crude. A converged solution is
credited only if Find_Orb used ≥ 80% of the observations, and the observations it actually
used still span three distinct nights. It is one threshold and one count; it is not one of
the MPC's criteria; and its rejection rate turns out to depend almost entirely on where the
associations came from.

## 2. The measurement

Four runs of the same pipeline, over the same source file, with the same fitter, the same
0.25″ RMS ceiling and the same guard at the same settings. Only the provenance of the
associations differs. Rows 2 and 3 differ in the hypothesis grid alone — its distances, and
the window length each band's orbital curvature permits — with everything downstream held
fixed: the narrower grid was re-run as one band of the wider configuration and reproduced
the earlier run's proposal, refusal, recall and precision figures digit for digit, so the
intervening rewrites are controlled for.

**Table 1.** Rejection rate of the subset guard by provenance of the associations. Column 5
counts converged fits meeting this pipeline's acceptance gate (an unconditional 0.25″ RMS
ceiling plus the σ limits on three-night links, stricter than the published rule on both);
column 6 is the subset of those the guard nevertheless rejects — the solutions an RMS-based
filter would have passed.

| Associations came from | Distance hypotheses | Converged fits | Rejected by the guard | Meet our acceptance gate | …of which guard-rejected |
|---|---:|---:|---:|---:|---:|
| Survey pipelines (survey-made groupings, whole file) | — | 917 | 59 (6.4%) | 132 | 4 (3.0%) |
| 1.4–5.6 AU grid, 2023–2026 observations | 387 | 5,950 | 4,413 (74.2%) | 497 | 288 (58.0%) |
| 0.55–50 AU grid, 2023–2026 observations | 2,555 | 11,113 | 9,383 (84.4%) | 1,237 | 983 (79.5%) |
| 0.55–50 AU grid, 1995–2023 observations ᵃ | 2,555 | 1,738 | 874 (50.3%) | 431 | 313 (72.6%) |

ᵃ A deliberately best-ranked 1.08% sample of that slice's 412,929 gated links, not a random
one; its rates are therefore optimistic. It is included because it is the one run that does
not fit the simple monotonic story — see §4.

## 3. The mechanism, and why RMS cannot see it

Residual RMS is not uncorrelated with subset fitting — over the third row, median RMS is
0.39″ for guard-rejected fits against 0.21″ for the rest. But a 0.25″ threshold does not act
on that difference usefully. Of the 4,802 converged fits with RMS ≤ 0.25″ in that run, 3,842
(80%) are subset fits; 583 of the 983 solutions that pass our acceptance gate and fail the
guard have RMS ≤ 0.10″. Discarding observations improves the residual
of what remains, so the statistic meant to detect a bad association is partly produced by
it.

The limit is instructive. Six orbital elements fitted to three observations have six
residuals and zero degrees of freedom, so the RMS is identically zero and the formal
uncertainties are small. Eleven such fits sit in that run's 983. One, from three
observatories over three nights, used 3 of its 11 observations and returned RMS 2 × 10⁻¹⁰″,
a = 1.4240 ± 0.0237 AU, q = 0.7083 ± 0.0066 AU — inside all four of the MPC's σ limits,
formally an Apollo, and, at an inclination of 0.017° ± 0.004°, an artefact. What catches it
is the fifth published quality condition, not any uncertainty: e = 1 − q/a ≈ 0.503 just
exceeds the e < 0.5 bound. The formal uncertainties it passes cleanly.

## 4. What this does and does not establish

The grid is not simply failing to reach its targets: against JPL Horizons astrometry of
thirteen real objects, the wide grid recovers 11 to the exact tracklet where the narrow grid
recovers 4, with none merged into a neighbour. What the widening did not buy was candidates.
It raised the hypothesis count 6.6× and yielded 26 more survivors and one fewer that is
numerically well constrained (140 against 141); across both slices, 6,029 converged
near-Earth orbits produced two surviving near-Earth candidates, both Amors the narrower grid
already reached.

This is one guard, at one threshold, in one pipeline, on one file, and it should be read as
suggestive for linking pipelines generally rather than established for them. The four rows
differ in more than the hypothesis count: row 1's associations were made by surveys rather
than by any grid and cover the whole file, so the 6.4% → 74.2% step measures provenance and
population together. The rates condition on convergence, which is itself provenance-
dependent (94%, 44%, 27%); per link submitted, the guard's rejections are 6.1%, 32.4% and
23.1% — not monotonic. Row 4 shows the same wide grid rejecting half rather than
five-sixths on older observations, though restricted to published-criteria passers the two
wide-grid runs agree far better (72.6% against 79.5%). And an 80% threshold with a
three-night rule is a blunt instrument that will reject some correct links whose astrometry
merely contains an outlier.

**How often it rejects a correct link is measurable, and the answer is zero of 26.** A daily
archive of the ITF gives ground truth independent of every gate here: a link whose members
have all since left the file is one somebody else independently made. Twenty-six exist, all
in the wide-grid run. The guard rejected none on its own; each it flagged was already failing
the acceptance gate, which discarded 22 of the 28 fitted rows. With *n* = 26 and a sample
biased toward easy links, this is a floor, not a rate.

The practical claim is narrower than the numbers look, and is this: on the widest grid a
check the MPC does not publish rejects more converged solutions than the published 0.25″
residual ceiling does — 9,383 against 6,311 — where on survey-made associations the ordering
is the other way round (59 against 263); its importance grows with the speculativeness of
the associations; and a pipeline that widens its search without adding a check of this kind
will not notice that it has stopped producing objects.

**Software and data.** The ITF is public and unauthenticated. Every figure above is a stored
field in the four archived run reports (`m1-report.json`, `m3-fits.json`, `m4-new.json`,
`m4-old.json`); columns 5 and 6 of Table 1 are recomputed from the per-fit records those
files carry.

## References

Gray, B., Find_Orb, https://www.projectpluto.com/find_orb.htm ·
Holman, M. J., Payne, M. J., Blankley, P., Janssen, R., & Kuindersma, S. 2018, AJ, 156, 135 ·
Nugent, C., Tan, N., & Bauer, J. 2025, PSJ, 6, 18 ·
Minor Planet Center, identification acceptance criteria,
https://www.minorplanetcenter.net/mpcops/documentation/identifications/additional/
