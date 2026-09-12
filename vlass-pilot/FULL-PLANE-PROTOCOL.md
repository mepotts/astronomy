# Fixed parent-plane calibration protocol, 2026-09-12

The small-cutout experiment recovered the known target but selected only one
reference. Its source, protocols, raw inputs and results are preserved unchanged.
This separately authorized calibration-feasibility experiment expands spatial
coverage to the **natural full archive plane** of the same three already-selected
QL2.1/3.1/4.1 observations, T10t18.J113801-033000. No adjacent plane, additional
epoch, second target or unknown-source search is authorized.

Known-target fluxes have already been seen. This is explicitly a retrospective
method-development follow-up with a prospectively fixed new calibration footprint,
not a blinded discovery search or independent confirmation of target variability.

## Before new pixels

1. Reuse the audited tree-aware `bounded_run` helper from
   `dyson-revet/scripts/check_e_release.py`, SHA-256
   `11ad0bef9fd2efae234e204358c6b6730e723ed3dc24c6fe0c345f2ddcfb53dd`.
   Test exact owned-tree termination and absolute-path worker commands before
   network access. Existing `pilot.py` and results remain untouched. Request socket
   timeout stays 25 seconds; worker deadline 75 seconds plus bounded cleanup.
2. Validate existing metadata hashes and construct the complete six-file plan from
   its official CADC datalinks. Each pair is full QL science and RMS, not SE data or
   multiple mosaics of one observation.
3. Require positive integer advertised sizes and reject the entire plan before
   new pixels if prior retained bytes plus all planned files exceed 500,000,000.
   No retries or fallback archives are automatically authorized.

Advertised bytes (science, RMS): QL2.1 55,431,360 + 55,431,360;
QL3.1 55,480,320 + 55,483,200; QL4.1 55,483,200 + 55,483,200.
Planned new bytes: 332,792,640. Prior retained bytes: 50,235,583.
Planned combined bytes: **383,028,223**, below the 500 MB ceiling. Refuse size
mismatches or altered target/campaign/product paths. Hash every retained download.

## Unchanged scientific criteria

Incorporate the identity, finite coverage, fixed-target photometry, reference
selection, >=5 common-reference, fixed-null and interpretation rules of
PROTOCOL.md unchanged. Use the existing immutable `pilot.py` functions
`load_epoch`, `ensemble_positions` and `photometry`; source SHA-256
`953a26cae7845e44811336c6a8553e949aa49dffcc2e69d739f041fd0ff41978`.
Reference selection remains QL3.1 only: up to 12 brightest qualifying isolated
peaks, S/N>=15, brightness<0.1 Jy/beam, target/edge separation>=45 arcsec,
pairwise separation>=20 arcsec, reference residual/noise<=3. Positions are fixed
before comparing epochs. Do not lower thresholds, relocate nulls or prune
comparisons according to flux-ratio behaviour.

At least five selected reference candidates must have positive amplitude/noise>=5
in all three epochs before a provisional median local scale and MAD scatter can
be reported. Report every selected source's measurements, exclusions, target
recovery and null responses. Record dates and beams. A reference candidate is not
a certified nonvariable calibrator.

Success label is **CALIBRATION_FEASIBILITY**, not discovery-ready; failure is
STOP_CALIBRATION or the exact earlier identity/acquisition gate. If the fixed full
plane is still insufficient, stop; do not expand again. This phase does not
validate common-beam convolution, morphology rejection, absolute flux calibration,
false-positive rates, the historical fading rate or physical classification.

Primary methodological and archive sources are linked in PROTOCOL.md; their
calibration caveats still apply. No publishing, submissions, accounts or messages.
