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
