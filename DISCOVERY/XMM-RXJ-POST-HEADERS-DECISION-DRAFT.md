# RXJ after headers: inventory the calibration dependency before installing it

2026-09-13; **decision draft, not an executable protocol**. Conditional on M5
authenticating the three intended event products. This task read public repo
notes/helper source, primary documentation and local runtime inventory only.
No retained FITS/private cards, scientific arrays, archive requests, downloads,
installations or calibration tasks were accessed or executed.

## Shortest next action

**Use existing Windows Python for one small, selected-column CALINDEX inventory
from the authenticated event products, if the actual headers identify that
table.** This turns an unspecified calibration dependency into a named finite
resource list. Do not immediately install SAS, mirror CCFs, reprocess ODFs,
decode photons or acquire every available map.

The pn pipeline documents CALINDEX alongside BADPIX, EXPOSU, STDGTI and OFFSETS,
and says it contains relevant EPN/XRT3/XMM calibration entries. This is a reason
to look for the table, not proof that the new PPS products retain it or that
MOS uses the same schema. CALINDEX is an index, not the calibration files.
[Official epchain output specification](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/epchain/node14.html).

Proposed finite execution boundary, to specialize from M5 metadata and freeze:

1. Bind M5 outcome, exact expanded/header hashes and each actual CALINDEX
   extension/schema. Select only columns that explicitly identify calibration
   constituent filenames, type, version and validity interval. Do not invent
   column names or read a whole unknown table into a generic parser. If the
   safe summary hashes unfamiliar column names, a separately allowed local
   schema-only adjudication can identify them; no payload is needed for that.
2. At most one identified calibration-index table per retained camera product,
   at most 2048 rows each, and at most 1 MiB aggregate selected bytes per pass.
   Require scalar fixed-width supported fields and exact selected-span offsets;
   missing, variable-length or over-cap layouts get explicit incomplete/STOP
   accounting, not a broader reader. No EVENTS, BADPIX, GTI, EXPOSU or image
   values are included. These are proposed limits, not measured RXJ dimensions.
3. Use unbuffered selected reads and the existing receipt/deadline patterns:
   60 seconds, 256 MiB monitored peak, 1 MiB safe JSON cap, explicit worker and
   one parent-verification pass. Account opaque provenance hashing separately
   from selected bytes, and budget it from actual file sizes. Keep duplicate
   rows, missing values and all camera slots; do not choose a preferred CCF
   version from a file timestamp alone.
4. Keep original strings/paths private. Publish only validated calibration
   basename identities or hashes, versions/types, counts and missingness;
   never execute a listed path or automatically fetch a referenced resource.

Useful outcome: `CALIBRATION_DEPENDENCIES_INVENTORIED_NOT_INSTALLED`. If CALINDEX
is absent or insufficient, say exactly which camera/dependency is unestablished.
Do not loop through speculative metadata parsers. Parent can then choose a
bounded supported calibration setup from the processing version and required
task documentation; absence of CALINDEX does not imply full ODF reprocessing.

## What is actually available locally

This task verified Windows Python 3.12.10, NumPy 2.5.2 and Astropy 8.0.1 in the
existing `dyson-revet/.venv` runtime. That is sufficient for the repo's reviewed
header, selected-span and pure geometry/timing arithmetic—not the missing
calibrated sky-to-detector transform. A Windows command lookup found no `sas`,
`ecoordconv`, `backscale` or `arfgen` on PATH; this is not a whole-disk search.

The initial restricted-context WSL enumeration returned access denied.
Read-only owner-context `wsl --list --verbose` succeeded: Ubuntu and
docker-desktop are WSL2 distributions, both stopped. Neither was started by
this task. Ubuntu's exact release and installed libraries remain unverified.
The earlier root environment check, recorded in
[CONTINUATION](CONTINUATION-2026-09-12.md), found no SAS/evselect/epiclccorr/cifbuild
on Ubuntu's login PATH and no SAS in its inspected standard locations. That
limited inventory is evidence against an already-ready SAS environment, not
an exhaustive proof that no copy exists anywhere.

ESA supplies Linux/macOS SAS builds and documents a Docker/WSL2 route on Windows.
Its Docker guide's example image occupies 14.9 GB; that is an illustrative
older image, **not a verified size for a current download**. It also includes
examples that download ODFs and discusses X11/access settings. None of those
commands/settings is adopted here. A headless task-specific setup should not
inherit GUI/network/privilege changes just because a tutorial includes them.
[ESA Docker/Windows guide](https://www.cosmos.esa.int/web/xmm-newton/sas-installation-docker4sas),
[ESA SAS release/platform notice](https://www.cosmos.esa.int/web/xmm-newton/news-archive-2025).
The guide text was available through primary-source search; direct opens of
the guide and download/install/requirements pages returned HTTP451 in this
research tool. Therefore no current package/version/size compatibility claim
or executable installation recipe has been verified.

## Where supported SAS becomes necessary

For the adopted calibrated detector/window/bad-pixel mapping, this repo has no
validated replacement for SAS/CAL. WSL availability alone does not supply it.
Unless a compatible existing SAS installation is located, **a scoped supported
installation is the practical next dependency for that stronger geometry step**.
It is not necessary for the small index inventory, nor established as necessary
for every descriptive diagnostic. Prefer a compatible native Linux SAS build
inside existing Ubuntu over defaulting to a large new container, conditional
on an explicit release/dependency/storage check; do not promise that choice
will work before checking the actual Ubuntu release.

After the inventory, the smallest environment decision is a read-only Ubuntu
release/architecture/free-space check, then a reviewed manifest for one official
SAS build and its declared runtime dependencies plus named necessary CCFs.
Pin distribution integrity evidence and caps before any install/download.
Start with version/import checks and one fixed-region coordinate smoke test,
not `startsas`, `epchain`, a full observation pipeline or a CCF mirror.

That conversion still needs a suitable authenticated standard pipeline image:
`ecoordconv` expects particular primary astrometry, and its documentation warns
that exposure maps need preprocessing. An unchanged EXPMAP or fabricated empty
image cannot be assumed equivalent. Image intensity need not determine region
placement. The previously recorded FK4-2000 versus FK5/J2000 input-convention
ambiguity and warning defaults must be resolved for the actual supported
version, or use an authenticated X/Y convention—not silently relabelled.
[Official source-image contract](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/ecoordconv/node5.html).

## Finite scientific requirements that remain

The adopted [joint-region calibration decision](XMM-CALIBRATION-NEXT-DECISION-2026-09-13.md)
still needs photon-blind CCD/window/mask mapping; the union of fixed catalogue
exclusions intersected with valid detector area; and per-region relative time
acceptance from relevant CCD GTI/frame/attitude information. The inventory
does not measure any of these. Do not infer CCD membership from photon occupancy
or turn observation-integrated maps into 200-second denominators.

Keep the source, four cardinal negatives and requirement for pn plus an eligible
MOS and at least two usable negatives. Geometry can establish eligibility, not
empirical quietness or background representativeness. Time-variable background,
fixed detector-artifact rules and unresolved uncertainty tolerances remain
essential before the proposed recovery photon pass. Absolute flux/ARF fitting,
a survey-wide false-alarm model and a new Monte Carlo framework are not added
as prerequisites for the limited published-control diagnostic.

**Decision:** continue the one named index inventory, then make the concrete
supported-environment/resource choice it enables. Do not claim headers or a
successful installation satisfy recovery; do not defer all useful work merely
because SAS is not currently ready. Existing protocols and STOPs are unchanged.
