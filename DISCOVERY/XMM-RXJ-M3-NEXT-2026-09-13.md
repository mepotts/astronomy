# After RXJ M3: adjudicate four retained metadata members offline

**Recommend a separately frozen, offline-only inspection of all four fixed
HTML member slices. No new GET, archive extraction or choice of the smaller
summary.** M3 remains `STOP_TAR_HTML_SIZE`; the first member exceeds its frozen
262144-byte limit. The additional evidence below does not retroactively pass
that limit, the one-file requirement or the zero-tail requirement.

## What was actually inspected

Raw archive:1044480 bytes, SHA256
`fa3c45838875c61f68e07508d862fc56d32e83f0b39ed3f6b1bef2207b9ccbe2`.
The local ignored file is `XMM-RXJ-M3-2026-09-13-data/summary.tar`.

This review first streamed the entire file for opaque SHA256 verification,
then interpreted **four512-byte TAR headers only**, at the offsets below,
using standard-library checksum-validated `TarInfo.frombuf`. It separately
read the8192-byte tail only for zero/nonzero statistics and a hash. No HTML
payload, alignment padding, owner field, coordinate or source value was
interpreted. No raw name/path was printed or written into this note.

| Ordinal | Instrument/data-source field | Header offset | Payload offset | Declared bytes | Next padded boundary |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | EP | 0 | 512 | 872917 | 873472 |
| 2 | OB | 873472 | 873984 | 48229 | 922624 |
| 3 | RG | 922624 | 923136 | 25265 | 948736 |
| 4 | OM | 948736 | 949248 | 86689 | 1036288 |

All four have regular-file type0, requested-observation identity, exposure
flagX/number000, productSUMMAR, subset0/source000 and extensionHTM. Their
basenames and normalized full names are pairwise distinct. Each relative
prefix has the same two categories: requested observation, then PPS directory.
No absolute path, backslash, colon or parent-traversal component was found.
There are no intervening member headers between the listed padded boundaries.

The four header SHA256 values, ordinal order, are:

```text
1515d452115254c73b8f402efec58b8d08cf8530b7b11e7a85172741ee194321
7e570189d8e9ad67d78a0e67bb5c4129e448b51120de24c8149b826e9c666f64
bb622ea07a7cbeb122f8ad7546f5086e9734521cc066e48d23822d3faac050c9
2c47e616fa9eb43ae3cf0cb712cebe0fb4ec23d0006b93d2cae4cf0295f4b607
```

## Four roles, not four demonstrated processing versions

The official Data Files Handbook Table37 defines EP as EPIC, OB as
observation, RG as combined RGS and OM as Optical Monitor. It lists SUMMAR
for EPIC, OM, PPS-observation and RGS summaries. X means exposure not
applicable;000 does not identify an exposure period. Table38 separately
lists observation and instrument-group summary pages.
[ESA PPS definitions, section8, Tables37–38](https://xmm-tools.cosmos.esa.int/external/xmm_user_support/documentation/dfhb/pps.html).

Therefore the observed names are consistent with **four distinct documented
summary roles**. They are not duplicate normalized paths or four copies of an
identical basename. Filenames alone do not prove processing versions, content,
mutual consistency or absence of duplicated sections inside pages. None of
those payload questions has been answered. C0d's approximately50KB OB summary
is not evidence that RXJ's48KB member is the only valid document or should be
selected without accounting for the others.

## Tail: exact issue and bounded interpretation

At offset1036288 there are two consecutive all-zero512-byte blocks. The
remaining7168 bytes comprise fourteen512-byte blocks, each with512 nonzero
bytes. The whole8192-byte tail hash is

`e3c5d4864109c463b69f6f7b124995ae36b2082f40e972339da26f0e9200a0ea`.

This violates M3's requirement that everything after the terminator be zero.
An explicitly authorized follow-up counted byte values in the7168-byte suffix
at offset1037312, without decoding text. Its SHA256 is

`c304f59f74ff1408146b797c68f001e4284f7bb014ae2267d98e60f44de040f9`.

The exact histogram is integer byte value to occurrence count:

```json
{"10":89,"32":310,"34":375,"35":10,"38":55,"40":10,"41":10,
 "45":24,"46":40,"47":193,"48":257,"49":189,"50":15,"51":27,
 "52":18,"53":73,"54":38,"55":13,"56":60,"58":24,"59":69,
 "60":386,"61":188,"62":385,"65":15,"67":15,"68":18,"69":65,
 "70":25,"72":15,"73":50,"77":120,"79":85,"80":45,"82":55,
 "83":114,"84":50,"85":20,"87":10,"88":11,"90":10,"91":10,
 "93":10,"95":10,"97":288,"98":80,"99":196,"100":155,"101":289,
 "102":30,"103":148,"104":153,"105":198,"108":257,"109":45,
 "110":242,"111":50,"112":70,"114":231,"115":461,"116":551,
 "117":25,"118":20,"119":10,"120":34,"121":24}
```

Thus the trailing bytes are **heterogeneous**, not uniform nonzero padding.
The review did **not** decode those bytes or establish their origin.
Do not claim harmless exporter padding, another archive, stale memory or
corruption from these statistics. Two logical terminator blocks and four
fully bounded earlier payloads support inspecting those fixed slices without
trusting the suffix. They do not prove the entire physical archive is clean.

The new stage should explicitly quarantine everything after the first two
zero blocks: retain it only as part of the immutable raw archive, bind the
tail hash/statistics and never interpret it as another header, payload,
executable or correction. Name this a **fixed-member metadata adjudication
with an uninterpreted nonzero trailer**, not a repaired M3 archive pass.
It is an observation-specific offline decision, not a generic change allowing
arbitrary nonzero tails in future network downloads.

## Smallest prospective offline contract

1. Bind the exact archive size/hash, M3 outcome/HTTP/transport receipts,
   source/protocol and this note. Reverify the four header hashes, fields,
   checksums, normalized-name distinctness, exact offsets/sizes and terminator/
   tail record before any payload. Fail on any mismatch; never discover a new
   member set dynamically or invoke an old network worker.
2. Read **all four** payload ranges above, one at a time, with no decompression,
   link following, browser/rendering, filesystem extraction or archive-named
   outputs. Selected payload bytes per complete pass are exactly1033100;
   the largest single payload is872917. Every skipped/failed member remains
   in the four-slot ledger. Permit fixed private ordinal copies only if the
   reviewed implementation needs them; otherwise parse bounded memory slices.
3. Decode HTML using declared encoding evidence where present; record missing
   or conflicting encoding rather than silently repair text. Use a parser that
   does not load external resources. Do not require literal closing HTML tags,
   an exact title, a fixed table count or an assumed exposure roster. Preserve
   parse/identity/missingness results separately for each of the four roles.
4. Inspect only explicit observation, instrument/exposure, mode/filter/timing,
   processing and relevant product-reference metadata. Retain all exposure
   rows, duplicate/conflicting IDs and missing units. A large EPIC page may
   contain source-level science; do not interpret fluxes, variability, photon
   curves, coordinates or catalogue rankings. No linked resource is fetched.
   The OM/RG pages remain accounted for even if they add no EPIC information.
5. Compare labelled observation identity across all four and compare overlapping
   exposure/processing metadata where actually supplied. Different role content
   need not contain identical fields. Report inconsistencies without choosing
   the most convenient version. Explicit observed product references may ground
   a later proposal, but filenames do not prove live access or bytes.

Suggested finite runtime envelope:30seconds per local worker/verification pass,
<=256MiB monitored memory,<=1MiB public JSON with64KiB terminal reserve, and
the exact1033100 selected-byte limit per pass. Opaque archive hashing and
header/tail checks are additional separately counted I/O. Freeze actual code,
synthetic parsing/privacy/partial-accounting tests and caps before execution.
Parent verification is one explicit additional local pass, never a request;
do not silently accumulate numerical/semantic replays.

Private raw archive and any HTML copies stay ignored and immutable. Public
receipts contain ordinal/role, name/header/content hashes, byte accounting and
allowlisted non-coordinate metadata, not paths, owner/contact fields, raw HTML
or arbitrary parser errors. Do not overwrite existing M3 files. This proposal
authorizes no implementation or payload read by itself.

## Decision boundary

The strongest useful outcome is four accounted metadata documents with explicit
verified/missing identity, exposure and product-reference fields. No document
is assumed complete because its filename matches. If their content establishes
the needed RXJ exposure IDs and modes, parent can freeze a narrow subsequent
acquisition contract. If it does not, report the specific missing information
without refreshing the archive or downloading the broad observation package.

No live exposure, region support, clean negatives, source recovery or discovery
is inferred. M3's recorded first-size STOP and all earlier outcomes remain
unchanged. Research used one official PPS documentation page and the precisely
bounded local header/tail inspection above; no HTML semantics or requests.
Including the authorized histogram follow-up, local I/O was two opaque full-
archive hash passes (2088960 bytes), four header reads (2048 bytes), and two
tail reads (16384 bytes). Selected HTML payload semantics remained zero.

Parent disposition: root read this complete note, independently checked the
official PPS role definitions, and verified the four header roles/hashes plus
the exact logical terminator and quarantined suffix hash. Adopt the offline-only
fixed-member adjudication direction. Its actual parser, metadata allowlist,
resource/privacy tests and independent review must precede payload semantics.
M3 stays STOP; no new request or generic archive-policy change follows.
