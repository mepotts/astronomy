# XMM C1: acquire one published-control bundle, inspect headers only

Prospective acquisition/structural stage, September 12. Parent decision under
the continuing authorized public-data discovery work. No unknown observation,
scientific publication, registry submission, correspondence or account changes.
Implementation, tests and independent review must be frozen before execution.

## Evidence and scope

C0d's four size-only requests succeeded; its summary validator stopped because
the fully retained 50010-byte HTML page omits the outer HTML end tag. Preserve
that STOP unchanged. The independent post-run audit supports separately labelled
offline interpretation, not rerunning C0d. Its successful HEAD receipts remain
usable advertised-size evidence. The following C1 operation does not require
turning the failed overall C0d status into a pass.

Bind C0d outcome SHA-256
`7895f2fd39ce85ab745fbff40a291abbf7376086e9f58a2245352b2c348453a3`
and verify every artifact it lists before selecting the four successful HEAD
slots. Require exact method, URL, positive length and consistent slot receipts.
The C0c2 inventory remains the observed origin of each URL. Do not construct a
replacement archive URL, add another exposure or refresh the directory.

| Fixed file | Expected compressed bytes |
| --- | ---: |
| `P0884250101PNS003PIEVLI0000.FTZ` | 109245605 |
| `P0884250101M1S001MIEVLI0000.FTZ` | 7643540 |
| `P0884250101M2S002MIEVLI0000.FTZ` | 9972723 |
| `P0884250101EPX000OBSMLI0000.FTZ` | 120581 |

Exactly four sequential anonymous GET slots, once each, in this order. These are
the first intentional scientific-product body downloads in the XMM route. They
are **known published-control data**, not unknown-source searches. No extra HEAD,
Range GET, retry, redirect, linked resource, remote processing or ODF bundle.
Fresh isolated session per file, environment/netrc/proxy use disabled, no auth
or cookies, identity transfer encoding, socket timeouts 5/15 seconds. Retain only
the same six safe header names as C0d; never authentication or Set-Cookie.

Require exact final URL, GET method, HTTP 200, an unambiguous Content-Length equal
to the successful HEAD value, and absent/identity Content-Encoding before body
reading. If HEAD supplied ETag or Last-Modified, require matching GET values;
otherwise STOP_CHANGED_PRODUCT. Do not require an undocumented FITS MIME subtype.
Stream raw transfer bytes without automatic HTTP decompression, at most the
expected entity length plus one overflow-detection byte; retain no excess byte.
Hash the actual retained compressed body and verify final length. Preserve any
partial file and failure. Stop remaining slots after the first failure.

## Resource contract

- Aggregate expected compressed bodies: **126982449 bytes**. Each per-file
  expected length is also its retained-body cap. No silent budget increase.
- Per-file expanded limit: **1073741824 bytes (1 GiB)**; aggregate expanded
  limit: **2147483648 bytes (2 GiB)**. These are chosen ceilings, not predictions
  derived from compressed sizes. Stream gzip decompression with bounded chunks,
  explicit overflow detection, completed stream/CRC verification and separate
  exclusive expanded files. Do not trust gzip's modulo uncompressed-size footer.
  No tar/zip extraction. Preserve both compressed and expanded hashes/lengths.
- One **300-second total worker deadline** for acquisition, decompression and
  header inspection using the existing pinned process-tree helper SHA-256
  `11ad0bef9fd2efae234e204358c6b6730e723ed3dc24c6fe0c345f2ddcfb53dd`.
  The helper's cleanup allowance is separate; it grants no further requests.
- Peak working-set acceptance ceiling **1000000000 bytes**. Use the existing
  Windows GetProcessMemoryInfo measurement pattern at startup, chunk/checkpoint
  boundaries and completion. Report the measured peak. This is monitored
  acceptance with STOP, not a claimed operating-system hard allocation limit.
  No psutil/SAS/package installation; psutil is absent from the current runtime.
- At least **3 GiB free space** before starting. At most **2 MiB of header JSON
  per file** and **10 MiB aggregate JSON receipts/reports**, excluding immutable
  source/tests/protocol. All output destinations are under the new C1 folder.

## Structural-only interpretation

Use reviewed `DISCOVERY/xmm_structure.py`, SHA-256
`96d9497dbdd45d2561fc0bbb27a0c11d6fbad91cd42c0b14191378dd9fd7fa63`,
on the expanded files. Its input-size, header-block and HDU caps remain unchanged.
Freeze the reader and test identities with the acquisition source. It reads
headers and skips data spans declared by accepted headers. Malformed header
scanning may consume unknown bytes within its cap before STOP; no array is
interpreted. Transport hashing and gzip verification necessarily traverse the
data bytes but do not constitute source-count analysis.

Retain HDU/header cards, extension names, row/column layout and byte spans. Do
not read EVENTS arrays, source-list rows, numeric GTI/exposure/bad-pixel tables,
images, light curves, PI distributions or aperture counts. Do not infer valid
GTIs, astrometry, source location, exposure correction or useful sensitivity
from header presence. Full FITS conformance/checksum and payload-semantic checks
are not claimed by the reader. Actual identity/mode/time/WCS/schema adjudication
is a separate offline report of this structural output.

## Receipts and outcome

Exclusive parent/worker and per-slot markers bind the exact plan, source,
protocol snapshot, dependencies and runtime. No resumption under the same
attempt. Every slot must be listed as successful, failed, interrupted or not
attempted. Preserve worker exit/timeout, safe error codes, raw product hashes,
header-report hashes, measured memory and immutable partial outputs. Parent
verification must independently check receipt/order closure, HTTP identities,
compressed/expanded file hashes and sizes, header replay and resource outcomes.
No nonzero worker exit or missing report can be accepted as successful.

Strongest label: `CONTROL_BUNDLE_RETAINED_HEADERS_ONLY`. It does not mean control
recovery, calibrated significance, valid exposure, unknown-search readiness or
discovery. A separately frozen counts protocol must resolve the documented
timing/geometry/exposure and background issues before event selection. Raw
products and full header-card reports stay local and ignored by Git (dedicated
products/ and headers/ subdirectories). Their hashes and byte lengths remain in
compact committable receipts. Do not publish RA/Dec, pointing/WCS coordinate
values or observer contacts in those receipts or console output. Commit only
reproducible code, non-coordinate metadata and compact receipts. No scientific
dissemination is authorized. C0d's coordinate-bearing original summary also
remains immutable and local-only; its public offline note is the derivative.
