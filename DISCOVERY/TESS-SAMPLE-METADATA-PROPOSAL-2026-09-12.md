# Sector 106: identifier-defined WD sample proposal

Research-only check, 2026-09-12. **An exact public identifier join is executable;
the Sector 106 WD sample has not been counted or selected.** No unknown light
curve, target-pixel file, flux, candidate coordinate, or bulk catalogue was
retrieved. No uploads, accounts, publications, or scientific outward actions.

Read alongside [incremental-coverage evidence](TESS-INCREMENTAL-COVERAGE-2026-09-12.md)
and the current [control-stage status](../tess-short-eclipses/README.md). Method
acceptance and source localization remain separate gates. This note does not
authorize unknown-target photometry.

## Exact catalogue and mapping

Use the Gentile Fusillo et al. (2021), MNRAS 508, 3877 catalogue, CDS identifier
`J/MNRAS/508/3877`, table `maincat`. Its schema explicitly supplies `GaiaEDR3`
(EDR3 source identifier), nullable `GaiaDR2` (the catalogue's DR2 association),
and `Pwd`. The catalogue recommends `Pwd > 0.75` as a generic high-confidence
candidate selection. Its separate reduced-proper-motion extension is not the
same population. [CDS author-catalogue schema](https://cdsarc.cds.unistra.fr/ftp/J/MNRAS/508/3877/ReadMe)

The CDS TIC snapshot is `IV/38/tic`, explicitly **TIC v8.0**, associated with
Stassun et al. (2019), AJ 158, 138 and the April 15, 2019 source version. Its
`TIC` identifier joins to the manifest; `GAIA` is explicitly a **Gaia DR2**
identifier, not EDR3/DR3. `Disp` and `m_TIC` encode problematic/related entries.
The schema describes duplicate, artifact and split dispositions; a later TIC
version must not silently be substituted. [CDS TIC schema](https://cdsarc.cds.unistra.fr/ftp/IV/38/ReadMe)

The deterministic chain is therefore:

| Input | Exact comparison | Output |
|---|---|---|
| Preserved Sector 106 manifest TIC ID | `manifest.tic_id = t.TIC` | TIC v8.0 row and disposition |
| TIC v8.0 DR2 association | `t.GAIA = w.GaiaDR2` | WD-catalogue row, `GaiaEDR3`, `Pwd` |
| WD-catalogue probability | finite `w.Pwd > 0.75` | Proposed high-confidence main-catalogue candidate subset |

Never join `t.GAIA` directly to `w.GaiaEDR3`, never cast Gaia identifiers through
floating point, and never interpret an absent join as proof that an object is
not a WD. Use decimal strings or exact 64-bit integers throughout. The WD
catalogue's DR2 association is adopted as published provenance, not independently
revalidated astrometry. A positional fallback would be a separate experiment,
not an implicit repair of missing identifiers.

## Executed small metadata proof

One read-only query to the anonymous
[CDS TAP endpoint](https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync) requested
at most two rows for **published control TIC 450781262**. This is one of the
already frozen M0 controls; it was not selected from Sector 106 and its presence
there is not asserted.

```sql
SELECT TOP 2 t.TIC, t.GAIA, t.Disp, t.m_TIC,
             w.GaiaEDR3, w.GaiaDR2, w.Pwd
FROM "IV/38/tic" AS t
LEFT OUTER JOIN "J/MNRAS/508/3877/maincat" AS w
  ON t.GAIA = w.GaiaDR2
WHERE t.TIC = 450781262
```

Request parameters were `REQUEST=doQuery`, `LANG=ADQL`, `FORMAT=tsv`, `MAXREC=2`.
A single row returned successfully:

```text
TIC         GAIA                 Disp  m_TIC  GaiaEDR3             GaiaDR2              Pwd
450781262   5346312514819760896              5346312514819760896  5346312514819760896  0.949728
```

The blank disposition/related-ID cells are retained as blank, not invented
values. This verifies the exact table names, column names, identifier join and
anonymous row-query availability for one published control. In this particular
row the two Gaia IDs happen to agree; that does not validate a cross-release
identity shortcut elsewhere. No source coordinates or time-series values were
requested. Transport was bounded by curl's 20-second deadline and 150,000-byte
response limit. The request was a public-identifier query, not a TAP table upload.

This research turn preserved the query and returned row here, not a new raw
response file. A production metadata stage must retain original response bytes,
response status, query, timestamp, hashes and overflow indicators before claiming
a fully reproducible sample selection.

## Sector 106 documentation gap

The official Sector 106 page gives July 11--August 9, 2026 and southern pointing,
but both science-collection and paused-collection days remain `TBD` in the page
retrieved here. It is not a completed processing-quality report.
[NASA sector summary](https://heasarc.gsfc.nasa.gov/docs/tess/sector106_summary.html)

The retrieved MAST release-note index ends at **DRN 142 / Sector 104** and labels
its last modification September 4, 2026. It explains that sector numbers and
release-note numbers are distinct, with special processing memos for some
releases. No Sector 106 note or memo appeared in this index. This is an observed
index gap, not proof that no unindexed document exists. Do not invent a DRN 144
URL, equate DRN 106 with Sector 106, or treat Sector 104's report as applicable.
[MAST release-note index](https://archive.stsci.edu/tess/tess_drn.html)

Accordingly no Sector 106-specific quality assessment was established. The
already preserved bulk manifest supplies 12,996 target products, not 12,996 WDs,
and its modification time is not each product's first-publication time. Public
rights, observing dates, processing release, product type and actual cadence
still require product/observation metadata checks. A catalogue join alone cannot
settle cadence flags, time gaps, scattered light or pipeline behavior. These
remain explicit gates before an unknown light-curve stage, not reasons to infer
quality from another sector. [Prior local manifest audit](TESS-INCREMENTAL-COVERAGE-2026-09-12.md)

## Prospective deterministic sample rule

This is a proposal to freeze before executing the sector join, not a reported
selection result:

1. Bind the existing manifest SHA-256
   `42daeac2b7939922f782156d68666d6fc614384ce40d1559632eb89dda575951`.
   Retain all 12,996 unique manifest TIC IDs as the denominator, ordered by exact
   integer value. Do not filter on TIC temperature, radius or dwarf labels as a
   surrogate for WD-catalogue membership.
2. Query the exact frozen TIC snapshot by those public identifiers in bounded
   batches, retaining absent rows, duplicate rows, `GAIA`, `Disp`, and `m_TIC`.
   Missing or ambiguous mappings are unresolved exclusions. For the initial
   strict subset, exclude nonblank disposition or nonnull related-ID cases;
   preserve their counts and raw rows. Do not follow related IDs automatically
   or replace a manifest target with a different aperture target.
3. Join each nonnull exact `GAIA` to the WD catalogue's `GaiaDR2`. Retrieve all
   matching catalogue rows, including rows below the eventual probability cut,
   so an ambiguous association cannot be hidden by filtering first. Require
   exactly one unambiguous WD association per accepted TIC. If multiple manifest
   TICs resolve to the same WD, flag the entire collision group for review rather
   than count it as independent stars or arbitrarily select an aperture.
4. Apply finite `Pwd > 0.75` in `maincat` only. Exclude the RPM extension from this
   initial population and name that loss. Do not add an untested magnitude or
   temperature cut. The result is a high-confidence **WD-candidate catalogue
   subset**, not spectroscopic confirmation or an unbiased eclipsing-binary
   sample.
5. Preserve a per-manifest-row ledger: TIC absent; TIC ambiguous; disposition;
   missing DR2 ID; no WD association; multiple WD associations; cross-TIC WD
   collision; missing probability; probability threshold; accepted. Keep both
   overlapping reasons and a fixed first-failure accounting order matching this
   list. Report star and product counts separately. No count is currently known
   beyond the parent manifest denominator.

The exact-ID policy intentionally sacrifices uncertain coverage rather than
claiming a complete population. The older TIC snapshot can miss later identifiers
or changed dispositions. WD main-catalogue selection and a DR2 association can
lose sources with problematic parallax, color, blends or missing older matches;
the separate RPM population is omitted. None of those losses has been quantified
for Sector 106. The catalogue probability is not a completeness correction, and
one successful known control does not measure any loss rate.

## Smallest next executable metadata-only step

Freeze a **32-target transport/coverage pilot**: the first 32 manifest TIC IDs in
ascending exact-integer order, chosen from the preserved manifest without flux
inspection. Keep the three already published M0 controls as a separate adapter
check, never mixed into the sector denominator or substituted for missing pilot
rows. Ascending-ID selection is deterministic, not a representative sky sample.

Before network, test exact 19-digit IDs, nulls, duplicate associations, disposition
handling, probability equality at 0.75, response overflow and omitted requested
IDs. Query only identifier/probability/disposition columns; no coordinates,
catalogue fluxes, unknown LC/TP products or table uploads. Freeze at most eight
metadata requests, 20 seconds and 150,000 bytes per request, 1 MB aggregate;
refuse truncation or unbounded server pagination. Preserve complete responses and
hashes. Report every missing/ambiguous row and stop on schema or coverage failure;
do not widen the sample to obtain a desired number of WDs. A zero-WD pilot is an
honest transport/coverage result, not grounds to tune the sample.

Only after that pilot establishes identifier parsing and honest accounting should
a separately authorized full **metadata-only** join of the fixed 12,996 targets
be specified. That is distinct from light-curve download/search, which also needs
the unresolved localization, negative-control and release-quality gates. The new
Sector 106 observing interval is incremental data; these joins establish neither
object novelty nor that other searches have not examined the same stars.

## Bounded source/access ledger

Eight distinct primary-source page/endpoint URLs were attempted. Re-displaying
the same small schemas after truncated tool output introduced no new catalogue
or endpoint. Failed pages were not treated as evidence of catalogue absence.

| # | URL | Actual observation |
|---|---|---|
| 1 | https://cdsarc.cds.unistra.fr/ftp/J/MNRAS/508/3877/ReadMe | Browser fetch failed; bounded curl retrieved the author-catalogue text schema, including both Gaia identifiers and probability column |
| 2 | https://archive.stsci.edu/hlsp/tic | Browser safety/fetch failure; no server-status or content claim |
| 3 | https://archive.stsci.edu/tess/tess_drn.html | Read successfully; index through Sector 104 only |
| 4 | https://heasarc.gsfc.nasa.gov/docs/tess/sector106_summary.html | Read successfully; dates available, collection-day fields TBD |
| 5 | https://vizier.cds.unistra.fr/viz-bin/ReadMe/J/MNRAS/482/4570?format=html&tex=true | Browser failure; bounded curl returned HTTP 500; older WD catalogue not adopted |
| 6 | https://vizier.cds.unistra.fr/viz-bin/ReadMe/IV/38?format=html&tex=true | Browser failure; bounded curl returned HTTP 500 |
| 7 | https://cdsarc.cds.unistra.fr/ftp/IV/38/ReadMe | Bounded curl successfully retrieved TIC v8.0 schema and disposition semantics |
| 8 | https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync | Bounded anonymous two-row-maximum identifier query returned the single published-control mapping above |

Only this proposal file was written by this research subtask. No raw science
inputs, repository settings, other project files or Git state were changed.
