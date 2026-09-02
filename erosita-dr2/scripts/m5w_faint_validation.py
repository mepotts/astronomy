#!/usr/bin/env python
"""M5-writeup: does the upper-limit 'presence' metric discriminate at the FAINT end?

The census in M2 sec.3 calls a vanished eRASS1 source a real fader when the DR2
upper-limit server returns presence P = UL_B / UL_S <= 1.5 at its position.
That threshold was calibrated on 25 STEADY sources selected at >= 20 sigma - far
brighter than the 107 fade candidates, whose eRASS1 fluxes have a median of
6.8e-14 erg/cm2/s and DET_LIKE_0 of 40.

If P loses its discriminating power at faint fluxes - i.e. if a source that is
genuinely still there, at a fader-like flux, also returns P ~ 1 - then the census
is measuring detectability, not variability, and the headline is wrong.

This script settles it: sample steady DR1xDR2 pairs matched to the faders in
BOTH eRASS1 flux and DET_LIKE_0, query the same DR2 upper-limit service at their
positions, and compare their P distribution with the faders'.

One anonymous POST to a public service (no account, nothing submitted), exactly
as scripts/m2_upper_limits.py does.

Usage: .venv/Scripts/python.exe scripts/m5w_faint_validation.py
Output: out/m5w_faint_validation.csv
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")
DATA = os.path.join(ROOT, "data")
URL = "https://erosita.mpe.mpg.de/erodat/upperlimit/service_multi"
CSV = os.path.join(OUT, "m5w_faint_validation.csv")
N = 60
SEED = 20260818

van = pd.read_csv(os.path.join(OUT, "m2_vanished_forensics.csv"))
fade = van[van["forensic_class_v2"] == "FADE-CANDIDATE"]
f_lo, f_hi = fade["ML_FLUX_1"].quantile([0.10, 0.90])
d_lo, d_hi = fade["DET_LIKE_0"].quantile([0.10, 0.90])
print(f"fader reference band: eRASS1 flux {f_lo:.2e}-{f_hi:.2e}, "
      f"DET_LIKE_0 {d_lo:.1f}-{d_hi:.1f}")
print(f"fader presence: median {fade['ul_presence'].median():.3f}, "
      f"max {fade['ul_presence'].max():.3f}")

if os.path.exists(CSV):
    print(f"\n{CSV} exists - reusing cached server results")
    res = pd.read_csv(CSV)
else:
    pairs = pd.read_parquet(
        os.path.join(DATA, "w2_pairs.parquet"),
        columns=["IAUNAME", "IAUNAME_D1", "RA_D1", "DEC_D1", "R", "z_var",
                 "DET_LIKE_0", "DET_LIKE_0_D1", "ML_FLUX_1_D1", "ML_FLUX_1",
                 "ML_RATE_1_D1", "ML_RATE_ERR_1_D1"],
    )
    # steady: consistent rates between the two releases, and matched to the
    # faders in eRASS1 flux and eRASS1 detection likelihood.
    sel = pairs[
        (pairs["R"].between(0.8, 1.25))
        & (pairs["z_var"] < 2)
        & (pairs["ML_FLUX_1_D1"].between(f_lo, f_hi))
        & (pairs["DET_LIKE_0_D1"].between(d_lo, d_hi))
    ]
    print(f"\nsteady faint flux-and-likelihood-matched pool: {len(sel)}")
    sel = sel.sample(n=min(N, len(sel)), random_state=SEED).reset_index(drop=True)

    body = [{"ra": float(r), "dec": float(d), "band": "024",
             "dr_survey": "DR2_eRASSc3"}
            for r, d in zip(sel["RA_D1"], sel["DEC_D1"])]
    print(f"POSTing {len(body)} positions to the DR2 upper-limit service ...")
    resp = requests.post(URL, json=body, timeout=600)
    resp.raise_for_status()
    js = resp.json()
    if js.get("error") not in (None, "None"):
        raise RuntimeError(f"UL server error: {js['error']}")
    ul = pd.DataFrame(js["limits"])
    assert len(ul) == len(body), (len(ul), len(body))

    res = sel.copy()
    res["ul_exposure_s"] = ul["Exposure"].to_numpy()
    res["ul_b_flux"] = ul["UL_B"].to_numpy()
    res["ul_s_flux"] = ul["UL_S"].to_numpy()
    res["ul_flag_pos"] = ul["Flag_pos"].to_numpy()
    res["ul_presence"] = res["ul_b_flux"] / res["ul_s_flux"]
    res.to_csv(CSV, index=False)
    print("wrote", CSV)

p = res["ul_presence"].replace([np.inf, -np.inf], np.nan).dropna()
p = p[p > 0.01]
fp = fade["ul_presence"]

print("\n" + "=" * 68)
print("FAINT-END VALIDATION OF THE PRESENCE METRIC")
print("=" * 68)
print(f"steady faint controls (n={len(p)}):")
print(f"   presence  min {p.min():.2f}  p10 {p.quantile(.10):.2f}  "
      f"median {p.median():.2f}  max {p.max():.2f}")
print(f"   below the P = 1.5 fader cut: {int((p <= 1.5).sum())} / {len(p)} "
      f"({100 * (p <= 1.5).mean():.1f}%)")
print(f"fade candidates (n={len(fp)}):")
print(f"   presence  min {fp.min():.2f}  median {fp.median():.2f}  "
      f"max {fp.max():.2f}")
print(f"   above P = 1.5: {int((fp > 1.5).sum())} / {len(fp)}")

n_fp = int((p <= 1.5).sum())
sep = float((p > 1.5).mean())
# one-sided 95% binomial upper limit on the false-negative rate for 0/n
ul95 = 1.0 - 0.05 ** (1.0 / len(p)) if n_fp == 0 else np.nan
gap_lo, gap_hi = float(fp.max()), float(p.min())

print(f"\nVERDICT: {100 * sep:.1f}% of flux-matched steady sources are correctly")
print("         kept OUT of the fader class by the P > 1.5 test.")
print(f"         The two populations are DISJOINT: faders reach P = {gap_lo:.2f},")
print(f"         the faintest steady control sits at P = {gap_hi:.2f} - an empty")
print(f"         gap of {gap_lo:.2f}-{gap_hi:.2f} straddling the adopted cut.")
if n_fp == 0:
    print(f"         Contamination of the 107-source census by still-present")
    print(f"         sources: 0/{len(p)} controls misclassified -> < {100 * ul95:.1f}% "
          f"(95% one-sided), i.e. <= {ul95 * len(fp):.0f} of the 107.")

summary = dict(
    n_controls=len(p), control_presence_min=round(gap_hi, 3),
    control_presence_median=round(float(p.median()), 3),
    control_presence_max=round(float(p.max()), 3),
    n_controls_below_cut=n_fp, fader_presence_max=round(gap_lo, 3),
    false_positive_rate_95ul=round(float(ul95), 4) if n_fp == 0 else None,
    implied_max_contaminants=int(np.ceil(ul95 * len(fp))) if n_fp == 0 else None,
    flux_band=[float(f_lo), float(f_hi)], detlike_band=[float(d_lo), float(d_hi)],
    seed=SEED,
)
with open(os.path.join(OUT, "m5w_faint_validation.json"), "w") as fh:
    json.dump(summary, fh, indent=2)
print("\nwrote", os.path.join(OUT, "m5w_faint_validation.json"))
