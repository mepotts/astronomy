# C3e retained pn and MOS1 maps; pixel compatibility remains unvalidated

**PN_MOS1_GEOMETRY_PRODUCTS_RETAINED_HEADERS_ONLY.** The
[two-product contract](XMM-C3e-2026-09-12.md), source, 14 tests and
[independent review](XMM-C3e-REVIEW.md) were frozen in commit `c516560`
before execution. Both exact HEASARC GETs returned HTTP 200 at
2026-09-13 01:47:43/44 GMT, matching the preserved C3 HEAD lengths,
ETags and Last-Modified values. No refreshed HEAD, MOS2 retry or attitude
request occurred. C3's MOS2 HTTP-404 STOP remains unchanged.

The pn product is 503855 compressed / 1728000 expanded bytes; MOS1 is
275217 / 1704960. Totals are **779072 compressed / 3432960 expanded bytes**.
Both gzip streams passed worker CRC/EOF verification and independent parent
hash/header replay. Worker exit 0, assessment completed, two OK slots.
Worker/parent recorded peaks are 65155072/60874752 bytes. Final JSON including
the ignored full header reports is 88956 bytes. Offline replay passed the same
header-only status; it did not decode map pixels or re-decompress the products.
Raw products and coordinate-bearing full headers remain ignored.
[Independent postrun review](XMM-C3e-POSTRUN-REVIEW.md) verifies exact file,
receipt, dependency and resource closure, including the preserved C3 STOP.

## What the headers establish

Both primary images are 648 by 648 float32, with celestial WCS keywords present.
The pn header identifies EPN/S003, PrimeFullWindow/Thin1, creator
`imweightadd (tools-1.68.1)`, exposure 33730.1879012585 seconds, OOTCORR true.
The MOS1 header identifies EMOS1/S001, PrimePartialW3/Thin1, creator
`eexpmap (eexpmap-4.12.1)`, exposure 40974.4891108274 seconds.
Both belong to the fixed public control observation 0884250101.

The pn weighted-product provenance and MOS1 data-subspace selections require
explicit compatibility adjudication against the planned energy, FLAG and
good-time filters. Delivery success and a WCS do not establish effective
exposure, pixel validity, detector-edge clearance or time-dependent coverage.
No BUNIT or energy-bound value was established by the safe header summary.
No actual pixels, photon events or source-list values were read in this stage.

## Identity

| Artifact | SHA-256 |
| --- | --- |
| Source | `ad80cb38306388f69e51bce78fe4787279e7ba5402b4b6f7b10b44362b54aa4e` |
| Tests | `d913c42299305bdb62fba2d0f3e8147e0568cf778f541649fab5adb1de51e825` |
| Protocol snapshot | `ca3fa37ad01c1542423f7ba3b8ebd1b81cd6a9375eb081728062e2cad45dfc44` |
| pn expanded FITS | `5a39eee5d2b438fb893e65ff6a9bc2a70896987b7b9f15ba990e24a87a4172dd` |
| MOS1 expanded FITS | `652846bddc9724aacd4a08fda52fc2065820615104536b3545aeb8712b63cb38` |
| Outcome | `af82c5ae3b7a5cd233589e6bd53eadc8d0ded37137ad6df6dac49d198a581d80` |

The outcome retains each request, marker, result, raw product and full-header
hash. This is acquisition evidence, not a discovery. Preserve missing MOS2 and
the original three-camera/region/time testing denominator in later stages.
