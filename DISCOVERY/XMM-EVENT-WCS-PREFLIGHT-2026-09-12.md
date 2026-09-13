# Event-coordinate metadata preflight, no photons read

Root inspected only the three retained C1 EVENTS header reports. All three
declare the same X/Y table-WCS mapping, despite different TUNIT spellings:

| Property | pn | MOS1 | MOS2 |
| --- | --- | --- | --- |
| X/Y column indices | 6/7 | 6/7 | 6/7 |
| TCTYP6/7 | RA---TAN/DEC--TAN | same | same |
| TCUNI6/7 | deg/deg | same | same |
| TCDLT6/7 | -/+1.38888888888889e-05deg | same | same |
| TCRPX6/7 | 25921/25921 | same | same |
| RADECSYS / EQUINOX | FK5 / 2000 | same | same |
| TUNIT6/7 | 0.05arcsec | pixel | pixel |
| Reference sky value equals retained MOS2 map | both axes true | true | true |

No absolute sky reference values are reproduced. All reference comparisons
were direct header-value equalities, not a fit or a numerical event transform.
The table WCS scale is0.05arcsec per coordinate unit; do not substitute the
4arcsec map-pixel scale or infer MOS scale from the generic word pixel.
RAW columns4/5 have separate coordinate metadata; never apply their WCS to X/Y.

This supports a concrete next implementation: construct a minimal primary TAN
WCS from these verified table-axis fields, preserving FITS coordinate origin
semantics and the same fixed FK5/J2000 centre convention, then test with
independent synthetic transforms before any photons. It is not an implemented
or validated projection, nor a RAW detector transform. Explicit null handling
for X/Y=-99999999 must precede transformation. Unsupported table matrices,
distortions, scaling and ambiguous cards require rejection, not silent fixes.

Exact C1 header hashes and row/field contracts remain in the
[decoder preparation](XMM-EVENT-DECODER-NEXT-2026-09-12.md). No event data,
source coordinates, recentering, count bins, rates or significance were produced
by this preflight. Source-list exclusions and detector/exposure calibration
remain separate unresolved requirements.
