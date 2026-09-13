# C3e independent post-run review

September 12, 2026 local / September 13 UTC. **Actual execution conforms to
the frozen two-GET acquisition/header-only contract.** The independent frozen
replay returned `PASS_OFFLINE_REPLAY PN_MOS1_GEOMETRY_PRODUCTS_RETAINED_HEADERS_ONLY`.
No new HTTP, decompression or map/attitude/photon/source-array interpretation
was performed. Replay hashed products and repeated header/seek validation only.

## Requests and retained files

Exactly the two planned GETs completed in order, both HTTP 200. Their safe
receipts retain the exact original HEAD URLs, lengths, ETags and Last-Modified
values. HTTP Date is September 13 01:47:43 / 01:47:44 GMT; request-start elapsed
times are 0.203 / 1.156 seconds, ordered and within the 60-second worker bound.
No refreshed HEAD, MOS2 or attitude request is present. Worker returned 0;
worker/parent ledgers both contain two OK slots and parent assessment completed.

The exact file set is two raw, two expanded and two local full-header reports.

| Product | Raw bytes | Expanded bytes | Header-report bytes | HDUs |
| --- | ---: | ---: | ---: | ---: |
| pn S003 EXPMAP8000 | 503855 | 1728000 | 49789 | 1 |
| MOS1 S001 EXPMAP8000 | 275217 | 1704960 | 25845 | 1 |

| Product artifact | SHA-256 |
| --- | --- |
| pn raw | `b51b8c6859c92bc8baa7904d0313932a8e17afa6bba931ce500083ab24966ab9` |
| pn expanded | `5a39eee5d2b438fb893e65ff6a9bc2a70896987b7b9f15ba990e24a87a4172dd` |
| MOS1 raw | `fc451c1f6f4613c2e1af61f576d54723062880c7e306f6fefea29a548857bd39` |
| MOS1 expanded | `652846bddc9724aacd4a08fda52fc2065820615104536b3545aeb8712b63cb38` |

All sizes and hashes were independently recomputed and agree with receipts.
Each worker receipt records gzip CRC/EOF completion; replay checks the bound
receipt rather than independently decompressing again. No full cards or
coordinates were printed by this review.

## Closure, limits and prior preservation

- All **16 outcome artifact hashes**, **15 worker artifact hashes** and **9
  dependency hashes** verify. Exact artifact closure and product/header sets
  pass both direct inspection and frozen replay. Source, tests, protocol,
  inventory/index, runtime/configuration and worker binding are revalidated.
- Original C3's **13 outcome artifact hashes**, **12 worker hashes** and **7
  dependency hashes** verify. Both imported HEAD record/hash pairs match the
  originals; the pinned original outcome remains its MOS2-HEAD404 STOP with
  zero acquired product bytes. It is not retroactively promoted by C3e.
- All **37 files** across C3/C3e data directories have identical hashes before
  and after audit/replay. No executed source, protocol, receipt or product changed.
- Compressed total **779072 bytes** equals the fixed sum exactly. Expanded total
  **3432960 bytes** is below 67108864, and each file is below 33554432.
- Actual JSON totals match both saved snapshots: **84831 bytes** before worker
  result, **86694 bytes** before outcome and **88956 bytes** final, below the
  10485760-byte aggregate budget. Both local reports are below 2097152 bytes.
- Recorded worker/parent memory peaks are **65155072 / 60874752 bytes**, below
  the 500000000-byte acceptance ceiling. The bound configuration retains
  60-second worker plus separate cleanup, 1-MiB chunks, 128-MiB pre-request free
  space checks and 262144-byte terminal reserve. The audit validates records
  and implementation, not historical free space or an OS allocation guarantee.

| Stage provenance | SHA-256 |
| --- | --- |
| C3e source | `ad80cb38306388f69e51bce78fe4787279e7ba5402b4b6f7b10b44362b54aa4e` |
| C3e tests | `d913c42299305bdb62fba2d0f3e8147e0568cf778f541649fab5adb1de51e825` |
| C3e protocol/snapshot | `ca3fa37ad01c1542423f7ba3b8ebd1b81cd6a9375eb081728062e2cad45dfc44` |
| C3e outcome | `af82c5ae3b7a5cd233589e6bd53eadc8d0ded37137ad6df6dac49d198a581d80` |
| Preserved C3 outcome | `62dedbf1b55a48210f447e454f0f1f574b7b8b073a873f48bce2c587cdf7fa5e` |

## Scientific boundary

This confirms retention and structural feasibility of the requested maps, not
their accepted exposure units, calibration, time/WCS compatibility, or source
and background coverage. The next step remains header/schema adjudication,
then a separately specified map-value experiment if supported. No scientific
gate or unavailable-camera/multiplicity rule is relaxed. No burst recovery,
unknown-source result or discovery is established by acquisition success.
