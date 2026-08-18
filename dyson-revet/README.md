# dyson-revet — the Gaia × WISE extreme-IR-excess screen, done with real false-positive control

**What this is.** Avenue **#7** of [`../DISCOVERY/run3-prospectus.md`](../DISCOVERY/run3-prospectus.md),
extending the portfolio's SETI thread: Project Hephaistos II selected 7 Dyson-sphere candidates from
~5M Gaia×2MASS×WISE stars ([MNRAS 2024](https://academic.oup.com/mnras/article/531/1/695/7665761)).
Radio imaging killed candidate G; a [Jul 2026 diagnostics paper](https://arxiv.org/abs/2607.03619)
finds B & C contaminated, D & I still clean — and says vetting is incomplete. **Nobody has redone
the full screen with blend forward-modeling and contamination priors.** That re-vet is the house
method (kill the fake wins), and the deliverable is valuable whichever way it lands: a quantified
null on the method's yield, or a defensibly clean extreme-IR-excess catalog (debris disks, WD
pollution — real astrophysics regardless of technosignature framing).

## Workstreams

- **W1 — reproduce the selection.** Implement Hephaistos II's cuts (Gaia DR3 × CatWISE2020 ×
  2MASS); acceptance: **all 7 published candidates recovered** by our implementation on a
  validation pull before any full-screen talk. Measure throughput; plan the 5M-star run honestly.
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
