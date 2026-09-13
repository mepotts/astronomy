# MOS2 exposure map: documented narrow XSA alternate

**DOCUMENTATION_ONLY_PROPOSAL.** No product HEAD/GET, array access, coordinate
query, installation or account action occurred. Two primary documentation pages
were read. The earlier HEASARC MOS2 HEAD 404 and C3 STOP remain unchanged.

## Decision and changed evidence

Recommend one separately frozen, capped GET from official ESA XSA AIO for
**only `P0884250101M2S002EXPMAP8000.FTZ`**, with exact returned basename required
before reading the body. The documented selectors can specify every variable
filename field; this is not a guessed `filename=` API. Actual availability and
whether the response is a raw named product remain unverified.

Parent reports that the actual C5 static diagnostics, frozen at `9cef69c`, found
positive pn source support but zero MOS1 source-aperture and source-annulus
support at both fixed subdivisions. Most MOS1 negative circles were also zero;
the east negative was only partly supported. C5 outcome anchor:
`58d8526abdaeb0347cecb252b740fcbd8b5f6956bf89a661b08eb5210d892a36`.
This note has not independently replayed those arrays. These static-map
findings do not prove zero physical observing exposure, but they do prevent
assuming the adopted MOS1 map supplies source-region support. They make testing
the already identified MOS2 map more useful than proceeding as if pn alone
satisfied the unchanged **pn plus at least one MOS** recovery requirement.

## Exact documented selector mapping

The ESA/ESAC-authored astroquery XMM API documents `obsno` construction from the
observation ID, PPS level, instrument values including M2, scheduled exposure
flag S, three-digit exposure number, six-character product type, one-character
data subset, source number, and FTZ extension. `filename` is a local destination
argument, not the remote selector.
[Stable XMM API, version 0.4.11](https://astroquery.readthedocs.io/en/stable/api/astroquery.esa.xmm_newton.XMMNewtonClass.html)

| Filename field | Exact AIO parameter |
| --- | --- |
| Observation `0884250101` | `obsno=0884250101` |
| Pipeline product | `level=PPS` |
| Instrument `M2` | `instname=M2` |
| Scheduled exposure `S002` | `expflag=S&expno=002` |
| Product `EXPMAP` | `name=EXPMAP` |
| Subset/band digit `8` | `datasubsetno=8` |
| Source field `000` | `sourceno=000` |
| Extension `FTZ` | `extension=FTZ` |

The implementation's `_parse_filename` assigns character index 23 to subset S,
indices 24–26 to the source field, 11–12 to instrument and 14–16 to exposure.
Its image extraction explicitly permits bands 1–5 and 8, interprets this S
field as the band, and includes EXPMAP when exposure maps are requested.
`_create_link` appends these documented keys directly to AIO. Thus `8` is the
subset selector here, not an undocumented `band=8` parameter or source number
8000. The client also uses HEAD before downloading, but that convenience
workflow is not needed or authorized for the proposed one-GET contract.
[ESA XMM client source, 0.4.12.dev710+g038841faa](https://astroquery.readthedocs.io/en/latest/_modules/astroquery/esa/xmm_newton/core.html)

Exact proposed request, **not executed**:

```text
GET https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0884250101&level=PPS&instname=M2&expflag=S&expno=002&name=EXPMAP&datasubsetno=8&sourceno=000&extension=FTZ
```

The already retained HEASARC index supplies the target basename; its 404 does
not explain whether the mirror lacked the object or handled HEAD differently.
An XSA response may also have a different processing version. Do not require an
invented previous MOS2 Content-Length, ETag, Last-Modified or compressed hash.

## Smallest prospective acquisition contract

Reuse the reviewed C3d **transport rules**, through a new isolated stage with
new bindings and receipts; never invoke or alter its old plan/worker. No source
code or executable stage is added by this note.

- One anonymous GET to exactly the URL above; no preceding HEAD, redirect,
  retry, Range, credentials, inherited environment authentication/proxies or
  cookie reuse. Fresh session; socket timeouts 5/15 seconds; hard 60-second
  process-tree worker bound, with the existing separate cleanup allowance.
- Require HTTP 200, exact final URL, identity/absent Content-Encoding and a
  safe unambiguous Content-Disposition basename exactly equal to
  `P0884250101M2S002EXPMAP8000.FTZ` **before body reads**. Allow only C3d's FITS,
  octet-stream and gzip media types. A TAR/ZIP/package name, absent/ambiguous
  filename, text/JSON/XML error, redirect or authentication response stops the
  stage. No package extraction fallback.
- Content-Length is optional; if supplied, it must be an unambiguous positive
  decimal <=2,097,152 and match retained bytes exactly. Stream at most 2 MiB
  plus one overflow-detection byte; never retain the overflow byte. Preserve
  all partials and named STOPs. Absent length is handled by the prospective
  local cap, not described as a passed size advertisement.
- Accept only the same explicit gzip or standard raw-FITS signature as C3d;
  record actual format. Gzip expansion must reach CRC-checked EOF under a
  32-MiB expanded cap plus one overflow check. Raw FITS copying must preserve
  the byte hash. Use the pinned structural reader to inspect headers while
  seeking over arrays; no map values are read in this stage.
- Keep 1-MiB chunks, 500,000,000-byte monitored worker/parent peak, 1-MiB
  aggregate JSON budget with 64-KiB terminal reserve, and C3d's nominal 2-MiB
  full-header ceiling subordinate to that aggregate budget. Require at least
  64 MiB free space. Ignore raw/expanded/full-header artifacts before execution;
  public receipts contain only safe metadata, hashes and structural summaries.
- Freeze protocol/source/tests, original C3 outcome and failed MOS2 receipt,
  exact index identity, helper/reader and runtime. Parent independently checks
  single-slot accounting, safe HTTP classification, magic, sizes/hashes,
  exact one-raw/one-expanded/one-header artifact set and header replay. Timeout,
  nonzero exit or conflicting/truncated receipts cannot become success.

The strongest success would be `MOS2_MAP_RETAINED_HEADERS_ONLY`. Before pixels,
adjudicate observation/instrument/exposure identity, image shape and WCS/frame,
processing history and DSS/energy/FLAG/GTI semantics against C1 and the existing
map-compatibility note. Do not presume that subset 8 guarantees compatibility
with the proposed strict event cuts, or that the map has positive source
support. A separately frozen static MOS2 value pass can then answer that limited
support question using the unchanged source/control centres and radii.

## Stops and scientific meaning

A rejected or unavailable response ends this attempt; it does not authorize a
broader observation bundle, instrument/band change or mirror retry. If the
service packages even this fully filtered selection, the next needed decision
is a separately bounded package/manifest contract, not automatic extraction.
The inspected documentation supports this narrow selection but does not promise
one-file raw response delivery; exact disposition plus header identity remains
the runtime safeguard.

MOS2 acquisition does not waive any recovery gate. Zero/incompatible MOS2
support would leave the current pn-plus-MOS recovery route incomplete. A
pn-only descriptive screen, if later adopted separately, must be labelled as
such rather than called the planned multi-camera control recovery. Source-list
confusion/exclusion geometry, regional exposure, detector-artifact checks and
independent recovery calibration remain necessary; no discovery is claimed.

Local context read: `XMM-ALTERNATE-PPS-SOURCE-2026-09-12.md`,
`XMM-C3d-2026-09-12.md` and `XMM-C3d-RESULT-2026-09-12.md`. C3d's successful
raw-named ATTTSR GET establishes a useful tested implementation precedent, not
MOS2 availability. No additional API/index/product request was made here.
