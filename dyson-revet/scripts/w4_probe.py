"""W4 probe: can the ESA Gaia TAP do the full parent-sample join server-side?

M1 measured the full screen at 2-4 days assuming 24 async strips on a 3-table
join (~5.3e6 rows) followed by ~10^4 chunked PK lookups for AllWISE/2MASS.
That lookup stage is the dominant cost. This probe tests whether the joins can
be pushed server-side instead, which would delete it:

  J3  gaia_source x gaiaedr3_distance x allwise_best_neighbour      (M1's plan)
  J4  J3 x gaiadr1.allwise_original_valid   (+ W3/W4 detection filter)
  J6  J4 x tmass_psc_xsc_best_neighbour x gaiadr1.tmass_original_valid

Run on one narrow dec strip so the answer is cheap. Output: stdout + timings.
"""

from __future__ import annotations

import sys
import time
import warnings

import pyvo

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

GAIA_TAP = "https://gea.esac.esa.int/tap-server/tap"
D0, D1 = 0.0, 1.0  # a 1-deg dec band, all RA: 720 deg^2


def timed(svc, q, tag, mode="async"):
    t0 = time.time()
    try:
        run = svc.run_async if mode == "async" else svc.search
        r = run(q).to_table().to_pandas()
        dt = time.time() - t0
        print(f"  [{tag}] {dt:6.1f} s  rows={len(r)}  cols={len(r.columns)}")
        return r, dt
    except Exception as e:  # noqa: BLE001
        dt = time.time() - t0
        print(f"  [{tag}] {dt:6.1f} s  FAILED: {type(e).__name__}: {str(e)[:300]}")
        return None, dt


BASE = f"""
FROM gaiadr3.gaia_source g
JOIN external.gaiaedr3_distance d ON d.source_id = g.source_id
JOIN gaiadr3.allwise_best_neighbour ab ON ab.source_id = g.source_id
"""

W_JOIN = "JOIN gaiadr1.allwise_original_valid w ON w.allwise_oid = ab.allwise_oid"
T_JOIN = ("JOIN gaiadr3.tmass_psc_xsc_best_neighbour tb "
          "ON tb.source_id = g.source_id "
          "JOIN gaiadr1.tmass_original_valid t "
          "ON t.designation = tb.original_ext_source_id")
WHERE = f"WHERE g.dec BETWEEN {D0} AND {D1} AND d.r_med_geo < 300"
WDET = "AND w.w3mpro_error IS NOT NULL AND w.w4mpro_error IS NOT NULL"


def main() -> None:
    svc = pyvo.dal.TAPService(GAIA_TAP)
    print(f"probe strip dec [{D0},{D1}] (~720 deg^2)")

    timed(svc, f"SELECT COUNT(*) AS n {BASE} {WHERE}", "T1 count (3-table)")
    timed(svc, f"SELECT COUNT(*) AS n {BASE} {W_JOIN} {WHERE} {WDET}",
          "T2 count (4-table +W34det)")
    timed(svc, f"SELECT COUNT(*) AS n {BASE} {W_JOIN} {T_JOIN} {WHERE} {WDET}",
          "T2b count (6-table +2MASS)")

    cols = """g.source_id, g.ra, g.dec, g.ruwe, g.phot_g_mean_mag,
        g.phot_bp_mean_mag, g.phot_rp_mean_mag, g.phot_g_mean_flux,
        g.phot_g_mean_flux_error, g.phot_g_n_obs,
        g.classprob_dsc_combmod_star, d.r_med_geo, ab.allwise_oid,
        w.w1mpro, w.w2mpro, w.w3mpro, w.w4mpro, w.w1mpro_error,
        w.w2mpro_error, w.w3mpro_error, w.w4mpro_error, w.cc_flags,
        w.ext_flag, w.ph_qual, t.designation AS tmass_designation,
        t.j_m, t.h_m, t.ks_m"""
    r, _ = timed(svc, f"SELECT {cols} {BASE} {W_JOIN} {T_JOIN} {WHERE} {WDET}",
                 "T2b ROWS (6-table pull)")
    if r is not None and len(r):
        print(r.head(3).to_string())


if __name__ == "__main__":
    main()
