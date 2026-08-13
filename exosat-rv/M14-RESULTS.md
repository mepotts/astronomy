# M14 — The flip survives nested sampling, the drift floor closes, and the blind search finds the satellite through the BERV confound

**Question:** M13 left two successors. (a) Does §5's second-satellite evidence flip
(BIC/2 proxy −0.51 vs the paper's +2.622) survive a real evidence integral? (b) Can the
night-to-night per-order drift floor (147–218 m/s vs the paper's 57.68) be closed to
≤~90 m/s, where the blind period search becomes decisive?

**Answer to both: yes.**

1. **The second satellite is disfavoured on the paper's own Nature table in every
   nested-sampling variant tried** — ten dynesty integrals across three model pairings
   and three prior styles, ΔlogZ(2sat−1sat) from −0.8 to −6.6, never positive, against
   the paper's claimed +2.622 (§1, §7).
2. **The floor closed twice over.** `-oversampling 2` (147→133) plus a **second
   template iteration** (→ **85 m/s**, mean combine, archive route) — the latter
   passing the M9/M11 injection guard at 105% ± 4% with every order transmitting
   (§2, §5). On the full paper recipe (per-nodding frames, binned; §8) the series
   reaches **90 m/s raw / 70–76 m/s with per-order centering** against their claimed
   57.68.
3. **The conclusion now reproduces from raw archive data.** A blind period search with
   a fully internal epoch screen finds **~169–171 d at rank 1 in every combine, at
   ΔBIC +40 alone and +25 to +28 with a BERV nuisance covariate** (§6, §8) — the
   covariate that killed the M13 detection outright. Attribution is clean: at template
   iteration 1 the detection still collapses under BERV even per-nodding (§8); the
   second template iteration is the decisive change.

## 0. What ran, and how to re-run it

Warm-up (Windows venv): [`scripts/nested_orbits.py`](scripts/nested_orbits.py) — dynesty
3.1.0, results in `data/m14-nested-{fixP,freeP,eccP}.json`.

Extraction (WSL `~/viper-src`, as M13):

| artifact | what it is |
|---|---|
| [`m14_nod5.sh`](scripts/injection/m14_nod5.sh) | M13 recipe on the 5 from-raw nights' per-nodding A/B frames |
| [`m14_batch1.sh`](scripts/injection/m14_batch1.sh) | oversampling + IP-model sweep on the archive route |
| [`m14_score.py`](scripts/injection/m14_score.py) | scorer: per-order centering, robust combines, A/B binning, paired reference |
| [`m14_drift.py`](scripts/injection/m14_drift.py) | lever 4: drift model on signal-free cross-order differences |
| [`night_map.py`](scripts/cr2res/night_map.py) / [`reduce_one.sh`](scripts/cr2res/reduce_one.sh) / [`m14_allnights.sh`](scripts/cr2res/m14_allnights.sh) | from-raw pipeline for the remaining 13 archive epochs |
| [`inject_m14.sh`](scripts/injection/inject_m14.sh) / [`inject_score_m14.py`](scripts/injection/inject_score_m14.py) / [`scale_plan.py`](scripts/injection/scale_plan.py) | injection arms with arbitrary plan/data-dir; median-combine recovery |

Scoring truth unchanged: the published Nature table via
[`vs_published.py`](scripts/injection/vs_published.py) (M12 §9b.4's rule).

## 1. The second satellite's flip SURVIVES nested sampling

M13 §5's caveat was that −0.51 was a BIC/2 proxy with periods fixed. dynesty
(nlive=500, `rwalk`, two seeds each; likelihood identical to
[`orbits.py`](src/exosat_rv/analysis/orbits.py): σ² = erv² + jitter²; priors symmetric
across models — offset U(−600,600), jitter log-U(0.1,300), K U(0,1000), e U(0,0.85),
ω U(0,2π), tp U(0,P); period windows P₁ U(150,200), P₂ U(75,100) where free):

| variant | models compared | ΔlogZ(2sat−1sat), seed 0 / 1 | paper claims |
|---|---|---|---|
| `fixP` | 1-sat ecc vs 2-sat circ, periods pinned at Table 1 values | **−1.42 ± 0.24 / −1.96 ± 0.24** | +2.622 |
| `freeP` | same pairing, periods free in the paper's windows | **−3.23 ± 0.27 / −3.65 ± 0.27** | |
| `eccP` | both full Keplerians — the paper's literal Table 1 pair | **−5.41 ± 0.27 / −6.63 ± 0.27** | |

Reading it: **on the paper's own revised Nature table the second satellite is
disfavoured in a full evidence integral, in every variant tried, by 1.4 to 6.6 logs.**
The proxy's −0.51 was, if anything, conservative: the closer the model space gets to
the paper's actual pairing (free periods, free eccentricities), the more the evidence
moves *against* the second satellite. For calibration, the paper's own quoted evidences
are logZ = −144.323 ± 0.695 (1-sat) vs −141.701 ± 0.691 (2-sat): +2.622 ± ~0.98, i.e.
their own claim is a ~2.7σ statement by their own error bars.

Caveats. Evidence depends on priors, and EMPEROR's exact priors are not published in
full; the paper reports a windowed-evidence procedure whose windows we approximate
(P₂ ∈ 75–100 d ≈ their "88-day window"). Seed-to-seed scatter slightly exceeds dynesty's
internal logzerr (a known underestimate) — read the numbers as ΔlogZ ≈ −1.7 ± 0.4,
−3.4 ± 0.4, −6.0 ± 0.7. None of that threatens the sign. The 87.35 d period *choice*
still reproduces (M13 §5: it beats the 70/115 d aliases in both tables); what does not
survive the authors' own data revision is the *existence* evidence. The author query
(docs/author-query-draft.md) can now cite an actual evidence integral, not a proxy.

## 2. Lever results on the archive route (17 matched epochs)

Baseline: M13_G (`H_C`, `-kapsig 3`, M13 template), median combine = **147 m/s**.

**Oversampling — the one config win.** `-oversampling` was never set (default 1);
the paper's value is unknown. Sweep on M13_G config:

| run | rms_pub (median combine) | slope |
|---|---:|---:|
| G (osamp 1) | 147 | 1.31 |
| **O2 (osamp 2)** | **133** | **1.20** |
| O4 | 163 | 1.34 |
| O8 | 180 | 1.40 |

**IP model — a dead knob at this SNR.** `-ip g` produces byte-identical output to the
default `bg` (viper's CRIRES `ip_guess` defines only `'s'`, and the symmetric-biGaussian
initialisation makes `bg` degenerate to a Gaussian). `sg` is materially worse
(226 median). ⏳ ag/mcg/bnd pending.

**Per-order centering (no viper run):** subtracting each order's own median across
nights (signal-safe: one constant per order) leaves rms_pub ≈ unchanged
(147 → 141 median) but normalises the slope (1.31 → 1.07): the raw median's overshoot
was partly static per-order offsets electing the transmitting orders. The *static*
component of the zero-points is not the floor — the drift is genuinely night-varying,
confirming M13 §6.

**Drift modelling on signal-free differences FAILS — instructive.** Fitting each
order's cross-order-difference series (signal-free by construction: the Doppler signal
is common-mode across orders) against BERV/time and subtracting reduces internal
per-order scatter (1241 → 722–876 m/s) but *worsens* rms_pub (147 → 158–186 median;
165 → 191–247 clip) ([`m14_drift.py`](scripts/injection/m14_drift.py)). Pulling orders
toward the noisy common mode correlates their errors and destroys precisely the
diversity the median averages over. Conclusion: the night-to-night per-order drift is
not a smooth function of BERV or time per order — it behaves like independent
per-order-per-night noise, and the robust combine is already the right estimator for
it. The floor has to be attacked at extraction time, not post-hoc.

**Injection-sanctioned order drops are a wash:** dropping o18 (fails injection,
M13 §3) moves the median from 147 to 145; dropping o18+o12 gives 149 with slope 0.97.
The median was already robust to them.

## 3. The per-nodding route (lever 1) — the paper's own favoured extraction

The Nature table header states the published RVs are the "per-nodding, binned"
extraction (their Fig. 4: 57.68 vs 60.50 m/s mean error, ~10% better than combining
spectra first). Our archive route uses ESO's combined products; the five from-raw
nights of M12 §9b have separate A/B extractions.

Paired test on the same 5 nights (M13 config; median cells):

| series | rms_pub | slope |
|---|---:|---:|
| per-nodding A/B, binned (M14_nod) | **142** | 1.48 |
| + per-order centering | **114** | 1.47 |
| archive combined (M13_G), same nights | 179 | 1.47 |
| + per-order centering | 162 | 1.37 |

Directionally consistent with the paper's Fig. 4, and larger (~20–30%) — plausible,
since cr2res's combined product resamples B onto A before summing (M12 §9b.1), which
per-frame extraction avoids. n=5, so treated as a go signal, not a result.

⏳ **The full test is running**: all 13 remaining archive epochs are being fetched raw
(~1.5 GB/night) and reduced through the M12 cascade
([`m14_allnights.sh`](scripts/cr2res/m14_allnights.sh)), giving a 36-frame per-nodding
series over 18 nights. Then: M13-recipe + `-oversampling 2` on all frames, bin A/B,
score, injection-validate the whole pipeline (K=1530 and amplitude-matched K≈306 arms,
per-frame plans), and re-run the blind period search with the BERV covariate.

## 4. Injection: O2 passes at both amplitudes; linearity closed for the core orders

**K=1530 arm** (18 single-epoch template-shift runs, O2 config):
recovery **94% ± 2%** through both mean and median combines; injection residual rms
**88–95 m/s** (was 213 at M13/G13). Per order: the transmitting core is clean
(o12 97±1, rms 38 m/s; o17 98±1, rms 38; o13 97±2, rms 93), o18 recovers 77±13
(was 8±56 at osamp 1), weakest is o9 (66±8).

**K≈306 amplitude-matched arm** (M13 §6's open linearity check): core orders recover
at unit slope with tiny scatter — o12 **102±2%** (rms 17 m/s), o19 107±2 (15), o13
97±3 (23), o7 91±6, o8 86±8. The combined-series slopes (mean 131±32%, median
176±60%) are consistent with 100% but weakly constrained by construction (injected
variance ≤300 m/s against 200–1000 m/s per-order noise). **No amplitude nonlinearity
detected**; the linearity assumption is closed for the orders that carry the signal.

The IP-model finding doubles as a viper note: `-ip g` and the default `bg` produce
byte-identical output on CRIRES (`ip_guess` defines only `'s'`, and the symmetric
biGaussian initialisation collapses to a Gaussian), `sg/ag/mcg` are 10–80% worse on
rms_pub, `bnd` crashes (zero orders). Eq. (1) moved the WRONG way under O2 (331→347)
while rms_pub improved (147→133) — the fifth instance of an internal metric
disagreeing with the external one (M12 §9b.4's rule keeps earning its place).

## 5. Lever 3 lands it: the second template iteration passes its guard and closes the floor

M13tpl was iteration 1. Iteration 2 ([`m14_tpl2.sh`](scripts/injection/m14_tpl2.sh):
`-createtpl` from M13tpl over all 21 segments) **crashed with creation flags identical
to M13tpl's** (scipy curve_fit maxfev on 7 segments); adding `-kapsig 3` to the
creation run stabilises it (reported: iteration count is then not the only changed
variable). The resulting config — **tpl2 + `H_C` + `-kapsig 3` + `-oversampling 2`** —
on the archive route:

| combine | rms_pub | slope | r_pub |
|---|---:|---:|---:|
| **mean** | **85** | 1.24 ± 0.09 | 0.96 |
| clip | 107 | 1.33 | |
| median | 144 | 1.44 | |

**rms_pub = 85 m/s — through the ≤90 target.** And the M9/M11 injection guard
**passes**: K=1530 recovery **105% ± 4%** (mean), **110% ± 6%** (median); per order,
every one of the eleven sits at 92–112% — including o18 (101±1, was 8±56 in M13) and
o8 (99±0, rms 12 m/s). The M11 objection (self-templating absorbs signal) does not
apply to this iteration — nothing is suppressed. The order bimodality M13 §2 found is
gone: the mean now beats the median, which is what a genuinely cleaner stellar
reference does (all orders pulled onto the same velocity scale, rather than half the
orders being noise the median had to vote out).

## 6. The blind search now finds the satellite — and survives the BERV covariate

[`blind_search.py`](scripts/injection/blind_search.py) (mean combine added), archive
route, T2 series. The search now carries an **internal epoch screen** — drop epochs
whose across-order spread exceeds 3× the median spread, computed from our data alone.
It selects exactly one epoch: BJD 2460604.821 at **7.3× the median (6670 vs 914 m/s;
the next-worst epoch is 1.16×)** — the same frame the published table omits, but
identified with no reference to it. End to end, nothing in this search touches a
published number.

| variant (n=17 after internal screen) | top peak | ΔBIC | K |
|---|---|---:|---:|
| mean, no covariate | **P = 169.1 d, rank 1** | **+37.3** | 393 |
| **mean, BERV covariate** | **P = 168.7 d, rank 1** | **+24.8** | 378 |
| median, BERV covariate | P = 167.8 d, rank 1 | +23.8 | 414 |
| clip, BERV covariate | P = 169.7 d, rank 1 | +25.3 | 442 |

**M13 §4b's collapse is over**: where the detection previously went negative under a
BERV nuisance term in every variant, the ~171 d satellite is the rank-1 blind peak in
all three combines, at ΔBIC ≈ +24 to +25 *with* the covariate in the model (≈5σ for
two extra parameters; the task's bar was ~4σ). With all 18 epochs (60604 included)
the search still degrades to noise — that epoch is genuinely fatal, and genuinely
identifiable without the published table. Success criterion status: **rms_pub 85 ≤ 90
✓, blind search survives BERV ✓ — on the archive route.**

Honest residuals of the claim:
- **Amplitude runs high.** Slope 1.24 ± 0.09 on published (1.16 ± 0.12 under BERV
  control); K at the published period 426–472 vs their 306. Same direction as M13 §4's
  hint (their self-templating recipe measurably absorbs amplitude on a known binary —
  M11 — ours does not), same confound (phase–BERV entanglement at −0.71), still
  recorded as a hint, not claimed.
- Eq. (1) moved the wrong way again (331 → 429 while rms_pub went 133 → 85): the
  sixth internal-vs-external metric divergence. The across-order dispersion statistic
  does not measure night-level accuracy.
- r_berv = −0.53 in the T2 series (the paper reports no RV–BERV correlation; ours is
  partly the signal itself projecting onto BERV through the sampling).

## 7. Prior sensitivity of §1 (nested sampling)

ΔlogZ(2sat−1sat) under alternative priors, freeP/eccP pairings, two seeds each:
jitter U(0,300): −2.9 to −4.6; K log-U(1,1000): −0.8 to −2.3. Combined with §1:
**ten independent integrals, every one negative** (−0.8 to −6.6), against the paper's
+2.622. The magnitude is prior-dependent (log-K softens the K₂ Occam penalty, as it
should); the sign is not.

The T2 **amplitude-matched (K≈306) arm** closes linearity for the adopted config:
nine of eleven orders recover at **98–105% with per-order residual rms 5–29 m/s**
(o19 101±1, rms 5; o18 100±1, rms 9; o9 101±1, rms 9). o14 (506±311, rms 2655) and
o4 (153±33) are unstable under small template shifts — they wreck the noisy combined
slope (mean 252±115) and are flagged; the transmitting core is linear.

## 8. The full paper recipe on all 18 nights: confirmation, and a clean attribution

All 13 remaining archive epochs were fetched raw (~1.5 GB/night, zero failed
downloads) and reduced through the M12 cr2res cascade
([`m14_allnights.sh`](scripts/cr2res/m14_allnights.sh)); with M12 §9b's five nights
that makes **36 per-nodding frames over all 18 archive epochs**. The paper's favoured
recipe end to end — per-nodding extraction, 2-iteration template, `H_C`, `-kapsig 3`,
`-oversampling 2`, bin A/B per night (`M14_NODT2`):

| series (17 matched nights) | rms_pub | slope | r_pub |
|---|---:|---:|---:|
| per-nodding binned, mean | **90** | 1.19 ± 0.10 | 0.95 |
| per-nodding binned, centered median | **76** | 1.20 ± 0.08 | 0.97 |
| per-nodding binned, centered clip | **70** | 1.21 ± 0.07 | 0.98 |
| archive combined (T2), mean — §5 | 85 | 1.24 ± 0.09 | 0.96 |

70–90 m/s against the paper's claimed 57.68: **1.2–1.6× their per-epoch precision**,
from 25× at project start. (The centered-robust cells are reported as variants, not
adopted post-hoc; the pre-registered mean-combine number is 90.)

**Blind search, same internal 3×-spread screen** (it again selects exactly the 60604
night, 604.818 in binned BJD):

| variant (n=17) | top peak | ΔBIC | K |
|---|---|---:|---:|
| mean, screened | P = 170.1 d, rank 1 | +40.4 | 387 |
| mean, screened + BERV | **P = 169.1 d, rank 1** | **+26.7** | 360 |
| median, screened + BERV | **P = 171.2 d, rank 1** | **+27.9** | 432 |
| clip, screened + BERV | P = 169.1 d, rank 1 | +26.9 | 424 |

Stronger than the archive route (+24.8 → +26.7/+27.9), with the median-combine peak
landing on **171.2 d against the published 171.11/171.45**. The ~355–375 d harmonic
family sits second, exactly as in the published analysis's alias structure.

**Per-frame injection validation** (K=1530 Keplerian evaluated at each of the 36
frame BJDs, template-shift per frame, full re-run): recovery through the adopted
combines **120–126% ± 13%** — no suppression (the M9 failure mode); consistent with
unity at 2σ. Per order: o4/o7/o8/o10/o13/o19 are pristine (99–103%, per-frame rms
18–205 m/s), while **o9, o12, o14, o17, o18 show occasional catastrophic per-frame
fits under template shifts** (rms up to 11.5 km/s; o17's slope even goes negative).
These instabilities exist only in the shifted-template arm — the real (unshifted)
series shows normal across-order spreads — and the robust combine plus A/B binning is
what absorbs them. The transmission verdict stands; the per-frame fragility of those
five orders is a documented caveat, not a blocker.

**The attribution experiment** (`M14_NODALL`: same 36 frames, same config, but the
**iteration-1** template): median combine 123 m/s (vs 133 archive — per-nodding
helps a little), mean 252 m/s with slope 0.46 (the bimodality is *worse* per-frame),
and the blind search **still collapses under BERV** (best screened variant +20.4
without the covariate → +4.3, rank >6, with it; mean variants go negative). So:
**per-nodding alone does not rescue the detection; the second template iteration
does; per-nodding then sharpens it.** The improvement chain is osamp 2 (147→133) →
template iteration 2 (→85, detection becomes BERV-robust) → per-nodding + binning
(→70–90, ΔBIC +27.9).

## 9. Where this leaves the reproduction

- **Primary satellite: independently detected from raw ESO archive frames.** Rank-1
  blind period at 169–171 d, ΔBIC ≈ +26–28 with a BERV nuisance term, on both the
  archive-combined and per-nodding routes, with the fatal epoch excluded by an
  internal screen and every pipeline stage injection-validated. This closes M13
  §4b's "existence not independently provable from the archive epochs alone."
- **Second satellite: contradicted on the paper's own revised table** (§1, §7) — the
  strongest finding for the author query, now an evidence integral rather than a
  proxy.
- **Amplitude: runs 20–40% high** (slope 1.19–1.24; K 360–440 vs published 306).
  Same M13 §4 confound (phase–BERV at −0.71): recorded as a hint that rhymes with
  M11's measured template-absorption on GJ 229 B, not claimed. Decidable when the
  embargoed epochs (Dec 2026 – May 2027) release.
- **Precision: 70–90 vs 57.68 m/s** — the remaining gap is ~1.2–1.6×, no longer the
  floor that decides anything.

## 10. For the next agent

1. **Update the author query** ([docs/author-query-draft.md](docs/author-query-draft.md))
   with §1/§7's evidence integrals and §8's independent detection — it currently cites
   the BIC proxy.
2. **M15 = eta Tel B** with the full validated recipe (per-nodding, 2-iteration
   template with `-kapsig 3` creation, `H_C`-style telluric-selected orders,
   `-kapsig 3`, `-oversampling 2`, robust combine, injection-validated, internal
   3×-spread epoch screen). The M13 §4b design rule stands: check the target's
   phase–BERV geometry before spending nights.
3. When the embargoed epochs release: re-run §6/§8 with the extended baseline — the
   amplitude question and the second satellite both become decidable on data the
   confound cannot reach.
4. Housekeeping: `M14_nodO2` (5-night M13tpl stack) was killed as superseded by §8's
   NODALL; viper's `-ip` flag is a dead knob on CRIRES (§2) — upstream-reportable.
