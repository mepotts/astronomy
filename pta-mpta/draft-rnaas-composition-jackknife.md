# DRAFT — NOT SUBMITTED

*Research Note of the AAS, draft. Nothing here has been sent to any journal, any collaboration, or
any person. Author, affiliation and ORCID are placeholders and are Matthew's to fill or delete.*

*Venue limits verified live from the AAS site on 2026-08-24,
<https://journals.aas.org/research-notes/>: **"1,500 words or fewer"**, **"no more than a single
figure or table (but not both)"**, abstract required (since 2020-05-01), **"moderated but not
edited"** and not peer reviewed, **"searchable in ADS and fully citable"**. The stated scope is
"works in progress, comments and clarifications, null results, or timely reports of observations in
astronomy and astrophysics"; this note is a clarification about a technique, with a null result of
our own as the worked example.*

*Every number below is re-derived from a committed artifact by
`scripts/m6_methods_note_numbers.py` and the drafted text is checked back against that artifact by
`scripts/m6_methods_note_check.py`. The audit table is in
[`M6-close-the-paper.md`](M6-close-the-paper.md) §4. Companion full paper:
[`draft-paper-mpta-noise-reproduction.md`](draft-paper-mpta-noise-reproduction.md).*

**Word count of the note proper (Title → end of "Scope"), excluding Table 1 and the reference list:
1,300** (RNAAS limit 1,500).

---

**Title:** A Factorised-Likelihood Pulsar Timing Array Amplitude Needs a Composition Jackknife, Not
Only a Credible Interval

**Authors:** [PLACEHOLDER — Independent Researcher], ORCID [PLACEHOLDER]

## Abstract

The factorised likelihood builds a common-signal amplitude posterior as the renormalised product of
per-pulsar marginals, and its credible interval is routinely quoted as that amplitude's uncertainty.
That interval is conditional on the set of pulsars in the product and carries no term for the set
itself. That such products lean on a few pulsars is established (Reardon et al. 2023; Johnson et
al. 2022), and Larsen et al. (2025) publish a drop-one-pulsar analysis of a difference of two of
them; what has not been published is how that dependence compares with the interval routinely
quoted beside it. Rebuilding two 83-pulsar products from the public MeerKAT Pulsar Timing Array
4.5-yr release, we find the tighter of the two has a 68% width of 0.149 dex and a delete-one jackknife
standard error over pulsar composition of 0.256 dex — **larger than its own credible interval** —
while its growth curve shows the width collapsing from 1.92 to 0.37 dex at a single pulsar's
addition. A difference of two such products tested against a fixed threshold is therefore not a
significance test. We give our own withdrawn claim as the worked example, and recommend three
numbers to quote alongside any factorised amplitude.

## The gap

The factorised likelihood (Taylor et al. 2022) obtains a common-signal amplitude
posterior by multiplying the per-pulsar marginal posteriors for that amplitude and renormalising.
It is cheap, it parallelises trivially, and pulsar timing arrays use it widely — for staged growth
curves, for dropout and subset tests, and for comparing noise-model configurations. Its output is a
posterior, and its 68% credible interval is quoted as the uncertainty on the amplitude.

That interval answers "how well is the amplitude determined **by these pulsars**?" It does not
answer "how much would it move if the set were slightly different?", and for this estimator the
second question can have the larger answer. The terms in the product are not exchangeable: a handful
of pulsars carry most of the constraint, so the product inherits their idiosyncrasies while the
interval, computed after the multiplication, cannot see them.

**What is already known, and what this adds.** Reardon et al. (2023) name the three pulsars
"likely to dominate the factorized likelihood"; Johnson et al. (2022) examine how a factorised
upper limit responds to pulsar ordering and dropout; and Larsen et al. (2025), comparing two
versions of one joint data set, publish exactly the drop-one-pulsar analysis of a *difference*
of two factorised products, concluding that "the overall discrepancy is sensitive to systematic
errors in the individual pulsars". **This note claims none of that.** It adds two numbers and a
rule: the composition sensitivity measured on the same axis as the product's own credible
interval and compared with it; the accumulation resolved to the single addition at which it
happens; and the consequence for anyone testing a difference of two products against a fixed
threshold.

## The measurement

We rebuilt the MPTA 4.5-yr single-pulsar noise models from the public release (Miles et al. 2025;
doi:10.57891/j0vh-5g31) with an independent implementation, and formed the factorised amplitude at
fixed γ = 13/3 over all 83 pulsars in two configurations that differ only in whether every pulsar
carries a free achromatic red process (Table 1). Both are consistent with the published 83-pulsar
value of −14.28 ± 0.21.

For each product we computed a delete-one jackknife over pulsars: drop pulsar *i*, re-form the
product, and take the usual jackknife standard error of the resulting mode.

> The product with the **narrower** credible interval is the **more** composition-sensitive of the
> two. Its 68% width is **0.149 dex** and its composition jackknife is **0.256 dex**, a ratio of
> **1.72**. For the other product the jackknife is **0.137 dex** against a width of **0.294 dex**, a
> ratio of 0.47.

Tightness is not stability. A reader who takes either width as the uncertainty on the amplitude
understates the composition dependence — by a factor of nearly two in one case, where the interval
is smaller than the effect it is being used to bound.

The growth curve shows the mechanism directly. Adding pulsars in a random order fixed in advance,
the 68% interval stays 1.9–2.4 dex wide with its lower edge pinned near the prior floor for the
first 57 additions while the mode wanders between −17.1 and −14.5. At the **58th** addition the
width collapses from **1.92 to 0.37 dex** in one step and never returns; over the final ten
additions the mode moves by **0.030 dex**. The 58th pulsar is J1909−3744, the array's single most
informative. This is not √N accumulation, and the pulsar count of a subset product is therefore not
a measure of its information: what matters is whether the strongest constraints are inside it.

## The worked example is our own withdrawn claim

The two configurations of Table 1 differ by a model choice the MPTA itself makes and itself flags as
costing sensitivity. We set out to size that cost, pre-registered a threshold of **0.21 dex** on the
difference between the two products' modes, measured **+0.257 dex**, and declared it significant.

That threshold had no uncertainty attached, and supplying one dissolves the result. The same
delete-one jackknife gives **+0.257 ± 0.212 dex — 1.2σ**. Removing the single most influential
pulsar, J2129−5721, takes the difference to **+0.075 dex**. Four hundred random 52-of-83 thinnings
of the same set give a difference with a standard deviation of **0.340 dex** and a 95% band of
[0.002, 0.407], so a subset version of this statistic carries almost no precision; one particular
subset of ours reads **+0.04 dex**, sits inside that band at its 5.5th percentile, and is not
distinguishable from the full-set value. **We withdraw the product-level magnitude.**

The effect itself is real; it was the estimator that could not carry it. Testing the same question
**pairwise, per pulsar**, without passing through any product, the amplitude moves **down in 49 of
70** pulsars (median **−0.073 dex**; sign test *p* = 0.0011, Wilcoxon signed-rank
*p* = 5.8 × 10⁻⁶), while over the **12** pulsars for which the two configurations are the same model
— a control in which any difference is sampler noise — the shift is consistent with zero (median
+0.0004, Wilcoxon *p* = 0.68). A paired test with a null control resolved at 10⁻⁶ what a difference
of two products could not resolve at 1.2σ on identical data.

## What to quote instead

Three numbers, none of which costs a new chain:

1. **The pulsar count**, always, and whether the set contains the array's strongest constraints. A
   product missing them is not yet an amplitude.
2. **A delete-one jackknife standard error over composition**, beside the credible interval. If it
   exceeds the interval, the interval is not the uncertainty a reader wants.
3. **For any comparison of two products, the composition spread of the difference** — by jackknife,
   or by random equal-sized thinnings. A fixed threshold with no composition term is not a
   significance test.

Where the question is per-pulsar in nature — as a noise-model configuration change is — a paired test
with a same-model control is better behaved than differencing two products, and it is available from
exactly the same chains.

## Scope

This is one array, one 4.5-yr release, a common process at fixed γ = 13/3, and our own reproduction
of it rather than the collaboration's chains; no detection, evidence or spatial-correlation claim is
made or implied anywhere. The jackknife is a heuristic here: the terms of the product are not
exchangeable, which is the point of the note, and the same non-exchangeability makes any resampling
estimate approximate. The ratios above are what one array gave, and the recommendation is that the
number be reported — not that 1.72 is a universal figure.

---

### Table 1

**Two factorised-likelihood common-amplitude products from the same 83 pulsars, and their
composition sensitivity.** The two configurations differ only in whether every pulsar carries a free
achromatic red process. Intervals are equal-tailed 68% intervals of the renormalised product; the
jackknife standard error is delete-one over pulsars. Published comparison value: −14.28 ± 0.21
(Miles et al. 2025).

| product | pulsars | MAP log₁₀A | 68% interval | 68% width | composition jackknife SE | SE / width |
|---|---|---|---|---|---|---|
| favoured single-pulsar models | 83 | −14.44 | [−14.64, −14.35] | 0.294 dex | 0.137 dex | 0.47 |
| every pulsar given a free red process | 83 | −14.18 | [−14.28, −14.13] | **0.149 dex** | **0.256 dex** | **1.72** |
| **difference of the two modes** | 83 | **+0.257 dex** | pre-registered threshold 0.21 dex | — | **± 0.212 dex (1.2σ)** | — |
| growth curve, one-pulsar transition | 57 → 58 | — | at J1909−3744 | **1.92 → 0.37 dex** | — | — |

### References

- Johnson, A. D., Vigeland, S. J., Siemens, X. & Taylor, S. R. 2022, ApJ 932, 105 —
  arXiv:2201.10657, doi:10.3847/1538-4357/ac6f5e
- Larsen, B., Mingarelli, C. M. F., Baker, P. T., et al. 2025, MNRAS 542, 3028 —
  arXiv:2503.20949, doi:10.1093/mnras/staf1420
- Miles, M. T., Shannon, R. M., Reardon, D. J., et al. 2025, MNRAS 536, 1467 — arXiv:2412.01148,
  doi:10.1093/mnras/stae2572
- Reardon, D. J., Zic, A., Shannon, R. M., et al. 2023, ApJL 951, L6 — arXiv:2306.16215,
  doi:10.3847/2041-8213/acdd02
- Taylor, S. R., Simon, J., Schult, L., Pol, N. & Lamb, W. G. 2022, PhRvD 105, 084049 —
  arXiv:2202.08293, doi:10.1103/PhysRevD.105.084049

---

## Notes for Matthew — NOT part of the note

### Why this is a separate note

The composition jackknife turned up while sizing something else, and it is the only result in this
project that is **not** about the MPTA. It is about an estimator that pulsar timing arrays use
widely, it costs no new compute, and it is directly actionable by the people who would otherwise be
its next casualty. Inside the companion paper it is four paragraphs of §6.2–§6.3 that a reader
interested in the technique would never find; on its own it is citable from the methods section of
any factorised-likelihood analysis.

**The prior-art position changed on 2026-08-24 and the note was rewritten for it.** A re-sweep
found Larsen et al. (2025), whose §4.1.4 and Figure 8 already publish the qualitative form of
this claim — leave-one-out over pulsars on a difference of two factorised products, concluding
composition sensitivity. It does not cite the MPTA paper and so appeared in no citing-works list;
the earlier citation-graph sweep could not have found it. The note now leads with that credit.
What survives as new is the comparison of the composition jackknife against the product's own
credible interval, the one-pulsar transition, and the rule about thresholds — and if a referee
judges that too little, the honest answer is that the note should not run.

### The single-graphic choice

RNAAS permits one figure **or** one table. The allowance is spent on Table 1, because the ratio of
jackknife SE to credible interval is the whole claim and it needs both numbers side by side for both
products. The alternative graphic — `figures/m4_fl_growth_fl.png`, the growth curve with its
one-pulsar transition — is in the repository and would be the better choice if the note were
re-scoped around the transition alone.

### Relationship to the other two drafts

- The companion paper keeps §6.2 and §6.3, because the withdrawal of our own claim belongs where the
  claim was made; it cites this note for the general treatment.
- The table-audit Research Note ([`draft-rnaas-mpta-table-audit.md`](draft-rnaas-mpta-table-audit.md))
  is untouched by this: none of its four claims involves a factorised product.
- If both notes go out they are separable, and neither depends on the other. Two RNAAS notes from one
  project is a submission-order question rather than a content one, and it is Matthew's call.

### What this note does not claim

It does not claim that any published factorised-likelihood amplitude is wrong, and it names no
analysis but our own. It does not claim the MPTA's mitigation choice was mistaken — the paper
being reproduced states the sensitivity cost itself, in its own sentence, and the point here is only
that a difference of two products was the wrong instrument for measuring that cost. Every failure
worked through above is ours.

### State

**DRAFT — NOT SUBMITTED.** Submission would additionally need: author, affiliation and ORCID; an AAS
account; and the same citable archive DOI as the other two documents, if the note is to point at the
per-pulsar marginals behind Table 1.
