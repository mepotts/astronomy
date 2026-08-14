"""M31: verify HiRISE extractions BY CONTENTS, not existence (LESSONS 4: a recipe can
exit 0 in under a second writing empty products -- YSES 1 2022).

Per night, for every ext/*_extr1D.fits:
  - per detector extension, count orders whose _SPEC column is non-empty
    (finite fraction > 0.5 and non-zero scatter);
  - wavelength coverage against the H1567 reference established by the bpbhi
    validation (M29 sec 19: 1499-1744 nm);
  - median flux / error / per-pixel S/N over finite pixels.

Frames are classed host/deep from the DIT column classify.py wrote into tags.tsv
(deep = the night's maximum DIT), and within the short-DIT class the measured
flux separates true host frames from sky/offset frames -- the M30 raw-percentile
probe showed h65hi2/3 carry faint trailing short frames and h65hi1 no bright
frame at all, so DIT alone is NOT a host label on these nights.

Writes a JSON summary and prints a PASS/FAIL verdict per gate; exit 1 on FAIL.

Usage (WSL): m31_verify.py <reddir> [<json_out>]
"""
import glob
import json
import os
import sys

import numpy as np
from astropy.io import fits

WL_LO_MAX = 1505.0   # global min wavelength must sit below this (nm)
WL_HI_MIN = 1735.0   # global max wavelength must sit above this (nm)
WL_HARD = (1450.0, 1800.0)  # and the whole range inside this
MIN_ORDERS_PER_FRAME = 15   # bpbhi reference: 21 non-empty orders per frame


def frame_stats(path):
    orders = 0
    per_det = {}
    wl_min, wl_max = np.inf, -np.inf
    fluxes, errs, snrs = [], [], []
    with fits.open(path) as h:
        for e in h[1:]:
            if e.data is None or not hasattr(e.data, "columns"):
                continue
            det = e.name
            for c in e.data.columns.names:
                if not c.endswith("_SPEC"):
                    continue
                base = c[:-5]
                try:
                    wl = np.asarray(e.data[base + "_WL"], float)
                    fl = np.asarray(e.data[c], float)
                    er = np.asarray(e.data[base + "_ERR"], float)
                except KeyError:
                    continue
                g = np.isfinite(wl) & np.isfinite(fl) & np.isfinite(er) & (er > 0)
                if g.mean() > 0.5 and np.nanstd(fl[g]) > 0:
                    orders += 1
                    per_det[det] = per_det.get(det, 0) + 1
                    wl_min = min(wl_min, float(np.nanmin(wl[g])))
                    wl_max = max(wl_max, float(np.nanmax(wl[g])))
                    fluxes.append(np.nanmedian(fl[g]))
                    errs.append(np.nanmedian(er[g]))
                    snrs.append(np.nanmedian(fl[g] / er[g]))
    return {
        "orders": orders,
        "per_det": per_det,
        "wl_min": None if not np.isfinite(wl_min) else round(wl_min, 1),
        "wl_max": None if not np.isfinite(wl_max) else round(wl_max, 1),
        "med_flux": float(np.median(fluxes)) if fluxes else None,
        "med_err": float(np.median(errs)) if errs else None,
        "med_snr": float(np.median(snrs)) if snrs else None,
    }


def main():
    red = sys.argv[1]
    out_json = sys.argv[2] if len(sys.argv) > 2 else None
    night = os.path.basename(red.rstrip("/"))

    dits = {}
    tags = os.path.join(red, "tags.tsv")
    with open(tags) as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 4 and p[1] in ("OBS_STARING_OTHER", "OBS_NODDING_OTHER"):
                b = os.path.basename(p[0]).replace(".fits", "")
                try:
                    dits[b] = float(p[3])
                except ValueError:
                    pass

    files = sorted(glob.glob(os.path.join(red, "ext", "*_extr1D.fits")))
    rows, fails = [], []
    for f in files:
        b = os.path.basename(f).split("_extr1D")[0]
        st = frame_stats(f)
        st["frame"] = b
        st["dit"] = dits.get(b)
        rows.append(st)

    n_sci = len(dits)
    if len(files) != n_sci:
        fails.append(f"extracted {len(files)} of {n_sci} science frames")
    for st in rows:
        if st["orders"] < MIN_ORDERS_PER_FRAME:
            fails.append(f"{st['frame']}: only {st['orders']} non-empty orders")
        if len(st["per_det"]) < 3:
            fails.append(f"{st['frame']}: detectors with content: {sorted(st['per_det'])}")
        if st["wl_min"] is None or not (
            WL_HARD[0] < st["wl_min"] < WL_LO_MAX and WL_HI_MIN < st["wl_max"] < WL_HARD[1]
        ):
            fails.append(f"{st['frame']}: wavelength range {st['wl_min']}-{st['wl_max']} nm "
                         f"outside H1567 expectation")

    max_dit = max((st["dit"] for st in rows if st["dit"]), default=None)
    deep = [st for st in rows if st["dit"] == max_dit]
    short = [st for st in rows if st["dit"] != max_dit]
    deep_rate = (np.median([s["med_flux"] / s["dit"] for s in deep if s["med_flux"] is not None])
                 if deep else float("nan"))
    bright, faint_short = [], []
    for s in short:
        rate = s["med_flux"] / s["dit"] if (s["med_flux"] is not None and s["dit"]) else 0.0
        (bright if rate > 3 * abs(deep_rate) else faint_short).append(s)

    summary = {
        "night": night,
        "n_science": n_sci,
        "n_extracted": len(files),
        "max_dit": max_dit,
        "deep": {"n": len(deep),
                 "med_flux": _med(deep, "med_flux"), "med_err": _med(deep, "med_err"),
                 "med_snr": _med(deep, "med_snr"),
                 "flux_per_s": None if not deep else _med(deep, "med_flux") / max_dit},
        "host_bright": {"n": len(bright), "frames": [s["frame"] for s in bright],
                        "med_flux": _med(bright, "med_flux"), "med_snr": _med(bright, "med_snr"),
                        "flux_per_s": None if not bright else
                        float(np.median([s["med_flux"] / s["dit"] for s in bright]))},
        "short_faint": {"n": len(faint_short), "frames": [s["frame"] for s in faint_short],
                        "med_flux": _med(faint_short, "med_flux"),
                        "med_snr": _med(faint_short, "med_snr")},
        "wl_range_nm": [min((s["wl_min"] for s in rows if s["wl_min"]), default=None),
                        max((s["wl_max"] for s in rows if s["wl_max"]), default=None)],
        "gates_failed": fails,
        "frames": rows,
    }
    if summary["host_bright"]["flux_per_s"] and summary["deep"]["flux_per_s"]:
        summary["host_over_deep_per_s"] = round(
            summary["host_bright"]["flux_per_s"] / summary["deep"]["flux_per_s"], 1)

    print(f"=== {night}: {len(files)}/{n_sci} extracted; "
          f"wl {summary['wl_range_nm'][0]}-{summary['wl_range_nm'][1]} nm ===")
    for st in rows:
        print(f"  {st['frame']}  DIT={st['dit']}  orders={st['orders']}  "
              f"flux={st['med_flux']:.1f}  err={st['med_err']:.1f}  SNR={st['med_snr']:.2f}"
              if st["med_flux"] is not None else f"  {st['frame']}  EMPTY")
    print(f"  deep (DIT={max_dit}): n={len(deep)} SNR={summary['deep']['med_snr']}")
    print(f"  host-bright: n={len(bright)} {summary['host_bright']['frames']}")
    print(f"  short-faint: n={len(faint_short)} {summary['short_faint']['frames']}")
    if "host_over_deep_per_s" in summary:
        print(f"  host/deep flux per second: {summary['host_over_deep_per_s']}")
    if out_json:
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=1)
        print(f"  wrote {out_json}")
    if fails:
        print("VERDICT: FAIL")
        for x in fails:
            print("  -", x)
        sys.exit(1)
    print("VERDICT: PASS (contents verified)")


def _med(rows, key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    return round(float(np.median(vals)), 3) if vals else None


if __name__ == "__main__":
    main()
