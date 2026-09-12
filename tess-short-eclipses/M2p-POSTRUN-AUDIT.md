# M2p independent post-run audit — 2026-09-12

**Replay and numerical-accounting verification PASS. Scientific localization
acceptance does not pass.** Both crowded controls retain their frozen STOPs;
the cleaner control remains validation-incomplete. Nothing here is a discovery,
a physical eclipse-depth measurement, or authorization to scan unknown targets.

This audit was performed after execution, independently of the experiment driver
author. It preserves all three controls and every failed trial. The auditor had
previously authored the numerical core; this is therefore a separate execution
and implementation cross-check, not an institutionally independent replication.
No frozen source, protocol, result, input or checkpoint was edited. No network
request, extra science fit, seed change or alternate aperture was used.

## Verification scope and reproducibility

The frozen stage is commit `16a6e1e`, manifest SHA-256
`6cf8d3c0b159d2fab06d5a5e1acf2f2d5924ac1eefff2e9085addfcea219dfed`.
The auditor's own bounded full replay completed with exit code 0 and exactly
reproduced all three field results and their checkpoints. It used its own process
handle, separate from the parent's successful replay.

The new [read-only audit script](scripts/m2p_audit.py) independently verifies:

- All 174 dependency and 112 artifact hashes, before and after numerical checks:
  287 distinct protected files including the manifest, with no changed bytes.
- All 96 conditions and 1,920 retained trial slots, fixed day-resampling indices,
  assignments, signed/radial displacements, covariance coverage, complete
  confusion matrices, denominator/failure accounting, vector-mean bias and
  prospective condition/field stop rules.
- All three primary model/residual arrays and weighted residual sums using
  separately implemented corner-array blending and SciPy interpolation, with
  full finite-support normalization before cropping.
- All 795 fixed-catalogue profiles using independent normal-equation linear
  solutions, checking signed amplitudes and weighted residual scores. This
  cross-check is specific to these full-rank retained designs; normal equations
  are not being proposed as a replacement for the frozen production solver.

The script reports `INDEPENDENT_NUMERICAL_AND_LEDGER_PASS`. Its three synthetic
unit tests (including subcases for classification and undefined covariance) and
pinned Ruff 0.16.5 pass. These are post-run verifier tests, not new empirical
calibration evidence. An initial pytest invocation found pytest absent; the tests
use the existing standard-library unittest runner, without environment changes.

From the repository root, using the existing runtime:

```powershell
& dyson-revet/.venv/Scripts/python.exe -B tess-short-eclipses/scripts/m2p.py replay
& dyson-revet/.venv/Scripts/python.exe -B tess-short-eclipses/scripts/m2p_audit.py
& dyson-revet/.venv/Scripts/python.exe -B -m unittest discover -s tess-short-eclipses/tests -p test_m2p_audit.py -v
```

The full replay retains the driver's bounded-worker checks. The separate audit
is a read-only, approximately 1.3-second reconstruction, not an injection rerun.
Machine evidence remains in [the summary](out/m2p-summary.json) and the three
field results linked below. Their execution workers used 10.422, 6.359 and
9.735 seconds, respectively; all returned 0 and stayed below the recorded memory
and byte limits. A completed slot can still contain a failed scientific fit.

## Primary recovery is not source-purity validation

| TIC | Free-fit signed amplitude (finite-model e-/s) | Weighted residual sum | Target / next profile score | Profiles / successful leave-one-day-out fits |
|---|---:|---:|---:|---:|
| [450781262](out/m2p-450781262.json) | 9.920479 | 111.495191 | 114.255207 / 142.762547 | 688 / 21 |
| [53206761](out/m2p-53206761.json) | 9.849960 | 141.716612 | 148.165279 / 1123.508327 | 12 / 19 |
| [2041210548](out/m2p-2041210548.json) | 7.067656 | 106.972905 | 126.107985 / 771.633658 | 95 / 26 |

All three free fits converge without a bound flag, their nearest centroid label
is the provisional target, and the target has the lowest fixed-position signed
profile score. The primary residual calculations agree independently. Each fit
uses 121 pixels and six parameters, but the scores are descriptive: correlated
pixel errors, PRF mismatch and registration uncertainty prohibit interpreting
score differences as calibrated significance or source probabilities.

The fitted PRF contribution to the original SAP aperture is respectively
4.656408, 4.287465 and 4.870303 e-/s; the fitted plane contributes −0.024816,
−0.062187 and +0.017540 e-/s. The original measured SAP decrements are 4.560366,
4.242997 and 4.834921 e-/s. Small remaining differences are retained residuals,
not renormalized away. Full-model lost-wing fractions outside the stamp are
approximately 0.00967, 0.00799 and 0.00588. None specifies true infinite stellar
flux or repairs negative baseline/background subtraction.

The closest geometric neighbour is also the profile runner-up for 450 and 204.
For 532 this is emphatically not so: its geometric nearest neighbour,
Gaia `3788606392856754944`, ranks last (12/12), with signed amplitude −0.032044
and score 1148.351602. The runner-up is another row, `3789356908327617664`,
with amplitude −1.445479. A signed negative solution is not a positive eclipse
alternative. Neither catalogue ranking nor nearest-label geometry is a purity
probability. The 66 overlapping leave-one-day-out fits demonstrate persistence
under day removal, not independent confirmation or absolute registration.

## 450781262: directly measured close-pair confusion

The target–nearest separation is only 0.12936714 pixel. At the observed aperture
decrement, nearest-neighbour injections are mislabeled as the target in 6/20,
3/20, 13/20 and 8/20 draws for corners 0–3. All four exceed the prospective
strict 5% wrong-row limit. Neighbour corners 0–2 also exceed half-separation
mean-bias norm (0.06468357 pixel); target corner 0 has bias 0.08999225 pixel and
fails that rule even though its nearest labels are all correct.

This is a direct counterexample to promoting the favorable primary target
profile into contaminant rejection. The 15–65% corner-specific wrong fractions
are measurements in paired same-data stress trials, not independent population
false-positive probabilities. The frozen `STOP_LOCALIZATION_CONFUSION` stands.

## 53206761: correct labels with 0/20 nominal ellipse coverage

All 480 injections have correct labels; the eight observed-amplitude conditions
also have complete fits/covariances and satisfy the predeclared bias rule.
Nevertheless **every nearest-neighbour corner has 0/20 nominal ellipse
coverage**. The neighbour is 2.72660762 pixels away from the target.

The fixed target SAP aperture receives only a small wing response at this
neighbour. Matching the same 4.2429965167 e-/s aperture decrement therefore
requires the following *injected*, full finite-model amplitudes:

| Corner | SAP response fraction | Injected amplitude (e-/s) | Mean-bias norm (pixel) | Nominal coverage |
|---|---:|---:|---:|---:|
| 0 | 0.003415967817154 | 1242.106701192 | 0.01706373 | 0/20 |
| 1 | 0.005742629924943 | 738.859472437 | 0.02534537 | 0/20 |
| 2 | 0.003457340232889 | 1227.242976083 | 0.00937722 | 0/20 |
| 3 | 0.004893774777656 | 867.019164044 | 0.02647089 | 0/20 |

These are injected amplitudes, not first-trial fitted amplitudes. Pixel errors
remain fixed by design and no extra photon noise is added. The large artificial
source amplitude consequently gives nominal coordinate errors of approximately
0.000194–0.000340 pixel. Corner-to-field-model mismatch produces displacements
much larger than those formal errors while still much smaller than the
2.7266-pixel catalogue separation. The retained coverage quadratic values span
approximately 2452–8114, versus the nominal threshold 5.99146; this is not a
rounding issue or undefined covariance. Correct nearest labels and catastrophically
undercovering ellipses can therefore coexist.

This is a fixed-aperture-response stress experiment, not a physically plausible
blend/eclipsing-star population simulation. There is no independent baseline
flux constraint establishing that this faint catalogue neighbour could undergo
the imposed decrement. The fixed-error signal-to-noise and model mismatch
prevent a physical-depth or calibrated-precision inference. A brighter star
outside the one-pixel injection-selection role also remains a separate concern.

The protocol specified no coverage acceptance threshold. The correct frozen
label remains `DIAGNOSTICS_COMPLETE_VALIDATION_INCOMPLETE`, not a retroactively
invented STOP or a purity PASS. This field does not replace the failed controls
or authorize an unknown scan.

## 2041210548: bias includes distant single-start failures

At observed amplitude, each target corner has one wrong-row assignment out of
20, exactly 5% rather than greater than 5%. Corner 0 additionally has two BOUND
slots, so its complete-trial mean bias is undefined rather than computed after
discarding them. Corner 3 has mean-bias norm 0.33263815 pixel, exceeding half
the closest-pair separation, 0.32576256 pixel. The umbrella
`STOP_LOCALIZATION_CONFUSION` is therefore driven by the separately recorded
`STOP_LOCALIZATION_BIAS`, alongside `INCOMPLETE_TRIAL_OR_COVARIANCE`, not by
claiming that 1/20 exceeded the strict wrong-row threshold.

The mean is not evidence of uniform subpixel drift. The four wrong-row fits
start at the same off-target absolute-peak seed [0,9] and land far from the
injected target (radial errors about 3.67–6.15 pixels); the first three have
negative signed amplitudes. The two corner-0 bound fits start [0,10], terminate
near y=10.5 with active mask [0,1], and have amplitudes approximately −11.02
and −10.25 e-/s. These receipts support a single-start edge/noise failure
interpretation; they do not establish what a global optimizer would return.
No alternate initialization was tried, and these outcomes stay in the ledger.
Across all amplitudes there are 58 BOUND slots among 720, none discarded.

## Nulls, limits and decision

All 36 signed negative-image fits are retained. Four FLUX fits hit bounds:
532 phases 0.25/0.8 and 204 phases 0.25/0.75. All 18 background fits have nearly
zero PRF amplitudes and explicitly undefined centroid covariance from rank or
condition failure; a fitted plane absorbs their background signal. Numerical
convergence of a zero-amplitude fit does not identify a source. Quiet off-phase
images are not independent population negatives, and the same 20 day draws
are paired across conditions rather than independent Bernoulli trials.

The result document's conservative claims are supported. Retain both STOPs
and the cleaner field's incomplete status. Any continuation needs a separately
prospective calibration/registration and real-negative design, not post-hoc
seed tuning, error inflation chosen to repair these outcomes, relaxed cuts, or
selecting only the cleaner control. Instrument angular resolution, catalogue
completeness, negative baseline flux and physical blend plausibility remain
distinct from interpolation correctness. No new scientific stage was executed
or authorized by this audit.
