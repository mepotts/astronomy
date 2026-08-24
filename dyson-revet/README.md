# dyson-revet — the Gaia × WISE extreme-IR-excess screen, done with real false-positive control

**What this is.** Avenue **#7** of [`../DISCOVERY/run3-prospectus.md`](../DISCOVERY/run3-prospectus.md),
extending the portfolio's SETI thread: Project Hephaistos II selected 7 Dyson-sphere candidates from
~5M Gaia×2MASS×WISE stars ([MNRAS 2024](https://academic.oup.com/mnras/article/531/1/695/7665761)).
Radio imaging killed candidate G; a [Jul 2026 diagnostics paper](https://arxiv.org/abs/2607.03619)
finds B & C contaminated — and says vetting is incomplete. **Nobody has redone the full screen with
blend forward-modeling and contamination priors.** That re-vet is the house method (kill the fake
wins), and the deliverable is valuable whichever way it lands: a quantified null on the method's
yield, or a defensibly clean extreme-IR-excess catalog (debris disks, WD pollution — real
astrophysics regardless of technosignature framing).

> **Premise correction, 2026-08-18 (M1) — D is retired; I is the last candidate standing.**
> This README originally read "D & I still clean", following Ren et al. 2026 (submitted ~3 Jul 2026).
> **Project Hephaistos IV** (Zackrisson et al., [arXiv:2607.09460](https://arxiv.org/abs/2607.09460),
> 10 Jul 2026 — JWST/MIRI imaging + MRS) attributes candidate **D**'s mid-IR excess to an IR-bright
> background galaxy at z ≈ 0.9, ~1″ from the star (AGN-like MIRI spectrum, Hot-DOG-like SED). D is
> **CONTAMINATION-CONFIRMED**; the same paper also kills **E**. My independent archival tests show
> *why* every archival method (theirs and mine) graded D "weak evidence": a real contaminant at 1.0″
> moves the AllWISE centroid by only ~0.5–1.4″, inside the noise floor — **centroid vetting has a hard
> sensitivity floor at ~1–2″ separations** ([M1 §3.2](M1-reproduce-and-vet.md#32-candidate-d--contamination-confirmed-externally-what-archival-data-alone-says),
> formally retired in [M2 §1](M2-dossier-and-screen.md)). Of the ten labelled candidates, **five have
> an identified contaminant** (B, C, D, E, G — two of them by JWST), one is suggestive (A), two carry
> ambiguous indications (H, J), and two have no positive contamination evidence (F and **I**).
> **Candidate I** — a Hephaistos *III* object that failed II's SNR cut — is the last one with no
> identified contaminant, and its own verdict is INDETERMINATE, not clean:
> see [`I-dossier.md`](I-dossier.md). A third candidate (**A**) was observed by JWST on 14 Jul 2026
> and the result is not yet published (M2 §0.4).

> **Premise update, 2026-08-21 (M3 §5) — the JWST-vetted sample is still 2, not 3.**
> M2 predicted the third GO 7199 target (candidate **A**, observed 2026-07-14) would shortly make
> it 3. It has not: as of 2026-08-21 **no result on candidate A has been published anywhere**
> (arXiv API sweeps over `Hephaistos`, Zackrisson, Suazo, Korn, Ren, Assef, Siemion, "Dyson
> sphere", technosignature, megastructure; Semantic Scholar and OpenAlex both give
> arXiv:2607.09460 **zero** citations; ADS remained unreachable). The collaboration's own newest
> papers agree — Ren et al. (arXiv:2607.03619 **v3**, 2026-08-07, accepted MNRAS) still calls the
> GO 7199 observations of "Candidates A, D, and E" **ongoing**, and Hephaistos III
> (arXiv:2607.25701, 2026-07-28) still says "for **two** of our stars". **The tally above is
> unchanged: five candidates with an identified contaminant (B, C, D, E, G), two of them by JWST.**
> New and actionable: **candidate D's JWST/MIRI data have been public since 2026-07-28**, and
> **candidate E's open on 2026-09-09**; candidate A's are under exclusive access until
> **2027-07-16** ([GO 7199 program info](https://www.stsci.edu/jwst-program-info/program/?program=7199&pi=1),
> MAST CAOM, 2026-08-21).

> **Premise update, 2026-08-21 (M4 §5) — candidate D's contaminant measured from the public JWST
> data, not cited from the paper.** GO 7199's D products have been public since 2026-07-28 and were
> pulled anonymously from MAST and re-measured here (the MAST L3 mosaics are `CAL_VER 2.0.1 /
> CRDS jwst_1535`, a **newer, independent re-reduction** than the 1.20.2/1364 Hephaistos IV used).
> **The contaminant is real and it is what carries the excess**: separation **1.23 ± 0.07″ at
> PA 33 ± 1°** (the paper says only "≈1 arcsec" and quotes no PA), contrast f_con/f_star = **0.236 /
> 7.24 / 83.1** in F560W/F1000W/F1500W, contaminant point-like to 94–97% of the CRDS point-source
> concentration, F<sub>ν</sub> ∝ λ<sup>+4.4</sup>, and the pair reproduces the AllWISE W3 flux to
> +12% with the contaminant supplying **88% at 10 μm and 98.8% at 15 μm**. The star itself is
> photospheric (3473 K blackbody, no intrinsic excess). **The tally above is unchanged** — D was
> already contamination-confirmed; what is new is that this project has now confirmed it from the
> data rather than from the citation. **The z ≈ 0.9 Hot-DOG identification is NOT independently
> confirmed here**: it rests on the MRS spectrum, which was not reduced — UNSOURCED by this project.
> **What this calibrates**: the flux-weighted centroid pull is `sep · ρ/(1+ρ)`, so the geometric
> ceiling is the separation itself, **1.23″**. Our own archival W4 offset for D (2.55 ± 0.50″) and
> Ren et al. 2026's (1.8″) both **exceed that ceiling**, and our W3 offset points at PA 82.9° — 50°
> away from the real contaminant, where MIRI shows nothing. The threshold separation an archival
> centroid test needs is **sep_thr(ρ) = F · (1 + 1/ρ)**, asymptoting to the floor F itself, so
> **≈10% (1″ floor) to ≈40% (2″ floor) of chance-aligned contaminants inside Suazo et al.'s own
> 3.25″ aperture are invisible to centroid vetting at any brightness.** The README's "~1–2″ floor"
> language above is confirmed and now carries a number.

> **Result, 2026-08-23 (M5) — the last irreproducible stage now has a reproducible replacement, and
> the positive deliverable exists.** M4 localised the entire 4.2× overproduction to Hephaistos II's
> unpublished nebular CNN. [M5](M5-nebular-stage-highlat-catalog.md) builds a stage out of public
> data — **N1**, a veto on the *published angular extent* of **29,462 nebulae from 14 VizieR
> catalogues** (no free parameter: the radius is the catalogue's own); **N2**, the percentile rank of
> AllWISE's own coadd background (`w3sky`/`w4sky`) against the **|b| > 50° parent binned by ecliptic
> latitude**, cut at 0.99; **N3**, the local source density, reported and not cut. **Pre-visual
> survivors 1,545 → 585 against the paper's 368: 4.20× → 1.59×**, and by latitude **20.89× → 2.62×
> at |b| < 5°** while **|b| > 50° is untouched at 1.05×**. **7/7 published candidates preserved**,
> the rejected fraction falls **monotonically** with |b|, and the 0.95/0.99/0.999 sensitivity band
> moves the answer by only ±5%. **Stated in advance and true: it does not close the plane** — ours
> rejects 31.2% at the RMSE gate where their CNN rejects 49.0%, and that **17.8-point difference is
> the measurement of what the unpublished stage was doing**. **The vetting of all 1,545 full-sky
> survivors is finished: 719 CONTAMINATION-CONSISTENT, 584 INDETERMINATE, 242 SUB-THRESHOLD,
> 0 STILL-CLEAN** — and the zero is **by construction**, because V5 is retired (below), so the
> survivors are *objects with no detectable contamination evidence given a method with a known blind
> spot*, never "clean". **The positive deliverable is shipped**:
> [`catalog/`](catalog/dyson-revet_highlat_extreme_IR_excess_v1.csv) — **223 extreme mid-IR-excess
> stars within 300 pc at |b| > 30°**, 62 columns, the **90-object |b| > 50° calibrated core flagged
> per row**, its own [README](catalog/README.md), and completeness/contamination stated as measured
> numbers including what is **UNMEASURED**. *Route finding, reusable everywhere: **IRSA's Gator
> multi-position upload is anonymous and runs at 0.0027 s/position against TAP's 3.5 s — ~1,300×**;
> it counted only after an acceptance test returned 1,545/1,545 identical designations with zero
> disagreements.*

> **Result, 2026-08-24 (M6) — the morphology stage exists, it closes part of the 17.8 points, and
> the reduction of candidate D's spectrum says what it can and cannot settle.**
> [M6](M6-morphology-mrs-completeness.md) adds **N4**, a structure statistic read off the AllWISE
> W3/W4 coadds themselves: **S = σ_obs/σ_exp** in a 12–45″ annulus — the robust dispersion of the
> PSF-smoothed image over what the coadd's *own uncertainty image* predicts — with **no training
> set** and a **parameter-free null of 1** (measured 1.396/1.245 on 27,876 |b| > 50° parent stars).
> Its threshold is M5's N2 rule *verbatim*, so no new free parameter enters. **All three validation
> criteria pass: 7/7 published candidates preserved**, the flagged fraction falls **monotonically**
> with |b| (70.3 → 1.1%), and at |b| > 50° that **1.14% is below the stage's own measured 1.20%
> false-positive rate.** **Pre-visual survivors 1,545 → 585 (M5) → 411 against the paper's 368;
> overproduction 4.20× → 1.59× → 1.117×, and every latitude band now sits within ±50% of the
> published rate.** **But the 17.8 points are only partly closed**: at the RMSE gate ours rejects
> **36.3%** against the CNN's **49.0%** — **5.1 points closed, 12.7 remaining**, with the candidates
> for the residual named. **N4 sees what N1 and N2 cannot: 486 objects, 5.1% of the RMSE survivors,
> that no catalogue lists and whose background is not in the top 1%.**
>
> **Candidate D's MRS cubes are reduced** — twelve public Level-3 cubes, 4.90–28.70 µm,
> 11,625 slices deblended — and **the first independent extraction of the 1.23″ contaminant's
> spectrum now exists**. **It cannot settle z ≈ 0.922, and the reason is measured**: the
> pre-registered acceptance test **fails 4-of-6, with the *dominant* member of the pair passing in
> every band and only the *sub-dominant* one failing** (PSF-wing leakage across 1.23″); the blind
> redshift scan's best z moves **0.47 → 1.06** for a ±0.02 dex change in the continuum window; a
> blind narrow-line test finds **41.1% of the redshift grid does as well as z = 0.922**; and the MRS
> **sub-band stitching offsets reach 11–28%, the same size as the features being searched for**.
> **No redshift is quoted**, per the pre-registration. What it *does* establish: the contaminant is
> spectroscopically non-stellar over twelve sub-bands, M4's 10–15 µm index **3.8 reproduces at
> 3.79**, and **M4's 441 K single blackbody is tested for the first time and comes out ~10% cooler,
> 394 K**. **The published identification still rests on a reduction only the collaboration has
> done.**
>
> **Completeness is measured at last** — 75,600 injections through the unmodified pipeline: in-grid
> pre-visual recovery **50.2% all-sky, 45.8% at |b| > 30°**, and **the RMSE fit is not the
> bottleneck** (it passes 90.3%). **Two hard walls become numbers: γ = 0.01 → 0.00%, 0.05 → 2.5%,
> 0.10 → 43.9%** — below γ ≈ 0.05 the screen is *blind*, not inefficient — and **T_ds = 1000 K →
> 0.17% against ~31% inside the [100, 700] K grid**, a second wall nobody had costed. A control of
> **8,400 bare photospheres gives a 0.00% RMSE-gate false-positive rate**. The catalogue is
> re-issued as [**v2**](catalog/dyson-revet_highlat_extreme_IR_excess_v2.csv) — same 223 rows, 13
> added columns, its own [README](catalog/README_v2.md) — **with v1 left untouched**.

> **Method retirement, 2026-08-23 (M5 §6) — V5, the archival centroid axis, is formally RETIRED.**
> M3 §3.2 disabled it and prescribed a retune (3″ search radius, neighbour-aware validity check);
> **that prescription is withdrawn.** M4 §5.3 measured candidate D's contaminant at
> **1.23 ± 0.07″, PA 33 ± 1°** from public JWST/MIRI mosaics, and against that truth the archival
> centroid is wrong in **direction** (our W3 offset points 50° away, where MIRI shows nothing) as
> well as **magnitude** (our W4 offset 2.55 ± 0.50″ is +2.6σ above a hard geometric ceiling of
> 1.23″; Ren et al. 2026's 1.8″ exceeds it too). A smaller search radius cannot repair a measurement
> whose direction carries no information, and D's contaminant was never a separate AllWISE source at
> all. **What replaces it**: `sep_thr(ρ) = F · (1 + 1/ρ)`, asymptoting to the floor itself — so
> **≈10% (1″ floor) to ≈40% (2″ floor) of chance-aligned contaminants are invisible at any
> brightness**. **Consequence, carried in every verdict table: STILL-CLEAN is unreachable, and there
> is no Matthew-gated candidate from this screen.** The falsifier that would un-retire the axis is
> written down ahead of candidate E's data (M5 §5.3).

> **Route correction, 2026-08-18 (M2 §4.1).** The W4 full-screen plan below was costed on ~24
> anonymous ESA **async** strip jobs. **Anonymous async is broken** (HTTP 500 on every job); the
> screen runs on sync with adaptive tiling instead, checkpointed and resumable. See
> [M2 §4](M2-dossier-and-screen.md) for the measured route and the resume command.

## Workstreams

- **W1 — reproduce the selection.** ✓ **done, 7/7** (M1). Implement Hephaistos II's cuts
  (Gaia DR3 × **AllWISE** × 2MASS — *corrected: the prospectus said CatWISE2020, which contains only
  W1/W2 and cannot host a W3/W4-excess selection*); acceptance: all 7 published candidates recovered
  by our implementation on a validation pull before any full-screen talk. Measure throughput; plan
  the 5M-star run honestly.
- **W2 — the vetting axes.** Per candidate (D and I first): image-domain centroid-offset tests
  (AllWISE/unWISE coadds), hot-DOG surface-density priors, blend forward-modeling. Every axis
  cited to its source; every verdict carries its evidence.
- **W3 — the SPHEREx axis.** 102-band public spectral images (IRSA QR2, account-free) at each
  candidate position — an SED axis that did not exist when Hephaistos ran. Coverage check first;
  honest about calibration limits.
- **W4 — the full re-screen.** ✓ **done, 100.00% of the sky** (M4) with the contamination
  machinery, the vetting finished and a reproducible nebular stage in place of the paper's
  unpublished CNN (M5). It produced **both** halves of the README's own framing: a **calibrated
  null** — no object reaches STILL-CLEAN, and none can while the centroid axis is retired — and
  a **defensibly-bounded extreme-IR-excess catalogue**,
  [`catalog/`](catalog/dyson-revet_highlat_extreme_IR_excess_v1.csv), 223 objects at |b| > 30°
  with per-object vetting flags and measured completeness and contamination.

## Conventions

Repo law: results docs `M<N>-*.md`, dated, sourced-or-UNSOURCED; `STATUS.md` newest-first; bulk
data in `data/` (gitignored), venv in `.venv/`; committed scripts LF; no accounts, no submissions,
nothing reported externally — candidate-level claims are Matthew-gated like everything else here.
