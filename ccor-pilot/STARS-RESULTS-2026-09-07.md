# Known-star geometry: measured, not fully passed

The [new independent protocol](STARS-SPEC-2026-09-07.md) selected eight public
Hipparcos stars before any retrospective pixels: HIP51624,51775,52911,51008
(training), HIP51802,52452,53449,51213 (held out). This bypasses the original
reporter's undocumented display mapping; it does not resolve that mapping.

| UTC frame | Training recovered /4 | Held-out recovered /4 | Held-out RMS, pixels | Gate |
|---|---:|---:|---:|---|
|13:00|3|3|0.4476|pass|
|13:15|1|3|0.3983|fail training count|
|13:30|3|3|0.4379|pass|
|13:45|2|3|0.2876|fail training count|

**Overall STOP_STAR_GEOMETRY.** Do not waive a training-count failure because
the surviving held-outs look good. The recovered stars support coarse local
WCSA/ICRS consistency but do not certify every frame, full-field distortion,
absolute photometry, moving-object completeness or a confirmed comet. Translation
norms were within the frozen 5-pixel bound; no reflection/rotation search occurred.
None of the 128 fixed offset controls passed the same measurement rule. These
are local engineering controls, not a calibrated false-positive probability.

Weak peak contrast caused most losses; HIP51624's second-frame source aperture
also failed the strict all-unflagged support test despite peak contrast9.38.
No masked source was silently recentered or reinstated, and no star was replaced.
Stars differ in broad visible response; Vmag ranking alone is not a guarantee
of CCOR detectability. A future stronger protocol would need an independent
calibrator selection/training interval and prospective sensitivity assessment,
not posthoc deletion of the inconvenient frames here.

The NOAA provisional ReadMe Table5-6, pages24-25, was rendered and visually
checked: PQF0 is unflagged/linear and bit values are not their flag suffixes.
All nonzero PQF was excluded in the source support. Astropy emitted documented
WCS normalization warnings (date-derived MJD, unrecognized bare CROTA and
derived OBSGEO spherical values); raw headers were not edited. Only the celestial
WCSA pixel transform was used, not derived terrestrial observer coordinates.
Proper motion was propagated from Hipparcos epoch1991.25; subpixel stellar
aberration/parallax were not fitted under the declared coarse tolerance.

[Results](results/stars-20260907/results.json),
[selection](results/stars-20260907/selection.json),
[exact Hipparcos response](results/stars-20260907/catalogue.zip),
[request provenance](results/stars-20260907/provenance.json),
[known-star pixel fixture](results/stars-20260907/known-star-cutouts.npz).
Four complete retrospective FITS remain ignored locally, preserving PQF and
negative-control patches for full-data follow-up. Source byte hashes bind the
downloads to the prior exact header prefixes. The 193,003-byte tracked fixture
replays all32 central-star measurements in CI; negative-control pixels require
the full retained source images and are not part of that compact replay.

28 offline tests pass, including five new star/mask/holdout/pixel replay tests.
The original operational experiment is still stopped before its pixel stage.
This separate retrospective experiment did measure pixels; no comet search or
NOAA message was sent.
