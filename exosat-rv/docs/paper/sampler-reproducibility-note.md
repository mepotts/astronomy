# A Nested Sampler's Internal Uncertainty Is Not Its Reproducibility

*Matthew Potts · independent analysis · draft 2026-08-13*

Bayesian model comparisons are often decided by a log-evidence difference, ΔlnZ,
quoted with the uncertainty a nested sampler reports internally — a number
describing one integration's numerical precision, not its reproducibility. Running
the same comparison 82 times — one likelihood, one real dataset, varying only the
seed and, separately, the priors and live-point count — the empirical run-to-run
scatter in ΔlnZ exceeds the sampler's quoted uncertainty by 1.1× to 8.1×.
Quadrupling live points shrinks the internal number as expected but not the
scatter, so the understatement grows to 4–5×.

## Setup

We fit two competing Keplerian models (one companion versus two) to the 23-epoch
CD-35 2722 B radial-velocity table published by Hoy et al. (2026, *Nature*), using
`dynesty` (Speagle 2020): random-walk (`rwalk`) proposals, `dlogz = 0.01` stopping,
ΔlnZ = ln Z(2-companion) − ln Z(1-companion) recorded per run. The likelihood is a
Gaussian with jitter added in quadrature (s² = σ_RV² + σ_jit²), identical between
models, with priors shared wherever a parameter is shared. Ten configurations vary
two axes: period handling (fixed; free within bounding windows; or free with both
models equally eccentric) and the jitter/amplitude prior (uniform; linear jitter;
log-uniform amplitude). Seven configurations ran at nlive = 500 (ten seeds each);
three were repeated at nlive = 2000 (four seeds each) as a convergence check — 82
runs in total.

## Result

**Table 1.** ΔlnZ over 82 nested-sampling runs. "Internal" is the sampler's own
quoted uncertainty (quadrature sum of both models' log-evidence errors);
"run-to-run σ" is the empirical scatter across seeds; "ratio" divides the second by
the first.

| priors | period handling | nlive | ΔlnZ (mean ± s.e.) | run-to-run σ | internal | ratio |
|---|---|---:|---:|---:|---:|---:|
| uniform | fixed | 500 | −1.83 ± 0.08 | 0.25 | 0.24 | 1.1× |
| uniform | in windows | 500 | −4.60 ± 0.27 | 0.87 | 0.27 | 3.3× |
| uniform | both eccentric | 500 | −5.51 ± 0.69 | 2.18 | 0.27 | **8.1×** |
| jitter U(0,300) | in windows | 500 | −3.82 ± 0.20 | 0.62 | 0.27 | 2.3× |
| jitter U(0,300) | both eccentric | 500 | −3.37 ± 0.38 | 1.19 | 0.27 | 4.4× |
| K log-uniform | in windows | 500 | −3.77 ± 0.30 | 0.96 | 0.27 | 3.5× |
| K log-uniform | both eccentric | 500 | −1.42 ± 0.44 | 1.40 | 0.27 | 5.3× |
| uniform | fixed | 2000 | −1.50 ± 0.24 | 0.49 | 0.12 | 4.1× |
| uniform | in windows | 2000 | −4.46 ± 0.31 | 0.62 | 0.13 | 4.7× |
| uniform | both eccentric | 2000 | −3.49 ± 0.27 | 0.54 | 0.13 | 4.1× |

Every configuration's mean favours one companion, and 81 of 82 individual runs are
negative; the single exception reaches +0.9 — not this note's point. The uncertainty
columns are. At nlive = 500 the internal estimate sits at ±0.24–0.27 regardless of
configuration, while the empirical scatter over ten seeds spans 0.25 to 2.18:
understated by 1.1× to 8.1×. Quadrupling live points to 2000 shrinks the internal
estimate to ±0.12–0.13, matching its N^−1/2 scaling — but the empirical scatter
barely moves (0.49–0.62), so the understatement *grows*, to 4.1–4.7×.

## Why more live points make it worse

This is consistent with the internal estimate measuring the wrong thing: one
integration's numerical precision, not the variance between independent runs —
which mode a random walk settles into, and how a degenerate posterior region gets
explored. More live points tighten the first without touching the second, so the
two move apart rather than together.

## The motivating case

This test was prompted by Hoy et al.'s tentative second, shorter-period companion: a
nested-sampling comparison at ΔlnZ = +2.622, with quoted log-evidence uncertainties
of ±0.695 and ±0.691 — the same class of internal number examined here. The
system's primary ~171 d companion signal itself reproduces independently from the
raw archival frames in our companion paper (in prep.); this note is not a challenge
to that detection. We did not test their sampler, or how its uncertainty was
computed; the runs above use a different code on their own published table, testing
only whether a comparable gap appears in a similar setting. The honest, conditional
statement: *if* other nested samplers show a similar gap, *then* an uncertainty of
that size may understate the comparison's reproducibility — worth checking before
treating an evidence difference of order unity as decisive.

## Recommendation

Where a model-comparison claim depends on an evidence difference, quote the scatter
of ΔlnZ over several independent runs — different seeds, same setup — rather than
the sampler's internal estimate. Ten runs is enough to see the effect here; three to
five would likely catch it. The internal number remains a useful convergence
diagnostic, not a substitute for an empirical one.

## Scope

This is one likelihood, one dataset, and one sampler (`dynesty`, `rwalk`
proposals). We have not tested other nested samplers, proposal methods, or
datasets; the factor of 1.1–8.1× should not be assumed to transfer. What we think
generalizes is narrower: an internal log-evidence uncertainty is a within-run
number, and checking it against run-to-run scatter costs only a handful of extra
sampler calls.

**Suggested figure (not produced here).** One panel per live-point count;
configurations on the x-axis, ΔlnZ on the y-axis. Plot each seed's result as a
point, the configuration mean as a marker, and two error bars — internal (thin) and
empirical standard error (thick). The gap between them, and its persistence across
panels, is the figure's entire content.

---

*Reproducibility: `scripts/nested_orbits.py` (dynesty 3.1.0) produced the four M28
run files in `data/`; derivation in `M28-RESULTS.md` §7. AI-assisted (Claude,
Anthropic); human-directed and reviewed.*

**Reference.** Hoy, K., Zurlo, A., Peña R., P. A., Köhler, J., et al. 2026, *Nature*.
