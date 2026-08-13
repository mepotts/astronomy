# M11 — The template rebuilt the published way. It suppresses the signal.

**Question:** M9 localised the extraction shortfall to the per-order forward model and named
the template as the leading suspect. Köhler et al. 2025 §2.2 publishes the template recipe
Hoy et al. defer to, and the paper says its results use **two template iterations**. Does
following it close the gap?

**Answer: no. It makes the target look better and the control worse, and the control is
right.** Recovered amplitude on a *known* binary collapses to **41% of its correct value
after a single template iteration**. The apparent gain on CD-35 2722 B is the same effect
seen from the side where the truth is unknown.

**Net movement on the reproduction: none.** The extraction still sits at 776 m/s against
31.44 m/s needed.

---

## 1. What was actually run

viper under WSL, per [`docs/viper-runbook.md`](docs/viper-runbook.md), on the same 18
archive nights. Two changes from M2's configuration, both taken from the published recipe:

1. **`-tpl_wave tell`** instead of the default `initial`. viper's default sets `bervt = 0`
   — **no barycentric correction is applied when co-adding** (viper.py line 616). Köhler
   et al. §2.2 requires it: *"Co-adding several spectra that were taken at different
   barycentric velocities, and are corrected for that, helps reduce residuals from the
   telluric correction."* `tell` uses the telluric-derived wavelength solution, which for
   cell-free CRIRES+ is the physically correct reference.
2. **Two template iterations**, matching the paper.

**A hypothesis died before the run started.** M9 suspected M2's co-added template skipped RV
alignment. Reading the source disproves it: viper.py line 624 divides by `(1 + par.rv/c)`
before co-adding, and line 630 applies exactly Köhler's eq. 14 weighting, `w = T_atm/ε²`.
**viper implements the published recipe faithfully.** The suspicion was wrong and reading
the code was cheaper than testing it.

## 2. The target improves

Combined RVs, equal weights with order 8 dropped (M9's accepted screen) for every run, so
the comparison is like-for-like:

| Run | Combined rms |
|---|---:|
| M2 baseline — single-epoch template, `tpl_wave=initial` | 776 m/s |
| RVs against 1-iteration template | 852 m/s |
| **RVs against 2-iteration template (`tell`)** | **620 m/s** |

viper's own printed figure for the last run is **308.7 m/s**, which looks like a 2.7×
improvement and is not comparable — `vpr.info()` recomputes the RV as a **weighted** mean
(`avg='wmean'`) rather than reporting the `RV` column it writes to `.rvo.dat`. The two
differ by 1.8× here. **Quote the column, not the banner**, or runs stop being comparable
across milestones.

Note also the non-monotonicity: 776 → 852 → 620. That is not a recipe converging.

## 3. The control says the improvement is not real

GJ 229 B, known 12.1-day binary. M3 §4 established that a single-template fit on this
unresolved double-lined pair should recover ~6000 m/s, not the 18070 m/s the masses imply,
and M3 measured 5948.

| Template | Δχ² | Recovered K | vs. correct |
|---|---:|---:|---:|
| **0 iterations** (M3 baseline) | **76.5** | **5948 m/s** | **100%** |
| 1 iteration (`tell`) | 23.7 | 2452 m/s | **41%** |
| 2 iterations (`tell`) | 21.1 | 2360 m/s | **40%** |

**The damage is done by the first iteration and does not recover.** A real, undisputed
signal is suppressed by 59%.

### The mechanism

Self-templating absorbs the signal. The template is built by co-adding the target's *own*
spectra, aligned by their *measured* RVs — but those RVs were measured against a template
that already contains the signal, so the alignment is incomplete and the residual is baked
into the new template. Velocities measured against it are then partly the star measured
against itself, and the amplitude is pushed toward zero.

Köhler et al. flag exactly this hazard: *"The method is straightforward for RV standard
stars... However, the situation becomes more complex when Doppler shifts are present, such
as in the case of a star with an existing exoplanet. In such cases, an alternative approach
is required."* Their alternative — RV-correct before co-adding — is what viper implements
and what we ran. **It was not sufficient at our precision.**

## 4. Why CD-35 2722 B looked like it improved

Because that is what suppression looks like when you cannot see the truth. On GJ 229 B the
recovered amplitude is checkable and visibly collapses. On CD-35 2722 B there is no detected
signal, so the same effect presents as tidier scatter.

Some of the 776 → 620 may be a genuine reduction in wavelength-solution systematics from
`tpl_wave=tell` — that part is plausible and untested in isolation. But it cannot be
separated from the suppression, so **the run cannot be adopted**, and the non-monotonic
sequence argues against reading much into it either way.

**This is the third time in this session that a change improving the science target has been
rejected by the control**, after M9's empirical weighting and telluric screen. The pattern is
now the most reliable finding the project has: *on a target with no detection, anything that
removes signal looks like success.*

## 5. What this means for the reproduction

The template hypothesis is **tested and does not deliver**. Combined with M9:

| Lever | Believed worth | Measured |
|---|---|---|
| individual nodding frames | "the only remaining difference" | **10%** (authors' Fig. 4) |
| order screening / reweighting | plausibly large | **6%** |
| **template rebuilt per the published recipe** | **the leading suspect** | **worse — suppresses signal** |

Three of the named suspects are now closed. What remains, in order:

1. **The wavelength solution itself, independent of the template.** `tpl_wave=tell` was
   changed *together with* iteration and cannot be scored separately. **Run it with zero
   template iterations** — one run, and it isolates the only part of M11 that might be real.
2. **The ADP→cr2res conversion.** M2 verified it is lossless (max difference 0), which
   proves the numbers arrived, not that they arrived in the right order/detector slots. A
   mis-slotted segment would give viper a wrong starting wavelength per chunk, the telluric
   fit would never lock, and `atm0` would be unconstrained — which M9 measured in 6 of 10
   orders. **This is now the leading suspect and it has never been checked.**
3. **The nodding frames**, last, at 10%.

## 6. Caveats

- `tpl_wave=tell` and template iteration were changed together. §5.1 is the experiment that
  separates them and it has not been run.
- The control is six nights and cannot recover the period blind (M3 §6). It tests amplitude
  preservation against a known answer, which is what is needed here.
- GJ 229 B is double-lined, so its "correct" recovered amplitude (~6000 m/s) is itself a
  model-dependent expectation from M3 §4, not a measured ground truth. The *relative*
  collapse from 5948 to 2452 under an unchanged target is the robust statement.
- Whether iterated self-templating biases **Hoy et al.'s** published amplitudes is **not**
  something this milestone can address. Their alignment RVs are 25× more precise than ours,
  and the bias should scale down accordingly. Raising it as a question is fair; asserting a
  bias in their result would not be.
