#!/usr/bin/env python
"""W1: single-star astrometric fits on the Gaia DR4 pre-release epoch astrometry.

Runs ESA's official `gaiasupdate` package (the "source update" = the same
single-star model as the DR4 core astrometric solution) on every source in the
June 2026 pre-release sample, mirroring the official tutorial notebook
  https://github.com/esa/gaia-jupyter-notebooks/tree/main/data-release-4-tutorials
  (Gaia-DR4-prerelease_analyse_epoch_astrometry.ipynb)

Inputs  : data/epoch-astrometry/GAIA_DR4_PRERELEASE_EPOCH_ASTROMETRY_RAW.xml
          (from https://anonftp.cosmos.esa.int/pub/GAIA_PUBLIC_DATA/Gaia_DR4/dr4-prerelease/
           gaia-dr4-prerelease-epoch-astrometry_2026-06-26.zip)
Outputs : out/supdate_results.csv        - one row per source, fitted parameters
          out/source_inventory.csv       - per-source transit counts / G mag
          out/supdate_<source_id>.png    - diagnostic plot for the worst-fit source

Run     : .venv/Scripts/python.exe scripts/fit_prerelease_single_star.py
"""

import logging
import os
import sys

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from astropy.table import Table

from gaiasupdate.epoch_astrometry import GaiaEpochAstrometryArchive

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XML = os.path.join(
    BASE, "data", "epoch-astrometry", "GAIA_DR4_PRERELEASE_EPOCH_ASTROMETRY_RAW.xml"
)
OUT = os.path.join(BASE, "out")
os.makedirs(OUT, exist_ok=True)

PARAM_NAMES = [
    "deltaAlphaStar_mas",
    "deltaDelta_mas",
    "varpi_mas",
    "muAlphaStar_maspyr",
    "muDelta_maspyr",
    "pseudoColor_offset",
]


def map_results(source_id, supdate):
    """Flatten one supdate result dict into a row (adapted from the ESA tutorial)."""
    row = {"source_id": source_id}
    row["model"] = supdate["model"]
    row["success"] = int(not np.isnan(supdate["parameters"][2]))
    row["excessNoise_mas"] = supdate["excess_noise"]
    row["excessNoiseSig"] = supdate["significance"]
    stat = supdate["solution_statistic"]
    for k in ("f2", "chi2", "n_measurements", "n_outliers"):
        row[k] = getattr(stat, k)
    for i, name in enumerate(PARAM_NAMES):
        row[name] = supdate["parameters"][i]
        row[name + "_err"] = supdate["parameters_formal_uncertainty"][i]
    return row


def main():
    log.info("Reading %s", XML)
    table = Table.read(XML, format="votable")
    df = table.to_pandas()
    source_ids = df["source_id"].unique()
    log.info("File contains %d transit rows for %d unique sources", len(df), len(source_ids))

    # per-source inventory
    inv = (
        df.groupby("source_id")
        .agg(
            n_transits=("transit_id", "nunique"),
            ra0_deg=("ra0", "first"),
            dec0_deg=("dec0", "first"),
            g_mag_median=("g_mag", lambda v: float(np.nanmedian([np.nanmedian(x) for x in v]))),
        )
        .reset_index()
    )
    inv.to_csv(os.path.join(OUT, "source_inventory.csv"), index=False)

    rows = []
    fitted = {}
    for sid in source_ids:
        log.info("supdate on source_id=%d", sid)
        try:
            res = fitted[sid] = GaiaEpochAstrometryArchive.supdate(df, sid)
            rows.append(map_results(sid, res))
        except Exception as exc:  # document failures, never hide them
            log.error("supdate FAILED on %d: %r", sid, exc)
            rows.append({"source_id": sid, "model": "FAILED", "success": 0, "error": repr(exc)})

    out = pd.DataFrame(rows)
    csv_path = os.path.join(OUT, "supdate_results.csv")
    out.to_csv(csv_path, index=False)
    log.info("Wrote %s", csv_path)
    with pd.option_context("display.width", 200, "display.max_columns", 50):
        print(out[["source_id", "model", "success", "varpi_mas", "varpi_mas_err",
                   "muAlphaStar_maspyr", "muDelta_maspyr", "excessNoise_mas", "f2",
                   "n_measurements", "n_outliers"]].to_string(index=False))

    # ---- diagnostic plot: per-CCD along-scan abscissa + single-star residual proxy
    # for the worst-fitting source by f2 (gaiasupdate 0.1.2 returns excess_noise=None,
    # so the goodness-of-fit statistic f2 is the usable badness ranking; the
    # orbit-category source should win)
    ok = out[out["success"] == 1].copy()
    ok["f2"] = pd.to_numeric(ok["f2"], errors="coerce")
    worst = ok.loc[ok["f2"].idxmax()]
    sid = int(worst["source_id"])
    log.info("Diagnostic plot for source_id=%d (largest f2 %.1f)", sid, worst["f2"])

    ea = GaiaEpochAstrometryArchive.from_dataframe(df[df["source_id"] == sid])
    ea.epoch_data = ea.epoch_data.epochastrometryarchive.filter_on_used_by_agis()
    ea.epoch_data.epochastrometryarchive.sort_by_column("obs_time_tcb")
    ea.epoch_data.epochastrometryarchive.set_relative_time()
    ea.epoch_data = ea.epoch_data.epochastrometryarchive.set_scan_angle_derived_columns()
    d = ea.epoch_data

    fig, axes = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    axes[0].errorbar(d["relative_time_year"], d["centroid_pos_al"],
                     yerr=d["centroid_pos_error_al"], fmt=".", ms=3, ecolor="0.8", color="k")
    axes[0].set_ylabel("AL abscissa (mas)")
    axes[0].set_title(f"Gaia DR4 pre-release epoch astrometry, source_id {sid}\n"
                      f"single-star fit f2 = {worst['f2']:.1f}, "
                      f"parallax {worst['varpi_mas']:.3f} mas")
    # parallax+PM-only expectation removed: show scan-angle folded view instead
    axes[1].scatter(d["relative_time_year"], d["scan_pos_angle"], s=4, c="tab:blue")
    axes[1].set_ylabel("scan position angle (deg)")
    axes[1].set_xlabel("time since J2017.5 TCB (yr)")
    fig.tight_layout()
    png = os.path.join(OUT, f"supdate_{sid}.png")
    fig.savefig(png, dpi=120)
    log.info("Wrote %s", png)


if __name__ == "__main__":
    sys.exit(main())
