# XMM C0d independent post-run audit

2026-09-12: the frozen stage correctly remains **STOP_SUMMARY_FOOTER**, with four
accepted HEAD measurements and a failed summary-acceptance slot. Offline evidence
supports a conservative parser-rule rejection, not observed HTTP-body truncation.
This is a separately labelled interpretation; it does not change the executed
source, protocol, receipts, acceptance rule or original STOP.

## Receipt and provenance verification

All 23 outcome artifact hashes match. The frozen script's read-only replay
independently returned `PASS_OFFLINE_REPLAY STOP`, including dependency binding,
ordered five-slot ledger, accepted HEAD measurements and worker artifact closure.
All 24 stage files present when the audit began were unchanged afterward.

Five request markers are present. All five retained HTTP receipts report 200;
four slots are accepted and the fifth is FAILED, not an accepted fifth response.
Worker exit code 1 and `STOP_SUMMARY_FOOTER` are preserved. Each HEAD receipt has
one positive decimal Content-Length matching the saved measurement, a null body
and zero body bytes read. No product body was requested by this reviewer, and no
request was repeated.

| Advertised compressed entity | HEAD Content-Length, bytes |
| --- | ---: |
| PN S003 PIEVLI FTZ | 109245605 |
| M1 S001 MIEVLI FTZ | 7643540 |
| M2 S002 MIEVLI FTZ | 9972723 |
| EP X000 OBSMLI FTZ | 120581 |
| Sum | 126982449 |

These are advertised stored-entity lengths, not downloaded product checksums,
expanded FITS sizes, working-memory estimates or verified photon contents.

## Entire retained summary structure

The summary receipt advertises Content-Length 50010, and exactly 50010 body bytes
were retained, below the 262144-byte cap. Content-Type is HTML with ISO-8859-1
charset; the final URL is the fixed authorized summary URL. No content encoding
is advertised. The retained body ends with `</body>` and has no `</html>` end tag.

An independent HTMLParser-based scan consumed the entire body using its declared
ISO-8859-1 encoding. Accounting for void elements, it found zero explicit tag-
nesting mismatches and zero unconsumed parser characters. All six tables, 132
rows, 1064 data cells, 18 header cells, ten divs and the body have matching closes.
Only the outer html element remains on the open-tag stack. The final footer is
present, including the processing metadata and return-to-top link. Observation
`0884250101` is present in parsed text outside script/style blocks, not merely in
the requested URL.

Matching the advertised body length and closing every examined non-void
structure except html provides no evidence of an interrupted transfer. The
frozen check explicitly required a final `</html>` and therefore rejected this
representation as designed. This audit does not prove archive-generation
intent, validate the document against an HTML standard or prove every possible
metadata field is present. It does support a new, clearly labelled offline
interpretation of the already retained metadata without another HTTP request.

## Identities and scientific boundary

| Artifact | SHA-256 |
| --- | --- |
| `outcome.json` | `7895f2fd39ce85ab745fbff40a291abbf7376086e9f58a2245352b2c348453a3` |
| `summary.html` | `aba0f32242f6d81b65132cdfa167dbc8f4d75c15ef2c5ab69a37d048e4fca837` |

The stage's eligibility remains `METADATA_INCOMPLETE_FOR_CONTROL_CONTRACT`.
Exposure-specific mode/version/timing statements require explicit offline
extraction with original labels and missing-value accounting. Neither this
structural audit nor the four HEAD lengths establish good-time overlap, event
validity, background quality, recovery, a usable science bundle or a discovery.
No science pass or new acquisition authority follows from this note.
