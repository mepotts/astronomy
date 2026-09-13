# XMM C3 independent post-run review

September 13, 2026 UTC: **the original C3 STOP is verified and preserved.**
The third HEAD returned 404; the four-HEAD gate prevented all GETs. The reviewer
made no network request, interpreted no arrays and changed no C3 artifact.

## Independent receipt audit

All 13 outcome artifact hashes, 12 worker artifact hashes and seven dependency
hashes match. Source/test identities and the protocol snapshot match the run
binding. Frozen read-only replay returned `PASS_OFFLINE_REPLAY STOP`. All 17
files present in the stage at audit start remained byte-identical afterward.

Exactly three HEAD request markers are retained in order, at approximately
0.172, 0.531 and 0.875 worker seconds. The eight-slot ledger is two OK, one
FAILED, then five NOT_ATTEMPTED. Parent assessment completed; worker return code
1 and `STOP_HTTP_IDENTITY_OR_STATUS` are preserved.

| Slot | Product role | HTTP result | Interpretation |
| --- | --- | --- | --- |
| 1 | pn S003 band-8 map | 200; Content-Length 503855 | Accepted advertised compressed length; zero body reads |
| 2 | MOS1 S001 band-8 map | 200; Content-Length 275217 | Accepted advertised compressed length; zero body reads |
| 3 | MOS2 S002 band-8 map | 404; Content-Length 19 | Failed HEAD; 19 is the error entity's advertised length, not a product size |
| 4 | Attitude HEAD | Not attempted | Availability/size still unmeasured by C3 |
| 5–8 | All four GETs | Not attempted | No product acquisition |

The MOS2 receipt date is 2026-09-13 00:38:53 GMT. Its exact requested URL was the
one present in the retained inventory. This demonstrates a listing/availability
mismatch at that attempt, not permanent absence or its cause. It does not
authorize a retry, alternative band or substituted filename.

Both compressed and expanded product totals are zero; no products/ or headers/
directory exists in the stage. All HEAD body branches remain unread under the
frozen implementation. Final JSON totals 11032 bytes, with worker/parent resource
snapshots reconciling after their later receipts. Recorded worker/parent peaks
are 50540544/48324608 bytes, within the 500000000-byte acceptance limit. These
resource facts do not turn the failed acquisition into success.

Outcome SHA-256:
`62dedbf1b55a48210f447e454f0f1f574b7b8b073a873f48bce2c587cdf7fa5e`.

## Scientific assessment of a possible separate subset stage

A prospectively frozen **pn plus MOS1 plus attitude** continuation can be
consistent with the original [counts-recovery draft](XMM-CONTROL-RECOVERY-DRAFT-2026-09-12.md),
which requires pn and at least one MOS with usable simultaneous coverage. The
draft's positive-camera criterion likewise asks for confirmation in at least
one eligible MOS. The subsequent four-product acquisition proposal was broader
than that minimum. No photon outcome has been used here to select the more
favorable camera; the reason for a subset would be observed archive availability.

This is a conditional scientific recommendation, not approval to change C3:

- Preserve C3's failed four-product gate, the MOS2 404 and MOS2's unavailable
  geometry status. Do not describe MOS2 as a negative result or clean coverage.
- Define any new request/size/identity/resource contract before requests. The
  successful pn/MOS1 HEAD facts do not imply current entity identity, and the
  attitude product has not yet passed even its HEAD check.
- Keep the fixed source/background apertures, negative-control positions,
  required usable negatives, screening, timing, overlap and exposure/geometry
  criteria. MOS1 must independently satisfy them; do not substitute its camera
  label for evidence of adequate source and background coverage.
- Freeze camera inclusion and the planned statistical test family before photon
  analysis. Retain unavailable planned cells where the counts contract requires
  them; never shrink a denominator or choose the confirming camera after seeing
  a light curve. Do not weaken the burst/negative/background rules to obtain
  recovery.

Even a technically successful two-map/attitude subset would remain a headers-only
input stage. It cannot establish pointing stability, per-bin exposure, aperture
coverage, published-control recovery or discovery without the separately defined
geometry and counts work. No new stage was implemented or executed by this audit.
