# XMM control input structure: evidence before photon acquisition

Public documentation inspection, September 12. This is a feasibility note, not
an executed event extraction or a claim that our selected files have these
contents. Exact product headers and extension schemas still require a bounded
structural inspection after acquisition. No new package or SAS installation.

## What the primary documentation establishes

Calibrated, concatenated event lists are distributed as PPS products. They are
the input for later extraction; different cameras remain separate. The handbook
explicitly warns that PPS format can differ from task-generated event files.
Consequently, generic task documentation cannot validate a particular archive
file by itself. [Event-list overview](https://heasarc.gsfc.nasa.gov/docs/xmm/sas/dfhb/event.html).

The MOS imaging description supplies per-CCD exposure-fraction, bad-pixel and
standard-GTI extensions. Exposure rows describe frame central time, integration
time and effective fraction. Additional GTIs can refer to data-subspace time
filters; their indexing differs from the standard per-CCD extensions. Event
sky X/Y and linearized detector coordinates are described in 0.05-arcsec units,
not celestial degrees. Thus an aperture must use the actual WCS, not treat X/Y
as RA/Dec or as physical detector pixels.
[MOS imaging structure](https://xmm-tools.cosmos.esa.int/external/xmm_user_support/documentation/dfhb/evmosima.html).

The pn description allows up to twelve CCD-specific exposure, bad-pixel and GTI
extensions. Exposure headers may identify the science window through MODE and
WINDOWX0/Y0/DX/DY. Discarded-line information can matter for exposure maps.
Its prose identifies calibrated PI in eV, while the accompanying generic column
table says channels; retain and verify actual units instead of concealing this
documentation ambiguity. Additional GTI/data-subspace filters must not be
silently ignored.
[pn imaging structure](https://xmm-tools.cosmos.esa.int/external/xmm_user_support/documentation/dfhb/evpnima.html).

The epchain output specification independently lists calibrated EVENTS with
per-CCD BADPIX, EXPOSU and STDGTI information, plus OFFSETS and CALINDEX. This
supports looking inside the selected event files before obtaining a bulk
ancillary bundle. It does not prove which optional extensions were retained by
the archive pipeline.
[epchain output specification](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/epchain/node14.html).

MOS task documentation distinguishes flare timeseries from GTI files and notes
that a combined-camera timeseries FRACEXP can exceed one. Do not impose a
universal FRACEXP range or mistake a background timeseries for a per-CCD exposure
table. This warning is specific to the documented combined product, not evidence
that per-CCD effective fractions exceed one.
[emchain outputs](https://heasarc.gsfc.nasa.gov/docs/xmm/sas/21.0/doc/emchain/node14.html).

The documented mission reference is MJD 50814.0 in TT. The page's numerical
TT-minus-UTC examples are explicitly dated; do not reuse its 2015 offset for a
2021 observation. Verify TIMESYS, MJDREF (or split reference), TIMEZERO, TIMEUNIT
and any barycentric correction in every relevant extension. A conversion must
use the appropriate dated leap-second convention; seconds of elapsed mission
time are not Unix timestamps.
[Mission time reference](https://heasarc.gsfc.nasa.gov/docs/xmm/sas/dfhb/timescale.html).

## Minimal structural inspection to specify after size metadata

Keep original compressed files immutable and hash-bound. A separate acquisition
contract must set per-file compressed, aggregate expanded, memory and wall caps;
directory K/M values alone are not such bounds. Stream decompression to an
exclusive, bounded destination and verify completion/CRC rather than trusting
the gzip footer's modulo-size field. No general archive extraction is needed.

Inspect only HDU headers, table schemas and row counts initially, without
accessing EVENTS arrays or optimizing a source aperture. Record exact camera,
exposure, mode/filter, processing identifiers, time conventions, WCS column
metadata, GTI/exposure/bad-pixel extension names and field definitions. Preserve
missing, contradictory and optional information. The first structural report
can define the next science protocol from real metadata without having examined
the source light curve.

An event-table name must be recognized from actual EXTNAME and required fields;
the documentation's EVENT/EVENTS wording is not permission to grab an arbitrary
first binary table. Instrument mode, exposure timing and detector identifiers
must agree across headers and the selected filename. No masking or counting
should proceed while that mapping is ambiguous.

For the later counts test, integrate per-CCD live exposure over each bin and
intersect relevant GTIs/data-subspace restrictions. Nominal TSTOP−TSTART is not
live exposure. Source and background need separately valid detector coverage;
blank event pixels are not proof of bad pixels or zero exposure. These are
requirements still to implement, not claims that the draft recovery already
handles them. The [recovery draft](XMM-CONTROL-RECOVERY-DRAFT-2026-09-12.md)
remains unexecuted.

## Implemented preparatory reader, not yet used on real files

[xmm_structure.py](xmm_structure.py) now implements bounded header-block reads
and skips declared array spans using Astropy's Header size properties. It
preserves cards rather than collapsing duplicate metadata into a dictionary;
duplicate layout keys are rejected. [Astropy header API](https://docs.astropy.org/en/stable/io/fits/api/headers.html).
Fifteen synthetic tests, including independent malformed-header and payload-read
guards, pass after four binary-table layout fixes. See the
[review record](XMM-STRUCTURAL-REVIEW-2026-09-12.md).

This is not a full FITS conformance validator. Array contents, checksums, heap
descriptors, scientific identity and calibration remain unchecked. A malformed
header can make its bounded scanner consume unknown bytes before STOP; only
payload spans declared by accepted headers are guaranteed to be skipped. No
actual event file has been processed by this preparatory code.
