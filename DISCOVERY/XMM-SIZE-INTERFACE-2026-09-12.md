# XMM control product-size interface: HEASARC directory route

Date: 2026-09-12. Read-only follow-up to the preserved
[C0b-1 STOP](XMM-C0b1-SCHEMA-2026-09-12.md) and
[eligibility investigation](XMM-EXOD-ELIGIBILITY-2026-09-12.md).
No science products, coordinates, accounts, stage queries or software created.

## Decision and exact next endpoint

**The published control has a reachable public HEASARC observation directory
which explicitly links a PPS subdirectory.** This supplies a concrete official
directory route around the size-less NXSA table, but **does not yet supply any
product filename or byte size**. The fixed two-index-request budget ended at
that directory. Do not represent its child directory's existence as complete
PPS availability or a passed acquisition-size gate.

The smallest next action, only if separately adopted, is one bounded metadata
GET of the exact link returned by the official observation index:

`https://heasarc.gsfc.nasa.gov/FTP/xmm/data/rev0/0884250101/PPS/`

That PPS listing was **not requested in this task**. Do not substitute a TAR or
FITS download, guess filenames, install SAS, or silently extend this request
budget to complete the file manifest.

## Actual index results

| Requested index | HTTP | Response bytes | What it actually showed |
|---|---:|---:|---|
| `https://heasarc.gsfc.nasa.gov/FTP/xmm/data/` | 200 | 1870 | Public HTML directory index with a `rev0/` child, among calibration and other directories. |
| `https://heasarc.gsfc.nasa.gov/FTP/xmm/data/rev0/0884250101/` | 200 | 881 | Exact control directory, containing links `4XMM/`, `ODF/`, `PPS/`. |

The second index labels the PPS directory's last modification as
`2026-05-28 05:38`, the ODF directory as `2022-07-09 22:09` and the 4XMM directory
as `2023-06-12 21:02`. Their size entries are **`-`**, not zero bytes, an aggregate
directory size, a product manifest or a processing-version receipt. The timezone
of these displayed modification times was not established. Modification is not
observing time, publication date, or scientific validation.
[Observed official control index](https://heasarc.gsfc.nasa.gov/FTP/xmm/data/rev0/0884250101/).

The root path follows the established HEASARC XMM archive layout. The control
directory path was a bounded, constructed index probe under the observed
`rev0/` branch, not a previously read explicit control URL. Its successful
response establishes its actual existence. In contrast, the **PPS URL above
is now an explicit observed link**, not a guessed scientific-product locator.

The raw response SHA-256 values, computed in memory, were:

- Root index: `eabbb45fe389d8b17e564aff4845d12bf8a9f5d2a165f2eefb89f0af78fd20c4`.
- Control index: `df2493ee2521f1bc8e57c394d1443b8733a97682cbc9b14c39d6fbdba8cb463d`.

Only this note may be created in this task, so these are tool-observed receipts,
not a locally retained raw-input package. Total index bodies: **2751 bytes**.
No response headers/cookie values were printed or retained. Each GET had no
redirects/retries, a 131072-byte streamed response cap and 5-second connect /
15-second read socket timeouts. Each worker used the existing absolute-path
Dyson `bounded_run` helper with a 30-second tree-aware deadline; both returned
code zero without timeout. Aggregate permitted index bytes were 262144. These
successful short probes do not independently test timeout cleanup behavior.

## What official documentation supports

The current HEASARC XMMMASTER documentation explicitly separates public-release
date from mirror availability: `data_in_heasarc` can be `N` even after release.
It also describes observation-level camera modes, exposure times, PPS generation
flags and versions. Such fields can assist a later metadata contract, but do
not supply per-file bytes or validated good-time intervals. The control's
directory response is positive mirror evidence; the general documentation
alone would not have established this particular control's presence.
[XMMMASTER documentation](https://heasarc.gsfc.nasa.gov/W3Browse/xmm-newton/xmmmaster.html).

The older XMMPUBLIC description lists separate ODF and pipeline TAR products.
Its historical product identifiers include `EEVLIS` for MOS calibrated event
lists, `ESRLIS` for EPIC observation source lists and `PPSDAT` for ancillary PPS
information. It also warns about U.S.-archive coverage. This is useful context,
**not a current file manifest or proof that PN products have that same old TAR
mapping**. Its old page-modification date and newer catalogue-update bulletin
should not be conflated with a modern exporter specification.
[XMMPUBLIC product documentation](https://heasarc.gsfc.nasa.gov/W3Browse/catalog/xmmpublic.html).

HEASARC's current GOF services page provides official archive/software links;
its page labelled Archive is chiefly a meetings/symposia archive and directs
users back to data-archive links. Neither page supplies per-product sizes.
[GOF services](https://heasarc.gsfc.nasa.gov/docs/xmm/xmmhp_gof.html),
[GOF archive page](https://heasarc.gsfc.nasa.gov/docs/xmm/xmmhp_archive.html).

## Interpretation and stop rules for a later PPS listing

1. Retain the complete bounded index before interpreting it. Account for every
   listed product and metadata entry. Do not follow calibration/ODF/other-control
   links or recursively crawl the mirror. A byte-cap failure or incomplete index
   must not become an empty or complete manifest.
2. Identify actual returned filenames and formats before mapping them to EXOD's
   required EPIC events and source lists. A legacy TAR category, PPS directory
   timestamp or filename alone cannot prove camera/submode support or FITS
   identity. No such filenames have been observed here.
3. An HTML `Size` column may be human-readable/rounded. Unless the interface
   supplies exact documented bytes, do not treat values such as `12M` as exact
   acquisition lengths. A directory's `-` is missing size. A package's size is
   the stored archive size, not necessarily decompressed members or RAM demand.
4. If exact size remains missing, stop and propose only a separately authorized
   metadata mechanism, such as a documented exact-byte manifest or bounded
   size-only HEAD on **already observed exact product URLs**. Do not request a
   product body to discover its size or assume every server supplies a usable
   Content-Length. No such HEAD request is authorized or executed here.
5. Even exact sizes would resolve only product-access/resource metadata. PPS
   version consistency, scientific mode coverage, published-control recovery,
   independent negatives and a viable local photon-processing runtime remain
   separate gates. No discovery or unknown-source search is implied.

## Budget completion

One discovery search batch; four primary documentation pages opened; exactly
two small directory-index GETs. No retries and no third metadata request.
The prior C0b-1 code, source-order STOP, receipts and privacy boundary remain
unchanged. The recommendation is the single explicit PPS-index metadata step
above, not a broad new experiment or automatic data acquisition.
