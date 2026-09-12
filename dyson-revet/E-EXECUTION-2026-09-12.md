# Candidate E execution - September 12, 2026

## Decision

**STOP_FROZEN_MEASUREMENT.** The release gate passed and the unchanged frozen
imaging experiment was executed. It failed at F560W centroiding. An independent
local audit reproduced the failure and identified its numerical cause. The frozen
attempt is closed at a method failure; the scientific question remains unresolved.
No four-outcome branch, validated contrast, or discovery is assigned. Do not
repeat identical daily runs, drop a filter, substitute a centroid, or relax the
original thresholds. A replacement method is a separate, control-first study.

This supersedes the pending-execution state in
[the September 5 follow-up](E-FOLLOWUP-2026-09-05.md), not the original
[M5 outcome map](M5-nebular-stage-highlat-catalog.md) or M7 conclusions.

## Release, inputs and execution

[Release receipt](out/e-release-20260912.json), checked at
2026-09-12T18:38:41.911982Z: D control **7 PASS / 0 FAIL**, **39 PUBLIC** MAST
observations, release date September 9, outcome-map SHA-256 unchanged:
`fa93e2c852befdb51f661f65a3a6bd92333d8e4cb8b581af33555feab87b937b`.
The guard returned `READY_FOR_FROZEN_ANALYSIS` before E measurement.

Executed from `dyson-revet` in its existing environment:

```text
.venv/Scripts/python.exe scripts/check_e_release.py --out out/e-release-20260912.json --timeout 45
.venv/Scripts/python.exe scripts/m5_jwst_target.py status --label E
.venv/Scripts/python.exe scripts/m5_jwst_target.py fetch --label E
.venv/Scripts/python.exe scripts/m5_jwst_target.py measure --label E --obsprefix jw07199-o006
```

All nine requested L3 products were fetched: `_i2d.fits`, `_cat.ecsv`, `_segm.fits`
for F560W/F1000W/F1500W, prefix `jw07199-o006_t008_miri_`, **135,386,830 bytes**.
The [MAST download service](https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:JWST/product/jw07199-o006_t008_miri_f560w_i2d.fits)
serves the exact public filenames recorded in the
[execution receipt](out/e-execution-20260912.json). It records each input's bytes
and SHA-256, the release receipt hash, and the executed script hash. Raw products
are retained under ignored `data/jwst/`, not embedded in Git. CAL_VER is 2.0.1,
CRDS `jwst_1535.pmap`; images are 1156 x 1205 pixels in MJy/sr.

The command completed partial F1000W and F1500W diagnostics, then exited 1 when
F560W's centroid became non-finite and `CircularAperture` refused its positions.
No final E summary or photometry product was produced. A second identical run
retained the failure log/receipt locally; their hash and timestamp are bound in
the aggregate receipt. Candidate-bearing logs are not committed.

## Independent failure and M7 validity audit

The [audit code](scripts/e_execution_audit.py) rereads the FITS files and checks
the same fitting patch with an independent least-squares quadratic Hessian.
Every 121 x 121 cutout is finite (14,641/14,641 pixels); every 7 x 7 fitting patch
is finite (49/49). **Missing image pixels did not cause this failure.**

| Diagnostic only | F560W | F1000W | F1500W |
|---|---:|---:|---:|
| Annulus peak / background RMS | 67.40 | 185.41 | 100.29 |
| Quadratic centroid finite | No | Yes | Yes |
| Hessian eigenvalues | -0.980, +9.835 | -1.642, -0.751 | -0.837, -0.277 |
| Partial separation, arcsec | Not measured | 0.97445 | 0.99024 |
| Separation / nominal PSF FWHM | Not measured | 2.971 | 2.029 |
| Separation / measured star FWHM | Not measured | 1.802 | 1.818 |
| Separation / measured second-profile FWHM | Not measured | 1.229 | 0.767 |

F560W's brightest annulus pixel is at radius 0.54214 arcsec, near the inner search
boundary. Its quadratic is a **saddle**, not a maximum. Photutils explicitly warns
that it has no maximum and returns NaNs, matching its
[documented failure behavior](https://photutils.readthedocs.io/en/stable/api/photutils.centroids.centroid_quadratic.html).
Keyword-deprecation warnings are incidental. No substitute centroid was used.

The peak threshold fires in all three filters, but a bright annulus pixel is not
independent validation of a second source. The broad profiles and aperture-dependent
ratios in the completed bands prevent treating partial separations and flux ratios
as a validated physical deblend. Nominal point-source resolution alone is inadequate.
M7's roughly two-FWHM caution is a diagnostic, not a newly fitted acceptance rule.

Six aperture pairs completed; none had negative flux. **This is not M7's MRS
negative-slice fraction.** No E MRS extraction was performed, so that fraction is
null in the receipt. Neither M7's 20% MRS criterion nor its contrast-bias correction
can be transplanted onto imaging aperture counts. See
[M7 sections 1.4 and 1.7](M7-empirical-psf-completeness-close.md).

Do not call this Outcome 2 because two partial separations are below one arcsec,
Outcome 3 because the command failed, or Outcome 4 merely because a method failed
on finite images. It neither independently confirms nor contradicts the published
contamination attribution.

## Verification and next work

Four new offline contracts prevent failed/incomplete runs from becoming valid
contrasts or non-detections; all **15** release/execution tests pass. Full local
FITS audit replay passes exactly. CI exercises offline contracts, not the 135 MB
raw-data reproduction. Replay requires retained products, failure log/receipt,
and the original numerical environment:

```text
.venv/Scripts/python.exe -B scripts/e_execution_audit.py --replay
python -B -m unittest discover -s tests -v
```

The [initial audit source](out/e-audit-initial-source-20260912.zip) and
[initial receipt](out/e-execution-initial-20260912.json) are preserved. An
import-order lint fix and `--reuse-log` option followed; the final receipt was
regenerated from the retained failure and its own code hash. No frozen scientific
script or outcome map was edited.

Decision under delegated local research authority: park E method development,
not its failure record. A replacement must first specify a joint spatial model,
PSF/control selection independent of E's desired answer, extended-source and
star-only controls, injection recovery across the relevant separation/contrast
range, residual checks, and uncertainty/coverage tests. E is already inspected
and cannot serve as a blind holdout. Passing D alone is demonstrably insufficient.
Only then consider an explicitly exploratory E result. No publication,
submission, private-coordinate request, or discovery claim was made.
