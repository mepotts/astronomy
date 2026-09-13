# MOS PI units: bounded documentary check

## Decision

**DOCUMENTED_NUMERIC_CONVENTION; EXACT-FILE PHYSICAL CALIBRATION NOT VERIFIED**. The retained MOS headers are consistent with PI numerical values representing calibrated energy in eV, despite `TUNIT9='CHAN'`. The three pages inspected by this subagent were insufficient on their own. A separately bounded parent follow-up supplies direct official MOS selection examples explicitly identifying the PI values as eV. The parent therefore adopts the standard numeric convention `E_eV = PI` for prospective calibrated MOS PI cuts, not for PHA. C1 acquisition success and its frozen artifacts are unchanged.

This is a metadata/documentation check only: no event arrays, photon counts, coordinates, full header cards, new data requests, or frozen-code changes.

## Exact retained header evidence

Only PI schema and instrument/processing metadata were inspected in the ignored, local C1 header reports. All three primary headers identify `evlistcomb-4.20` and SAS `xmmsas_20241108_1150-21.0.0`.

| C1 slot / instrument | Imaging submode | EVENTS PI schema | Header range metadata |
| --- | --- | --- | --- |
| 1 / EPN | PrimeFullWindow | column 9; `TFORM9='I'`; `TUNIT9='eV'`; comment `Corrected Event Energy` | `TNULL9=-32768`, `TLMIN9=0`, `TLMAX9=32767` |
| 2 / EMOS1 | PrimePartialW3 | column 9; `TFORM9='I'`; `TUNIT9='CHAN'`; comment begins `measured energy in eV (gain corr` | `TLMIN9=0`, `TLMAX9=15000`; `TDMIN9=77`, `TDMAX9=13875` |
| 3 / EMOS2 | PrimePartialW3 | column 9; `TFORM9='I'`; `TUNIT9='CHAN'`; same comment prefix | `TLMIN9=0`, `TLMAX9=15000`; `TDMIN9=80`, `TDMAX9=14223` |

Neither `TSCAL9` nor `TZERO9` appears in these selected PI schemas. Absence of an explicit FITS storage scaling card is not independent proof of a physical energy calibration. The TDMIN/TDMAX values above are retained header metadata, not independently recalculated array statistics.

SHA-256 of the exact local header reports:

- `DISCOVERY/XMM-C1-2026-09-12-data/headers/slot-1-headers.json`: `a6d78ea07324eeef06ed544555525ebb4e071f069eb428ed050913d6cbcbf0ba`
- `DISCOVERY/XMM-C1-2026-09-12-data/headers/slot-2-headers.json`: `a99589df5bbce769557e09f150365a109a705bf20cf1e464819559d7af1d15ae`
- `DISCOVERY/XMM-C1-2026-09-12-data/headers/slot-3-headers.json`: `4ab18a78e8677e9db62c9ad07bbefe143bfcecb72aebb640fa6f4da721e20417`

The full reports remain ignored/local; this note deliberately omits coordinates and unrelated cards.

## Primary-source evidence and limits

This subagent opened exactly three official documentation pages on 2026-09-12, following one search batch. The parent separately performed two targeted searches and opened two additional official pages, reported below. No scientific product or service query was made in this check.

1. [SAS User Guide: MOS processing](https://xmm-tools.cosmos.esa.int/external/xmm_user_support/documentation/sas_usg/USG/MOSmetatask.html) describes production of calibrated MOS event lists, `emenergy` filling PI, and `evlistcomb` merging event lists by observing mode. It distinguishes PHA from PI but gives no numerical PI energy conversion.
2. [SAS emenergy task index](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/emenergy/index.html) identifies the task as assigning event energy and quality flags for MOS CCD/node exposures. The retrieved page is emenergy 8.10, SAS 22 documentation, not an exact SAS 21 implementation audit.
3. [SAS emenergy output files](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/emenergy/node7.html) confirms that PI is an output column and that processing metadata propagate into the event product. It does not specify eV/channel or an energy offset.

Search snippets mentioning spectral bin sizes or response-matrix channel widths were not treated as conversion evidence. A grouped spectral channel width must not be substituted for the native event PI scale.

### Parent follow-up: resolving the operational numeric convention

The following evidence was inspected and supplied by the parent, rather than independently reopened by this subagent:

- [HEASARC XMM ABC Guide, imaging analysis, section 7.2](https://heasarc.gsfc.nasa.gov/docs/xmm/abc/node9.html) supplies MOS1 and MOS2 event-selection commands using `PI in [200:12000]` and explicitly describes these numbers as eV. This directly supports interpreting calibrated MOS event PI numerically in eV, without an extra multiplication or additive channel offset in the selection.
- [ESA SAS User Guide, command-line processing](https://xmm-tools.cosmos.esa.int/external/xmm_user_support/documentation/sas_usg/USG/workcommandline.html) describes a flare-screening band above 10 keV and selects MOS events using `PI>10000`, corroborating the same numeric convention.

The parent explicitly accepted this documentary evidence together with the exact-file PI comments and schema. The original three-page search's insufficiency is preserved here as provenance, not as an ongoing unit blocker.

## Prospective selection and remaining limits

For these standard calibrated MOS event products, use the documented convention `E_eV = PI`: one numerical PI increment corresponds to 1 eV, with no additional channel offset applied by the energy selection. This is an operational calibrated-PI convention, not a claim that one eV is the detector's energy resolution or a statement about raw PHA gain. Do not introduce the 5 eV or other bin widths used for grouped spectra/response files.

Under that convention, the draft's strict `200 < PI < 12000` interval corresponds numerically to 0.2–12 keV. The official inclusive interval demonstrates units; it does not silently replace the draft's strict endpoint rule. Keep that endpoint convention explicit in the eventual frozen science protocol. No selection was executed or draft edited here.

The unity convention does not independently establish correctness of this observation's gain/CTI calibration, current calibration currency, event quality, GTIs, or scientific control recovery. No actual photon-energy distribution was inspected. Future code should bind the actual PI column/instrument/processing schema and stop on an incompatible product instead of applying a universal conversion to arbitrary `CHAN` columns.
