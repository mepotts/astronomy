# DATA SOURCES

Exact endpoints, auth, rate limits, formats, and minimal Python access snippets for every
external feed the broker consumes. Verified via web research, June 2026. Where a value could
drift, the "last verified" note says so — re-check before relying on it in production.

Summary table:

| Source | What | Endpoint / host | Auth | Rate limit | Format |
|---|---|---|---|---|---|
| Lasair ZTF | ZTF transient alerts + Gaia crossmatch | `https://lasair-ztf.lsst.ac.uk/api/` | Token | reg 100/hr · power 10k/hr | JSON |
| Gaia DR3 | Parallax, pmRA/Dec, RUWE | `astroquery.gaia` TAP (gea.esac.esa.int) | Anonymous (or login) | async results kept 3 days; ≤5000 ids/batch | VOTable/table |
| ASAS-SN Sky Patrol V2 | Optical light curves, ~111M targets | `pyasassn.client.SkyPatrolClient()` | None | bandwidth-bound; ≤1M curves/pull | pandas/Parquet |
| CHIME/FRB | Real-time FRB VOEvents (RA, Dec, DM) | `chimefrb.physics.mcgill.ca:8099` via Comet | Free subscription + static public IP | ~2 events/day | VOEvent XML |

---

## 1. Lasair ZTF REST API (primary source for v0)

- **Base URL:** `https://lasair-ztf.lsst.ac.uk/api/`
  (There is also a Rubin/LSST instance at `https://lasair-lsst.lsst.ac.uk/` — **not** used in v0.)
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
- **Columns we need:** `source_id`, `ra`, `dec`, `parallax`, `parallax_over_error`, `ruwe`,
  `pmra`, `pmdec`, `phot_g_mean_mag`. Distance ≈ `1000 / parallax` pc (parallax in mas);
  for v0 the simple inversion under the quality cuts below is adequate (Bailer-Jones
  geometric distances are an M2+ refinement).
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
