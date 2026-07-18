# DATA SOURCES

Exact endpoints, auth, rate limits, formats, and minimal Python access snippets for every
external feed the broker consumes. Verified via web research, June 2026. Where a value could
drift, the "last verified" note says so — re-check before relying on it in production.

Summary table:

| Source | What | Endpoint / host | Auth | Rate limit | Format |
|---|---|---|---|---|---|
| **Transients CSV** (live input) | Externally-exported alert list (any broker / your own) | local file, `--transients-csv` | **None** | n/a | CSV |
| Gaia DR3 (distance layer) | Parallax, pmRA/Dec, RUWE, zero-point inputs | `astroquery.gaia` TAP (gea.esac.esa.int) | **Anonymous** | async results kept 3 days; ≤5000 ids/batch | VOTable/table |
| Gaia DR3 zero-point (§2a) | −17 µas parallax bias correction | `gaiadr3-zeropoint` pkg (offline tables) | None | n/a | coeff tables |
| Lasair ZTF (auto-ingest, stub) | ZTF transient alerts | `https://lasair-ztf.lsst.ac.uk/api/` | Token — **account-gated** (§0) | reg 100/hr · power 10k/hr | JSON |
| ASAS-SN Sky Patrol V2 (M2) | Optical light curves, ~111M targets | `pyasassn.client.SkyPatrolClient()` | None | bandwidth-bound; ≤1M curves/pull | pandas/Parquet |
| CHIME/FRB (M2/M3) | Real-time FRB VOEvents (RA, Dec, DM) | `chimefrb.physics.mcgill.ca:8099` via Comet | Free subscription + static public IP | ~2 events/day | VOEvent XML |

---

## 0. Account situation & the account-free live path (READ FIRST)

**Lasair auto-ingest is account-gated and effectively unavailable to most users.** Lasair-ZTF
accounts do **not** transfer to the Rubin era: new registration has moved to the Rubin/LSST
instance (`lasair-lsst.lsst.ac.uk`) and the ZTF instance (`lasair-ztf.lsst.ac.uk`) is winding
down. The previously-documented free *shared* token (10 calls/hr) is no longer published, and
tokens must not be shared. In practice you cannot rely on obtaining a working `LASAIR_TOKEN`,
so the `ingest/lasair.py` auto-ingest path (and `seti-broker run --live`) stays a stub and
`--live` exits 2.

**Use the account-free live path instead.** Everything the broker needs downstream of the alert
list is account-free: Gaia DR3 is queryable **anonymously** over TAP (§2), and the parallax
zero-point correction (§2a) uses only public coefficient tables. So export an alert list from
**any** broker (Lasair web UI, Fink, ALeRCE, ANTARES, TNS) or hand-build your own, and feed it in:

```bash
seti-broker run --transients-csv your_alerts.csv     # no token, no account
```

CSV columns: `name,ra,dec` required; `gaia_source_id,mjd/discovery_date,survey,mag` optional
(schema + aliases in `src/seti_ellipsoid_broker/ingest/transients.py`; example in
`examples/transients_example.csv`). The pipeline then runs CSV → anonymous Gaia crossmatch +
zero-point → ellipsoid → rank → export with **no credentials**.

---

## 1. Lasair ZTF REST API (account-gated auto-ingest — stub; prefer §0's CSV path)

- **Base URL:** `https://lasair-ztf.lsst.ac.uk/api/`
  (There is also a Rubin/LSST instance at `https://lasair-lsst.lsst.ac.uk/` where registration
  now lives. Neither auto-ingest path is wired up; both are account-gated — see §0.)
- **Auth:** per-account token.
  - GET: token passed as a query-string parameter (`token=...`).
  - POST: token in header `Authorization: Token <token>`.
  - Get a token from your Lasair account profile page after registering
    (register at `https://lasair-ztf.lsst.ac.uk/register/` → log in → your name, top
    right → "My Profile"). Support: `lasair-help@lists.roe.ac.uk`.
  - **Do not commit tokens.** Read from `LASAIR_TOKEN` env var (see `.gitignore` / settings).
- **Rate limits / row caps** (last verified July 2026):
  - Registered token: **100 calls/hour**, max **10,000 rows/query**.
  - Power user (email lasair-help with use case): **10,000 calls/hour**, max **1,000,000 rows/query**.
  - (A free *shared* token at 10 calls/hour was documented in June 2026 but is no longer
    published; docs now say tokens must not be shared.)
- **Key endpoints:**
  - `POST /api/cone/` — cone search. Params: `ra`, `dec`, `radius` (arcsec, max 1000),
    `requestType` ∈ {`nearest`, `all`, `count`}.
  - `POST /api/query/` — ADQL/SQL `SELECT`. Params: `selected`, `tables`, `conditions`,
    optional `limit`, `offset`. Pagination via `limit`+`offset` (watch for off-by-one at the
    last page — dossier flagged this).
- **Format:** JSON list of objects. ZTF object fields include `objectId`, `ramean`, `decmean`,
  `gmag`/`rmag`, discovery/last-detection MJD, and (where present) Gaia crossmatch columns.
  Note: the Gaia crossmatch in the alert schema does **not** carry a usable distance for the full
  catalog — this is the documented blocker and the reason we run our own Gaia TAP layer.
- **Python access** (official `lasair` client; `pip install lasair`):

```python
import os
from lasair import lasair_client

L = lasair_client(os.environ["LASAIR_TOKEN"], endpoint="https://lasair-ztf.lsst.ac.uk/api")

# Cone search: nearest object within 5 arcsec of a position
hits = L.cone(ra=83.8, dec=-69.3, radius=5.0, requestType="all")

# SQL query: recent bright transients
rows = L.query(
    selected="objects.objectId, objects.ramean, objects.decmean, objects.gmag",
    tables="objects",
    conditions="objects.gmag < 18.5",
    limit=100,
)
```

(Equivalent raw call with `requests`: POST to `https://lasair-ztf.lsst.ac.uk/api/query/`
with header `Authorization: Token <token>` and the params above as form data.)

---

## 2. Gaia DR3 via `astroquery.gaia` (distance layer — the differentiator)

- **Service:** ESA Gaia TAP+ at `gea.esac.esa.int`, fronted by `astroquery.gaia.Gaia`.
- **Auth:** anonymous works for DR3 `gaia_source`. Logging in
  (`Gaia.login()`) raises async result retention and quotas — optional for v0.
- **Default table:** `gaiadr3.gaia_source` (`Gaia.MAIN_GAIA_TABLE`).
- **Limits / behavior** (last verified June 2026):
  - Async (`launch_job_async`) results retained **3 days** for anonymous users.
  - Batch source-id helpers (e.g. `load_data`) cap at **~5000 source ids** per call.
  - Be polite: one batched ADQL upload-join per night beats thousands of cone queries.
- **Columns we need:** `source_id`, `ra`, `dec`, `parallax`, `parallax_error`,
  `parallax_over_error`, `ruwe`, `pmra`, `pmdec`, `phot_g_mean_mag`, **plus the four parallax
  zero-point inputs** (§2a): `nu_eff_used_in_astrometry`, `pseudocolour`, `ecl_lat`,
  `astrometric_params_solved`. Distance ≈ `1000 / parallax_corrected` pc (parallax in mas),
  where `parallax_corrected` applies the zero-point of §2a **before** the inversion. The
  fetch is implemented in `gaia.py` (`GAIA_COLUMNS`, `crossmatch*`).
- **Quality cuts (carried from Nilipour/Gallay):** `ruwe < 1.4` AND `parallax_over_error > 5`.
- **Python access:**

```python
from astroquery.gaia import Gaia

Gaia.MAIN_GAIA_TABLE = "gaiadr3.gaia_source"
Gaia.ROW_LIMIT = -1  # unlimited (async)

adql = """
SELECT TOP 50 source_id, ra, dec, parallax, parallax_over_error, ruwe,
       pmra, pmdec, phot_g_mean_mag
FROM gaiadr3.gaia_source
WHERE CONTAINS(POINT('ICRS', ra, dec),
               CIRCLE('ICRS', 83.8, -69.3, 0.0014)) = 1   -- ~5 arcsec
  AND ruwe < 1.4 AND parallax_over_error > 5
"""
job = Gaia.launch_job_async(adql)
table = job.get_results()   # astropy Table
```

For the real pipeline: build one ADQL with an uploaded VOTable of all nightly alert positions
and a single `JOIN ... ON 1=CONTAINS(...)` crossmatch instead of per-row cone queries.

---

## 2a. Gaia DR3 parallax zero-point correction (mandatory, account-free)

Gaia DR3 parallaxes carry a systematic **zero-point offset** (global mean ≈ **−17 µas**;
parallaxes biased *too small* → stars look *too far*) that depends on magnitude, colour, and
ecliptic latitude. At the few-hundred-pc–few-kpc distances that dominate the SN 1987A ellipsoid
crossings, that offset shifts the inferred crossing epoch by **~0.7–4.5 yr — larger than the
±1–1.6 yr statistical windows** the pipeline reports. It must be removed **before** the
`1000/parallax` inversion. Implemented in `zeropoint.py`; applied in `pipeline.gaia_fields_from_source`;
escape hatch `seti-broker run --no-zeropoint` (diagnostics only).

- **Method / reference:** Lindegren, L., et al. 2021, *"Gaia EDR3: Parallax bias versus
  magnitude, colour, and position"*, A&A 649, A4 (DOI 10.1051/0004-6361/202039653). We use the
  authors' official reference implementation, the **`gaiadr3-zeropoint`** package
  (`pip install gaiadr3-zeropoint`; import name `zero_point`), evaluated as:

  ```python
  from zero_point import zpt
  zpt.load_tables()
  corrected = parallax - zpt.get_zpt(phot_g_mean_mag, nu_eff_used_in_astrometry,
                                     pseudocolour, ecl_lat, astrometric_params_solved)
  ```

  (Under numpy≥2 the package's scalar path trips NEP-50; `zeropoint.py` passes numpy arrays,
  which sidesteps it. The offset `Z` is usually negative, so `corrected` is slightly *larger*.)
- **Required Gaia input columns (all in `gaiadr3.gaia_source`, all account-free):**
  `phot_g_mean_mag`, `nu_eff_used_in_astrometry` (5-parameter solutions),
  `pseudocolour` (6-parameter solutions), `ecl_lat`, and `astrometric_params_solved`
  (3 = 2p → uncorrectable, 31 = 5p, 95 = 6p).
- **Validity domain (Lindegren 2021):** `6 < G < 21`, `1.1 < nu_eff < 1.9`,
  `1.24 < pseudocolour < 1.72`. Outside it the correction is undefined → we return NaN and fall
  back to the uncorrected parallax (never invent a correction). 2-parameter solutions have no
  defined zero-point and are likewise left uncorrected.
- Distances remain simple (corrected) parallax inversions; full Bailer-Jones geometric-distance
  posteriors are a further M2+ refinement.

---

## 3. ASAS-SN Sky Patrol V2 (added in M2 — optical light-curve corroboration)

- **Client:** `pyasassn` (the `SkyPatrolClient`). Install from the repo:
  `git clone https://github.com/asas-sn/skypatrol.git && pip3 install skypatrol/`.
- **Auth:** **none** — public read.
- **Server host:** the client targets the ASAS-SN Sky Patrol API host internally
  (`asas-sn.ifa.hawaii.edu`); you do not pass a URL.
- **Coverage / limits:** ~111M targets, pre-crossmatched (GaiaDR2, ATLAS Refcat2, SDSS,
  AllWISE, TIC v8); photometry typically served within ~1 hour of observation; a single pull
  can return up to ~1M light curves, bandwidth-bound.
- **Format:** returns pandas DataFrames / `LightCurveCollection`; bulk export to Parquet.
- **Python access:**

```python
from pyasassn.client import SkyPatrolClient

client = SkyPatrolClient()
print(client.catalogs)                       # list input catalogs

# Cone search returning light curves near SN 1987A field
lcs = client.cone_search(
    ra_deg=83.8, dec_deg=-69.3, radius=0.5,   # degrees
    catalog="stellar_main", download=True,
)
# or ADQL against the input catalogs:
df = client.adql_query(
    "SELECT asas_sn_id, ra_deg, dec_deg FROM stellar_main "
    "WHERE g_mag < 14 AND dec_deg < -60"
)
```

Role in pipeline: secondary corroboration of ZTF alerts (variability sanity-check), **not** the
primary alert trigger.

---

## 4. CHIME/FRB VOEvent stream (added in M2/M3 — radio FRB events)

- **Subscribe host/port:** `chimefrb.physics.mcgill.ca`, **port 8099** (VOEvent transport).
- **Mechanism:** run a VOEvent broker (`comet`) subscribed to the CHIME remote:
  - `twistd -n comet --remote=chimefrb.physics.mcgill.ca:8099 --verbose --print-event`
    (older Comet: `--subscribe=chimefrb.physics.mcgill.ca`).
- **Auth / prerequisites:** a **free subscription** must be requested via the CHIME/FRB form;
  the subscribing machine needs a **static, publicly reachable IP** (no NAT/firewall) that
  **exactly matches** the address given on the form; allow **~3 working days** to be activated.
  → This is why CHIME is M2/M3, not v0: it needs hosting + an allowlisted IP, not a laptop.
- **Rate:** ~**2 detections/day** broadcast since Oct 2021.
- **Format:** VOEvent XML. Payload carries sky position (RA, Dec, with error) and dispersion
  measure (DM), event timestamp, and IVORN. Parse with `voevent-parse`:

```python
import voeventparse as vp

with open("chime_event.xml", "rb") as f:
    v = vp.load(f)
pos = vp.get_event_position(v)        # ra, dec, err, system
toa = vp.get_event_time_as_utc(v)
# DM lives in a What/Param; pull by name:
params = vp.get_grouped_params(v)
```

DM→distance for the ellipsoid consistency check uses the Macquart relation (speculative,
flagged in the dossier; M3 stretch).

---

## 5. SN 1987A SETI Ellipsoid geometry (the science core)

The SETI Ellipsoid (Davenport 2022; Nilipour et al. 2023) has its two **foci at Earth and at the
source event** (SN 1987A). A target star lies on the *current* ellipsoid when light/signal
re-broadcast from that star, triggered by its view of SN 1987A, would reach Earth **now**.

Defining quantities:

- `d` = distance Earth → SN 1987A ≈ **51.4 kpc ≈ 168,000 ly** (the inter-foci baseline `2C`,
  so `C = d/2`).
- `T` = time elapsed since Earth *observed* SN 1987A, in years; reference epoch
  **1987-02-23** (observed). `cT` = that elapsed time expressed as a light-travel distance.
- **Semi-major axis:** `A = (d + cT) / 2 = C + cT/2`. It grows at **c/2** (half a light-year of
  semi-major axis per calendar year). Ellipsoid surface: `d1 + d2 = 2A = d + cT`, where
  `d1` = Earth→target, `d2` = SN1987A→target.

Crossing test for a Gaia star at geocentric distance `r_E` and angular separation `θ` from
SN 1987A (so its distance from the SN by law of cosines is
`d2 = sqrt(r_E^2 + d^2 - 2*r_E*d*cos θ)`):

- Compute `S(t) = (r_E + d2) - (d + c·t)`. The star is **on the shell** when `S = 0`.
- The **crossing epoch** is `t_cross` solving `r_E + d2 = d + c·t_cross`. Because the RHS grows
  at `c`, the crossing date is essentially set by the star's fixed geometry; the broker reports
  `t_cross` and flags stars whose **uncertainty window** (propagated from parallax error) is
  **< 2 yr** around "now".
- **Crossing rate peaks ~2026–2028** and falls off after ~2030 (Nilipour Fig. 4) → the natural
  sunset noted in `SPEC.md`.

Constants are centralized in code at `src/seti_ellipsoid_broker/ellipsoid.py`
(`SN1987A_RA_DEG`, `SN1987A_DEC_DEG`, `SN1987A_DISTANCE_KPC = 51.4`,
`REFERENCE_EPOCH = "1987-02-23"`).
