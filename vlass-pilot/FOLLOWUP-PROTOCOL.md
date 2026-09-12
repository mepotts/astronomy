# Independent-epoch feasibility follow-up, 2026-09-12

Frozen before any science pixels, following the preserved metadata-only failure
in INITIAL-RESULT.md. The original PROTOCOL.md and acquisition.json are immutable.

This follow-up incorporates every measurement, selection, identity, noise,
comparison/null, interpretation and promotion rule in PROTOCOL.md, with exactly
these acquisition changes:

1. Use QL2.1, QL3.1 and QL4.1 only, exactly one science/RMS pair per campaign.
   QL1.1 is excluded prospectively because CADC advertises v1 provenance rather
   than the required corrected v2. No measured flux informed that exclusion.
2. At most six FITS files; <=250,000,000 combined stored bytes across initial and
   follow-up acquisitions, retaining the same socket/worker timeouts and target
   cutout radius. Follow-up raw products have their own directory and manifest.
3. Comparison reference remains QL3.1. At least five common comparison sources
   must meet the original criteria in all three retained independent epochs.

Scope remains VT 1137-0337 and its same-field comparison/null positions only.
The strongest possible result remains MEASUREMENT_FEASIBILITY. No claim about
historical turn-on, secular fading, new physical class, or new discovery is allowed.
Any fatal identity, recovery or calibration failure is reported before another
changed experiment. No automatic expansion to another field or unknown targets.
