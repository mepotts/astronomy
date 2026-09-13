# XMM C3b stopped at the attitude HEAD; no geometry products retained

**STOP_HTTP_IDENTITY_OR_STATUS: HTTP 404 on the sole new attitude HEAD.**
The [C3b contract](XMM-C3b-2026-09-12.md), implementation, 11 tests and
[independent review](XMM-C3b-REVIEW.md) were frozen in commit `118b1dc`
before execution. The prior C3 STOP and two successful size receipts were
validated unchanged. No new pn/MOS1 HEAD or MOS2 retry was made.

At 2026-09-13 00:53:35 GMT the exact listed
`P0884250101OBX000ATTTSR0000.FTZ` URL returned HTTP 404. The 19-byte
Content-Length belongs to an unread error entity, not an attitude product.
The filename/URL occurs once in the earlier inventory, displayed as 148K,
and exactly matches the request. The underlying serving/listing discrepancy
and its persistence remain unknown.

New slot 1 is FAILED; conditional GET slots 2–4 are NOT_ATTEMPTED. Zero
product-body, compressed or expanded bytes were retained. There are no new
map/attitude headers or arrays to interpret. Parent assessment completed;
worker exit was 1 and a separate replay returned `PASS_OFFLINE_REPLAY STOP`.
Worker/parent peak working sets were 50999296/50266112 bytes, within the
monitored 500000000-byte ceiling. Final aggregate JSON is 9854 bytes, below
10 MiB. [Independent postrun audit](XMM-C3b-POSTRUN-REVIEW.md).

## Next decision, not another relaxed gate

Preserve both [C3](XMM-C3-RESULT-2026-09-12.md) and C3b failures. The available
pn/MOS1 HEAD facts do not establish usable pointing information or permit the
proposed temporal coverage claim. Do not drop the pointing requirement, treat
sampled mean pointing as a movement bound, or silently retry these URLs with
a different method to obtain a passing acquisition label.

The safe next transport investigation is a bounded check of documented official
alternate individual-PPS retrieval, with no science-product request until an
exact route and a new finite contract are justified. A documented alternate
source would be new provenance, not a repair of these outcomes. Avoid bulk
ODF reprocessing or another field merely to get a successful download.
Subsequent [bounded source research](XMM-ALTERNATE-PPS-SOURCE-2026-09-12.md)
identifies documented ESA XSA AIO selectors and intended HEAD support. This
is not a tested product endpoint or an executed acquisition: a new one-request
metadata contract and, if eligible, a separate package contract are still needed.
Photon-blind frame-boundary methods remain independent useful preparation;
they cannot substitute for spatial/pointing evidence. The XMM control is not
recovered, no unknown-source scan has run, and no discovery is established.

## Identity

| Artifact | SHA-256 |
| --- | --- |
| Source | `bc8f6ab039234e98347329412e706547c0c91e543ebffbfe9d8a4d1f5a4b7b92` |
| Tests | `e3295401c6801193a11a2d046acecfc80ceabb9348a685984203e970f7cefaff` |
| Protocol snapshot | `7025a0af3a2714528b8a4360487760972e5977c48eb232a236c8ec239a2ff18a` |
| Run start | `6ff56f5955923606f8c700d9ca8c4635b955d1ec5fc0e89579758a47b338d636` |
| Worker result | `9ef548581fd0dc3ce7c8194800ba86df635bb1e1a2d6299aa0a9a734ce96aafb` |
| Outcome | `b785146094702538ff8c2ef2300ba243133f44309bf0f1f63c7af0aa90fe7229` |

The broader discovery goal remains active. Repository updates are authorized
after verification; scientific publication/submission remain gated.
