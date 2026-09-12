# M1d2 independent structural review

2026-09-12. Metadata-only audit after the preserved M1d stop. No retained binary
row was decoded, no catalog request or service URL was invoked, and no numeric
parity tolerance or scientific gate was changed by this review.

## Correction of the preflight record

Our M1d preflight missed the ancillary RESOURCE while describing the retained
response structure. The independent review's claim of a single RESOURCE was
incomplete, and its synthetic fixtures reproduced that mistaken assumption.
This was a reviewer/preflight omission, not evidence that ARI supplied a
malformed table. The real M1d execution correctly obeyed its frozen contract and
stopped with `STOP_M1D / STOP_TABLE_STRUCTURE` before numeric row decoding.
The M1d source, tests, protocol, review, manifest and all receipts remain frozen;
this document corrects the interpretation without rewriting them.

Anchors independently checked:

- Retained ARI XML SHA-256:
  `17c3c8a22488bb9b40a37d77b47807aa900decc28486e04bc5a48c0739ad2639`.
- Preserved `out/m1d-result.json` SHA-256:
  `a5b60584321ab05592c8ab7e5f44f142091a51a09805324b30a3e4a64997cd6c`.
- M1d result's manifest hash:
  `058edc26b4882486ff9fc282c66d5550bbede00987b21d3c3970f4418211ad11`.

## Complete structural inventory

The audit traversed every XML element and inspected attributes and non-STREAM
leaf text. STREAM text was explicitly omitted from output and not decoded.

ARI: UTF-8 declaration, VOTable 1.4, standard v1.3 namespace, **33 elements**.
Root has two direct sibling RESOURCEs, not one. Counts: VOTABLE 1, RESOURCE 2,
INFO 3, COOSYS 1, TABLE 1, FIELD 8, DESCRIPTION 10, VALUES 1, DATA 1, BINARY 1,
STREAM 1, PARAM 2 and GROUP 1. All elements use the expected namespace.

The results RESOURCE contains, in order, QUERY_STATUS=OK, PROVIDER and QUERY
INFOs, an ICRS COOSYS with epoch 2016 and ID GDR3_ICRS, and one TABLE. Its eight
FIELDs retain the previously reviewed names, types, unit scales and descriptions.
Each FIELD ID equals its name; ra/dec reference GDR3_ICRS. Only source_id has
VALUES, declaring the signed-64 minimum as null. DATA contains the single inline
base64 BINARY STREAM. No nrows, arraysize or xtype appears on these FIELDs.

The second RESOURCE has exactly these attributes:
`type="meta" utype="adhoc:service" name="Datalink_GaiaDR3"`. Its children are:

1. A plain DESCRIPTION of linked data for a Gaia DR3 source.
2. PARAM with `arraysize="51" datatype="char" name="accessURL"
   ucd="meta.ref.url" value="https://gaia.ari.uni-heidelberg.de/datalink/gaiadr3"`,
   containing one plain DESCRIPTION.
3. GROUP with `name="inputParams"`, containing one childless PARAM with
   `name="sourceid" datatype="long" ref="source_id" value=""`.

There is no standardID, nested RESOURCE, TABLE, FIELD, DATA, STREAM, LINK or INFO
in this ancillary subtree. The PARAM ref identifies the unique source_id FIELD
ID; it is metadata about a possible service invocation, not another row array.

The ESA structural cross-check also corrects the earlier resource-count wording:
**55 elements, three RESOURCEs**, but still exactly one TABLE and BINARY2 STREAM.
Its direct results RESOURCE contains four INFOs (including QUERY_STATUS=OK), nine
descriptive PARAMs, COOSYS and an untyped nested RESOURCE containing a second
COOSYS and the eight-column table. Its sibling meta RESOURCE describes ancillary
DataLink access using standardID/accessURL/contentType PARAMs and an inputParams
GROUP (ID ref=SOURCE_ID and RELEASE). Counts are VOTABLE 1, RESOURCE 3, INFO 4,
COOSYS 2, TABLE 1, FIELD 8, DESCRIPTION 18, DATA 1, BINARY2 1, STREAM 1, PARAM 14,
GROUP 1. **Do not adapt ESA through the ARI-only repair**: preserve the existing
strict Astropy ESA path, which already interprets this structure.

## Primary specification and exact allowance

IVOA DataLink 1.0 Recommendation sections 4.1–4.2 permit table-free service
descriptors alongside a query-result resource. The descriptor uses type=meta and
utype=adhoc:service; PARAMs describe service metadata and inputParams describes
inputs. A parameter ref resolves to a FIELD's XML ID. accessURL is required,
whereas standardID is optional for custom services. Thus the ARI descriptor's
name alone does not establish conformance to the standard DataLink links API.
[Official IVOA DataLink 1.0 Recommendation](https://www.ivoa.net/documents/DataLink/20150617/REC-DataLink-1.0-20150617.html).

Recommended new-stage allowance is deliberately narrower than the standard:

- Require the one direct results RESOURCE and exactly one additional direct
  meta/adhoc:service RESOURCE with the observed name and subtree profile above.
  Reject all additional or nested resources. Require exactly one TABLE globally.
- Validate the entire document's namespaces and QUERY_STATUS values **before**
  removing anything. Retain XML/byte bounds and all external-reference/DTD/entity
  prohibitions. Never follow the descriptor URL or schemaLocation.
- Validate every ancillary node, attribute, child count and order against the
  observed inert descriptor; require the input ref to identify exactly one
  source_id FIELD. No broad “ignore all meta resources” rule. Reject any
  additional TABLE/DATA/STREAM/FIELD, INFO, href, LINK, namespace or nested content.
- Remove only that validated service subtree in memory, retaining raw input
  bytes on disk. Bind raw and adapted hashes, and prove the table subtree and
  STREAM text are unchanged. Reuse the frozen M1d numeric decoder, validation,
  ESA reader, parity checks and gates unchanged.
- Freeze new source/protocol/tests/manifest before a bounded M1d2 execution.
  Passing adaptation is not catalog parity, and catalog parity is not scientific
  localization or permission for new acquisition.

Required synthetic tests should accept the exact descriptor and prove unchanged
numeric output for the same synthetic BINARY payload; reject altered type/utype,
name, URL/input ref, duplicate/nested descriptors and any concealed data or status
node. A metadata-only retained-file preflight may compare the entire structural
tree against the frozen allowance while a patched decoder forbids row access.

**Current status:** structural diagnosis and narrow allowance recommended;
M1d2 implementation acceptance awaits its source/protocol/test review. No numeric
result is predicted from this metadata audit.

## Bounded pre-execution implementation review

The complete adapter, protocol and author tests were independently reviewed.
**GO to freeze and a single bounded offline run, conditional only on binding the
new independent test file in the manifest's dependency collector.** The test
file is stable; no other blocking finding remains.

Fifteen M1d2 synthetic tests pass: eight author tests and seven independent tests
in `tests/test_m1d2_review.py`. Pinned Ruff 0.16.5 passes for source and both test
files. Independent tests check hostile descendants/attributes/references,
duplicate identities, unchanged table serialization and STREAM text, and extra
tables still being rejected by the original reader. Harness tests verify the
five receipt/manifest paths and launch filename, dependency/execute bindings,
unchanged decoder, runtime-only save redirection, save restoration after failure
and a separately imported original module retaining its M1d state. Original
manifest inconsistency and an unexpected original stop both reject.

The reviewer also ran the **retained metadata-only adapter**, with BASE.decode
patched to raise if invoked. It passed without numeric row decoding and exactly
reproduced the parent's structural receipt:

- Descriptor serialization SHA-256:
  `424c8c5dafa9311c9d49eab9769cbd085b8bb8de20df7bbfbe0a83628fdc27f3`.
- Derived XML SHA-256:
  `b951081d0f7f7824d52f001c9b750bd074af10433f2903c6bb51cdfd907ab5bd`.
- Original results subtree unchanged: true. Service URL not fetched.

The allowance checks exact structural attributes and values while permitting
arbitrary plain descriptive text, which is inert and included in the descriptor
hash. It does not claim full VOTable validation. Unrecognized results-table
structure is still checked by the unchanged M1d reader before numeric unpacking.
Hard-deadline and memory/output acceptance behavior is inherited; a harness or
provenance failure may be recorded as STOP_WORKER instead of a scientific
STOP_M1D2 result. Neither is permission to retry the frozen stage.

Stable independent test SHA-256:
`7b8dda3fc21144141d5edafd2a5e5792eeb8958f25fc94c70460b25d486c6803`.
Source/protocol and all test hashes must be captured by the new frozen manifest.
This review accepts software readiness only; numeric parity remains unmeasured
at review time, and the original M1d STOP remains part of the record.

The parent added and the reviewer verified the independent-test dependency
before freeze. Final source SHA-256 is
`6415e4f371a203a2cce7bbf13f356ed0e8beafa90054a57bfee173fa95a71db8`.
The sole condition above is satisfied: **GO for freeze and the single bounded
offline M1d2 run.**
