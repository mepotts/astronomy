# RXJ M5: three named event products, header-only authentication

Prospective, unexecuted. Adopt the complete
[M4 next decision](XMM-RXJ-M4-NEXT-2026-09-13.md), SHA256
4a2a3af7f8837f036605b7e1956dcb8019119fa732f31a31c4e2fda95a1033f4.
Prior STOPs and M4 metadata incompleteness remain unchanged. No HTML repair,
old worker/replay, additional metadata request or photon interpretation.

## Exact three GET slots, fail-stop order

1. PN: `https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0851180501&level=PPS&instname=PN&expflag=S&expno=001&name=PIEVLI&datasubsetno=0&sourceno=000&extension=FTZ`
2. M1: `https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0851180501&level=PPS&instname=M1&expflag=S&expno=002&name=MIEVLI&datasubsetno=0&sourceno=000&extension=FTZ`
3. M2: `https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0851180501&level=PPS&instname=M2&expflag=S&expno=003&name=MIEVLI&datasubsetno=0&sourceno=000&extension=FTZ`

Each exclusive slot marker precedes its single attempt. At the first failure,
later slots are NOT_ATTEMPTED. No preliminary HEAD, redirects, retry, Range,
asynchronous work, broadened filters or bundle fallback. Fresh anonymous requests
Session per slot, trust_env=False/auth=None, cleared cookies, identity encoding,
5/15-second socket timeouts. HTTP200/exact URL required. Save actual URL match as
a boolean, not an arbitrary response URL. No invented length/ETag validators.

Accept MIME image/fits, application/fits, application/x-fits,
application/octet-stream, application/gzip or application/x-gzip. Content-Encoding
must be absent/identity. Disposition must be one≤2,048-character ASCII inline or
attachment filename parameter (quoted/unquoted), exactly the corresponding
observed P0851180501PNS001PIEVLI0000.FTZ, P0851180501M1S002MIEVLI0000.FTZ or
P0851180501M2S003MIEVLI0000.FTZ. Reject missing/extended/duplicate/ambiguous fields.
Only parse status and expected filename hash are retained; never raw disposition.
Six safe HTTP fields, one ASCII value each≤2,048 characters; no controls, cookies
or duplicate framing. HTTP parser≤65,536 bytes/line and100 headers. Optional
Content-Length must be positive decimal≤256MiB, fit remaining batch allowance
before body access and equal complete bytes. Missing length uses frozen local cap.

## Prospective resource boundaries

Raw≤256MiB per file/512MiB batch; expanded≤1GiB per file/2GiB batch. Read at most
the remaining allowance plus one overflow-detection byte, retain only allowance.
Maximum chunk1MiB. Exactly one300-second tree-enforced worker for all three slots;
deadline includes transfers, expansion, header work and worker reporting. Parent
header/hash verification receives a separate300-second cooperative deadline; an
explicit root replay may perform one further such local pass. No repeat
decompression in parent/replay. Cleanup allowance is not another request.

Fresh free space≥4GiB before launching worker and before its first request; this
exceeds the2.5GiB product maximum with receipts and working margin. Peak memory
acceptance cap500,000,000 bytes, sampled with reviewed real Windows lifetime-peak
helper; this is not an OS allocation quota. JSON≤10MiB including private header
reports and public identity derivatives. Each private header report and public
identity derivative≤2MiB. Reserve256KiB for failure/worker/outcome receipts; normal
successful slot/identity receipts cannot consume it. Failed slot receipt≤64KiB.

Dispatch only by actual raw magic: gzip with complete EOF/CRC checks or raw FITS
SIMPLE signature. No TAR/ZIP extraction or gzip/format retry. Stream expansion
into fixed predetermined paths; CRC/size/magic failures preserve partials. For
raw FITS, verify raw/copied-expanded hashes equal. Separate progress counters
record returned/retained bytes, unknown read/write invocation, EOF and gzip CRC
completion. Count returned bytes before writes; failed writes may leave unknown
retention, independently exposed by actual partial-file byte counts. Known hard
kill work is not guessed; marker-only slots are explicitly unverified/interrupted.

## Structural headers, identity and privacy

Use the pinned structural reader only:≤128HDUs/64header blocks per HDU,
syntax/layout-validated header parsing and seeking over declared spans. It establishes
HEADER_LAYOUT_ONLY, not FITS checksum or scientific-payload validity. No EVENTS,
GTI, BADPIX, EXPOSU, CALINDEX or image values are decoded. On malformed headers,
unknown bytes can be read while seeking the header boundary; therefore do not
claim unconditional zero physical payload bytes. Capture warnings always and
STOP without printing warning text.

Full header reports stay in ignored headers/; raw/expanded products stay in
ignored products/. Public derivatives use the new validated pure identity helper,
not old permissive header_summary. Require exactly one EVENTS and at least one
explicit OBS_ID/INSTRUME/EXPIDSTR match across primary and EVENTS for
0851180501 plus EPN/S001, EMOS1/S002 or EMOS2/S003. Missing placement is reported,
not silently inherited. Any conflicting/unrecognized or within-HDU duplicated
identity fails. Optional EXP_ID corroborates but cannot substitute for the flag.
Record all returned safe metadata/schema fields and identity missingness. Compare
SUBMODE/DATAMODE/FILTER against M4 OB PrimeFullWindow/Imaging/Thin1 without gating
identity or replacing returned values; conflicts, duplicates and unknowns remain.

Strongest success: RXJ_EVENT_PRODUCTS_RETAINED_HEADERS_ONLY. This does not prove
aperture coverage, acceptance, calibration constituents, event counts, source
recovery, clean negatives or discovery. Preserve pn-plus-MOS and fixed-negative
requirements. CALINDEX schema inventory is not permission to read its rows.

## Audited composition and validation

Fresh hash-pinned C1 module supplies only peak/checkpoint/hash/save and verified
deadline-loader primitives. No C1 plan, binding, worker, download or historical
replay is called, and no C3d inheritance chain is loaded. Own three-slot harness,
transport, expansion, safe result schema and ordered artifact closure. Bind
C1/tests, structure/tests, identity/tests, deadline helper, M4 safe evidence and
decision, current source/tests/protocol/privacy/runtime. No private prior input
opens during binding. Source and fixtures remain synthetic-only until root freeze.

Parent verifies retained raw/expanded/header hashes, exact layout and safe identity
against a fresh header-only pass; no decompression or requests. Successful and
failed parent assessments preserve three compact per-slot started/completed flags
for this additional header/identity pass. Started is set immediately before header
inspection; completed means layout and available retained identity comparison
returned successfully, not overall acquisition success. Caught replay failure
reports its own additional pass flags without rewriting the original outcome;
these flags do not measure header bytes or claim hard-killed work is known.
Successful and
failed receipts cannot promote absent worker completion, wrong status, reordered
requests, extra/missing artifacts or exceeded caps. Late peak overflow downgrades
to STOP while retaining terminal evidence. Artifact-only replay of an interrupted
or unassessed worker is explicitly not completed product/header verification.
Tests must cover raw/gzip success, identities, partial/overflow/CRC errors,
aggregate budgets, first-failure gating, safe receipt tampering and one-shot
read-only replay. Freeze exact bytes before any archive request.
