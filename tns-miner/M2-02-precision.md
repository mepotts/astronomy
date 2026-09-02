# M2-02 — Precision, measured: the M1 candidate list is not submittable

**Date:** 2026-08-24 · **Protocol frozen first in [`M2-01`](M2-01-preregistration.md) Part A** ·
`scripts/m2_vet_evidence.py`, `scripts/m2_precision.py` →
`out/m2_vetting.csv`, `out/m2_precision.json`, `out/vet/*.png`,
`out/m2_vet_diag_m1list.csv`, `out/m2_xmatch_m1list.csv`

---

## The headline

> **Precision of the 184-object M1 candidate list = 3.5%, 95% CI [1.1%, 15.6%].**
> Two of 40 hand-vetted objects are plausible real transients. **40% are image
> artifacts and 53% are known or evident variables.**
>
> The pre-registered decision rule of `M2-01` A5 — *"if the strict whole-list
> precision has a 95% upper bound below 0.20, the list is declared NOT
> SUBMITTABLE"* — **fires. The M1 candidate list is NOT SUBMITTABLE.**
>
> The second pre-registered rule also fires: tiers A+B were vetted as a census
> (8 of 8) and yielded **one** plausible transient, below the threshold of two.
> **`M1-05`'s declared triage does not work either.**

This is the number `M1-04` could not claim, and it is the reason M1's 68.6% recall
was never sufficient on its own. A filter can recover two thirds of somebody
else's designations and still produce a list that is 96% junk, because recall is
measured on objects that were real by construction and precision is not.

## What was vetted, and how

| | |
|---|---|
| population | the 184 rows of `out/m1_candidates_recent.csv`, untouched |
| tier A + B | **census, 8 of 8** |
| tier C | **random sample, n = 32**, `default_rng(20260824)` over the sorted oids, drawn once and not re-rolled |
| total vetted | **40** |
| evidence per object | cutout triplet (science/template/difference), full per-band light curve with the per-band `magnr` level, alert diagnostics, and six archival catalogues via CDS X-Match |
| rubric | `M2-01` A3, four classes, mechanical rules, first rule that fires wins |

One change was made to the *rendering* of the evidence before any classification
was finalised, and it mattered: difference stamps were first drawn on a zscale
grey stretch, which hides both faint real sources and dipoles. They are now drawn
**symmetrically about the median at ±6σ (robust MAD) on a diverging colour map**,
so a positive lobe is red, a negative lobe is blue, and a bipolar subtraction
residual is unmistakable. Every classification in this document was made on the
second rendering. Sheets are in `out/vet/`.

## The result

| class | n | share |
|---|---|---|
| **artifact** | **16** | **40.0%** |
| **known_variable** | **21** | **52.5%** |
| **plausible_transient** | **2** | **5.0%** |
| undecidable | 1 | 2.5% |
| *of which* `known_cv_outburst` (real outburst, already catalogued) | 0 | — |

Rule that fired: R2b (persistent variability, no quiescent floor) 16 · R1a
(bipolar residual / saturated star) 14 · R2c (the Mira trap) 5 · R3 (plausible
transient) 2 · R1c (not a clean PSF) 2 · R4 (undecidable) 1.

### By stratum

| stratum | N | vetted | plausible | precision | Wilson 95% |
|---|---|---|---|---|---|
| tier A | 3 | **3 (census)** | 1 | 0.333 | [0.061, 0.792] |
| tier B | 5 | **5 (census)** | 0 | 0.000 | [0.000, 0.434] |
| tier C | 176 | 32 | 1 | 0.031 | [0.006, 0.157] |
| **whole list (stratified)** | **184** | **40** | **2** | **0.035** | **[0.011, 0.156]** |

Both pre-registered figures agree: **strict** (undecidable counted as a failure)
0.0353, **lenient** (undecidable dropped) 0.0363. The stratified normal interval
is [0.000, 0.087]; because the normal approximation is unreliable at a proportion
this close to zero, the interval quoted in the headline is the more conservative
one built from the tier-C Wilson bounds with the two censused strata entered
exactly: **[1.1%, 15.6%]**. Both upper bounds are below the pre-registered 0.20.

## The three things that broke it

### 1. `drb ≥ 0.90` does not see a bad subtraction. Forty percent of the list is one.

Sixteen of forty objects are image artifacts, and **every one of them has
`drb ≥ 0.913`** — the minimum deep-real-bogus score across all sixteen. The
median is 0.989. ZTF's real-bogus classifier is asking *"is there a real source in
this stamp?"*, and for a registration dipole on a bright star the answer is yes:
there is a genuine positive lobe. It is not asking *"is this source's flux
excess real?"*, which is the question a discovery report depends on.

The signature is unmistakable once the difference stamp is stretched properly: a
positive lobe with a deep negative lobe a pixel or two away, produced when the
science and template images are not perfectly registered or the PSF match is
imperfect. `ZTF18abbdqqd` — one of M1-05's "also worth a look" objects — sits on
the edge of a saturated-star mask in a stamp full of bipolar residuals.

**This contaminant is invisible to every cut in the M1 filter, and none of the
three fixes M2 was asked to make addresses it.** What does address it is in
`M2-03` fix (d): the *sign history* of the alerts, which is a column, not an image.

### 2. The catalogue layer leaks. It is reading one catalogue when it needs four.

| catalogue | matches among the 40 |
|---|---|
| Fink's `d:vsx` (what the M1 filter actually reads) | **1** |
| **ATLAS variable stars** (`J/AJ/156/241`) at ≤ 5″ | **14** |
| Gaia DR3 variability classification (`I/358/vclassre`) | 2 |
| **any of the three** | **16 of 40 (40%)** |

The M1 filter's entire notion of "uncatalogued" comes from Fink's per-alert
cross-match columns. An independent match against the ATLAS variable-star
catalogue — 4.7 million objects, not in Fink's panel — finds a counterpart within
about one arcsecond for **fourteen** of the forty. Two more carry a Gaia DR3
variability classification, both `AGN`. So **40% of the list was already
catalogued as variable and the filter did not know.**

### 3. The Mira trap is not theoretical. It ate the best candidate in the list.

`M1-06` named the classic false positive: *"Unfiltered CCDs over-respond to red
objects, so long-period variables masquerade as novae."* Measured:

- **17 of 39** objects with a Gaia colour have **BP−RP > 2.0**;
- **13 of 34** with 2MASS photometry have **J−K > 1.0**;
- five objects fire rule R2c on all three of its conditions.

**`ZTF18abobdzu`, written up in `M1-05` as the single best candidate in the list,
is one of them**: Gaia BP−RP = **5.18**, 2MASS J−K = **1.69**, G = 12.70, an
ATLAS variable-star counterpart 0.39″ away, and 700 alerts showing seven years of
continuous detection with no quiescent floor. It is a red long-period variable in
the galactic plane — the exact object class M1-06 warned about, sitting at the top
of M1's list.

## The one cheap discriminator M1 had and never used

**39 of 40 objects have a Gaia DR3 counterpart within 3″.** The single exception
is `ZTF19acbplek` — and that is one of the two plausible transients.

The physics is simple and it is the whole thesis of the front: a CV or nova
progenitor is faint. If Gaia sees a star at that position, the "outburst" is
usually a modest variation on a star that was always there. If Gaia sees nothing
and PS1's reference magnitude is ~22, the quiescent object is below G ≈ 21 and an
18th-magnitude detection there is a genuine 4-magnitude event.

This is not applied as a cut in M2 — it was found by looking at outcomes, and the
pre-registration rule forbids choosing a threshold that way. It is reported here,
carried as a **column** on every candidate row in `M2-04`, and named in the
operating guide as the first thing a human should look at.

## The two survivors

**`ZTF19acbplek` — 17:48:04.23 +08:03:39.8, |b| = +17.7°** *(tier A)*
Compact clean positive PSF in the difference, no dipole. **No Gaia DR3 source
within 3″, and no VSX, ATLAS-VS or Gaia-variability match at all.** A PS1 point
source 0.11″ away with reference magnitude 21.88 — quiescence below Gaia's limit.
Fifty-one alerts in episodic clusters at 17.7–19.6 separated by months to years,
returning to non-detection in between. **A textbook uncatalogued dwarf nova**, and
the only object in the sample where every strand of evidence agrees.

**`ZTF22aaqkjgl` — 21:29:34.7 −37:55:47, |b| = −37.9°** *(tier C)*
Compact clean positive PSF, no dipole, no archival variability match. A single
monotonic ~2 mag rise from 20.5 to 18.5 over roughly 400 days, then a plateau —
a genuine excursion from a definable baseline, and not repeated, which is why R2b
does not fire. **Caveat recorded at the moment of vetting, not afterwards:** a
400-day rise is not nova-shaped. An AGN turning on, or a slow symbiotic, are live
alternatives. It passes the rubric; it is not a good candidate.

## What this does and does not say

**It does say** the M1 candidate list must not be submitted from, that its
declared triage did not identify the good objects, and that the two best-named
objects in `M1-05` are a red long-period variable and a bad subtraction.

**It does not say** the front is worthless. Recall was real: `M1-04`'s rewind
recovered 70 of DCAP's 102 designations from pre-report data, and that is not an
artifact of a loose filter — the negative control was 6.9× lower. What the
precision measurement shows is that **the M1 filter was tuned to not miss and had
nothing at all tuned to reject**, and the fresh-data consequence is a list
dominated by contaminants. `M2-03` measures what closing that costs.

## Limitations, stated

1. **Not blind.** The vetter could see the tier and M1's one-liner. Mitigated by
   freezing the rubric in mechanical form first, and by recording the rule that
   fired and the evidence for every object in `out/m2_vetting.csv`, but not
   eliminated.
2. **n = 32 in tier C** is what fits at this evidence depth. The interval is wide
   at the top end (15.6%) and it is the number that should be quoted, not 3.5%
   alone.
3. **Rule R2a under-covers ATLAS-VS's vocabulary.** The pre-registered periodic
   family list does not contain ATLAS's own `dubious` and `IRR` classes, so R2a
   never fired on the eleven `dubious` and three `IRR` matches; they were caught
   by R2b or R2c instead. A future pre-registration should enumerate each
   catalogue's actual class vocabulary rather than a generic family list.
4. **Precision is measured on one night's pass.** 184 candidates from MJD
   61274–61277. Whether it is stable across the season is unmeasured.
