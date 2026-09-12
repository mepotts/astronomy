# M2 independent pre-execution review

2026-09-12. **Scoped implementation review cleared for the already authorized
bounded M2 experiment. This is not a scientific-result acceptance or a discovery.**

A separate agent reviewed the protocol, complete M2 driver, immutable underlying
photometry/selection functions and M2 tests before real M2 measurements. The
reviewer changed no scientific source, protocol, input, threshold or result and
made no network requests or real-data measurements. The author implemented the
repairs and parent-authorized clarifications below before real outputs.

## Findings resolved before execution

1. **Geometry consistency.** The provisional convolution used the local celestial
   Jacobian, but returned the original global pixel-scale matrix to photometry.
   It now returns the local Jacobian. The numerical preflight now tests the actual
   fixed-position photometry estimator as well as an independent exact-sky
   template projection; the narrower initial numerical receipt is retained.
2. **Selected coordinates versus true coordinates.** Selecting an injected source
   at its noisy QL3 peak and then measuring all conditioned fluxes at its true
   coordinates omits centroid-selection bias. True-position recovery is retained;
   an additional triplet is measured at the frozen selected QL3 coordinates while
   the injected source remains at the original true position. Conditioned bias
   uses the selected-coordinate measurements.
3. **Final selection conditioning.** Original native local eligibility and global
   top-12 entry are reported separately from global entry plus the final all-epoch
   common-beam morphology/amplitude criteria. The latter criteria also use the
   selected-coordinate injected measurements.
4. **Failure accounting.** Originally a selection-fit exception could be caught
   as an original-data blank-screen exclusion. Screening and injected-stage
   errors are now separate: a failure after original screening keeps the trial
   in its denominator and invalidates selection testing. Missing injected flux
   makes bias unmeasurable, not a `nanmedian` computed after dropping failures.
5. **Exact selected-peak eligibility.** Target/edge/separation cuts are reapplied
   at the selected peak under the original selector's pixel-scale convention.
   An allowed grid centre cannot excuse a peak displaced inside the target's
   45-arcsec exclusion. The full 21-by-21 maximum rule and tie-losing insertion
   rank are retained.
6. **Triplet recovery.** The parent clarified before real outputs that the bright
   held-out strata require at least 95% recovery jointly across all three epochs,
   in addition to reported per-epoch rates. Disjoint failures that leave each
   epoch at 95% cannot produce a passing 90%-recovered triplet population.

These changes did not move the 200 planned positions or their split/strata. The
retained first plan and current plan have identical positions; 97 planned slots
are held out, before the prospective reference-epoch screening.

## Geometry and statistical checks

The native Gaussian covariance uses the major-axis vector `(sin BPA, cos BPA)`
in celestial east/north. The common-minus-native covariance is required positive
definite and transformed to pixels with `J^-1 C J^-T`. The matching kernel is
normalized; the Jy/native-beam to Jy/pixel to Jy/common-beam conversion supplies
the necessary common/native beam-area ratio. WCS handedness is exercised by a
reflection fixture. The local linear Jacobian remains a small-patch approximation,
not an exact nonlinear reprojection or validation of extended radio morphology.

The convolved-image background MAD is explicitly a noise proxy. The code does
not divide by square-root pixel count or pretend the RMS map is independent
white noise. Held-out null statistics remain conditional on the original QL3
blank screening; the output flags this. “Unmasked” in the protocol must not be
read as an unscreened sky population: other-epoch contamination is retained,
but the original reference-epoch exclusions have already occurred.

The fixed reference halves and leave-one-out scale tests do not choose the more
favorable set. They can expose instability but cannot certify references as
nonvariable. Selected strata with no members have unmeasured bias. Reused sky
locations, paired injections/nulls and epochs do not supply independent trials.

## Independently executed verification

```powershell
dyson-revet/.venv/Scripts/python.exe -B -m unittest discover -s vlass-pilot/tests -p test_m2.py -v
dasch-pilot/.venv/Scripts/ruff.exe check --no-cache vlass-pilot/m2.py vlass-pilot/tests/test_m2.py
```

**17 M2 tests PASS; Ruff PASS.** Direct fixtures exercise the repaired geometry,
selected-peak exclusion, source remaining fixed when measurement position moves,
conditioned flux/morphology coordinate choice, post-screen errors, missing-bias
denominators, empty selected strata and joint-versus-per-epoch recovery.

The reviewer additionally inspected the retained 240-trial numerical receipt:
maximum exact-template amplitude error 0.0002317102, actual-estimator amplitude
error 0.0002317294, maximum localization offset 0.7071525 arcsec. These are within
the 1% and 1-arcsec gates. The reviewer checked the receipt and its test assertions,
not an independent rerun of all 240 synthetic numerical trials; the execution
driver reruns that numerical preflight before real measurements.

Reviewed SHA-256 anchors:

| Artifact | SHA-256 |
|---|---|
| m2.py | `f76854d02568d1ebf78f6bbe367d7093a149e681bbe4b4b83bbe150ff3ee9ffa` |
| tests/test_m2.py | `1e66d457eefce09dc9ba43c0ecf108cbd953f434b6af84e955efa38cf437c5e4` |
| m2-protocol.md | `07f0df26052f78fa0e40725c646df659d804d44fbd893fb7bce7145eebaea356` |
| m2-plan.json | `ae410ffa184db03894822f1cee2179445ab48977997aa6dd43c163d1ea57e7e3` |

No remaining pre-execution issue was identified in this scoped review. Any failed
fixed gate must remain a STOP; no field expansion, threshold adjustment or unknown
search is authorized by this review. Real-output provenance/replay and scientific
interpretation remain to be reviewed after execution. Even success is only
common-beam calibration feasibility on this already inspected known-source field.

## Independent post-execution result audit

2026-09-12. **The recorded STOP_M2 is correct and remains a STOP.** The reviewer
read the frozen result and independently recomputed gates and summaries directly
from its individual measurement records, without importing the author's
`summarize` function or making new real-data measurements. This is an independent
accounting audit, not a second independent measurement pipeline. The author's
separate exact raw-data replay is documented in the results report.

The frozen result SHA-256 remains
`2ee432bbaad062499b68e54e04d8af5f76e96e784b408a29c48d2921582d8247`.
The reviewer verified the protocol, plan, M2 driver, old photometry, full-plane
driver and process-helper hashes, both bound parent receipts, and all six actual
raw-input file hashes. Source/protocol/plan hashes still equal the pre-execution
anchors above. All 240 recorded numerical trials satisfy their fixed gates.

Exactly these two failed gates are independently reproduced:

| Gate | Recomputed value | Frozen limit |
|---|---:|---:|
| QL2.1 common known-target amplitude/noise | 4.2246896400 | at least 5 |
| QL3.1 held-out null normalized MAD | 1.6517358654 | at most 1.5 |

QL2.1's amplitude is 0.8011438351 mJy with a 0.1896337727 mJy noise proxy;
its 0.3210423-arcsec peak displacement is not the failing criterion. No held-out
null reaches an absolute response of 5, but absence of that tail does not waive
the separate dispersion failure.

Accounting checks reproduce:

- All 200 planned identities, positions, flux strata and split labels, and 200
  output slots in each of three epochs. Each planned flux stratum has 40 slots.
- Exactly two allowed reference-data exclusions: one original reference peak,
  one protected position. No injected-selection or cross-epoch measurement errors.
  Usable counts are 102 development and 96 held out, with no replacement trials.
- Held-out denominators 11, 17, 25, 25 and 18 at 0.3, 0.5, 1, 3 and 10 mJy.
  Joint recoveries are respectively 0, 0, 5, 25 and 18. The two bright strata
  pass 25/25 and 18/18 with all unconditional per-epoch median biases within 5%.
- Ten common references, fixed halves of six and four, every half-scale and
  leave-one-out gate. Largest discrepancies are 3.23228% and 0.254857% respectively.
- All split denominators and spatial-block medians/MADs, held-out null summaries,
  and all 40 selection-conditioning summaries, including their selected-coordinate
  measurements and final morphology membership. Only 10 mJy has nonempty
  held-out global-selection strata (18 entries); lower-stratum conditioned bias
  is unmeasured, not zero.

Development null MADs also reproduce as 1.59531, 1.70765 and 1.75428. These
diagnostics support caution about the fitted-amplitude noise proxy but do not
identify a unique cause. The author's `m2-results-2026-09-12.md` preserves the
STOP, weak faint recovery, selection gaps, integer-centred real-data injections,
and correlated/conditional sample limitations without claiming variability or
discovery readiness. No scientific overclaim was identified in that writeup.

**Next step recommendation:** archive this experiment as complete and failed at
its promotion gates. Do not simply rescale noise until its failed held-out
dispersion passes, lower the target recovery threshold, or promote its bright
successes into a faint unknown-source search. A separately specified method
study could diagnose spatial/background/correlated-noise effects using development
records and the real-source native/common discrepancy. Any revised estimator
would need fresh prospectively held-out controls or independent confirmation;
the now-inspected 96 held-out locations cannot be presented as a newly blind
validation set. The route remains parked for discovery scanning pending that
separate validated design, not waiting on a date alone.
