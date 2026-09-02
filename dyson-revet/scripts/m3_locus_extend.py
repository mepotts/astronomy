"""M3: extend the photospheric WISE colour locus BLUEWARD, and prove it is safe.

Closes the caveat carried by M1 §, M2 §4.3 and M2 §4.5: the screen fitted only
the M_G 6-14.5 window (K/M dwarfs) because the empirical locus was built from
<30 pc dwarfs, while Hephaistos II's 265 template stars spanned M_G 0-13.6.
Two thirds of the full-10-band stars were therefore never fitted, which made
the RMSE row of the funnel a lower bound rather than a measurement.

The question is not "can we interpolate blueward" -- np.interp already
flat-extrapolates -- it is "is there a SOURCED photospheric colour blueward,
and does it agree with anything measurable?". Both halves are answerable:

  1. SOURCE. Pecaut & Mamajek (2013) tabulate W1-W2, W1-W3 and W1-W4 for
     B5V..K5V (36 rows with M_G < 6 have all three plus the Gaia colours).
     The famous gap in that table is K6V-M4.5V ONLY -- exactly the range the
     empirical locus was built to fill. Blueward of K5V nothing needs building.

  2. CROSS-CHECK. The same <30 pc query that built the M-dwarf locus also
     returned 258 stars with M_G < 6.5. Every one of them is in WISE's
     saturated regime (W1 < 8), so they were excluded from the locus and
     cannot define it -- but they can TEST it. If saturated-regime empirical
     medians and PM13's independent tabulation agree, the blueward extension
     is safe at a level far below the RMSE <= 0.2 gate.

Output: data/photometry/wise_locus_extended.csv (M_G 0.5-14), plus the
agreement table that is the evidence for the M3 write-up.

Run:  python scripts/m3_locus_extend.py
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
DATA = ROOT / "data" / "photometry"
OUT = ROOT / "out"
MDWARF = DATA / "mdwarf_wise_locus.csv"
RAW = DATA / "mdwarf_wise_locus_raw.csv"
EXT = DATA / "wise_locus_extended.csv"

SPLICE = 6.5      # M_G below which PM13's own WISE colours are used
W1_SAT = 8.0      # AllWISE W1 profile-fit saturation regime (mag)


def pm13_full() -> pd.DataFrame:
    """PM13 dwarf table, unfiltered in M_G, with the WISE colour columns."""
    from w1_selection import DATA as WDATA, PM13_URL  # noqa: PLC0415
    path = WDATA / "EEM_dwarf_UBVIJHK_colors_Teff.txt"
    if not path.exists():
        import requests  # noqa: PLC0415
        r = requests.get(PM13_URL, timeout=120)
        r.raise_for_status()
        path.write_bytes(r.content)
    rows, header = [], None
    for ln in path.read_text().splitlines():
        if ln.startswith("#SpT") and header is None:
            header = ln.lstrip("#").split()
        elif header and ln and not ln.startswith("#"):
            p = ln.split()
            if len(p) == len(header):
                rows.append(p)
    df = pd.DataFrame(rows, columns=header)

    def num(c):
        return pd.to_numeric(df[c].str.replace("...", "nan", regex=False)
                             .str.replace(":", "", regex=False), errors="coerce")

    o = pd.DataFrame({"SpT": df["SpT"], "M_G": num("M_G"),
                      "w12": num("W1-W2"), "w13": num("W1-W3"),
                      "w14": num("W1-W4"), "BpRp": num("Bp-Rp")})
    return o.dropna(subset=["M_G"]).sort_values("M_G").reset_index(drop=True)


def blueward_empirical() -> pd.DataFrame:
    """Saturated-regime <30 pc stars, binned. NOT used to define the locus."""
    df = pd.read_csv(RAW)
    df["mg"] = df["phot_g_mean_mag"] + 5 - 5 * np.log10(df["r_med_geo"])
    df = df[df["cc_flags"].astype(str).str.strip().isin(["0000", "0"])]
    df["snr3"] = 1.0857 / df["w3mpro_error"]
    df["snr4"] = 1.0857 / df["w4mpro_error"]
    df = df[(df["snr3"] > 8) & (df["snr4"] > 4) & (df["mg"] < SPLICE)]
    df["w12"] = df["w1mpro"] - df["w2mpro"]
    df["w13"] = df["w1mpro"] - df["w3mpro"]
    df["w14"] = df["w1mpro"] - df["w4mpro"]
    rows = []
    for lo, hi in [(0.5, 3.0), (3.0, 4.5), (4.5, 6.5)]:
        s = df[(df["mg"] >= lo) & (df["mg"] < hi)]
        if len(s) < 3:
            continue
        rec = {"mg_lo": lo, "mg_hi": hi, "n": len(s),
               "f_saturated": float((s["w1mpro"] < W1_SAT).mean())}
        for c in ("w12", "w13", "w14"):
            v = s[c].to_numpy()
            med = np.median(v)
            mad = 1.4826 * np.median(np.abs(v - med))
            keep = np.abs(v - med) < 2.0 * max(mad, 0.05)
            rec[c] = float(np.median(v[keep]))
            rec[c + "_scatter"] = float(np.std(v[keep]))
        rows.append(rec)
    return pd.DataFrame(rows)


def main() -> None:
    pm = pm13_full()
    mdw = pd.read_csv(MDWARF)
    emp = blueward_empirical()

    blue = pm[(pm["M_G"] < SPLICE) & pm["w13"].notna() & pm["w14"].notna()
              & pm["BpRp"].notna()]
    print(f"PM13 rows with M_G < {SPLICE}, all three WISE colours and Bp-Rp: "
          f"{len(blue)}  (M_G {blue['M_G'].min():.2f} to "
          f"{blue['M_G'].max():.2f}, {blue['SpT'].iloc[0]}..{blue['SpT'].iloc[-1]})")
    gap = pm[pm["w13"].isna() & (pm["M_G"] > 6) & (pm["M_G"] < 13)]
    print(f"PM13 gap with no WISE colours: {gap['SpT'].iloc[0]}.."
          f"{gap['SpT'].iloc[-1]} (M_G {gap['M_G'].min():.2f}-"
          f"{gap['M_G'].max():.2f}) -- exactly the empirical locus's range")

    # ---- the cross-check that closes the caveat -------------------------
    print("\nCROSS-CHECK  PM13 (sourced, unsaturated) vs <30 pc empirical "
          "(saturated regime, W1 < 8):")
    print(f"{'M_G bin':>12} {'n':>4} {'sat':>5} | "
          f"{'W1-W3 PM13':>10} {'emp':>7} {'diff':>7} | "
          f"{'W1-W4 PM13':>10} {'emp':>7} {'diff':>7}")
    diffs = []
    for _, r in emp.iterrows():
        mid = 0.5 * (r["mg_lo"] + r["mg_hi"])
        p13 = np.interp(mid, blue["M_G"], blue["w13"])
        p14 = np.interp(mid, blue["M_G"], blue["w14"])
        d3, d4 = r["w13"] - p13, r["w14"] - p14
        diffs += [d3, d4]
        print(f"{r['mg_lo']:5.1f}-{r['mg_hi']:<6.1f} {int(r['n']):4d} "
              f"{100 * r['f_saturated']:4.0f}% | {p13:10.3f} {r['w13']:7.3f} "
              f"{d3:+7.3f} | {p14:10.3f} {r['w14']:7.3f} {d4:+7.3f}")
    amax = float(np.max(np.abs(diffs)))
    arms = float(np.sqrt(np.mean(np.square(diffs))))
    # a systematic in 2 of the 10 RMSE bands propagates as sqrt(2/10)*d
    prop = arms * np.sqrt(2.0 / 10.0)
    print(f"\nmax |diff| = {amax:.3f} mag, rms = {arms:.3f} mag over "
          f"{len(diffs)} comparisons")
    print(f"propagated into the 10-band RMSE (2 affected bands): "
          f"{prop:.4f} mag, against the RMSE <= 0.2 gate "
          f"({0.2 / max(prop, 1e-9):.0f}x margin)")

    # ---- build the spliced locus ---------------------------------------
    grid = np.arange(0.5, 14.01, 0.25)
    rows = []
    for mg in grid:
        if mg < SPLICE:
            rec = {"mg": float(mg), "n": -1, "src": "PM13"}
            for c in ("w12", "w13", "w14"):
                rec[c] = float(np.interp(mg, blue["M_G"], blue[c]))
                # scatter blueward: use the saturated-regime empirical scatter
                # as the honest (conservative) estimate; it is not a defining
                # measurement, only a width for the template-diversity term.
                near = emp.iloc[int(np.clip(np.searchsorted(
                    emp["mg_hi"], mg), 0, len(emp) - 1))]
                rec[c + "_scatter"] = float(near[c + "_scatter"])
                rec[c + "_nkeep"] = int(near["n"])
        else:
            rec = {"mg": float(mg), "n": -1, "src": "empirical"}
            for c in ("w12", "w13", "w14"):
                rec[c] = float(np.interp(mg, mdw["mg"], mdw[c]))
                rec[c + "_scatter"] = float(np.interp(
                    mg, mdw["mg"], mdw[c + "_scatter"]))
                rec[c + "_nkeep"] = int(np.interp(mg, mdw["mg"],
                                                  mdw[c + "_nkeep"]))
        rows.append(rec)
    ext = pd.DataFrame(rows)
    EXT.parent.mkdir(parents=True, exist_ok=True)
    ext.to_csv(EXT, index=False)
    print(f"\nwrote {EXT} : {len(ext)} rows, M_G "
          f"{ext['mg'].min():.2f}-{ext['mg'].max():.2f}")

    # continuity at the splice
    lo = ext[ext["mg"] < SPLICE].iloc[-1]
    hi = ext[ext["mg"] >= SPLICE].iloc[0]
    print(f"splice continuity at M_G {SPLICE}: "
          f"W1-W3 {lo['w13']:+.3f} -> {hi['w13']:+.3f} "
          f"(jump {hi['w13'] - lo['w13']:+.3f}); "
          f"W1-W4 {lo['w14']:+.3f} -> {hi['w14']:+.3f} "
          f"(jump {hi['w14'] - lo['w14']:+.3f})")

    OUT.mkdir(exist_ok=True)
    emp.to_csv(OUT / "m3_locus_blueward_crosscheck.csv", index=False)
    print(f"wrote {OUT / 'm3_locus_blueward_crosscheck.csv'}")


if __name__ == "__main__":
    main()
