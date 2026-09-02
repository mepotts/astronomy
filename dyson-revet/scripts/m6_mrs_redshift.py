"""M6: what redshift do candidate D's MRS cubes actually support?

Runs on the spatially resolved extraction from `m6_mrs_reduce.py extract`.
Three stages, in the order M6 PR-2 fixed:

  1. ACCEPTANCE.  The extracted MRS spectra are integrated over the real MIRI
     imaging bandpasses (SVO Filter Profile Service, anonymous) and compared
     with M4 Sec 5.1's INDEPENDENTLY measured F560W/F1000W/F1500W fluxes for
     both components.  Tolerance fixed in advance at +-30% per band per
     component.  If it fails, no redshift is quoted from these data.

  2. BLIND SEARCH.  A redshift grid over 0 < z < 3 is cross-correlated against
     a FIXED mid-IR feature list, using a continuum estimator that is the same
     at every z so the continuum choice cannot favour one.  Whatever the grid's
     best z is, it is reported -- including if it is nothing at all.  A control
     runs the identical scan on the STAR extracted from the same cubes by the
     same code.

  3. FEATURE FITS.  At the blind best z and at the published z = 0.922, each
     feature is fitted on the global-continuum residual.  PR-2's criterion for
     claiming a redshift: >= 2 independent features, each >= 5 sigma, agreeing
     on z to +-0.01.  A single feature is not a redshift.

    python scripts/m6_mrs_redshift.py --label D
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
FILT = ROOT / "data" / "jwst" / "filters"
FILT.mkdir(parents=True, exist_ok=True)

# M4 Sec 5.1, Table: measured from the public MIRI mosaics, uJy
M4_PHOT = {"f560w": {"star": 300.6, "con": 70.9},
           "f1000w": {"star": 124.0, "con": 898.2},
           "f1500w": {"star": 50.0, "con": 4159.1}}
M4_TOL = 0.30                       # PR-2's fixed tolerance

# PR-2's fixed line list.  (rest um, intrinsic FWHM um, kind, name)
LINES = [
    (6.220, 0.19, "pah", "PAH 6.2"),
    (7.700, 0.90, "pah", "PAH 7.7"),
    (8.610, 0.35, "pah", "PAH 8.6"),
    (11.330, 0.14, "pah", "PAH 11.3"),
    (12.700, 0.20, "pah", "PAH 12.7"),
    (6.985, 0.02, "fs", "[Ar II]"),
    (8.991, 0.02, "fs", "[Ar III]"),
    (10.511, 0.02, "fs", "[S IV]"),
    (12.814, 0.02, "fs", "[Ne II]"),
    (15.555, 0.02, "fs", "[Ne III]"),
    (18.713, 0.03, "fs", "[S III]"),
    (25.890, 0.04, "fs", "[O IV]"),
    (17.035, 0.02, "h2", "H2 S(1)"),
    (12.279, 0.02, "h2", "H2 S(2)"),
    (9.665, 0.02, "h2", "H2 S(3)"),
]
SILICATE = 9.7                      # broad absorption, handled separately
ZMIN, ZMAX, DZ = 0.0, 3.0, 0.0005
CONT_DEX = 0.08                     # LOESS continuum half-window, dex


# --------------------------------------------------------------- bandpasses --
def bandpass(name):
    import requests
    from astropy.io.votable import parse_single_table
    p = FILT / ("MIRI." + name.upper() + ".xml")
    if not p.exists():
        r = requests.get("http://svo2.cab.inta-csic.es/theory/fps/fps.php",
                         params={"ID": "JWST/MIRI." + name.upper()}, timeout=120)
        r.raise_for_status()
        p.write_bytes(r.content)
    t = parse_single_table(str(p)).to_table()
    return (np.asarray(t["Wavelength"], float) / 1e4,
            np.asarray(t["Transmission"], float))


def synth(lam, flux, name):
    """Photon-weighted synthetic photometry in F_nu (STScI convention)."""
    wl, tr = bandpass(name)
    ok = (wl >= lam.min()) & (wl <= lam.max()) & (tr > 1e-4)
    if ok.sum() < 10:
        return np.nan, 0.0
    f = np.interp(wl[ok], lam, flux)
    w = tr[ok] * wl[ok]
    cover = float(np.trapezoid(tr[ok] * wl[ok], wl[ok]) / np.trapezoid(tr * wl, wl))
    return float(np.trapezoid(f * w, wl[ok]) / np.trapezoid(w, wl[ok])), cover


# ------------------------------------------------------------------ stitch --
def stitch(df, col, ecol):
    """One spectrum from the 12 sub-bands, overlaps inverse-variance averaged.

    Offsets measured in the overlaps are REPORTED (a known MRS systematic) and
    not corrected -- correcting them would be a free parameter this project has
    not earned.
    """
    d = df[np.isfinite(df[col])].sort_values("lam_um")
    lo, hi = float(d["lam_um"].min()), float(d["lam_um"].max())
    grid = np.arange(lo, hi, 0.002)
    num = np.zeros_like(grid)
    den = np.zeros_like(grid)
    for _, g in d.groupby("band"):
        gg = g.sort_values("lam_um")
        m = (grid >= gg["lam_um"].min()) & (grid <= gg["lam_um"].max())
        if m.sum() < 5:
            continue
        f = np.interp(grid[m], gg["lam_um"], gg[col])
        e = np.interp(grid[m], gg["lam_um"], gg[ecol].clip(lower=1e-12))
        w = 1.0 / e ** 2
        num[m] += f * w
        den[m] += w
    ok = den > 0
    return pd.DataFrame({"lam_um": grid[ok], "f": num[ok] / den[ok],
                         "e": 1.0 / np.sqrt(den[ok])})


def band_overlap_report(df, col):
    rep = []
    bands = sorted(df["band"].unique(),
                   key=lambda b: df.loc[df["band"] == b, "lam_um"].min())
    for b1, b2 in zip(bands[:-1], bands[1:]):
        g1 = df[(df["band"] == b1) & np.isfinite(df[col])]
        g2 = df[(df["band"] == b2) & np.isfinite(df[col])]
        lo, hi = g2["lam_um"].min(), g1["lam_um"].max()
        if hi <= lo:
            rep.append({"pair": b1 + "|" + b2, "overlap_um": 0.0, "ratio": None})
            continue
        m1 = g1[(g1["lam_um"] >= lo) & (g1["lam_um"] <= hi)][col].median()
        m2 = g2[(g2["lam_um"] >= lo) & (g2["lam_um"] <= hi)][col].median()
        rep.append({"pair": b1 + "|" + b2, "overlap_um": float(hi - lo),
                    "ratio": float(m2 / m1) if m1 else None})
    return rep


# ----------------------------------------------------------- continuum, z --
def continuum(lam, f, dex=CONT_DEX, deg=2, iters=4, clip=1.0, step=25):
    """Smooth, z-INDEPENDENT continuum: local quadratic regression in
    log F vs log lambda, refitted with asymmetric clipping of points ABOVE it.

    The window is a fixed width in log-lambda, i.e. the same FRACTIONAL width
    at every wavelength, so it treats a rest feature seen at 12 um exactly as
    it treats the same feature seen at 24 um -- which is what keeps a blind
    redshift scan fair.  At +-0.08 dex it is ~2x wider than the broadest
    feature in PR-2's list (PAH 7.7 at z ~ 1) and ~6x wider than the rest, so
    it cannot absorb one; and it never looks at z, so it cannot favour a
    redshift.  The upward clipping makes it a lower envelope: emission is
    excluded from the fit, absorption is not.
    """
    x, y = np.log10(lam), np.log10(np.maximum(f, 1e-12))
    keep = np.ones(len(x), bool)
    anchors = np.arange(0, len(x), step)
    if anchors[-1] != len(x) - 1:
        anchors = np.append(anchors, len(x) - 1)
    cont = np.zeros(len(x))
    for _ in range(iters):
        vals = np.empty(len(anchors))
        for j, i in enumerate(anchors):
            m = (np.abs(x - x[i]) <= dex) & keep
            if m.sum() < deg + 3:
                m = np.abs(x - x[i]) <= dex
            vals[j] = np.polyfit(x[m] - x[i], y[m], deg)[-1]
        cont = np.interp(x, x[anchors], vals)
        r = y - cont
        sd = 1.4826 * np.median(np.abs(r - np.median(r)))
        keep = r < clip * sd
        if keep.sum() < 0.2 * len(x):
            keep = np.ones(len(x), bool)
            break
    return 10 ** cont


def empirical_noise(lam, f, e, halfwin=0.05):
    """Local high-frequency scatter, floored by the formal error.

    Adjacent MRS slices are strongly correlated (same detector pixels, cube
    resampling), so the per-slice formal error under-states the noise on a
    combined spectrum.  The high-frequency scatter about a short running median
    is an empirical noise that carries those correlations and the fringe
    residuals.
    """
    from scipy.signal import medfilt
    k = max(int(0.02 / np.median(np.diff(lam))) | 1, 5)
    hi = f - medfilt(f, k)
    out = np.empty_like(f)
    for i, x in enumerate(lam):
        m = np.abs(lam - x) <= halfwin
        out[i] = 1.4826 * np.median(np.abs(hi[m] - np.median(hi[m])))
    return np.maximum(out, e)


def template(lam, z, kinds=None):
    t = np.zeros_like(lam)
    for lr, fw, kind, _ in LINES:
        if kinds and kind not in kinds:
            continue
        lo = lr * (1 + z)
        if lo < lam.min() or lo > lam.max():
            continue
        s = fw * (1 + z) / 2.3548
        t += (1.0 if kind == "pah" else 0.7) * np.exp(-0.5 * ((lam - lo) / s) ** 2)
    return t


def zscan(lam, r, er, kinds=None, minpix=50):
    zs = np.arange(ZMIN, ZMAX + DZ, DZ)
    sc = np.full(len(zs), np.nan)
    w = 1.0 / er ** 2
    for i, z in enumerate(zs):
        t = template(lam, z, kinds)
        n = float(np.sum(w * t * t))
        if n <= 0 or (t > 0.1).sum() < minpix:
            continue
        sc[i] = float(np.sum(w * r * t) / np.sqrt(n))
    return zs, sc


def fit_on_residual(lam, r, er, lam0, fwhm0):
    """Matched-filter amplitude of one feature on the global-continuum residual.

    No local continuum is refitted, so a broad feature cannot trade against a
    local baseline -- the degeneracy that made an earlier version of this
    script report meaningless 1000-sigma detections on PAH 7.7.
    """
    sig = fwhm0 / 2.3548
    m = np.abs(lam - lam0) <= 2.5 * fwhm0
    if m.sum() < 15:
        return None
    best = None
    for lc in np.arange(lam0 - 0.5 * fwhm0, lam0 + 0.5 * fwhm0 + 1e-9, fwhm0 / 30):
        g = np.exp(-0.5 * ((lam[m] - lc) / sig) ** 2)
        w = 1.0 / er[m] ** 2
        den = float(np.sum(w * g * g))
        if den <= 0:
            continue
        amp = float(np.sum(w * r[m] * g)) / den
        snr = amp * np.sqrt(den)
        if best is None or snr > best[0]:
            best = (snr, amp, 1.0 / np.sqrt(den), float(lc))
    if best is None:
        return None
    return {"snr": best[0], "amp": best[1], "e_amp": best[2], "lam_fit": best[3]}


def prep(sp):
    """Continuum-normalised residual on the range where the continuum's own
    window is TWO-SIDED -- a property of the estimator, fixed before any z."""
    lm = sp["lam_um"].to_numpy()
    ff = sp["f"].to_numpy()
    ee = sp["e"].to_numpy()
    k = np.isfinite(ff) & np.isfinite(ee) & (ee > 0) & (ff > 0)
    lm, ff, ee = lm[k], ff[k], ee[k]
    ee2 = empirical_noise(lm, ff, ee)
    cc = continuum(lm, ff)
    x = np.log10(lm)
    v = (x - CONT_DEX >= x.min()) & (x + CONT_DEX <= x.max())
    return lm[v], ff[v], ee2[v], cc[v], ee[v]


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--label", default="D")
    ap.add_argument("--assoc", default="")
    a = ap.parse_args()
    tag = "" if not a.assoc else "_" + a.assoc
    df = pd.read_csv(OUT / ("m6_mrs_%s_spectra%s.csv" % (a.label, tag)))
    meta = pd.read_csv(OUT / ("m6_mrs_%s_cubes%s.csv" % (a.label, tag)))
    res = {"label": a.label, "assoc": a.assoc or "o002", "n_cubes": int(len(meta)),
           "cal_ver": sorted(set(meta["cal_ver"].astype(str))),
           "crds_ctx": sorted(set(meta["crds_ctx"].astype(str))),
           "lam_range_um": [float(meta["lam_min"].min()),
                            float(meta["lam_max"].max())],
           "n_slices": int(len(df))}

    df["e_star_jy"] = df["e_con_jy"]
    con = stitch(df, "f_con_jy", "e_con_jy")
    star = stitch(df, "f_star_jy", "e_star_jy")
    res["band_overlap_ratios_contaminant"] = band_overlap_report(df, "f_con_jy")

    # ------------------------------------------- 1. PR-2's acceptance test --
    acc = {}
    for fname in ("f560w", "f1000w", "f1500w"):
        for who, sp in (("star", star), ("con", con)):
            v, cover = synth(sp["lam_um"].to_numpy(), sp["f"].to_numpy(), fname)
            ref = M4_PHOT[fname][who]
            acc["%s_%s" % (fname, who)] = {
                "mrs_uJy": v * 1e6, "m4_imaging_uJy": ref,
                "ratio": v * 1e6 / ref, "bandpass_covered": cover,
                "pass": bool(abs(v * 1e6 / ref - 1) <= M4_TOL),
                "dominant_component": bool(
                    (who == "star")
                    == (M4_PHOT[fname]["star"] > M4_PHOT[fname]["con"]))}
    res["acceptance"] = acc
    res["acceptance_pass"] = all(v["pass"] for v in acc.values())
    res["acceptance_pass_dominant_only"] = all(
        v["pass"] for v in acc.values() if v["dominant_component"])
    print("PR-2 ACCEPTANCE TEST  (tolerance +-%.0f%%)" % (100 * M4_TOL))
    for k, v in acc.items():
        print("  %-14s MRS %9.1f uJy   M4 imaging %9.1f uJy   ratio %5.2f  "
              "%-12s %s"
              % (k, v["mrs_uJy"], v["m4_imaging_uJy"], v["ratio"],
                 "dominant" if v["dominant_component"] else "sub-dominant",
                 "PASS" if v["pass"] else "FAIL"))
    print("  -> %s   (dominant component in every band: %s)"
          % ("PASS" if res["acceptance_pass"] else "FAIL",
             "PASS" if res["acceptance_pass_dominant_only"] else "FAIL"))

    # ------------------------------------------------- 2. the blind z scan --
    lam, f, e, c, e_formal = prep(con)
    res["valid_range_um"] = [float(lam.min()), float(lam.max())]
    res["noise"] = {
        "median_formal_uJy": float(np.median(e_formal) * 1e6),
        "median_empirical_uJy": float(np.median(e) * 1e6),
        "inflation_factor": float(np.median(e / e_formal)),
        "note": "adjacent MRS slices are correlated, so the per-slice formal "
                "error under-states the noise on a combined spectrum; the "
                "empirical high-frequency scatter is used everywhere below"}
    r, er = f / c - 1.0, e / c
    zs, sc = zscan(lam, r, er)
    good = np.isfinite(sc)
    zbest = float(zs[good][np.nanargmax(sc[good])])
    peak = float(np.nanmax(sc[good]))
    nullsd = float(np.nanstd(sc[good]))
    res["blind_scan"] = {
        "z_grid": [ZMIN, ZMAX, DZ], "z_best": zbest, "peak_score": peak,
        "scan_rms": nullsd,
        "peak_over_scan_rms": peak / nullsd if nullsd else None,
        "score_at_0.922": float(np.interp(0.922, zs[good], sc[good])),
        "delta_z_from_published": zbest - 0.922}
    pd.DataFrame({"z": zs, "score": sc}).to_csv(
        OUT / ("m6_mrs_%s_zscan%s.csv" % (a.label, tag)), index=False)
    print("\nBLIND REDSHIFT SCAN  (0<z<3, dz=%.4f, %d points, %.2f-%.2f um)"
          % (DZ, len(zs), lam.min(), lam.max()))
    print("  best z = %.4f   score %.1f   scan rms %.1f   peak/rms %.1f"
          % (zbest, peak, nullsd, peak / nullsd if nullsd else np.nan))
    print("  score at the published z = 0.922: %.1f   (dz = %+.4f)"
          % (res["blind_scan"]["score_at_0.922"], zbest - 0.922))
    print("  noise: formal %.2f uJy -> empirical %.2f uJy (x%.2f)"
          % (res["noise"]["median_formal_uJy"],
             res["noise"]["median_empirical_uJy"],
             res["noise"]["inflation_factor"]))
    order, seen, shown = np.argsort(np.where(good, sc, -np.inf))[::-1], [], []
    for i in order:
        if any(abs(zs[i] - t) < 0.03 for t in seen):
            continue
        seen.append(zs[i])
        shown.append((float(zs[i]), float(sc[i])))
        if len(shown) == 5:
            break
    res["blind_scan"]["top5_separated_peaks"] = shown
    print("  five best separated peaks: "
          + ", ".join("z=%.4f (%.1f)" % t for t in shown))

    sens = {}
    for dx in (0.06, 0.08, 0.10):
        cc = continuum(lam, f, dex=dx)
        z2, s2 = zscan(lam, f / cc - 1.0, e / cc)
        g2 = np.isfinite(s2)
        sens[str(dx)] = float(z2[g2][np.nanargmax(s2[g2])])
    res["blind_scan"]["z_best_vs_continuum_window"] = sens
    print("  continuum-window sensitivity (dex -> z_best): %s" % sens)

    # A second, sharper blind test on the SAME fixed line list and the SAME
    # fixed 5-sigma rule: at every z, how many of PR-2's NARROW features (the
    # fine-structure and H2 lines, whose centroids are not degenerate with the
    # continuum) are detected in emission at >= 5 sigma?  Scanned blind over
    # 0 < z < 3, so the look-elsewhere cost is measured, not assumed.
    zc_grid = np.arange(0.05, 2.5, 0.002)
    narrow = [(lr, fw, nm) for lr, fw, kind, nm in LINES if kind in ("fs", "h2")]
    cnt = np.zeros(len(zc_grid), int)
    tot = np.zeros(len(zc_grid), float)
    for i, z in enumerate(zc_grid):
        n = 0
        t = 0.0
        for lr, fw, nm in narrow:
            lo = lr * (1 + z)
            if lo < lam.min() + 0.3 or lo > lam.max() - 0.3:
                continue
            ff = fit_on_residual(lam, r, er, lo, fw * (1 + z))
            if ff and ff["snr"] >= 5 and ff["amp"] > 0:
                n += 1
                t += ff["snr"]
        cnt[i], tot[i] = n, t
    nmax = int(cnt.max())
    i922 = int(np.argmin(np.abs(zc_grid - 0.922)))
    tie = zc_grid[cnt == nmax]
    res["narrow_consensus_scan"] = {
        "grid": [0.05, 2.5, 0.002],
        "max_narrow_lines_at_5sigma": nmax,
        "n_at_published_z": int(cnt[i922]),
        "sum_snr_at_published_z": float(tot[i922]),
        "n_grid_points_reaching_max": int((cnt == nmax).sum()),
        "fraction_of_grid_reaching_n_at_published_z":
            float((cnt >= cnt[i922]).mean()),
        "z_of_best_sum_snr_among_max": float(zc_grid[cnt == nmax][
            np.argmax(tot[cnt == nmax])]) if len(tie) else None,
        "published_z_is_among_best": bool(
            len(tie) and np.min(np.abs(tie - 0.922)) <= 0.01)}
    pd.DataFrame({"z": zc_grid, "n_5sigma": cnt, "sum_snr": tot}).to_csv(
        OUT / ("m6_mrs_%s_narrow_consensus%s.csv" % (a.label, tag)), index=False)
    nc = res["narrow_consensus_scan"]
    print("")
    print("NARROW-LINE CONSENSUS SCAN (fixed list, 5 sigma, blind in z)")
    print("  most narrow lines detected at any z: %d   at z=0.922: %d "
          "(sum SNR %.1f)" % (nc["max_narrow_lines_at_5sigma"],
                              nc["n_at_published_z"], nc["sum_snr_at_published_z"]))
    print("  fraction of the z grid doing as well as z=0.922: %.4f"
          % nc["fraction_of_grid_reaching_n_at_published_z"])
    print("  z=0.922 among the best: %s" % nc["published_z_is_among_best"])

    lam_s, f_s, e_s, c_s, _ = prep(star)
    z3, s3 = zscan(lam_s, f_s / c_s - 1.0, e_s / c_s)
    g3 = np.isfinite(s3)
    res["star_control"] = {
        "z_best": float(z3[g3][np.nanargmax(s3[g3])]),
        "peak_score": float(np.nanmax(s3[g3])),
        "peak_over_scan_rms": float(np.nanmax(s3[g3])
                                    / max(np.nanstd(s3[g3]), 1e-12)),
        "score_at_0.922": float(np.interp(0.922, z3[g3], s3[g3])),
        "note": "the star is a bare M-dwarf photosphere (M4 Sec 5.2) and must "
                "show no PAH pattern; it is also the component the deblend "
                "leaks INTO, since the contaminant supplies >94% of the light "
                "beyond 10 um"}
    print("\nSTAR CONTROL (same cubes, same code): best z = %.4f  peak/rms %.1f"
          "  score at 0.922 = %.1f"
          % (res["star_control"]["z_best"],
             res["star_control"]["peak_over_scan_rms"],
             res["star_control"]["score_at_0.922"]))

    # ------------------------------------------------- 3. per-feature fits --
    res["features"] = {}
    for zname, z in (("blind_best", zbest), ("published_0.922", 0.922)):
        rows = []
        for lr, fw, kind, nm in LINES:
            lo = lr * (1 + z)
            if lo < lam.min() + 0.3 or lo > lam.max() - 0.3:
                continue
            ff = fit_on_residual(lam, r, er, lo, fw * (1 + z))
            if ff is None:
                continue
            rows.append({"name": nm, "kind": kind, "lam_rest_um": lr,
                         "lam_pred_um": lo, "lam_fit_um": ff["lam_fit"],
                         "z_from_centroid": ff["lam_fit"] / lr - 1,
                         "amp_rel": ff["amp"], "e_amp_rel": ff["e_amp"],
                         "snr": ff["snr"]})
        t = pd.DataFrame(rows)
        res["features"][zname] = json.loads(t.to_json(orient="records"))
        det = t[(t["snr"] >= 5) & (t["amp_rel"] > 0)] if len(t) else t
        zc = det["z_from_centroid"] if len(det) else pd.Series(dtype=float)
        res["features"][zname + "_summary"] = {
            "n_tested": int(len(t)), "n_detected_5sigma": int(len(det)),
            "detected": list(det["name"]) if len(det) else [],
            "z_centroid_mean": float(zc.mean()) if len(det) else None,
            "z_centroid_std": float(zc.std()) if len(det) > 1 else None,
            "z_spread_within_0.01": bool(len(det) >= 2
                                         and (zc.max() - zc.min()) <= 0.01)}
        print("\nFEATURE FITS at z = %.4f (%s)" % (z, zname))
        if len(t):
            print(t.round(4).to_string(index=False))
        print("  >=5 sigma in emission: %d  (%s)"
              % (len(det), ", ".join(det["name"]) if len(det) else "none"))

    # ---------------------------------------- silicate: an independent z ----
    sil = {}
    lo, hi = SILICATE * 1.5, SILICATE * 2.5
    m = (lam > lo) & (lam < hi)
    if m.sum() > 100:
        ratio = np.log10(f[m] / c[m])
        k = max(int(0.4 / np.median(np.diff(lam))), 9)
        sm = np.convolve(ratio, np.ones(k) / k, "same")
        i = int(np.argmin(sm[k:-k])) + k
        lmin = float(lam[m][i])
        sil = {"trough_lam_um": lmin, "z_from_silicate": lmin / SILICATE - 1,
               "depth_dex": float(sm[i]),
               "note": "9.7 um silicate absorption trough on the same global "
                       "continuum; a broad feature, so this z is indicative "
                       "and is NOT counted towards PR-2's two-feature test"}
    res["silicate"] = sil
    if sil:
        print("\nSILICATE 9.7 um: trough at %.2f um -> z = %.3f (depth %.3f dex)"
              % (sil["trough_lam_um"], sil["z_from_silicate"], sil["depth_dex"]))

    # --------- the continuum shape: M4 Sec 5.2's 441 K, now with 11,625 points
    # M5 Sec 7 item 3 asked for exactly this: M4 inferred a single-blackbody
    # T ~ 441 K (rest frame, granting z = 0.922) from THREE photometric points.
    # The MRS continuum tests it over the whole 5-27 um range.
    def bb_nu(lam_um, T):
        h, kB, cc = 6.62607015e-34, 1.380649e-23, 2.99792458e8
        nu = cc / (lam_um * 1e-6)
        x = np.clip(h * nu / (kB * T), 1e-6, 700)
        return nu ** 3 / np.expm1(x)

    grid = np.arange(60.0, 1200.0, 1.0)
    chi = []
    for T in grid:
        m = bb_nu(lam, T)
        A = float(np.sum(c * m / er ** 2) / np.sum(m * m / er ** 2))
        chi.append(float(np.sum(((c - A * m) / (er * c)) ** 2)))
    Tobs = float(grid[int(np.argmin(chi))])
    pw = np.polyfit(np.log10(lam), np.log10(c), 1)
    lo56 = np.abs(lam - 5.9).argmin()
    hi10 = np.abs(lam - 10.0).argmin()
    hi15 = np.abs(lam - 15.0).argmin()
    res["continuum_shape"] = {
        "best_single_blackbody_T_observed_K": Tobs,
        "implied_rest_frame_T_at_z0.922_K": Tobs * 1.922,
        "M4_sec5.2_rest_frame_T_K": 441.0,
        "global_power_law_index_5.9_to_23.8um": float(pw[0]),
        "index_5.9_to_10um": float(np.log10(c[hi10] / c[lo56])
                                   / np.log10(lam[hi10] / lam[lo56])),
        "index_10_to_15um": float(np.log10(c[hi15] / c[hi10])
                                  / np.log10(lam[hi15] / lam[hi10])),
        "M4_index_5.6_to_10um": 4.4, "M4_index_10_to_15um": 3.8,
        "note": "a single blackbody is a poor description of a PAH-bearing, "
                "silicate-absorbed spectrum; the number is reported because "
                "M4 Sec 5.2 quoted one from three photometric points, and this "
                "is the first test of it"}
    cs = res["continuum_shape"]
    print("\nCONTINUUM SHAPE (11,625 slices vs M4's three photometric points)")
    print("  best single blackbody: T_obs = %.0f K -> rest-frame %.0f K at "
          "z = 0.922   (M4 Sec 5.2: 441 K)"
          % (Tobs, cs["implied_rest_frame_T_at_z0.922_K"]))
    print("  power-law index: %.2f global; %.2f over 5.9-10 um (M4: 4.4); "
          "%.2f over 10-15 um (M4: 3.8)"
          % (cs["global_power_law_index_5.9_to_23.8um"],
             cs["index_5.9_to_10um"], cs["index_10_to_15um"]))

    s = res["features"]["published_0.922_summary"]
    b = res["features"]["blind_best_summary"]
    res["verdict"] = {
        "acceptance": "PASS" if res["acceptance_pass"] else "FAIL",
        "acceptance_dominant_component_only":
            "PASS" if res["acceptance_pass_dominant_only"] else "FAIL",
        "criterion": ">=2 independent features, each >=5 sigma, agreeing on z "
                     "to +-0.01 (M6 PR-2, fixed before the extraction)",
        "met_at_published_z": bool(s["n_detected_5sigma"] >= 2
                                   and s["z_spread_within_0.01"]),
        "met_at_blind_best_z": bool(b["n_detected_5sigma"] >= 2
                                    and b["z_spread_within_0.01"]),
        "blind_best_z": zbest,
        "blind_agrees_with_published": bool(abs(zbest - 0.922) <= 0.01),
        "PR2_consequence_of_acceptance":
            ("PR-2 fixed in advance that if the acceptance test fails, no "
             "redshift is quoted from these data.  Everything below the "
             "acceptance line is reported as what the data show, not as a "
             "quoted redshift.") if not res["acceptance_pass"] else "n/a"}
    p = OUT / ("m6_mrs_%s_redshift%s.json" % (a.label, tag))
    p.write_text(json.dumps(res, indent=2, default=str))
    con.to_csv(OUT / ("m6_mrs_%s_contaminant_spectrum%s.csv" % (a.label, tag)),
               index=False)
    star.to_csv(OUT / ("m6_mrs_%s_star_spectrum%s.csv" % (a.label, tag)),
                index=False)
    print("\nVERDICT " + json.dumps(res["verdict"], indent=2))
    print("->", p.name)


if __name__ == "__main__":
    main()
