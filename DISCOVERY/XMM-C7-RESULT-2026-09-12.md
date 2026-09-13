# C7 result: positive MOS2 source sampling restores a usable next step

Executed after reviewed freeze `6c7d456`. Worker, parent numerical validation
and one subsequent numerical replay passed. **Static-sign diagnostic only;
no burst recovery or discovery.** C5 pn/MOS1 results remain unchanged.
[Independent postrun review](XMM-C7-POSTRUN-REVIEW.md) accepted receipt integrity
and all20 region-resolution aggregates without another map decoding pass.

The MOS2 published-source circle is positive at every selected subpixel at
both frozen resolutions. Together with C5's pn result, this supplies affirmative
static source-support sampling in pn and oneMOS camera. It does not establish
matched simultaneous/per-bin exposure or pass the stronger recovery draft.

| Fixed region | MOS2 positive area estimate,4 | MOS2, nominal8 |
| --- | ---: | ---: |
| Published circle | 100.0000% | 100.0000% |
| Published annulus | 65.1078% | 65.1064% |
| North circle | 100.0000% | 100.0000% |
| North annulus | 100.0000% | 100.0000% |
| East circle | 65.5777% | 65.5337% |
| East annulus | 68.8605% | 68.8506% |
| South circle | 0.0000% | 0.0000% |
| South annulus | 12.6663% | 12.6547% |
| West circle | 100.0000% | 100.0000% |
| West annulus | 100.0000% | 100.0000% |

All sampled remainder is zero; no negative, nonfinite or out-of-image samples
in these regions. Both resolutions are retained, not selected post hoc.
These are estimated spherical-area sign fractions, not exposure percentages.
Source background annulus is about34.8936% zero nominally; do not substitute
the full geometric area or map amplitude as a calibrated background scale.
North/west are promising MOS2 static negatives, but still require catalogue
confusion and detector/time-dependent checks. C5 pn west has a fine-grid zero
sample and its annulus is partially zero: no automatic two-negative pass.

Nearest unsupported pixel centre to the source is35.139370540543176arcsec,
not a guaranteed finite-pixel boundary. The source-radius-subtracted number
15.139370540543176arcsec is only the already qualified centre-distance diagnostic.
No continuous-coverage, window-cause, exposure or coordinate-calibration claim.

Outcome `STATIC_SUPPORT_APPROXIMATION_NOT_COVERAGE`, SHA256
`3916067cc6a32722ed35d13d6c0bef2a391134890c87d936d01685a1c2d2b621`.
Map result SHA256 `a2a7e0a7c0f9cd7c142bcf61ad6409deea6ed100eb81a6129ccf653b813735b4`.
All10 regions complete, one persisted map ledger. Each numerical pass reads
and decodes1679616 bytes; **three known passes total5038848 bytes**. No extra
pn/MOS1 map decoding occurred. Hash/header input I/O is separate. Worker peak
79699968 and parent80154624 bytes, below fixed500000000. Pre-outcome JSON40350
bytes; final JSON42284 bytes. No new product copies,
network requests or photon/source-list/GTI/attitude-array interpretation in C7.

Next decision: proceed with fixed catalogue-contamination geometry and the
bounded descriptive photon screen design. The source-support gap no longer
requires another map endpoint or aperture choice. Keep all3 cameras and all
fixed controls in future outputs, including the MOS1 zeros. Source association,
masked region areas, regional exposure, detector artifacts and published burst
recovery remain unresolved; do not delay raw descriptive counts indefinitely
or mislabel those counts as calibrated recovery.
