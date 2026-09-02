"""W1 throughput: run the coded Hephaistos II selection on one bounded field
and measure stage counts + wall time -> honest cost estimate for the full
~5M-star screen (the full run itself is W4, NOT this milestone).

Field: RA [140, 150] deg, Dec [0, 10] deg (contains candidate I; high |b|).
Exact area = (ra1-ra0) * (sin dec1 - sin dec0) * 180/pi = 99.48 deg^2.

Stages (paper Table 4 gives the published funnel from ~5e6 -> 7):
  T0  Gaia DR3 x Bailer-Jones EDR3 r_med_geo < 300 pc         (COUNT, server)
  T1  T0 with an AllWISE best-neighbour match                 (COUNT, server)
  T2  T1 with W3 AND W4 measured errors (=detections, snr>2)  (rows pulled)
  local: cc_flags '0000', C3 RMSE<=0.2 grid fit, C5a-C5e, C6 SNR proxy
         snr_i ~= 1.0857 / w_improsigma  (validated vs IRSA w?snr on the 10
         candidates in w1_selection output)

Output: out/w1_throughput.json, stdout log with timings.
"""

from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyvo

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "scripts"))
from w1_selection import fit_ds, load_pm13  # noqa: E402

GAIA_TAP = "https://gea.esac.esa.int/tap-server/tap"
RA0, RA1, DEC0, DEC1 = 140.0, 150.0, 0.0, 10.0
AREA = (RA1 - RA0) * np.degrees(np.sin(np.radians(DEC1)) - np.sin(np.radians(DEC0)))
BOX = f"g.ra BETWEEN {RA0} AND {RA1} AND g.dec BETWEEN {DEC0} AND {DEC1}"
FIELD_CACHE = DATA / "photometry" / "throughput_field.csv"
COUNTS_CACHE = DATA / "photometry" / "throughput_counts.json"


def timed(svc, q, tag, mode="sync"):
    t0 = time.time()
    run = svc.run_async if mode == "async" else svc.search
    r = run(q).to_table().to_pandas()
    dt = time.time() - t0
    print(f"  [{tag}] {dt:.1f} s")
    return r, dt


def fetch(svc) -> tuple[dict, pd.DataFrame]:
    counts, timings = {}, {}

    r, dt = timed(svc, f"""
        SELECT COUNT(*) AS n FROM gaiadr3.gaia_source g
        JOIN external.gaiaedr3_distance d ON d.source_id = g.source_id
        WHERE {BOX} AND d.r_med_geo < 300""", "T0 dist<300pc")
    counts["T0_dist300"] = int(r["n"][0]); timings["T0"] = dt

    r, dt = timed(svc, f"""
        SELECT COUNT(*) AS n FROM gaiadr3.gaia_source g
        JOIN external.gaiaedr3_distance d ON d.source_id = g.source_id
        JOIN gaiadr3.allwise_best_neighbour ab ON ab.source_id = g.source_id
        WHERE {BOX} AND d.r_med_geo < 300""", "T1 +AllWISE")
    counts["T1_allwise"] = int(r["n"][0]); timings["T1"] = dt

    # T2 split into the proven-fast pattern: a 3-table sync pull of the
    # matched stars, then chunked primary-key lookups on the AllWISE and
    # 2MASS-neighbour tables (the 4/5-way join exceeds the sync limit and
    # queues indefinitely on async under load).
    base, dt = timed(svc, f"""
        SELECT g.source_id, g.ra, g.dec, g.ruwe,
               g.phot_g_mean_mag, g.phot_bp_mean_mag, g.phot_rp_mean_mag,
               g.phot_g_mean_flux, g.phot_g_mean_flux_error, g.phot_g_n_obs,
               g.classprob_dsc_combmod_star, d.r_med_geo, ab.allwise_oid
        FROM gaiadr3.gaia_source g
        JOIN external.gaiaedr3_distance d ON d.source_id = g.source_id
        JOIN gaiadr3.allwise_best_neighbour ab ON ab.source_id = g.source_id
        WHERE {BOX} AND d.r_med_geo < 300
        """, "T2a matched-star rows")
    timings["T2a"] = dt

    t0 = time.time()
    oids = base["allwise_oid"].astype("int64").tolist()
    wparts = []
    for i in range(0, len(oids), 500):
        ol = ",".join(str(x) for x in oids[i:i + 500])
        wparts.append(svc.search(f"""
            SELECT allwise_oid, w1mpro, w2mpro, w3mpro, w4mpro,
                   w1mpro_error, w2mpro_error, w3mpro_error, w4mpro_error,
                   cc_flags, ext_flag, ph_qual
            FROM gaiadr1.allwise_original_valid
            WHERE allwise_oid IN ({ol})
              AND w3mpro_error IS NOT NULL AND w4mpro_error IS NOT NULL
            """).to_table().to_pandas())
    wall = pd.concat(wparts, ignore_index=True)
    rows = base.merge(wall, on="allwise_oid", how="inner")
    timings["T2b_allwise_chunks"] = time.time() - t0
    print(f"  [T2b AllWISE chunks] {timings['T2b_allwise_chunks']:.1f} s")
    counts["T2_w34det"] = len(rows)

    t0 = time.time()
    ids2 = rows["source_id"].astype("int64").tolist()
    tparts = []
    for i in range(0, len(ids2), 500):
        il = ",".join(str(x) for x in ids2[i:i + 500])
        tparts.append(svc.search(f"""
            SELECT source_id, original_ext_source_id AS tmass_designation
            FROM gaiadr3.tmass_psc_xsc_best_neighbour
            WHERE source_id IN ({il})""").to_table().to_pandas())
    if tparts:
        rows = rows.merge(pd.concat(tparts, ignore_index=True),
                          on="source_id", how="left")
    timings["T2c_tmassbn_chunks"] = time.time() - t0
    print(f"  [T2c 2MASS-bn chunks] {timings['T2c_tmassbn_chunks']:.1f} s")

    # Halpha pEW by chunked PK lookup (a LEFT JOIN on the 2.4e9-row
    # astrophysical_parameters table times out the sync endpoint)
    t0 = time.time()
    aps = []
    ids = rows["source_id"].astype("int64").tolist()
    for i in range(0, len(ids), 500):
        il = ",".join(str(x) for x in ids[i:i + 500])
        aps.append(svc.search(
            f"""SELECT source_id, ew_espels_halpha, ew_espels_halpha_uncertainty
                FROM gaiadr3.astrophysical_parameters
                WHERE source_id IN ({il})""").to_table().to_pandas())
    if aps:
        rows = rows.merge(pd.concat(aps, ignore_index=True),
                          on="source_id", how="left")
    else:
        rows["ew_espels_halpha"] = np.nan
        rows["ew_espels_halpha_uncertainty"] = np.nan
    timings["T2_halpha"] = time.time() - t0
    print(f"  [T2 Halpha chunks] {timings['T2_halpha']:.1f} s")

    # 2MASS photometry for the pulled rows (chunks of 400 designations)
    desigs = [x for x in rows["tmass_designation"].dropna().astype(str) if x]
    tms = []
    t0 = time.time()
    for i in range(0, len(desigs), 400):
        dl = ",".join(f"'{x}'" for x in desigs[i:i + 400])
        tms.append(svc.search(
            f"""SELECT designation AS tmass_designation, j_m, h_m, ks_m
                FROM gaiadr1.tmass_original_valid
                WHERE designation IN ({dl})""").to_table().to_pandas())
    timings["T2_tmass"] = time.time() - t0
    print(f"  [T2 2MASS chunks] {timings['T2_tmass']:.1f} s")
    if tms:
        rows = rows.merge(pd.concat(tms, ignore_index=True),
                          on="tmass_designation", how="left")
    counts["_timings"] = timings
    return counts, rows


def main() -> None:
    svc = pyvo.dal.TAPService(GAIA_TAP)
    if FIELD_CACHE.exists() and COUNTS_CACHE.exists():
        rows = pd.read_csv(FIELD_CACHE)
        counts = json.loads(COUNTS_CACHE.read_text())
        print("using cached field pull")
    else:
        print(f"field: {AREA:.2f} deg^2 box RA[{RA0},{RA1}] Dec[{DEC0},{DEC1}]")
        counts, rows = fetch(svc)
        rows.to_csv(FIELD_CACHE, index=False)
        COUNTS_CACHE.write_text(json.dumps(counts))

    # ---- local cuts -------------------------------------------------------
    t0 = time.time()
    rows["cc_ok"] = rows["cc_flags"].astype(str).str.strip().isin(["0000", "0"])
    counts["T3_ccflags"] = int(rows["cc_ok"].sum())

    # Gvar: medians per 0.2-mag bin from the field itself
    ref = rows.dropna(subset=["phot_g_mean_flux"])
    bins = np.arange(rows["phot_g_mean_mag"].min() - 0.1,
                     rows["phot_g_mean_mag"].max() + 0.3, 0.2)
    rows["_bin"] = np.digitize(rows["phot_g_mean_mag"], bins)
    med = ref.groupby(np.digitize(ref["phot_g_mean_mag"], bins)).agg(
        fp=("phot_g_mean_flux", "median"),
        ep=("phot_g_mean_flux_error", "median"),
        np_=("phot_g_n_obs", "median")).reset_index(names="_bin")
    rows = rows.merge(med, on="_bin", how="left")
    rows["gvar"] = (rows["fp"] * rows["phot_g_mean_flux_error"]
                    * np.sqrt(rows["phot_g_n_obs"])
                    / (rows["phot_g_mean_flux"] * rows["ep"]
                       * np.sqrt(rows["np_"])))

    halpha_em = (rows["ew_espels_halpha"].notna()
                 & (rows["ew_espels_halpha"] < 0)
                 & (rows["ew_espels_halpha"].abs()
                    >= 3 * rows["ew_espels_halpha_uncertainty"]))
    rows["extra_ok"] = ((~halpha_em) & (rows["gvar"] < 2)
                        & (rows["ruwe"] < 1.4) & (rows["ext_flag"] == 0)
                        & (rows["classprob_dsc_combmod_star"] > 0.9))

    # C6 SNR proxy
    rows["snr3"] = 1.0857 / rows["w3mpro_error"]
    rows["snr4"] = 1.0857 / rows["w4mpro_error"]
    rows["snr_ok"] = (rows["snr3"] >= 3.5) & (rows["snr4"] >= 3.5)

    # C3 RMSE grid fit on all cc-clean rows with full 10-band photometry,
    # in the paper's funnel order (Table 4: RMSE before the extra cuts)
    pm = load_pm13()
    pre = rows[rows["cc_ok"]].copy()
    have_bands = pre.dropna(subset=["phot_bp_mean_mag", "phot_rp_mean_mag",
                                    "j_m", "h_m", "ks_m", "w1mpro", "w2mpro",
                                    "w3mpro", "w4mpro", "r_med_geo"])
    counts["T2_note_full10band"] = len(have_bands)
    t_fit0 = time.time()
    rmse_pass_ids, fitted = [], 0
    for _, r in have_bands.iterrows():
        dmod = 5 * np.log10(r["r_med_geo"] / 10.0)
        obs = {"BP": r["phot_bp_mean_mag"], "G": r["phot_g_mean_mag"],
               "RP": r["phot_rp_mean_mag"], "J": r["j_m"], "H": r["h_m"],
               "Ks": r["ks_m"], "W1": r["w1mpro"], "W2": r["w2mpro"],
               "W3": r["w3mpro"], "W4": r["w4mpro"]}
        obs_abs = {k: v - dmod for k, v in obs.items()}
        if not (6.0 <= obs_abs["G"] <= 14.5):
            continue  # PM13 dwarf-locus validity window used for templates
        fit = fit_ds(obs_abs, pm, 100, 700, 0.10, 0.90, nt=60, ng=30)
        fitted += 1
        if fit["rmse"] <= 0.2:
            rmse_pass_ids.append(int(r["source_id"]))
    fit_dt = time.time() - t_fit0
    counts["_fit_seconds"] = fit_dt
    counts["_fit_n"] = fitted

    surv = have_bands[have_bands["source_id"].isin(rmse_pass_ids)]
    counts["T3_rmse"] = len(surv)                       # paper: 3.2e5 -> 11243
    surv2 = surv[surv["extra_ok"]]
    counts["T4_extra"] = len(surv2)                     # paper: 5732 -> 5137
    final = surv2[surv2["snr_ok"]]
    counts["T5_snr"] = len(final)                       # paper: 5137 -> 368
    counts["_local_seconds"] = time.time() - t0
    counts["_area_deg2"] = AREA

    print(json.dumps({k: v for k, v in counts.items()}, indent=2, default=str))
    if len(final):
        print(final[["source_id", "ra", "dec", "phot_g_mean_mag", "r_med_geo",
                     "snr3", "snr4", "gvar"]].to_string(index=False))

    # ---- extrapolation ----------------------------------------------------
    sky = 41253.0
    scale = sky / AREA
    t_q = sum(v for k, v in counts["_timings"].items()) if isinstance(
        counts.get("_timings"), dict) else 0
    print(f"\nField {AREA:.1f} deg^2: query wall time {t_q:.0f} s, "
          f"local {counts['_local_seconds']:.0f} s "
          f"(of which RMSE grid {fit_dt:.0f} s for {fitted} stars)")
    print(f"Naive full-sky scaling (x{scale:.0f}): "
          f"queries ~{t_q * scale / 3600:.0f} h, local ~"
          f"{counts['_local_seconds'] * scale / 3600:.1f} h "
          f"-- see M1 doc for the honest plan (bulk table download beats "
          f"per-field TAP).")
    OUT.joinpath("w1_throughput.json").write_text(
        json.dumps(counts, indent=2, default=str))


if __name__ == "__main__":
    main()
