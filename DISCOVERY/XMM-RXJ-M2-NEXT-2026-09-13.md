# After RXJ M2: bounded summary-only TAR, not an observation bundle

**Recommend one separately frozen metadata acquisition accepting the advertised
plain TAR packaging for the unchanged SUMMAR/HTM selector.** No request, archive
read, extraction or implementation accompanies this decision. M2 remains STOP.

## Established evidence

The retained M2 receipt records HTTP200 and `application/x-tar` on
2026-09-13 at05:15:05GMT. Its worker stopped at `STOP_NOT_HTML` before body
reads. No Content-Length was retained. Disposition is classified REJECTED;
the discarded raw value cannot establish its filename or rejection cause.
Do not invent either a size or a filename from that classification.

- [Outcome](XMM-RXJ-M2-2026-09-13-data/outcome.json), SHA256
  `f57b43c9a551a7812afed2be845e1dc88b579251ef36f6e1cceceba3cf20705a`.
- [Safe HTTP receipt](XMM-RXJ-M2-2026-09-13-data/http.json), SHA256
  `ec3da2ce6dcd0de66e30e6b18cbb96e5d14aa5ad902083bf4104da5c7a5254fc`.

The ESA/ESAC-authored client builds the AIO query from `obsno` and selector
keywords, obtains HTTP filename metadata, and includes TAR-product processing.
Its extraction code expects relative directory structure in typical packages,
including a `pps` directory; that is useful compatibility evidence, not a
universal exact path or single-file guarantee. Its fully-trusted extraction
setting is not appropriate to reuse here.
[Official client implementation,0.4.12.dev710+g038841faa](https://astroquery.readthedocs.io/en/latest/_modules/astroquery/esa/xmm_newton/core.html).
Selector provenance is already recorded in
[the M1 next-step note](XMM-RXJ-M1-NEXT-2026-09-13.md).

## One unchanged selector, new explicit representation contract

```text
GET https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0851180501&level=PPS&name=SUMMAR&extension=HTM
```

No HEAD, retry, redirect, wildcard substitution, broader level, new observation,
linked request or guessed product URL. In particular, M1's `*/*` and
`0851180501.tar.gz` rows are not used as retrieval instructions. This is a new
representation-specific stage, not a claim that M2 passed or a relaxation of a
scientific recovery criterion.

Fresh anonymous session, disabled environment authentication/proxies and cookie
reuse, no Range, identity Accept-Encoding. Require HTTP200/exact final URL,
absent/identity Content-Encoding and `application/x-tar` or `application/tar`
media type. Optional Content-Length must be unambiguous positive decimal,
<=1048576 and match the completed raw byte count. No previous ETag/length is
available to require. Keep bounded safe headers only.

An outer Content-Disposition filename is **not an identity prerequisite**:
the selector and validated inner member establish the narrower identity. Do
not write any server-named path. If inspecting disposition, retain only a
bounded parse-status/filename hash, never raw text; missing or unparseable
optional disposition is explicitly non-authoritative. Unsafe HTTP framing,
oversized headers and conflicting Content-Length still stop independently.
This avoids another invented exact package-name gate.

Raw cap **1048576 retained bytes plus one unretained overflow-detection byte**;
inner summary cap **262144 bytes**. No gzip/ZIP autodetection or decompression
fallback: this contract accepts plain TAR bytes, as advertised. Hard30second
worker process-tree deadline with existing audited helper and separate cleanup
allowance;5/15second socket timeouts. The same worker deadline covers transfer
and bounded local validation. JSON<=1MiB with64KiB terminal reserve; raw TAR
and admitted HTML budgets are separate. Freeze implementation/runtime caps and
synthetic tests before executing; no additional acquisition is implied.

## Bounded TAR member contract

Preserve the raw package under a fixed local name and hash it before inspection.
Do not use `extract`, `extractall`, invoke an external archive utility, execute
members, or create archive-specified directories. Read the small admitted
member's byte slice only after the complete package structure is accepted,
then copy it to a fixed ignored `summary.html` destination. This is a bounded
byte copy, not filesystem extraction under member paths.

At most **16 physical non-terminator member headers**, including directory
headers. Admit exactly one regular file (TAR regular type0 or its legacy NUL
equivalent), plus zero or more directory entries of declared size0. Do not
require directories to be explicitly listed, require their order, or require
a `pps`, observation or revolution folder. Reject additional regular files,
duplicate normalized member paths, links, devices, FIFOs, sparse entries and
other special types. No README, checksum or unrelated product exception is
silently added. More than one matching summary is ambiguous, not a choice.

Support ordinary short-name legacy/USTAR headers and the USTAR prefix field;
do not demand that the filename fit entirely into the100-byte name field.
Verify every header checksum, bounded nonnegative size and512-byte layout;
declared payload plus padding must lie inside the retained archive. Require
the standard two zero terminator blocks and only zero trailing block padding;
do not ignore a second concatenated archive or truncated tail. Plain GNU
regular/directory headers can be admitted if they use the same validated
fields without extension semantics. No acceptance of arbitrary bytes merely
because Content-Type says TAR.

Explicitly reject GNU long-name/long-link and PAX local/global extension
headers before a library silently merges or hides them. None is needed to
represent an ordinary PPS basename with short relative prefixes. This is a
bounded supported-format decision, not a claim the unseen server never uses
extensions. An unsupported-format STOP preserves the already fetched archive
for a possible separately reviewed **offline-only** decision; it does not
trigger another GET or a generic archive framework.

Path handling is lexical only. Accept safe relative prefixes, including
ordinary `./`; remove harmless `.` and empty separator components for identity
comparison. Permit a root `.` directory entry. Reject leading absolute `/`,
backslashes, drive/colon syntax, control/non-ASCII bytes and any `..` component;
bound the combined name/prefix to512 bytes and at most8 substantive components.
No percent decoding, environment expansion or operating-system resolution.
These bounds are prospective safety limits, not an inferred archive layout.
Directory prefixes never determine product identity and are not printed.

The sole file's basename must match the existing PPS field-position rule:
`P0851180501`, two instrument characters, exposure flag and three exposure
digits, `SUMMAR`, four subset/source characters, `.HTM`. Use the M2 bounded
uppercase-alphanumeric field contract without asserting OB/X000/0000 values.
Its size must be positive and <=262144. The exact basename remains unknown
until observed; no constructed RXJ filename is described as verified.

## Receipts, privacy and scientific meaning

Ignore raw TAR and copied HTML before execution; they can contain contacts,
coordinates or other metadata not needed in the public report. The safe
inventory records ordinal, normalized-path hash, accepted type, declared size,
validated payload offset and file-content hash, plus aggregate directory/file
counts. Do not serialize raw member names, uname/gname, link targets, header
text or HTML. Preserve exclusive attempt/worker markers, all partials and
named STOPs. A killed worker's unrecorded inspection work remains unknown.

Parent performs bounded offline archive validation and checks exact raw/member
hashes, offsets/sizes, one-request accounting, artifact closure, return code and
EOF evidence. That is an additional local validation pass, not a new request.
No receipt can promote missing/truncated worker completion. A successful
archive outcome is **SUMMARY_MEMBER_RETAINED_UNADJUDICATED** only.

Offline observation/exposure-table interpretation remains a subsequent explicit
step. A correctly named file could still contain an error or incomplete page.
Do not add a literal HTML footer/title rule to package validation, infer modes
from filenames, follow summary links, or call its duration live exposure.
Useful explicit rows can later support a narrow event-product proposal; no
photon request, source recovery, clean-negative claim or discovery follows.

Research accounting: M2 safe receipts/protocol and existing interface notes
read; one primary client-source page revisited. No body, archive, product or
new service query was requested. Only this decision note was written.

Parent disposition: adopted after full note review, the actual M2 receipts and
the primary client/Python TAR documentation checks. A reviewed metadata-only
package validator and new acquisition runtime must be frozen before execution.
Any unsupported packaging is retained for offline diagnosis; it is not an
automatic retry. This decision does not alter M2 or authorize scientific data.
