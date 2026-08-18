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
