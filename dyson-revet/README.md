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
- **W4 — the full re-screen** (only after W1–W2 validate): the 5M-star selection re-run with the
  contamination machinery, producing the vetted catalog or the calibrated null.

## Conventions

Repo law: results docs `M<N>-*.md`, dated, sourced-or-UNSOURCED; `STATUS.md` newest-first; bulk
data in `data/` (gitignored), venv in `.venv/`; committed scripts LF; no accounts, no submissions,
nothing reported externally — candidate-level claims are Matthew-gated like everything else here.
