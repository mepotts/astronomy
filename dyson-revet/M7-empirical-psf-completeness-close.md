# M7 — an empirical PSF settles what candidate D's spectrum can say, a second model family moves the completeness, and the front closes

*2026-08-24 · follows [M6](M6-morphology-mrs-completeness.md), executing M6 §5's own
recommendations. **This is the front's closing milestone.** Every externally-sourced number
carries its source; anything unsourced is marked UNSOURCED. **Nothing in this milestone has been
submitted, posted, or sent anywhere.** The candidate-I dossier and the Ren+24 note remain
Matthew-gated and are unchanged by this document. The front's stand-alone hand-over document is
[`FRONT-SUMMARY.md`](FRONT-SUMMARY.md).*

---

## 0. Pre-registrations

*Written and timestamped **before** the runs they govern, per repo law. Nothing in §1–§4 was
chosen after seeing a result. **M6 PR-2's acceptance test is carried forward verbatim and is not
weakened anywhere in this document** — same reference fluxes, same ±30%, same six comparisons,
same consequence on failure.*

### PR-1 — the empirical PSF, and the re-run of M6 PR-2's **unchanged** acceptance test

M6 §2.2 failed PR-2's acceptance test **4 of 6**, with the failure structured exactly as
PSF-wing leakage across the 1.23″ pair would predict: **in every band the *dominant* member
passes and only the *sub-dominant* one fails.** M6 §2.5 named the fix and it needs no new data —
each component overwhelmingly dominates the light in some sub-band of the cubes already on disk,
so a wing-carrying PSF can be measured **from the data themselves**. M7 builds it.

**Two facts about the geometry, measured before this pre-registration was written and stated here
as inputs rather than results.** (i) In all twelve cubes the Gaia position propagated to the
cube's own `EXPSTART` lands **within 1.0 pixel** of the white-light peak — 0.6–1.0 pix in Ch1
(where the peak is the *star*) and 0.1–0.7 pix in Ch2/3/4 (where it is the *contaminant*). The
astrometric prediction is therefore already good, and any plate-offset search that wanders
further than ~1 pixel has found a false minimum, not a pointing error. (ii) M6's own extraction
metadata shows **Ch4-long railed against both edges of its ±1.5-pixel search grid**
(`dx,dy = −1.50,+1.50`) and against the top of its width grid (`psf_k = 1.60`), and returned a
contaminant/star ratio of **0.86** where its neighbour Ch4-medium returns **33.5**. That is a
defect in M6's extraction, it is recorded here as one, and PR-1's construction is designed so it
cannot recur.

- **The donor rule — which component's light defines the PSF in each sub-band.** For each
  sub-band the **donor** is the component nearer the sub-band's white-light peak, and its
  **dominance ratio ρ_ap** is measured **model-free**: background-subtracted aperture flux at
  radius 0.5 FWHM about each fixed position, donor over the other. A sub-band is a **donor
  sub-band** if **ρ_ap ≥ 3**. The count of donor sub-bands is reported whatever it is; sub-bands
  that do not qualify take the λ-scaled empirical PSF of the nearest donor sub-band in log λ, and
  **which sub-bands those are is reported.**

- **The construction, per sub-band, per wavelength bin.** Eight equal-width λ bins per sub-band
  (each ≲3% in λ, so the PSF FWHM varies less than 3% inside a bin); slices median-combined in
  each bin; the fit region is every finite pixel within **max(3 × FWHM, 2 × separation)** of the
  pair midpoint, weighted by the cube's own `ERR` extension. Then, starting from M6's parametric
  model and iterating **four** times:

  > 1. subtract the current model of the **non-donor** component and the constant background;
  > 2. take the **median** radial profile of what is left about the **donor's fixed position**, in
  >    bins of 0.25 FWHM out to r_max = the largest radius wholly inside the fit region (the
  >    median, not the mean, so residual companion light in one azimuth cannot pull the profile);
  > 3. normalise it to unit total flux by numerical integration over the measured range plus an
  >    analytic power-law tail fitted to the outer third — **and the tail's fractional
  >    contribution is reported per sub-band**, because a large tail is a caveat on the absolute
  >    flux scale;
  > 4. re-solve the three linear amplitudes (donor, non-donor, background) with the new profile at
  >    **both** fixed positions.

  Positions stay fixed at PR-2's values — the Gaia position propagated to `EXPSTART` and that
  position plus M4 §5's measured (1.233″, PA 32.998°). **The plate offset is measured, not
  grid-searched**: the donor's flux-weighted centroid inside a 3-pixel box about its predicted
  position, **hard-bounded at ±1.0 pixel**, which is the fact (i) above turned into a
  constraint. Any cube whose measured offset reaches that bound is reported as such.

- **The internal validation, and it can fail.** The empirical PSF derived from the **star** (a
  known point source, an M-dwarf photosphere per M4 §5.2) and the one derived from the
  **contaminant** are compared in units of **r/λ**, where a diffraction-limited profile is
  invariant. Encircled energy at 2, 4 and 6 λ/D is reported for both. **If the contaminant-derived
  profile is materially broader, that is either a resolved source or a PSF error and it is
  reported as an unresolved ambiguity, not silently adopted.** The **primary** extraction adopts
  the **donor-derived** profile in each sub-band; the star-scaled profile is run as a **declared
  sensitivity** and both acceptance outcomes are printed.

- **The decisive validation — an injection–recovery *on the cubes themselves*, declared here as
  PR-1's primary test of whether the deblend is unbiased.** In each donor sub-band a synthetic
  companion of **known** amplitude fraction f ∈ {0.01, 0.02, 0.05, 0.10, 0.30} of the donor is
  injected at the same 1.233″ separation but at **PA + 90°** — a position used nowhere in the PSF
  construction — and the identical two-component deblend is run at (donor, injected) positions.
  The recovered/true ratio is reported as a **2 × 2 matrix**: injected with the Gaussian and with
  the empirical PSF, recovered with each. The Gaussian-injected / Gaussian-recovered cell is
  M6's method graded against a known truth for the first time; the off-diagonal cells price the
  circularity of injecting and recovering with the same profile. **This test is what converts
  "PSF-wing leakage" from a diagnosis into a number.**

- **The acceptance test itself is M6 PR-2's, verbatim and unweakened.** The extracted spectra are
  integrated over the same SVO MIRI bandpasses and compared with M4 §5.1's independently measured
  fluxes — **F560W star 300.6 / contaminant 70.9 µJy; F1000W 124.0 / 898.2; F1500W 50.0 /
  4159.1** — at a tolerance of **±30% per band per component**, six comparisons. **PASS requires
  6 of 6.** The tolerance is not moved, the reference values are not moved, no comparison is
  dropped, and no component is exempted. M6's result to beat is **4 of 6**.

- **What may be claimed, unchanged from M6 PR-2 and restated so it cannot drift.** If acceptance
  **passes**, a redshift may be quoted only from **≥ 2 independent spectral features** identified
  with the **same** z to within **±0.01**, each at **≥ 5σ** against the local continuum, from the
  same fixed 15-feature line list, with the **blind** scan over 0 < z < 3 run first and reported
  first. If acceptance **fails**, **no redshift is quoted from these data** and the reported
  result is that the published identification **cannot be independently checked from public
  data** — which is a finding, not a gap. **The star control, the continuum-window sensitivity,
  the narrow-line consensus scan and the sub-band stitching report are all re-run unchanged and
  reported whatever they say**; if the empirical PSF is right, the stitching offsets should
  shrink, and that is a prediction PR-1 is making in advance and can lose.

### PR-2 — injection–recovery beyond the single-blackbody family

M6 §3.4 stated the limit precisely: *"an injection–recovery test measures the pipeline against its
own model."* M6's completeness rests on one family — a single blackbody shell around a
main-sequence photosphere — and its two hard walls (γ < 0.05 blind; T_ds = 1000 K outside the
grid) are properties of that family and that grid. **M7 tests physically distinct families.**
Fixed here, before the run:

- **The families.** Two, both generated by the **same** host/noise machinery as M6 §3 and both
  pushed through the **unmodified** pipeline (`fit_ds`, the γ ≥ 0.10 grid, RMSE ≤ 0.2, the extra
  cuts, S/N ≥ 3.5 — no stage re-tuned, no threshold moved):
  1. **Two-temperature shell.** The reprocessed luminosity is split between a warm and a cool
     blackbody, **f_warm ∈ {0.3, 0.5, 0.7}** of the total, with **T_cool = T_warm / 3** — a
     radially extended shell rather than a single radius. Physically distinct because no single
     blackbody in the fit's grid can represent the resulting curvature.
  2. **Optically-thin dust emission**, the standard modified blackbody **f_ν ∝ ν^β B_ν(T)** with
     **β ∈ {1.0, 2.0}** — the emissivity law for astronomical silicate/graphite grains. Physically
     distinct because it is broader on the Rayleigh–Jeans side than any blackbody, which is
     exactly the part of the SED W3 and W4 sample.
- **The axis is held fixed so the comparison means something.** Both families are parameterised
  by the **same bolometric covering fraction γ = L_reprocessed / L_star** and carry the **same**
  Suazo Eq. 3 obscuration dimming as M6's family. The temperature axis is the same
  **{100, 150, 200, 300, 450, 700, 1000 K}** (read as T_warm for family 1 and as T for family 2),
  the γ axis is M6's **{0.01, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50}**, the six |b| bands are
  M6's, the hosts are real parent rows and the per-band uncertainties are drawn at the **injected**
  brightness from real parent rows, exactly as M6 §3 did. Seed **20260825**, fixed here.
- **What is delivered.** The recovery fraction as a function of (family, γ, T, |b|), and
  **Δ = the in-grid |b| > 30° recovery of each new family minus M6's 45.8%**. Declared in
  advance: **if |Δ| ≥ 5 percentage points for either family, the catalogue's completeness
  statement is materially family-dependent and the catalogue is re-issued as v3 with the
  completeness restated per family; if |Δ| < 5 points for both, v2's statement stands and v3 is
  not issued.** The threshold is written here so the versioning decision is not made after seeing
  the number.
- **The two walls are re-measured on the new families, because they are the claims most likely to
  be family-specific**: the γ cliff (does the screen stay blind below γ ≈ 0.05?) and the
  temperature wall (does T = 1000 K still collapse?). Whatever they do is reported.
- **A control, labelled as one**: the **same generator run with f_warm = 1.0 and β = 0** reduces
  analytically to M6's single blackbody, and must reproduce M6's own recovery numbers. **If it
  does not, the new generator is wrong and the family comparison is void.** This is a falsifier
  and it is written before the run.

### PR-3 — candidate E: readiness only, and nothing else

E's data open **2026-09-09**, sixteen days after this milestone. **Nothing about E is
pre-empted.** M6 PR-4's three permitted actions and no others: (i) confirm M5 §5.3's four-case
outcome map is byte-identical to what was committed, by hash; (ii) confirm M5 §5.2's
parameterised chain still reproduces M4 §5 on all seven checks; (iii) re-check E's MAST status
anonymously. **E's data are not fetched and not analysed, and would not be even if they had
become public early** — M5 PR-4 fixed the analysis to on-or-after the release date.

### PR-4 — the front summary

This is a closing milestone, so the front's hand-over document is itself a deliverable and its
scope is fixed here so it cannot become a highlight reel: it states **what the re-screen
established, what it could not, what the catalogue is and is not usable for, and the standing
dated triggers**, with every negative result carried across rather than summarised away. It lives
in its own file so it can be read without reading seven milestone documents.

### PR-5 — what this milestone may not do

Unchanged and restated: **no account is created anywhere; nothing is submitted, posted, or sent;
no commit and no push** (the orchestrator's); the Ren+24 note and the candidate-I dossier stay
Matthew-gated and untouched; **V5 stays retired** (M5 §6) and nothing here re-enables, re-tunes or
re-scores it; **STILL-CLEAN stays unreachable** and no object in any product is described as
clean; **v1 and v2 of the catalogue are not edited, moved or deleted.**

---

*(Everything below is written after the runs. Numbers are emitted by the scripts named, never
hand-copied.)*

---

## 0b. What M7 established

1. **The named fix worked, and M6 PR-2's acceptance test now PASSES 6 of 6 —
   graded by byte-identical code.** An empirical, wing-carrying PSF built from
   the cubes already on disk takes the six flux ratios from
   **0.96 / 0.69✗ / 0.77 / 0.84 / 1.52✗ / 0.75** to
   **1.09 / 0.78 / 0.97 / 1.02 / 0.76 / 0.98**. The extraction was written to
   the filename and schema the M6 grader already reads, so the test was run by
   `m6_mrs_redshift.py` **unmodified** — the tolerance, the reference fluxes and
   the six comparisons are the same objects M6 failed (§1.3).
2. **The leakage is now a number, not a diagnosis. PR-1's injection–recovery on
   the cubes returns a companion of *known* flux fraction, and a wingless
   Gaussian under-recovers a faint companion by 42% at f = 0.01, 15% at 0.02,
   7% at 0.05 and 1% at 0.30 — 59% at f = 0.01 on the resolved sub-bands
   alone.** The empirical PSF is flat and unbiased over the same range
   (1.036 / 0.986 / 1.002 / 1.003 / 1.000). **The bias is severe for the
   sub-dominant component and vanishes for the dominant one — exactly the
   pattern of M6's 4-of-6 failure, reproduced against a known truth** (§1.4).
3. **And with the deblend fixed and validated, the spectrum *still* does not
   support a redshift at the unchanged pre-registered bar. The verdict is that
   the published z ≈ 0.922 cannot be independently confirmed from public data —
   and the reason is no longer the reduction.** The blind cross-correlation
   peaks at **z = 2.436 at 2.60× the scan rms**, below the **3.92×** the *star
   control* reaches; a ±0.02 dex change in the continuum window still moves the
   answer by **Δz ≈ 1.5**; and the blind narrow-line consensus scan finds
   **42.9% of the redshift grid does at least as well as z = 0.922**, which is
   **not** among the best (§1.5).
4. **A defect in this project's own pre-registration, found by M7 and reported
   as a correction to ourselves: PR-2's redshift criterion could never have
   decided this case.** The feature fitter searches ±0.5 FWHM about each
   predicted centroid, so a **narrow** line can only move by **Δz ≤ 0.0028** —
   any narrow line detected at *any* trial redshift satisfies the "agree to
   ±0.01" clause **vacuously** — while **PAH 7.7 alone can roam ±0.112**, so one
   detected broad PAH forces the clause to fail. The criterion is decided by
   *which kind of feature is detected*, not by whether the redshift is right
   (§1.6).
5. **A quantitative limit that applies to M6, to M7 and to candidate E: a
   two-component deblend of this pair is only determined while it is
   resolved.** The separation falls from **4.38 to 1.26 PSF FWHM** across the
   cubes, and the model-free symptom — an unphysical **negative** fitted flux —
   tracks it exactly, reaching **86% of slices** in Ch4-medium. **Restricting
   to the determined sub-bands does not change either verdict** (M6 still fails
   4 of 6; M7 still passes, and its worst ratio improves from 0.76 to 1.00), so
   the defect is bounded and the acceptance result is robust to it (§1.7).
6. **PR-1's declared star-scaled sensitivity FAILS 5 of 6, and its single
   failure is diagnostic**: forcing the *star's* Ch1 profile on every sub-band
   fixes F560W but leaves **F1500W star at 1.41** — the band where the
   contaminant's own wings must be modelled. **The donor rule is doing real
   work, and the sensitivity shows which half of it matters** (§1.8).
7. **PR-1 made a prediction and LOST IT.** It said the sub-band stitching
   offsets should shrink if the empirical PSF were right. They do not: median
   |ratio − 1| moves **0.109 → 0.138**, and one join degrades badly. The
   improvement is in the band-integrated fluxes, not in the piecewise flux
   scale, and the lost prediction is reported rather than dropped (§1.9).
8. **The completeness function is materially family-dependent, and PR-2's
   pre-declared trigger fired.** 100,800 new injections through the
   **unmodified** pipeline: in-grid recovery at |b| > 30° runs **26.1% to
   44.4%** across six arms against the matched single-blackbody control's
   **43.7%** — a spread of **17.6 percentage points**, against PR-2's 5-point
   trigger (§2.2).
9. **The γ ≈ 0.05 blindness is a property of the blackbody family, not of the
   screen.** At γ = 0.05 the recovery is **1.8%** for a single blackbody but
   **11.3%** for optically-thin dust at β = 1 — *six times less blind* — and
   **0.05–0.14%** for a two-temperature shell, i.e. blinder still (§2.3).
10. **M6's "hard temperature wall at 1000 K" is withdrawn as a property of the
    screen.** For a two-temperature shell, recovery at T_warm = 1000 K is
    **30.3–36.9%**, because T_cool = T_warm/3 is back inside the grid. For
    optically-thin dust the wall moves the *other* way — **0.0% already at
    700 K for β = 1 and at 450 K for β = 2**. **Every family has its own wall,
    at its own temperature** (§2.3).
11. **The catalogue's tabulated parameters are biased when the SED is not the
    assumed family, and the RMSE gate does not catch it.** On objects the fit
    *accepts*, median T_fit/T_true runs **0.638** (two-temperature, f_warm 0.3)
    to **1.480** (optically thin, β = 2), and γ_fit/γ_true down to **0.659**.
    Accepted non-blackbody objects sit at **3–5× the residual** of a blackbody
    and still clear the 0.2 mag gate (§2.4).
12. **Two controls passed and one tolerance was moved with its reason on
    record.** The new generator reduces **analytically** to M6's family — the
    f_warm = 1 arm to **exactly 0.0** and the β = 0 arm to **8.03 × 10⁻⁸ mag**,
    a residual traced to the **truncated Stefan–Boltzmann constant in the
    pre-existing `w1_selection.py`** (5.670374e-8 against CODATA's
    5.670374419184e-8), not to the new code; and the β = 0 arm run through the
    whole pipeline lands at **43.7%** against M6's **45.8%**, which sets the
    run's own **~2-point Monte-Carlo floor** (§2.1).
13. **Catalogue v3 issued, rows byte-identical to v2 and asserted so.** v3
    carries a per-family completeness function, both walls re-measured per
    family, and the parameter bias — plus the plain statement that **there is
    no single completeness number for this catalogue**. **v1 and v2, their
    stats files and their READMEs are verified unmodified by checksum** (§2.5).
14. **Candidate E is READY and nothing about it was pre-empted.** M5 §5.3's
    outcome map is byte-identical to the committed M5 (SHA-256
    `fa93e2c852befdb5…`, the same hash M6 recorded); the chain reproduces M4 §5
    on **7 of 7**; E is **0 PUBLIC of 39, release 2026-09-09**, unchanged.
    Nothing was fetched (§3).
15. **The front has a stand-alone hand-over document**,
    [`FRONT-SUMMARY.md`](FRONT-SUMMARY.md) — what the re-screen established,
    what it could not, what the catalogue is and is not usable for, and the
    standing dated triggers (§4).

---

## 1. Candidate D's redshift — the empirical PSF, and what it settles

*`scripts/m7_mrs_epsf.py` (`build`, `inject`), `scripts/m7_mrs_sensitivity.py`
(`resolved`, `starscaled`); graded throughout by **unmodified**
`scripts/m6_mrs_redshift.py`. Artifacts `out/m6_mrs_D_epsf_*.csv/json`,
`out/m7_epsf_{diagnostics,profiles,psfs,psf_check,injection}.*`,
`out/m7_mrs_resolved.json`, `out/m7_grade_*.log`, `out/m7_fig_epsf.png`.
**No network was used at any point** — the twelve cubes were already on disk
from M6.*

### 1.1 Two defects in M6's extraction, found before the fix was built

Reading M6's own extraction metadata before writing anything:

- **Ch4-long railed against every edge of its search.** M6's plate-offset grid
  search returned `dx,dy = −1.50, +1.50` — both edges of its ±1.5-pixel grid —
  and `psf_k = 1.60`, the top of its width grid. Its contaminant/star ratio came
  out **0.86** where its neighbour Ch4-medium gives **33.5**, and its `f_star`
  is **50× that of any adjacent sub-band**. It found a false minimum.
- **The astrometry never needed the search.** In **all twelve** cubes the Gaia
  position propagated to the cube's own `EXPSTART` lands **within 1.0 pixel** of
  the white-light peak — 0.6–1.0 pix in Ch1, where the peak is the *star*, and
  0.1–0.7 pix in Ch2/3/4, where it is the *contaminant*. **The pair's identity
  flips band by band exactly as the photometry says it should**, which is an
  independent confirmation of M4 §5's (1.233″, PA 32.998°) and of which source
  is which.

PR-1 therefore **measures** the plate offset from the donor's centroid and
**hard-bounds it at ±1.0 pixel**. Measured offsets run **−0.48 to +0.75
pixels**, and **no cube reaches the bound**.

### 1.2 The empirical PSF, and what it looks like

| sub-band | donor | ρ_ap | donor sub-band? | dx, dy (pix) | measured to | tail fraction |
|---|---|---|---|---|---|---|
| 1-short | star | 8.9 | yes | −0.15, +0.75 | 1.9 FWHM | 0.009 |
| 1-medium | star | 4.5 | yes | −0.17, +0.41 | 1.7 FWHM | 0.014 |
| 1-long | star | **1.4** | **no — borrows** | −0.22, +0.68 | 1.8 FWHM | 0.029 |
| 2-short | con | **1.9** | **no — borrows** | −0.03, −0.12 | 3.0 FWHM | 0.023 |
| 2-medium | con | 3.9 | yes | −0.04, −0.21 | 3.0 FWHM | 0.021 |
| 2-long | con | 12.5 | yes | −0.05, −0.15 | 2.4 FWHM | 0.005 |
| 3-short | con | 22.6 | yes | −0.02, −0.25 | 3.9 FWHM | 0.010 |
| 3-medium | con | 38.7 | yes | −0.07, −0.17 | 3.7 FWHM | 0.013 |
| 3-long | con | **92.3** | yes | −0.08, −0.19 | 3.2 FWHM | 0.001 |
| 4-short | con | 11.7 | yes | −0.01, −0.11 | 3.5 FWHM | 0.040 |
| 4-medium | con | 21.7 | yes | +0.08, −0.03 | 3.6 FWHM | 0.082 |
| 4-long | con | 4.9 | yes | −0.48, +0.19 | 3.6 FWHM | **0.401** |

**Ten of twelve sub-bands qualify as donors**; the two that do not are exactly
the **crossover** sub-bands where the star and the contaminant are within a
factor 2 of each other (7.1 µm and 8.1 µm), and they borrow the λ-scaled
profile of the nearest donor. **Ch4-long's tail fraction is 0.401** — 40% of its
normalisation is extrapolated rather than measured — and that is reported here
as a caveat on that sub-band's absolute flux scale, not buried.

**PR-1's internal validation, and it does not come out clean.** Encircled energy
of the empirical profile:

| | 1 FWHM | 2 FWHM | 3 FWHM | | 2 λ/D | 4 λ/D | 6 λ/D |
|---|---|---|---|---|---|---|---|
| **star-derived** | 0.814 | 0.989 | 0.991 | | 0.898 | 0.991 | 0.991 |
| **contaminant-derived** | 0.688 | 0.892 | 0.961 | | 0.813 | 0.970 | 0.988 |

**The contaminant's profile is measurably broader than the star's** — 0.892
against 0.989 inside 2 FWHM. Two readings, and M7 does not choose between them:
the contaminant is a galaxy at the published z ≈ 0.9, where 1″ is ≈ 7.9 kpc, so
it may be **marginally resolved**; or the star-derived profile, which exists only
in Ch1, misses wings that matter at longer wavelengths. **Reported as an
unresolved ambiguity**, exactly as PR-1 required. The primary extraction adopts
the donor-derived profile per sub-band; §1.8's star-scaled sensitivity is the
declared alternative, and it discriminates between the two readings.

### 1.3 M6 PR-2's acceptance test, unchanged, re-run — **PASS, 6 of 6**

**The test was not touched.** The empirical extraction is written to
`out/m6_mrs_D_epsf_spectra.csv`, in the schema and under the filename
`m6_mrs_redshift.py --label D_epsf` already reads, so the grading — the SVO
bandpasses, M4 §5.1's reference fluxes, the ±30% tolerance, the six comparisons
— ran through **byte-identical code**.

| | M4 imaging, µJy | M6 Gaussian | | **M7 empirical** | |
|---|---|---|---|---|---|
| F560W star (dominant) | 300.6 | 0.96 | PASS | **1.09** | **PASS** |
| F560W contaminant (sub-dominant) | 70.9 | **0.69** | **FAIL** | **0.78** | **PASS** |
| F1000W star (sub-dominant) | 124.0 | 0.77 | PASS | **0.97** | **PASS** |
| F1000W contaminant (dominant) | 898.2 | 0.84 | PASS | **1.02** | **PASS** |
| F1500W star (sub-dominant) | 50.0 | **1.52** | **FAIL** | **0.76** | **PASS** |
| F1500W contaminant (dominant) | 4159.1 | 0.75 | PASS | **0.98** | **PASS** |
| | | **FAIL — 4 of 6** | | **PASS — 6 of 6** | |

**Both of M6's failures were on the sub-dominant component and both are
closed.** The dominant-component ratios also tighten — 0.96 / 0.84 / 0.75 →
1.09 / 1.02 / 0.98 — which is the signature of flux that was being mis-assigned
rather than lost. *M4 §5.4's own caveat on the F1500W star flux (its leak
correction is ~50% of the raw aperture signal) is unchanged and is not used here
to reinterpret anything.*

### 1.4 PR-1's decisive validation — the leakage, priced against a known truth

Synthetic scenes: the donor plus a companion of **known** flux fraction f at the
same 1.233″ separation but at **PA + 90°**, a position used nowhere in the PSF
construction. Recovered / true, median over sub-bands:

| inject → recover | f = 0.01 | 0.02 | 0.05 | 0.10 | 0.30 |
|---|---|---|---|---|---|
| Gaussian → Gaussian | 0.972 | 1.008 | 0.989 | 1.003 | 1.000 |
| **realistic (empirical) → Gaussian** | **0.576** | **0.851** | **0.930** | **0.947** | **0.987** |
| Gaussian → empirical | 1.206 | 1.194 | 1.020 | 1.050 | 1.012 |
| **empirical → empirical** | **1.036** | **0.986** | **1.002** | **1.003** | **1.000** |

**The second row is the finding.** Given a PSF with real wings, a wingless
Gaussian deblend **loses 42% of a companion at f = 0.01** and is essentially
unbiased at f = 0.30 — **the bias is a function of how sub-dominant the component
is, which is precisely the structure of M6's acceptance failure.** On the
resolved sub-bands alone (Ch1–Ch3) it is sharper still: **0.411 at f = 0.01,
0.770 at 0.02, 0.907 at 0.05.**

**The circularity is priced, not ignored.** Row 1 shows the Gaussian is unbiased
*on its own terms* — a Gaussian truth recovered by a Gaussian is fine — so the
failure is not the fitter, it is the profile. Row 3 shows the reverse error costs
+20%: if the truth were wingless, the empirical PSF would *over*-assign. **The
MRS PSF has real Airy wings, so row 2 is the physically relevant one, and row 4
is what M7 does.**

### 1.5 The redshift, with a validated deblend — and it still cannot be pinned

**PR-1 permits a redshift now, and the pre-registered criterion is not met.**

| | M6 (Gaussian) | **M7 (empirical)** |
|---|---|---|
| blind cross-correlation best z | 1.046 | **2.4355** |
| its peak / scan rms | 3.27 | **2.60** |
| **star control's** peak / scan rms | 4.16 | **3.92** |
| best z vs continuum window (±0.06 / 0.08 / 0.10 dex) | 0.468 / 1.057 / 1.026 | **2.433 / 2.435 / 0.957** |
| narrow lines ≥ 5σ at z = 0.922 (of 8 in range) | 3 | 3 (summed SNR 37 → **98.5**) |
| fraction of the z grid doing as well | 41.1% | **42.9%** |
| z = 0.922 among the best | no | **no** |
| noise: empirical / formal | 1.00 | **1.61** |

**Every blind test is negative or non-committal, and the controls are what make
that a conclusion rather than an absence.**

- **The star control still out-peaks the contaminant.** A bare M-dwarf
  photosphere run through the same scan reaches **3.92× the scan rms** against
  the contaminant's **2.60×**. A statistic whose control scores higher than its
  signal has no discriminating power here, and that is measured, not asserted.
- **The continuum degeneracy is undiminished.** A ±0.02 dex change in a continuum
  window that cannot absorb any feature in the list still moves the best redshift
  by **Δz ≈ 1.5**. The scan is driven by the broad PAH complex, whose centroid
  trades against the continuum.
- **43% of all redshifts do as well on the blind narrow-line count.** The residual
  spectrum carries enough structure — fringing, sub-band scale steps, and the
  **×1.61** excess of empirical over formal noise — that a 5σ threshold is not a
  meaningful detection threshold in this spectrum.

**What is *not* contradicted, and is stated as such.** Testing the published
hypothesis directly still finds **7 of 8 features at ≥ 5σ with the right sign** at
z = 0.922 (PAH 6.2, 7.7, 8.6, 11.3, [Ar II], [S IV], H₂ S(3); summed SNR 98.5),
and the 9.7 µm silicate trough lands at **17.78 µm → z = 0.833**, 0.09 from the
published value, now at **−0.092 dex** depth (M6: −0.065). **The data are
consistent with a PAH-bearing, silicate-absorbed dust-obscured galaxy at
z ≈ 0.9. They do not single that redshift out against the alternatives, and the
controls say why.**

**The verdict, in the terms M6 PR-2 fixed and M7 PR-1 carried forward: the
identification cannot be independently checked from public data.** What M7
changes is *which* statement that is. M6 could not tell whether its negative was
the data or its own deblend. **M7 removes the deblend from the list**: the
extraction now passes the same acceptance test at the same tolerance, is unbiased
against a known injected truth, and still cannot pin the redshift. **The limit is
the achievable spectral fidelity of public MRS Level-3 cubes on a 1.23″ pair, not
the reduction — and that is a publishable negative about a published claim.**

### 1.6 A correction to ourselves: PR-2's redshift criterion could not have decided this

**M7's sharpest methodological finding is about this project's own
pre-registration.** M6 PR-2 required "≥ 2 independent features, each ≥ 5σ,
agreeing on z to within ±0.01". The feature fitter searches the centroid over
**±0.5 FWHM** about each predicted position, so how far a fitted z can move is
fixed by the feature's *width*, not by the data:

| | max \|Δz\| the search allows |
|---|---|
| **narrow** lines ([Ar II] … H₂ S(3)) | **0.0011 – 0.0028** |
| **broad** PAHs | 0.0119 – **0.1123** (PAH 7.7) |

- **The narrow lines satisfy the ±0.01 clause vacuously.** Their maximum possible
  mutual spread is **0.0055**, already inside the tolerance. Any narrow line the
  fitter reports, at *any* trial redshift, "agrees". The measured spread at
  z = 0.922 is **0.0016** — and it carries **no information**.
- **One detected broad PAH forces the clause to fail.** Their maximum possible
  spread is **0.2247**; the measured spread is **0.1514**.

**So the criterion is decided by which *kind* of feature is detected, not by
whether the redshift is right.** It could not have confirmed z = 0.922 from this
line list under any deblend. **This is reported as a defect in M7's inherited
pre-registration and it is not used to re-read the result** — reaching for the
narrow-line-only sub-selection *after* seeing that it "agrees" would be exactly
the move repo law forbids, and it would be reaching for a statistic that is
tautological anyway. **The tests that do carry information are the blind ones in
§1.5, and they are negative.**

### 1.7 A limit that applies to M6, to M7 and to candidate E: the pair stops being resolved

The pair is 1.233″ apart and the MRS PSF FWHM runs 0.28″ at 5 µm to 0.98″ at
26.5 µm, so **the separation falls from 4.38 to 1.26 PSF FWHM across the cubes**.
Below ~2 FWHM the two-component design matrix is nearly collinear and **no
deblend is determined, by either method**. The model-free symptom is an
**unphysical negative fitted flux**:

| sub-band | sep / FWHM | negative-flux fraction, M6 Gaussian | **M7 empirical** |
|---|---|---|---|
| 1-short … 2-long | 4.38 → 2.66 | ≤ 0.4% | ≤ 0.5% |
| 3-short | 2.38 | 1.3% | 5.6% |
| 3-medium | 2.11 | 0.5% | 11.2% |
| 3-long | 1.88 | 17.3% | **44.3%** |
| 4-short | 1.66 | **20.7%** | **48.9%** |
| 4-medium | 1.45 | **35.3%** | **85.9%** |
| 4-long | 1.26 | 13.8% | **80.7%** |

**A wing-carrying PSF makes the collinearity worse**, because two broad profiles
1.3 FWHM apart are more nearly the same function than two narrow ones. **That is
a real cost of the fix and it is stated as one: M7 buys accuracy where the pair
is resolved at the price of determinacy where it is not.**

**Bounded, and it changes nothing.** Re-grading each extraction with the
undetermined sub-bands dropped, again through the unmodified M6 code:

| | all sub-bands | determined sub-bands only |
|---|---|---|
| M6 Gaussian | **FAIL 4/6** | **FAIL 4/6** (identical ratios) |
| **M7 empirical** | **PASS 6/6** | **PASS 6/6**, and F1500W star moves **0.76 → 1.00** |

**Neither verdict moves, and M7's worst ratio improves when the undetermined
bands are removed** — so the 6-of-6 is not being carried by a sub-band its own
diagnostic distrusts. **The improvement is the empirical PSF and not the band
restriction**: restricting M6's Gaussian extraction the same way leaves it at
4 of 6, digit for digit.

**This is the most transferable thing in M7 and it goes straight into candidate
E's file** (§3).

### 1.8 PR-1's declared star-scaled sensitivity — FAILS 5 of 6, and the failure is informative

Forcing the **star**-derived Ch1 profile onto every sub-band, as PR-1 declared:

| | F560W star | F560W con | F1000W star | F1000W con | F1500W star | F1500W con | |
|---|---|---|---|---|---|---|---|
| star-scaled | 1.04 | 0.76 | 0.88 | 0.91 | **1.41** | 0.85 | **FAIL 5/6** |
| **donor (primary)** | 1.09 | 0.78 | 0.97 | 1.02 | **0.76** | 0.98 | **PASS 6/6** |

**It sits exactly between M6 and M7**: it fixes F560W (a Ch1 band, where the
star's own profile is the right one) and leaves F1500W star at 1.41, barely
better than M6's 1.52. **That is the donor rule earning its keep, and it also
resolves §1.2's ambiguity in favour of the second reading**: what F1500W needs is
the *contaminant's* profile at 15 µm, so the extra width in the
contaminant-derived profile is behaving like PSF the star's Ch1 profile does not
carry — not purely like a resolved source. *Not decisive, and not claimed to be.*

### 1.9 A prediction PR-1 made in advance and LOST

PR-1 said: *"if the empirical PSF is right, the stitching offsets should shrink,
and that is a prediction PR-1 is making in advance and can lose."* **It lost.**

| eleven sub-band joins, ratio of redder to bluer | M6 Gaussian | **M7 empirical** |
|---|---|---|
| median \|ratio − 1\| | **0.109** | **0.138** |
| joins worse than 10% | 7 of 11 | 6 of 11 |
| worst join | 0.496 (4-medium\|4-long) | **3.821** (4-short\|4-medium) |

The two worst M7 joins are `1-long|2-short` (1.544) — **the two crossover
sub-bands that had to borrow a profile** — and `4-short|4-medium` (3.821), both
of which §1.7's diagnostic independently flags. **The empirical PSF improves the
band-integrated fluxes and does not improve the piecewise flux scale, and those
are different things.** Since the acceptance test integrates over a bandpass it
is sensitive to the first and largely blind to the second, which is why the two
results point in opposite directions. **M6 §2.5's claim that the stitching
offsets were *the* limit on the redshift is therefore only half right**: they are
*a* limit, they are not fixed by fixing the PSF, and §1.5's controls show the
continuum degeneracy and the ×1.61 noise excess are limits of their own.

### 1.10 What the reduction establishes, updated

Carried from M6 and re-measured on the validated extraction:

1. **The contaminant is spectroscopically non-stellar** over 12 sub-bands.
2. **M4 §5.2's 10–15 µm index reproduces**: **3.96** here, against M4's **3.8**
   from imaging and M6's **3.79**. The 5.9–10 µm index is **6.88** (M6: 7.12;
   M4: 4.4 over a slightly different baseline).
3. **M4's 441 K single blackbody is now tested twice and lands in the same
   place**: **T_obs = 200 K → 384 K rest-frame** granting z = 0.922, against M6's
   394 K and M4's 441 K. **The better deblend moved it by 10 K, so the ~50 K
   offset from M4 is the model, not the extraction.**
4. **An independent, acceptance-validated extraction of the contaminant's
   spectrum exists and is in this repository** — which is new, and is the thing
   that makes §1.5's negative worth stating.

---

## 2. Injection–recovery beyond the single-blackbody family

*`scripts/m7_injection_families.py` (`run`, `report`), `scripts/m7_catalog_v3.py`;
artifacts `data/injection/m7_injection_families.csv` (100,800 rows, gitignored bulk),
`out/m7_injection_families.json`, `out/m7_injection_families_{headline,walls,by_b,bias}.csv`,
`out/m7_injection_control_identity.json`, `out/m7_fig_families.png`,
`catalog/*_v3.*`. **No network was used at any point.***

M6 §3.4 named its own limit in one sentence — *"an injection–recovery test
measures the pipeline against its own model"* — and marked everything outside
the single-blackbody family **UNMEASURED**. **100,800 injections across six
arms now measure it**, on the same γ axis, the same temperature axis, the same
six |b| bands, the same real hosts and the same real per-band uncertainties
drawn at the *injected* brightness, all pushed through the **unmodified**
pipeline.

### 2.1 The controls first, because the comparison is void without them

**PR-2's analytic falsifier — passed, with one tolerance moved and its reason on
the record.** Both new generators must reduce to M6's family in their degenerate
limits:

| | max \|Δ mag\| vs `w1_selection.ds_absolute_mags` |
|---|---|
| two-temperature at f_warm = 1.0 | **0.0** — exact |
| optically thin at β = 0 | **8.03 × 10⁻⁸** |

**PR-2 said "machine precision" and the β = 0 arm does not reach it — so the
residual was traced rather than the threshold quietly moved.** It is **entirely
the truncated Stefan–Boltzmann constant inside the pre-existing
`w1_selection.py`**: `SB = 5.670374e-8` against the CODATA-derived
**5.670374419184e-8**, a relative **7.393 × 10⁻⁸**, which is **exactly** the
8.026 × 10⁻⁸ mag observed. **The new generator is not the source.** The stated
tolerance is therefore **1 × 10⁻⁶ mag** — five millionths of the 0.2 mag RMSE
gate — and this paragraph exists so a reader can grade that decision instead of
taking it.

**PR-2's run-through falsifier — passed, and it sets the run's own precision
floor.** The β = 0 / f_warm = 1 family pushed through the whole pipeline gives
in-grid |b| > 30° recovery of **43.73%** against M6's **45.85%** — a **−2.12
point** offset at a different seed (20260825 vs 20260824) and a smaller per-cell
count (50 vs 200), which is ≈ 2σ of the combined Monte-Carlo error. **So this
run resolves differences of about 2 points and no better, and every family
comparison below is quoted against the *matched* control from this same run
rather than against M6's number.**

**A third control, not required and passed anyway**: on objects the fit
*accepts*, the single-blackbody arm recovers **T_fit/T_true = 1.006** and
**γ_fit/γ_true = 0.989** — the fitter is unbiased when the SED is the family it
assumes (§2.4).

### 2.2 The headline: completeness is materially family-dependent

In-grid (γ ≥ 0.10 and 100 ≤ T ≤ 700 K) pre-visual recovery, n = 9,000 per arm:

| family | all sky | **\|b\| > 30° — the catalogue's footprint** | \|b\| > 50° | RMSE gate | **Δ vs matched control** |
|---|---|---|---|---|---|
| **single blackbody (control)** | 49.24% | **43.73%** | 42.33% | 90.08% | — |
| two-temperature, f_warm 0.7 | 46.67% | **44.37%** | 44.87% | 84.68% | **+0.64** |
| optically thin, β = 1 | 41.37% | **37.20%** | 37.33% | 74.09% | **−6.53** |
| optically thin, β = 2 | 30.22% | **26.20%** | 26.27% | 54.20% | **−17.53** |
| two-temperature, f_warm 0.5 | 32.24% | **30.20%** | 30.87% | 59.01% | **−13.53** |
| two-temperature, f_warm 0.3 | 26.41% | **26.10%** | 26.00% | 49.77% | **−17.63** |

**PR-2's trigger, declared before the run at 5 percentage points, fires at
19.75** (against M6's own 45.85% reference) **and at 17.6 against the matched
control.** The catalogue is therefore re-issued as **v3** with completeness
stated per family (§2.5).

**The ordering is monotonic in how far the SED is from a blackbody, which is the
sanity check this measurement most needed.** Two-temperature at f_warm = 0.7 —
70% of the reprocessed light in one warm component, i.e. nearly a single
blackbody — is **indistinguishable from the control** (+0.64 points, inside the
2-point floor). Push the light into the cool component and recovery falls
monotonically: 0.7 → 0.5 → 0.3 gives 44.4% → 30.2% → 26.1%. Steepen the
emissivity and the same thing happens: β = 1 → 37.2%, β = 2 → 26.2%. **Nothing
here is a step change; it is a smooth function of SED shape, and that is why it
has to be quoted per family rather than averaged.**

**The RMSE gate is where the loss happens**, and it is a much bigger effect than
M6 saw: the gate passes **90.1%** of in-grid single blackbodies but only
**49.8%** of two-temperature f_warm = 0.3 shells. **M6's "the RMSE fit is not
the bottleneck" is a statement about the blackbody family only** — for a
non-blackbody SED it becomes the bottleneck, because no model in the grid can
represent the curvature.

### 2.3 Both of M6's walls move, and one of them is withdrawn

**The γ cliff is family-dependent** (pre-visual recovery):

| γ | single BB | optically thin β=1 | β=2 | two-temp 0.3 | 0.5 | 0.7 |
|---|---|---|---|---|---|---|
| 0.01 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| 0.02 | 0.00% | 0.05% | 0.05% | 0.00% | 0.00% | 0.00% |
| **0.05** | **1.76%** | **11.33%** | **9.24%** | **0.05%** | **0.14%** | **0.05%** |
| 0.10 | 43.33% | 37.24% | 27.71% | 28.29% | 26.67% | 50.10% |

**At γ = 0.05 the screen is six times less blind to optically-thin dust than to
a blackbody** — 11.3% against 1.8% — because a modified blackbody puts more of
the same bolometric γ into the W3/W4 bandpasses. And it is **blinder still to a
two-temperature shell** (0.05–0.14%), because half the reprocessed light is at
T/3 where W4 no longer samples the peak. **M6's "below γ ≈ 0.05 the screen is
blind" survives as a statement about blackbodies and fails as a statement about
the screen.** The γ ≤ 0.02 floor is family-independent and stands: **nothing is
recovered below γ = 0.02 in any family.**

**The temperature wall is withdrawn as a property of the screen:**

| T (K) | single BB | β=1 | β=2 | two-temp 0.3 | 0.5 | 0.7 |
|---|---|---|---|---|---|---|
| 300 | 52.27% | 53.20% | **34.93%** | 43.20% | 51.87% | 51.00% |
| 450 | 51.27% | 50.20% | **0.00%** | 21.67% | 8.80% | 49.60% |
| 700 | 47.53% | **0.00%** | **0.00%** | 20.27% | 11.13% | 32.13% |
| **1000** | **0.60%** | **0.00%** | **0.00%** | **36.93%** | **30.33%** | **32.53%** |

**M6 called T_ds = 1000 K "a second hard boundary nobody had costed". It is not
a boundary of the screen — it is the edge of the *blackbody* grid.** For a
two-temperature shell, recovery at T_warm = 1000 K is **30.3–36.9%**, barely
different from 700 K, because **T_cool = T_warm/3 = 333 K is back inside the
grid** and the fit latches onto the cool component. And for optically-thin dust
the wall moves the *other* way, to **below 700 K at β = 1 and below 450 K at
β = 2** — a modified blackbody at 700 K looks, to a fitter that only knows
blackbodies, like something hotter than anything it has.

**So every family has its own temperature wall, at its own temperature, and the
screen's blind region in (γ, T) is a different shape for each.** This is the
single biggest revision M7 makes to M6.

### 2.4 What the fit does with an SED it cannot represent

Restricted to in-grid objects the pipeline **accepted** — i.e. rows that would
have entered the catalogue:

| family | n accepted | median RMSE | **median T_fit / T_true** | **median γ_fit / γ_true** |
|---|---|---|---|---|
| single blackbody (control) | 8,107 | **0.028** | **1.006** | **0.989** |
| two-temperature, f_warm 0.7 | 7,621 | 0.091 | 0.938 | 0.903 |
| optically thin, β = 1 | 6,668 | 0.077 | **1.249** | 1.000 |
| optically thin, β = 2 | 4,878 | 0.107 | **1.480** | 1.067 |
| two-temperature, f_warm 0.5 | 5,311 | 0.096 | 0.907 | **0.667** |
| two-temperature, f_warm 0.3 | 4,479 | 0.133 | **0.638** | **0.659** |

**Two things follow, both directly usable by anyone reading the catalogue.**

1. **A row's tabulated `t_ds` and `gamma` are biased by −36% to +48% if the true
   SED is not a single blackbody**, and the direction is diagnostic: an
   optically-thin emitter is fitted *hotter* than it is, a cool-dominated
   two-temperature shell *cooler* and *thinner*.
2. **The RMSE gate does not catch it.** Accepted non-blackbody objects sit at
   **3–5× the residual** of an accepted blackbody (0.077–0.133 against 0.028)
   and still clear the 0.2 mag gate comfortably. **A high but sub-threshold RMSE
   is the only in-catalogue signature that a row may not be the family the
   parameters assume**, and it is now measured rather than speculated.

### 2.5 Catalogue v3

PR-2's declared consequence is honoured. **`catalog/dyson-revet_highlat_extreme_IR_excess_v3.csv`
— 223 rows, byte-identical to v2, and the build asserts it** before writing:
an injection–recovery result says what the selection function is, not which
objects passed it, and M7 did not re-run the screen. What changes is
`catalog_stats_v3.json`, whose completeness block now carries the per-family
recovery function, both walls per family, the parameter bias of §2.4 and the
run's ~2-point Monte-Carlo floor, and `README_v3.md`, which opens on the one
thing a user must know:

> **There is no single completeness number for this catalogue.** Pre-visual
> recovery at |b| > 30° runs **26.1% to 44.4%** depending on the SED family.
> Quote the family you mean.

**`v1` and `v2` — their CSVs, their stats files and their READMEs — are verified
unmodified by checksum after the v3 build** (§5).

**Still UNMEASURED and still marked so in v3**: silicate-featured SEDs, edge-on
geometry, and anything whose 10-band photometry none of the three families can
generate. M7 widens M6's measurement from one family to three; it does not close
the statement, and v3 says so.

---

## 3. Candidate E — READY, nothing pre-empted, and one thing added to its file

*`scripts/m6_e_ready.py` (unmodified); artifacts `out/m6_e_readiness.json`,
`out/m7_e_ready.log`.*

PR-3 permits three actions and no analysis. All three were run today, through
**M6's unmodified script**.

1. **The outcome map is unedited, and the check is a hash.** M5 §5.3 is
   **3,586 characters**, SHA-256 `fa93e2c852befdb51f661f65a3a6bd92333d8e4cb8b581af33555feab87b937b`,
   **byte-identical to the same section of the last committed M5** — and
   identical to the hash M6 recorded, so it has not moved across two
   milestones. All four cases present.
2. **The procedure still reproduces M4 §5 on 7 of 7**: separation 1.233″,
   PA 32.998°, ρ F560W 0.236, ρ F1000W 7.242, ρ F1500W 83.135, ρ(W3, 12 µm)
   21.811, predicted W3 pull 1.179″ — every one inside its tolerance. **READY.**
3. **E is still embargoed**: anonymous MAST, `proposal_id = 7199`, target
   `Object_E` — **0 PUBLIC of 39**, single release date **2026-09-09**,
   unchanged from M5 and M6. **Nothing was fetched and nothing was analysed.**

**What M7 adds to E's file, and it is a sharper version of M6's warning.** M6
told E's chain to treat a band's contrast as uncertain at the tens-of-percent
level when the contaminant is the fainter member there. **§1.4 now gives that
warning a number and §1.7 gives it a boundary:**

- **The bias is a function of contrast, and it is large.** A wingless deblend
  under-recovers a companion at 1% of the primary by **42%** (59% on resolved
  sub-bands), at 5% by **7%**, and at 30% by **1%**. E's imaging has D's
  geometry, so **any band where E's contaminant is ≳ 20× fainter than E's star
  should be treated as biased low by tens of per cent unless an empirical PSF is
  built first** — and §1's code builds one from whatever cubes exist.
- **There is a hard floor below which no deblend is determined at all.** At
  separations under ≈ 2 PSF FWHM the two-component system is collinear and the
  fitted fluxes go **unphysically negative** — 44% to 86% of slices in D's Ch3-long
  through Ch4. **Before quoting any contrast for E, check sep/FWHM and check the
  negative-flux fraction**; both are one line and both are in
  `m7_mrs_sensitivity.py`.

**None of this alters M5 §5.3's outcome map**, which turns on (separation,
contrast) at the order-of-magnitude level and on whether the archival centroid
points at the real contaminant — neither of which a tens-of-per-cent contrast
error can flip. **The map is not edited, and its hash is the proof.**

---

## 4. The front summary

PR-4's deliverable is [`FRONT-SUMMARY.md`](FRONT-SUMMARY.md), written as its own
file so the front can be picked up from one document: what the re-screen
established, what it could not, what the catalogue is and is not usable for, and
the standing dated triggers. It carries the negatives across rather than
summarising them away.

---

## 5. Corrections to ourselves, and what M7 got wrong on the way

Repo law: negative results are results, and so are one's own errors.

1. **M6's Ch4-long extraction is a defect.** Its plate-offset grid search railed
   at both ±1.5-pixel edges and its width at the top of its grid, returning a
   contaminant/star ratio of 0.86 where the neighbouring sub-band gives 33.5
   (§1.1). M6 reported the ratio without flagging the railing.
2. **M6 §2.5's "what would fix it" is half right.** The empirical PSF *did* fix
   the acceptance test, as M6 predicted. It did **not** fix the sub-band
   stitching offsets, which M6 named as *the* limit — they got slightly worse
   (§1.9).
3. **M6 PR-2's redshift criterion is structurally undecidable for this line
   list** (§1.6). Reported as a defect in the pre-registration, not used to
   re-read the result.
4. **M6's "the RMSE fit is not the bottleneck" is family-specific.** It passes
   90.1% of in-grid blackbodies and 49.8% of two-temperature shells (§2.2).
5. **M6's temperature wall at 1000 K is withdrawn as a property of the screen**
   (§2.3).
6. **M7's own first empirical PSF was wrong twice, and both were caught by
   internal checks rather than by the acceptance test.** (a) The profile was
   normalised over a range that included a noisy negative wing, which made the
   encircled energy exceed 1 — caught because EE > 1 is impossible, and fixed by
   truncating at the first non-positive radial bin and extrapolating a fitted
   power-law tail. (b) Profiles were normalised at each λ-bin's own FWHM but
   evaluated at each slice's, leaving a systematic of order 2 × (ΔFWHM/FWHM)
   across every sub-band — caught by the star-scaled sensitivity coming out a
   uniform factor ~6 low, and fixed by storing the profile scale-free and
   applying the FWHM² scaling at evaluation. **The corrected build's acceptance
   ratios are identical to two decimal places, so neither bug drove the 6-of-6**
   — but a synthetic point source now integrates to 1.000 at any FWHM, which it
   did not before.
7. **A latent truncation in `w1_selection.py`**: `SB = 5.670374e-8` against
   CODATA's 5.670374419184e-8 (§2.1). Harmless at 8 × 10⁻⁸ mag; recorded because
   it is the kind of thing that is only ever found by a control.
8. **M6's file index lists `.log` files as committed artifacts and they never
   were** — the repo-root `.gitignore` has excluded `*.log` since before M6, and
   `git ls-files` returns nothing for `dyson-revet/out/*.log`. Corrected in §7;
   no number depends on it, because every number is also in a committed `.json`
   or `.csv`.

---

## 6. Recommended M8 — or, the honest answer: the front is done pending its dated triggers

**M7 was commissioned as a closing milestone and it closes.** The three things
M6 left open are now settled or bounded: D's redshift has a verdict, the
completeness has a second and third model family, and E is ready. **There is no
M8 that this front needs before 2026-09-09.**

**The standing dated triggers, unchanged and all in `FRONT-SUMMARY.md` §6:**

1. **Candidate E, 2026-09-09.** §3's three commands, M5 §5.3's hash-verified
   outcome map, and §1.7's determinacy check added to the procedure. This is the
   only dated item.
2. **Candidate A, 2027-07-16** — GO 7199 exclusive access ends; it would make the
   JWST-vetted sample 3.
3. **Matthew's two calls, unchanged since M2 and M4 and adding nothing new**:
   (a) whether the Ren+24 unit-error note is worth submitting given Blain 2024's
   prior "(sic)", and if so the three manual browser checks first; (b) whether
   the candidate-I dossier becomes a JWST DDT / small-GO proposal, an RNAAS note,
   or stays internal. **M7 adds no new Matthew-gated item.**

**If a further milestone is wanted rather than needed**, the ranked leftovers,
none of which changes a headline:

- **§1.5's negative is the most publishable thing in the front and is not
  written up.** An independent, acceptance-validated extraction that cannot
  confirm a published redshift — with the deblend excluded as the cause by an
  injection test — is a short-note-sized result. It would be **Matthew-gated
  before leaving the repository**, per M5 PR-4's own rule, because it is a
  negative about a published claim.
- **The 12.7-point residual at the RMSE gate** (M6 §1.7) is still unmeasured; the
  named candidates are source morphology inside 1 W4 FWHM, nebulosity beyond the
  45″ aperture, and whatever a CNN trained on 960 images encodes.
- **A silicate-featured injection family**, the one physically distinct family
  §2 did not reach.
- **Separate galaxies from stars in N3** (carried from M5 §7 and M6 §5).
- **Re-cost the γ ≥ 0.01 grid floor** now that §2.3 shows the γ = 0.05 recovery
  is family-dependent — M6's costing used the blackbody number alone.
- **M4 §7.7's ~3% parent residual.**

---

## 7. File index (new in M7)

**Documents:** `M7-empirical-psf-completeness-close.md` (this),
**`FRONT-SUMMARY.md`** (the front's stand-alone hand-over document).

**Product:**

- `catalog/dyson-revet_highlat_extreme_IR_excess_v3.csv` — **223 rows,
  byte-identical to v2**, asserted at build time
- `catalog/catalog_stats_v3.json` — completeness **per SED family**, both walls
  per family, the parameter bias, the Monte-Carlo floor
- `catalog/README_v3.md` — opens on "there is no single completeness number"
- `catalog/*_v1.*`, `catalog/*_v2.*` — **unmodified, checksum-verified after the
  v3 build**

**Scripts (new):**

- `scripts/m7_mrs_epsf.py` — `build` (the donor rule, the empirical PSF, the
  per-slice deblend), `inject` (PR-1's 2 × 2 injection–recovery)
- `scripts/m7_mrs_sensitivity.py` — `resolved` (the determinacy diagnostic and
  the band-restricted spectra), `starscaled` (PR-1's declared sensitivity)
- `scripts/m7_injection_families.py` — `run` / `report`: the two new SED
  families, their controls, the walls, the parameter bias
- `scripts/m7_catalog_v3.py` — the v3 build, with the v1/v2 integrity assertions
- `scripts/m7_figures.py` — the two figures, from the artifacts

**Scripts changed: none.** M6's, M5's and M4's scripts are untouched — which is
what makes §1.3's "graded by byte-identical code" checkable. `m7_mrs_epsf.py`
writes to the filenames `m6_mrs_redshift.py` already reads rather than editing
that script; `m7_injection_families.py` imports M6's host, noise and fitting
machinery rather than copying it.

**Artifacts:**

- `out/m6_mrs_D_epsf_{spectra,cubes,contaminant_spectrum,star_spectrum,zscan,narrow_consensus}.csv`,
  `out/m6_mrs_D_epsf_redshift.json` — the primary extraction and its grading
- `out/m6_mrs_D_{res,epsf_res,starscaled}_*.csv/json` — the three sensitivities
  and their gradings
- `out/m7_epsf_{build,inject}.log`, `out/m7_epsf_diagnostics.csv`,
  `out/m7_epsf_profiles.csv`, `out/m7_epsf_psfs.json`,
  `out/m7_epsf_psf_check.json`, `out/m7_epsf_injection.{csv,json}`,
  `out/m7_epsf_stack.npy`
- `out/m7_mrs_resolved.json`
- `out/m7_injection_families.json`,
  `out/m7_injection_families_{headline,walls,by_b,bias}.csv`,
  `out/m7_injection_control_identity.json`
- `out/m6_e_readiness.json`
- `out/m7_fig_{epsf,families}.png`
- **Console logs are LOCAL, not committed** — `out/m7_{epsf_build,epsf_inject,resolved,starscaled_build,e_ready,injection_families_run}.log`
  and `out/m7_grade_{epsf,D_res,D_epsf_res,D_starscaled}.log`. The repo-root
  `.gitignore` has excluded `*.log` all along, so **M6's file index was wrong to
  list its own `out/m6_e_ready_{validate,status}.log` as committed artifacts —
  no `.log` under `dyson-revet/out/` has ever been tracked.** Every number in
  this document is also in a committed `.json` or `.csv`; the logs are
  reproduction convenience only, and each is regenerated by the single command
  named at the head of its section.
- `data/injection/m7_injection_families.csv` (100,800 rows) — bulk, gitignored
  per repo convention, as M6's injection table is

**Nothing in this milestone has been submitted, posted, or sent anywhere. No
account was created at MAST, IRSA, SVO or anywhere else; every service was used
anonymously, and §2 and §3 used no network at all. Nothing was committed and
nothing was pushed. The candidate-I dossier and the Ren+24 note remain
Matthew-gated and unchanged.**
