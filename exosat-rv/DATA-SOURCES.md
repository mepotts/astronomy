# DATA SOURCES

Every endpoint below is anonymous-access. No credentials exist anywhere in this repository.

---

## ESO Science Archive — TAP

`https://archive.eso.org/tap_obs`

Two tables, and the difference between them is the whole of M0.

### `dbo.raw` — one row per raw frame

What the telescope took. Columns used: `object`, `ra`, `dec`, `date_obs`, `prog_id`,
`filter_path`, `release_date`, `instrument`, `dp_cat`, `dp_tech`.

`filter_path` is `<setting>,<band group>` — e.g. `H,HK`, `HX5E-2,HK`, `K,HK`, `J,YJ`.
The setting before the comma is what selects the paper's H-band configuration.

**Three ADQL traps, each of which cost a failed query:**

1. `CONTAINS(POINT('ICRS', ra, dec), CIRCLE(...))` **fails on this table** with a SQL-Server
   geography error (`Latitude values must be between -90 and 90 degrees`) — some rows hold
   coordinates that do not validate. Use a plain `ra`/`dec` box; it also runs faster.
2. `ORDER BY MIN(col)` is rejected: `MIN` is a reserved ADQL word in that position. Sort
   client-side.
3. There is no `exptime` and no `tel_ambi_fwhm`. The exposure column is `exp_start`.

**`filter_path` is not fully reliable.** M2 cross-checked all 18 reduced products against the
raw table and found **1 mismatch in 18**: the two frames of 2024-01-03 are labelled
`K,HK` in `dbo.raw`, but the ADP product built from exactly those frames (its `PROV1`/`PROV2`
name them) carries `HIERARCH ESO INS WLEN ID = H1567`, `CWLEN = 1567.099 nm`, and spans
1468.9–1779.9 nm. It is an H-band observation.

**The product header is authoritative; `filter_path` is a hint.** Any band-based count taken
from `dbo.raw` alone is therefore approximate — see M0-RESULTS §1 for the count this
corrected.

### `ivoa.ObsCore` — one row per product

`calib_level = 2` is a **pipeline-reduced 1-D spectrum**. These are what let this project
skip esorex for 17 of 20 epochs. Columns used: `target_name`, `t_min` (MJD),
`obs_release_date`, `em_min`/`em_max` (metres), `access_url`, `access_estsize`,
`obs_collection` (`CRIRESplus`).

Coordinate columns are `s_ra`/`s_dec`, **not** `ra`/`dec`.

`access_estsize` returned 0 for every CRIRES+ product queried in M0. Download size is
therefore unknown until M1 actually fetches one; do not plan around that column.

ObsCore carries no `filter_path`, so a reduced product's setting is recovered by joining on
night against `dbo.raw`. A reduced night with no raw counterpart keeps `?` and is excluded
from every band selection — deliberately conservative.

### Release dates

Per-frame, ISO with a trailing `Z`. A night is treated as public if its **earliest** frame
release date has passed: if any frame is out, the night has usable data. Taking the latest
would silently hide partially released nights.

---

## NASA Exoplanet Archive — TAP

`https://exoplanetarchive.ipac.caltech.edu/TAP`, table `pscomppars`,
`discoverymethod = 'Imaging'` → 98 companions.

**Known incompleteness that shapes M5: the table caps companion mass at 30 M_Jup, so
CD-35 2722 B (~37 M_Jup) is not in it.** A target list built from this source alone would
exclude the very object being reproduced, and would systematically miss the most favourable
class of host — brown dwarf companions wide enough to put in a slit. M5 must supplement it
from the direct-imaging literature (e.g. VizieR catalogues of substellar companions).

Second caveat: `sy_hmag` is the **system** H magnitude, dominated by the primary. It is not
the companion's brightness and must not be used for the flux cut. Companion photometry has
to come from SIMBAD or the discovery papers, and SIMBAD resolves it for only some
companions — of 17 tried in M0 scoping, 6 returned H magnitudes.

---

## ESO Science Archive — VLTI/GRAVITY (M10)

Same TAP endpoint, different instrument. Two facts worth recording:

- `dbo.raw` rows use `instrument='GRAVITY'` and `dp_cat='SCIENCE'`; calibrations (`FLAT`,
  `DARK`) dominate the table and must be filtered out or counts are meaningless.
- `ivoa.ObsCore` serves reduced products as **`dataproduct_type='visibility'`**, not
  `spectrum`, with `calib_level=2`. Query on `instrument_name LIKE 'GRAVITY%'`.

Holdings measured 2026-08-10: beta Pic b **322 products / 28 nights / 2987 d**,
HD 206893 B 234 / 22 / 2153 d, AF Lep b 34 / 6 / 711 d.

**Whether those visibility products carry the dual-field differential phase that companion
astrometry is extracted from is UNVERIFIED.** Existence is not usability — M1 learned that
the hard way for CRIRES+. See [`M10-RESULTS.md`](M10-RESULTS.md) §5.

## NASA Exoplanet Archive — young close-in planets (M8)

`pscomppars` filtered on `st_age < 0.2` (Gyr), `pl_orbsmax < 2.0`, and a giant-ish cut
`(pl_bmassj > 0.05 OR pl_radj > 0.4)` returns ~32 rows. Caveats that bite:

- **Most masses come from mass–radius relations, not measurements**, and M8's survival
  window depends on both M_p and R_p.
- `st_age` is the *host* age and is often poorly constrained for young stars.
- The 30 M_Jup companion-mass cap that excludes CD-35 2722 B (see below) does not bite here,
  since M8 targets are all well under it.

## SIMBAD

Via `astroquery.simbad`, for target coordinates, parallaxes, and such companion photometry
as exists. Note `plx` is deprecated in favour of `plx_value`.

---

## The paper itself

[arXiv:2607.05193](https://arxiv.org/abs/2607.05193). The **v1 abstract** was read directly
and is the source for both satellite masses and periods. The **body was not** — the PDF did
not extract through M0's fetch path (`pdftoppm` missing locally; compressed content
streams). Everything taken from the body is an AI summary, tagged `[SUMM]` in `config.py`,
and M0 proved at least one such value wrong. Reading the PDF properly (poppler under WSL)
is an M1 task and a prerequisite for M3.
