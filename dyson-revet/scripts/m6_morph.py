"""M6 N4: a training-free structure statistic on the AllWISE W3/W4 coadds.

M5 Sec 3.6 measured the residual exactly -- our reproducible nebular stage
rejects 31.2% at the RMSE gate where the paper's unpublished CNN rejects
49.0% -- and named the missing ingredient: image structure.  N1 can only
remove what somebody has catalogued; N2 measures the background LEVEL and is
blind to its SHAPE.  N4 reads the coadds themselves.

    python scripts/m6_morph.py coadd  --what calib      # coadd_id per position
    python scripts/m6_morph.py stats  --what calib      # the cutouts + S,A,G,C
    python scripts/m6_morph.py calibrate                # PR-1's threshold rule
    python scripts/m6_morph.py apply  --what rmse
    python scripts/m6_morph.py funnel

THE STATISTIC (M6 PR-1, fixed before any survivor was counted).  In an annulus
12" < r < 45" about the source, after 3-sigma iterative clipping of
neighbouring point sources:

    S = sigma_obs / sigma_exp

where sigma_obs is the robust dispersion (1.4826*MAD) of the PSF-smoothed
intensity in the annulus and sigma_exp is the dispersion the coadd's own
uncertainty image predicts under the same smoothing.  S is dimensionless, needs
no training set, and has a parameter-free null: on sky whose only structure is
noise, S -> 1.  A raised but FLAT background -- the thing N2 already measures --
leaves S at 1.

THE THRESHOLD is M5 PR-2's N2 rule verbatim, applied to S instead of w?sky:
percentile rank within |ecliptic latitude| bins of the |b| > 50 deg parent, max
over the two bands, cut at 0.99.  No new free parameter.

REPORTED AND NOT CUT (M5's N3 precedent): A the azimuthal asymmetry, G the
local gradient, C the source's concentration against the coadd PSF.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import threading
import time
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import requests

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "out"
CACHE = ROOT / "data" / "nebular" / "cache"
MORPH = ROOT / "data" / "morph"
MORPH.mkdir(parents=True, exist_ok=True)
OUT.mkdir(exist_ok=True)

from m5_nebular import (CALIB_BAND_DEG, ECL_BIN_DEG, GATOR,  # noqa: E402
                        SCORE_THRESHOLD, SENSITIVITY, ecliptic_lat, galactic,
                        nearest_per_row, positions_for)

IBE = "https://irsa.ipac.caltech.edu/ibe/data/wise/allwise/p3am_cdd"
PIX_AS = 1.375                      # AllWISE Atlas coadd plate scale
CUT_AS = 100.0                      # PR-1: 100" cutouts
R_IN_AS, R_OUT_AS = 12.0, 45.0      # PR-1: the measurement annulus
PSF_FWHM = {"w3": 6.5, "w4": 12.0}  # WISE Explanatory Supplement Sec IV.4.c
CLIP_SIGMA, CLIP_ITERS, DILATE_PIX = 3.0, 5, 2
NAN_TOL = 0.02                      # PR-1: <2% non-finite inside the annulus
CALIB_SEED = 20260824
CALIB_PER_BIN = 4000
NTHREAD = 8


# ------------------------------------------------------- coadd_id via Gator --
def parse_ipac_keepstr(txt: str) -> pd.DataFrame | None:
    """m5_nebular.parse_ipac, but a column that will not go numeric stays text.

    m5's version has a hard-coded whitelist of string columns and therefore
    turns `coadd_id` ("3524p045_ac51") into NaN.  Nothing else differs.
    """
    lines = txt.splitlines()
    hdr_i = [i for i, l in enumerate(lines) if l.startswith("|")]
    if not hdr_i:
        return None
    hl = lines[hdr_i[0]]
    names = [c.strip() for c in hl.strip("|").split("|")]
    pos = [i for i, ch in enumerate(hl) if ch == "|"]
    widths = [(a + 1, b) for a, b in zip(pos[:-1], pos[1:])]
    rows = []
    for l in lines[max(hdr_i) + 1:]:
        if not l.strip() or l.startswith(("\\", "|")):
            continue
        rows.append([l[a:b].strip() if b <= len(l) else l[a:].strip()
                     for a, b in widths])
    df = pd.DataFrame(rows, columns=names)
    for c in df.columns:
        num = pd.to_numeric(df[c], errors="coerce")
        nonblank = df[c].astype(str).str.strip().ne("")
        if nonblank.sum() == 0 or (num.notna() & nonblank).sum() >= 0.5 * nonblank.sum():
            df[c] = num
    return df


def cmd_coadd(a) -> None:
    pos = positions_for(a.what).reset_index(drop=True)
    if a.what == "calib":
        pos = stratified_calib(pos)
    cache = MORPH / f"m6_coadd_{a.what}.csv"
    if cache.exists() and not a.refresh:
        print(f"  {cache.name} exists ({len(pd.read_csv(cache)):,} rows) -- reuse")
        return
    cols = "designation,ra,dec,coadd_id,w3mpro,w4mpro,w3snr,w4snr"
    frames, chunk = [], 5000
    n = int(np.ceil(len(pos) / chunk))
    for k in range(n):
        lo, hi = k * chunk, min((k + 1) * chunk, len(pos))
        buf = io.StringIO()
        buf.write("|      ra      |     dec      |\n|   double     |   double     |\n")
        for x, y in zip(pos["ra"][lo:hi], pos["dec"][lo:hi]):
            buf.write(" %13.6f %13.6f\n" % (x, y))
        for att in range(5):
            try:
                t0 = time.time()
                r = requests.post(GATOR, data={
                    "catalog": "allwise_p3as_psd", "spatial": "Upload",
                    "uradius": "3.0", "uradunits": "arcsec", "outfmt": "1",
                    "selcols": cols},
                    files={"filename": ("pos.tbl", buf.getvalue())}, timeout=1800)
                r.raise_for_status()
                t = parse_ipac_keepstr(r.text)
                if t is None:
                    raise RuntimeError("no data block")
                t["_row"] = t["cntr_01"].astype(int) - 1 + lo
                frames.append(t)
                print("    chunk %d/%d (%d pos) -> %d rows in %.1fs"
                      % (k + 1, n, hi - lo, len(t), time.time() - t0), flush=True)
                break
            except Exception as e:                       # noqa: BLE001
                if att == 4:
                    raise SystemExit("chunk %d FAILED: %s" % (k, e))
                time.sleep(10 * (att + 1))
    g = pd.concat(frames, ignore_index=True)
    m = nearest_per_row(g, len(pos))
    out = pos.copy()
    for c in ("coadd_id", "w3mpro", "w4mpro", "w3snr", "w4snr", "dist_x"):
        out[c] = m[c].to_numpy() if c in m.columns else np.nan
    _, b = galactic(out["ra"].to_numpy(), out["dec"].to_numpy())
    out["glat"] = b
    out["ecl_lat"] = ecliptic_lat(out["ra"].to_numpy(), out["dec"].to_numpy())
    out.to_csv(cache, index=False)
    print("  %d positions, %d with a coadd_id -> %s"
          % (len(out), int(out["coadd_id"].notna().sum()), cache.name))


def stratified_calib(pos: pd.DataFrame) -> pd.DataFrame:
    """PR-1's seeded, ecliptic-stratified subsample of the |b|>50 parent."""
    p = pos.copy()
    p["ecl_lat"] = ecliptic_lat(p["ra"].to_numpy(), p["dec"].to_numpy())
    p["ecl_bin"] = np.floor(np.abs(p["ecl_lat"]) / ECL_BIN_DEG).astype(int)
    rng = np.random.default_rng(CALIB_SEED)
    keep = []
    for bn, g in p.groupby("ecl_bin"):
        take = min(CALIB_PER_BIN, len(g))
        keep.append(g.iloc[np.sort(rng.choice(len(g), take, replace=False))])
    s = pd.concat(keep).reset_index(drop=True)
    print("  PR-1 calibration subsample: %d of %d, seed %d, per bin: %s"
          % (len(s), len(p), CALIB_SEED,
             dict(s["ecl_bin"].value_counts().sort_index())))
    return s.drop(columns=["ecl_bin"])


# ------------------------------------------------------------- the cutouts --
_LOCAL = threading.local()


def session() -> requests.Session:
    if not hasattr(_LOCAL, "s"):
        _LOCAL.s = requests.Session()
    return _LOCAL.s


def fetch_cut(coadd_id: str, band: str, kind: str, ra: float, dec: float):
    from astropy.io import fits
    c = str(coadd_id)
    # AllWISE Atlas stores int- uncompressed and unc-/cov- gzipped; IBE
    # decompresses on the fly when asked for gzip=false.
    suf = ".fits" if kind == "int" else ".fits.gz"
    url = "%s/%s/%s/%s/%s-%s-%s-3%s" % (IBE, c[:2], c[:4], c, c, band, kind, suf)
    # MEASURED 2026-08-24: IBE answers 503 in ~0.1 s when a client exceeds its
    # concurrency limit -- the same instant-failure signature M3 Sec 1.1
    # diagnosed on ESAC.  A 503 is NOT a missing image, and a run that records
    # it as one silently marks good objects invalid.  So 5xx/429 back off and
    # then RAISE, and only a real 404 returns None.
    for att in range(6):
        try:
            r = session().get(url, params={"center": "%.6f,%.6f" % (ra, dec),
                                           "size": "%.0farcsec" % CUT_AS,
                                           "gzip": "false"}, timeout=120)
            if r.status_code == 404:
                return None
            if r.status_code in (429, 500, 502, 503, 504):
                raise RuntimeError("throttled %d" % r.status_code)
            r.raise_for_status()
            with fits.open(io.BytesIO(r.content), memmap=False) as h:
                return np.asarray(h[0].data, float)
        except Exception:                                # noqa: BLE001
            if att == 5:
                raise
            time.sleep(2.0 * (2 ** att))
    return None


def nan_gauss(img: np.ndarray, sig_pix: float) -> np.ndarray:
    """Gaussian smoothing that ignores NaNs (mask-renormalised)."""
    from scipy.ndimage import gaussian_filter
    ok = np.isfinite(img).astype(float)
    z = np.where(np.isfinite(img), img, 0.0)
    num = gaussian_filter(z, sig_pix, mode="nearest")
    den = gaussian_filter(ok, sig_pix, mode="nearest")
    with np.errstate(invalid="ignore", divide="ignore"):
        out = num / den
    out[den < 0.2] = np.nan
    return out


def kernel_sq_sum(sig_pix: float) -> float:
    """sum(k^2) for a normalised 2-D Gaussian kernel -> variance shrink factor."""
    n = int(np.ceil(6 * sig_pix)) | 1
    y, x = np.mgrid[:n, :n] - (n // 2)
    k = np.exp(-(x ** 2 + y ** 2) / (2 * sig_pix ** 2))
    k /= k.sum()
    return float((k ** 2).sum())


def measure(img: np.ndarray, unc: np.ndarray, band: str) -> dict:
    """PR-1's S (primary) plus A, G, C (reported, not cut)."""
    from astropy.stats import sigma_clip
    from scipy.ndimage import binary_dilation
    out = {"ok": False, "reason": ""}
    npix = int(round(CUT_AS / PIX_AS))
    if img is None or unc is None:
        out["reason"] = "no_image"
        return out
    if (abs(img.shape[0] - npix) > 2 or abs(img.shape[1] - npix) > 2
            or img.shape != unc.shape):
        out["reason"] = "clipped_at_tile_edge"
        return out
    ny, nx = img.shape
    cy, cx = (ny - 1) / 2.0, (nx - 1) / 2.0
    yy, xx = np.mgrid[:ny, :nx]
    r_as = np.hypot(xx - cx, yy - cy) * PIX_AS
    ann = (r_as >= R_IN_AS) & (r_as <= R_OUT_AS)
    bad = ~np.isfinite(img) | ~np.isfinite(unc) | (unc <= 0)
    out["nan_frac"] = float(bad[ann].mean())
    if out["nan_frac"] > NAN_TOL:
        out["reason"] = "nan_fraction"
        return out
    # 3-sigma iterative clip of neighbouring point sources, then dilate
    cl = sigma_clip(np.where(bad, np.nan, img)[ann], sigma=CLIP_SIGMA,
                    maxiters=CLIP_ITERS, masked=True)
    src = np.zeros_like(img, bool)
    src[ann] = np.asarray(cl.mask)
    src = binary_dilation(src, iterations=DILATE_PIX) | bad
    out["clip_frac"] = float(src[ann].mean())
    work = np.where(src, np.nan, img)
    var = np.where(src, np.nan, unc.astype(float) ** 2)
    sig_pix = PSF_FWHM[band] / 2.3548 / PIX_AS
    sm = nan_gauss(work, sig_pix)
    svar = nan_gauss(var, sig_pix) * kernel_sq_sum(sig_pix) * (2 * np.pi * sig_pix ** 2)
    use = ann & np.isfinite(sm) & np.isfinite(svar) & ~src
    n = int(use.sum())
    out["n_ann"] = n
    if n < 200:
        out["reason"] = "too_few_annulus_pixels"
        return out
    v = sm[use]
    med = float(np.median(v))
    sig_obs = 1.4826 * float(np.median(np.abs(v - med)))
    sig_exp = float(np.sqrt(np.median(svar[use])))
    if not np.isfinite(sig_exp) or sig_exp <= 0:
        out["reason"] = "bad_uncertainty"
        return out
    out["S"] = sig_obs / sig_exp
    out["level"] = med
    out["sig_exp"] = sig_exp
    # A: azimuthal asymmetry -- dispersion of 12 sector medians, in noise units
    th = np.arctan2(yy - cy, xx - cx)
    sect = ((th + np.pi) / (2 * np.pi) * 12).astype(int) % 12
    meds = [np.median(sm[use & (sect == s)]) for s in range(12)
            if int((use & (sect == s)).sum()) >= 8]
    out["A"] = (1.4826 * float(np.median(np.abs(np.array(meds) - np.median(meds))))
                / sig_exp) if len(meds) >= 8 else np.nan
    # G: plane gradient across one PSF beam, in noise units
    A_ = np.column_stack([(xx[use] - cx) * PIX_AS, (yy[use] - cy) * PIX_AS,
                          np.ones(n)])
    try:
        co = np.linalg.lstsq(A_, v, rcond=None)[0]
        out["G"] = float(np.hypot(co[0], co[1]) * PSF_FWHM[band] / sig_exp)
    except np.linalg.LinAlgError:
        out["G"] = np.nan
    # C: source concentration against the coadd PSF
    base = np.where(bad, np.nan, img) - med
    f1 = float(np.nansum(base[r_as <= PSF_FWHM[band]]))
    f2 = float(np.nansum(base[r_as <= 2 * PSF_FWHM[band]]))
    out["C"] = f1 / f2 if f2 > 0 else np.nan
    out["ok"] = True
    return out


def one_object(row) -> dict:
    rec = {"_row": int(row["_row"]), "source_id": row.get("source_id", np.nan)}
    cid = row["coadd_id"]
    if not isinstance(cid, str) or not cid.strip():
        rec["morph_ok"] = False
        rec["reason"] = "no_coadd_id"
        return rec
    okall = True
    for band in ("w3", "w4"):
        try:
            img = fetch_cut(cid, band, "int", row["ra"], row["dec"])
            unc = fetch_cut(cid, band, "unc", row["ra"], row["dec"])
        except Exception as e:                           # noqa: BLE001
            # the service refused, not the image missing.  Mark it so the
            # resume logic re-issues it instead of caching a false invalid.
            rec["morph_ok"] = False
            rec["reason"] = "fetch_failed"
            rec["w3_reason"] = rec["w4_reason"] = "fetch_failed"
            rec["_err"] = type(e).__name__
            return rec
        m = measure(img, unc, band)
        for k in ("S", "A", "G", "C", "level", "sig_exp", "nan_frac",
                  "clip_frac", "n_ann"):
            rec["%s_%s" % (band, k)] = m.get(k, np.nan)
        rec["%s_ok" % band] = bool(m["ok"])
        rec["%s_reason" % band] = m.get("reason", "")
        okall = okall and m["ok"]
    rec["morph_ok"] = okall
    return rec


def cmd_stats(a) -> None:
    src = MORPH / f"m6_coadd_{a.what}.csv"
    if not src.exists():
        raise SystemExit(f"run `coadd --what {a.what}` first")
    pos = pd.read_csv(src)
    pos["_row"] = np.arange(len(pos))
    base = MORPH / f"m6_morph_{a.what}.csv"
    # --part i --nparts n splits the work over n processes with DISJOINT row
    # sets and separate caches, so two clients never write the same file.  Every
    # part cache is read back in at merge time, so the product is identical to a
    # single run.  IRSA's per-client cap means this is only worth doing when the
    # single-process rate is below it (measured 2026-08-24: ~12 requests/s).
    cache = (base if a.nparts <= 1
             else MORPH / f"m6_morph_{a.what}_p{a.part}.csv")
    done = set()
    frames = []
    for other in sorted(MORPH.glob(f"m6_morph_{a.what}_p*.csv")) + [base]:
        if other == cache or not other.exists():
            continue
        o = pd.read_csv(other)
        ok = o[~o.get("w3_reason", pd.Series("", index=o.index)).fillna("")
               .isin({"fetch_failed", "no_image"})]
        done |= set(ok["_row"].astype(int))
    if done:
        print(f"  {len(done):,} rows already done by another part/cache")
    if cache.exists() and not a.refresh:
        prev = pd.read_csv(cache)
        # A row whose cutout FAILED TO FETCH is not a measurement; it is a
        # service refusal (see fetch_cut).  Drop it from the cache so the
        # resume re-issues it.  A row that measured and failed on its own
        # merits -- tile-edge clip, NaN fraction -- is kept.
        badreason = {"fetch_failed", "no_image"}
        bad = (prev.get("w3_reason").fillna("").isin(badreason)
               | prev.get("w4_reason").fillna("").isin(badreason)
               | prev.get("reason", pd.Series("", index=prev.index)).fillna("")
               .isin(badreason))
        if int(bad.sum()):
            print(f"  dropping {int(bad.sum()):,} cached rows whose cutout "
                  f"never arrived (service refusal, not a measurement)")
            prev = prev[~bad]
        done |= set(prev["_row"].astype(int))
        frames.append(prev)
        print(f"  resuming: {len(done):,} of {len(pos):,} already measured")
    todo = pos[~pos["_row"].isin(done)]
    if a.nparts > 1:
        todo = todo[todo["_row"] % a.nparts == a.part]
        print(f"  part {a.part}/{a.nparts}: {len(todo):,} rows in this slice")
    print(f"  {len(todo):,} objects x 4 cutouts, {NTHREAD} threads")
    t0, chunk, buf = time.time(), 500, []
    with ThreadPoolExecutor(max_workers=NTHREAD) as ex:
        for i, rec in enumerate(ex.map(one_object,
                                       (r for _, r in todo.iterrows())), 1):
            buf.append(rec)
            if i % chunk == 0 or i == len(todo):
                frames.append(pd.DataFrame(buf))
                buf = []
                pd.concat(frames, ignore_index=True).to_csv(cache, index=False)
                el = time.time() - t0
                print("    %6d/%d  %.1f obj/s  eta %.0f min"
                      % (i, len(todo), i / el, (len(todo) - i) / max(i / el, 1e-9) / 60),
                      flush=True)
    if buf:
        frames.append(pd.DataFrame(buf))
    for other in sorted(MORPH.glob(f"m6_morph_{a.what}_p*.csv")) + [base]:
        if other != cache and other.exists():
            frames.append(pd.read_csv(other))
    res = pd.concat(frames, ignore_index=True)
    res = (res.sort_values("morph_ok", ascending=False)
           .drop_duplicates("_row", keep="first"))
    merged = pos.merge(res.drop(columns=[c for c in ("source_id",) if c in res]),
                       on="_row", how="left")
    # the 28,000-row calibration table is bulk and lives under data/
    # (gitignored) exactly as M5 Sec 8 put its own; the survivor tables,
    # which are small and are the product, go to out/.
    path = (MORPH if a.what == "calib" else OUT) / f"m6_morph_{a.what}.csv"
    merged.to_csv(path, index=False)
    ok = int(merged["morph_ok"].fillna(False).sum())
    print("  %d/%d valid (%.1f%%) -> %s" % (ok, len(merged), 100 * ok / len(merged),
                                            path.name))


# ----------------------------------------------------------------- ranking --
_CAL4: pd.DataFrame | None = None


def calib4() -> pd.DataFrame:
    global _CAL4
    if _CAL4 is None:
        c = pd.read_csv(MORPH / "m6_morph_calib.csv")
        c = c[c["morph_ok"].fillna(False)
              & np.isfinite(c["w3_S"]) & np.isfinite(c["w4_S"])].copy()
        c["ecl_bin"] = np.floor(np.abs(c["ecl_lat"]) / ECL_BIN_DEG).astype(int)
        _CAL4 = c
    return _CAL4


def score4(df: pd.DataFrame, cal: pd.DataFrame | None = None) -> np.ndarray:
    """N4's score: N2's rule verbatim, on S instead of w?sky."""
    cal = calib4() if cal is None else cal
    d = df.copy()
    if "ecl_bin" not in d.columns:
        d["ecl_bin"] = np.floor(np.abs(d["ecl_lat"]) / ECL_BIN_DEG).astype(int)
    out = np.full(len(d), np.nan)
    for bn, g in d.groupby("ecl_bin"):
        ref = cal[cal["ecl_bin"] == bn]
        if len(ref) < 50:
            order = cal["ecl_bin"].unique()
            ref = cal[cal["ecl_bin"] == order[np.argmin(np.abs(order - bn))]]
        r3 = np.searchsorted(np.sort(ref["w3_S"].to_numpy()),
                             g["w3_S"].to_numpy(), side="right") / len(ref)
        r4 = np.searchsorted(np.sort(ref["w4_S"].to_numpy()),
                             g["w4_S"].to_numpy(), side="right") / len(ref)
        sc = np.maximum(r3, r4)
        sc[~(np.isfinite(g["w3_S"].to_numpy()) & np.isfinite(g["w4_S"].to_numpy()))] = np.nan
        out[d.index.get_indexer(g.index)] = sc
    return out


def cmd_calibrate(a) -> None:
    c = calib4()
    rows = []
    for band in ("w3_S", "w4_S"):
        for bn, g in c.groupby("ecl_bin"):
            for q in SENSITIVITY:
                rows.append({"stat": band, "ecl_bin": int(bn), "q": q,
                             "n": int(len(g)), "value": float(np.quantile(g[band], q))})
    pd.DataFrame(rows).to_csv(OUT / "m6_morph_thresholds.csv", index=False)
    sc = score4(c, c)
    meas = {str(q): float(np.nanmean(sc > q)) for q in SENSITIVITY}
    raw = pd.read_csv(MORPH / "m6_morph_calib.csv")
    summary = {
        "calibration_population":
            f"parent sample at |b| > {CALIB_BAND_DEG:.0f} deg, PR-1 stratified "
            f"subsample (seed {CALIB_SEED}, <= {CALIB_PER_BIN}/ecliptic bin)",
        "n_requested": int(len(raw)),
        "n_valid": int(len(c)),
        "valid_fraction": float(len(c) / max(len(raw), 1)),
        "invalid_reasons": {k: int(v) for k, v in
                            pd.concat([raw["w3_reason"], raw["w4_reason"]])
                            .fillna("").replace("", np.nan).dropna()
                            .value_counts().items()},
        "ecl_bin_deg": ECL_BIN_DEG,
        "per_bin_n": {str(int(k)): int(v) for k, v in
                      c["ecl_bin"].value_counts().sort_index().items()},
        "rule": ("score = max(percentile rank of W3 S, percentile rank of W4 S) "
                 "within the object's |ecliptic latitude| bin of the calibration "
                 "population; flagged if score > 0.99 (M6 PR-1) -- M5 PR-2's N2 "
                 "rule verbatim, on S instead of w?sky"),
        "threshold": SCORE_THRESHOLD,
        "measured_combined_FPR_on_calibration": meas,
        "S_null": {"w3_median": float(c["w3_S"].median()),
                   "w4_median": float(c["w4_S"].median()),
                   "w3_q99": float(c["w3_S"].quantile(0.99)),
                   "w4_q99": float(c["w4_S"].quantile(0.99)),
                   "note": "on nebulosity-free sky S should approach its "
                           "parameter-free null of 1; it sits slightly above "
                           "because AllWISE coadd noise is spatially "
                           "correlated by the resampling, which the per-pixel "
                           "uncertainty image does not carry"},
        "spearman_w3S_w4S": float(c["w3_S"].corr(c["w4_S"], method="spearman")),
        "diagnostic_corr_S_vs_source_brightness": {
            "w3_spearman_S_w3mpro": float(c["w3_S"].corr(c["w3mpro"], method="spearman")),
            "w4_spearman_S_w4mpro": float(c["w4_S"].corr(c["w4mpro"], method="spearman"))},
        "reported_not_cut": {
            "A_w3_median": float(c["w3_A"].median()), "A_w4_median": float(c["w4_A"].median()),
            "G_w3_median": float(c["w3_G"].median()), "G_w4_median": float(c["w4_G"].median()),
            "C_w3_median": float(c["w3_C"].median()), "C_w4_median": float(c["w4_C"].median())},
    }
    (OUT / "m6_morph_calibration.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


def cmd_apply(a) -> None:
    m = pd.read_csv(OUT / f"m6_morph_{a.what}.csv")
    m["n4_score"] = score4(m)
    for q in SENSITIVITY:
        m[f"n4_flag_{q}"] = (m["n4_score"] > q) & m["morph_ok"].fillna(False)
    m["n4_flag"] = (m["n4_score"] > SCORE_THRESHOLD) & m["morph_ok"].fillna(False)
    path = OUT / f"m6_morph_flags_{a.what}.csv"
    m.to_csv(path, index=False)
    print("  %s: %d positions, %d valid, N4 flags %d (%.1f%% of valid)"
          % (a.what, len(m), int(m["morph_ok"].fillna(False).sum()),
             int(m["n4_flag"].sum()),
             100 * m["n4_flag"].sum() / max(int(m["morph_ok"].fillna(False).sum()), 1)))
    print("  ->", path.name)


SKY_DEG2 = 41252.96124
BANDS = [(0, 5), (5, 10), (10, 20), (20, 30), (30, 50), (50, 90)]
PAPER = {"rmse": 11243, "post_cnn": 5732, "extra": 5137, "snr": 368}


def band_area(lo, hi):
    """Area of the band |b| in [lo, hi], BOTH hemispheres, in deg^2.

    Omega = 2 * 2*pi*(sin hi - sin lo); checked against M5 Sec 3.4's own
    areas (0-5 deg -> 3595.4 deg^2, all sky -> 41,253 deg^2).
    """
    return (4 * np.pi * (np.sin(np.radians(hi)) - np.sin(np.radians(lo)))
            * (180 / np.pi) ** 2)


def cmd_funnel(a) -> None:
    """M5 Sec 3.4's funnel with N4 added at the same position in Table 4."""
    rm = pd.read_csv(OUT / "w4_rmse_survivors_m4_g0.1.csv")
    neb = pd.read_csv(OUT / "m5_nebular_flags_rmse.csv")
    m4 = pd.read_csv(OUT / "m6_morph_flags_rmse.csv")
    assert (rm["source_id"].to_numpy() == neb["source_id"].to_numpy()).all()
    d = rm.reset_index(drop=True).copy()
    d["glat"] = neb["glat"].to_numpy()
    d["n1_flag"] = neb["n1_flag"].to_numpy()
    d["n2_flag"] = neb["n2_flag"].to_numpy()
    d["neb_m5"] = neb["nebular_flag"].to_numpy()
    mm = m4.set_index("source_id").reindex(d["source_id"])
    for c in ("n4_flag", "morph_ok", "n4_score", "w3_S", "w4_S", "w3_A", "w4_A",
              "w3_G", "w4_G", "w3_C", "w4_C"):
        d[c] = mm[c].to_numpy() if c in mm.columns else np.nan
    for q in SENSITIVITY:
        d[f"n4_flag_{q}"] = (mm[f"n4_flag_{q}"].to_numpy()
                             if f"n4_flag_{q}" in mm.columns else False)
    d["n4_flag"] = d["n4_flag"].fillna(False).astype(bool)
    d["morph_ok"] = d["morph_ok"].fillna(False).astype(bool)
    d["neb_m6"] = d["neb_m5"].astype(bool) | d["n4_flag"]
    d["ab"] = np.abs(d["glat"])
    d.to_csv(OUT / "m6_rmse_survivors_morph_m4_g0.1.csv", index=False)

    extra = d["extra_ok"].astype(bool)
    snr = d["snr_ok"].astype(bool)
    out = {"n_rmse": len(d),
           "morph_measured": int(d["morph_ok"].sum()),
           "morph_measured_frac": float(d["morph_ok"].mean())}
    print("N4 measured for %d of %d RMSE survivors (%.1f%%)"
          % (out["morph_measured"], len(d), 100 * out["morph_measured_frac"]))
    for tag, keepmask in (("M5 N1|N2", ~d["neb_m5"].astype(bool)),
                          ("M6 N4 alone", ~d["n4_flag"]),
                          ("M6 N1|N2|N4", ~d["neb_m6"])):
        rows = [("RMSE <= 0.2", len(d), PAPER["rmse"]),
                ("+ nebular stage", int(keepmask.sum()), PAPER["post_cnn"]),
                ("+ extra cuts", int((keepmask & extra).sum()), PAPER["extra"]),
                ("+ S/N >= 3.5 (pre-visual)",
                 int((keepmask & extra & snr).sum()), PAPER["snr"])]
        f = {}
        print("\n== funnel with %s ==" % tag)
        for name, ours, theirs in rows:
            f[name] = {"ours": ours, "paper": theirs, "ratio": ours / theirs}
            print("  %-30s %7d   paper %7d   %.3fx" % (name, ours, theirs,
                                                       ours / theirs))
        rej = 1 - rows[1][1] / rows[0][1]
        f["reject_frac_at_rmse"] = rej
        f["paper_cnn_reject_frac"] = 1 - PAPER["post_cnn"] / PAPER["rmse"]
        f["gap_points"] = 100 * (f["paper_cnn_reject_frac"] - rej)
        print("  rejects %.1f%% at the RMSE gate; the paper's CNN rejects "
              "%.1f%%; gap %.1f points"
              % (100 * rej, 100 * f["paper_cnn_reject_frac"], f["gap_points"]))
        out[tag] = f

    # latitude behaviour of N4 alone, and of the union
    rate = PAPER["snr"] / SKY_DEG2 * 1000.0
    lat = []
    for lo, hi in BANDS:
        s = d[(d["ab"] >= lo) & (d["ab"] < hi)]
        area = band_area(lo, hi)
        pre5 = int(((~s["neb_m5"].astype(bool)) & s["extra_ok"].astype(bool)
                    & s["snr_ok"].astype(bool)).sum())
        pre6 = int(((~s["neb_m6"]) & s["extra_ok"].astype(bool)
                    & s["snr_ok"].astype(bool)).sum())
        raw = int((s["extra_ok"].astype(bool) & s["snr_ok"].astype(bool)).sum())
        lat.append({"band": "%d-%d" % (lo, hi), "area_deg2": area,
                    "n_rmse": len(s),
                    "n4_flag_frac_of_rmse": float(s["n4_flag"].mean()),
                    "n4_measured_frac": float(s["morph_ok"].mean()),
                    "median_maxS": float(np.nanmedian(
                        np.maximum(s["w3_S"], s["w4_S"]))) if len(s) else None,
                    "previsual_raw": raw, "previsual_m5": pre5,
                    "previsual_m6": pre6,
                    "x_before": raw / (rate * area / 1000.0),
                    "x_after_m5": pre5 / (rate * area / 1000.0),
                    "x_after_m6": pre6 / (rate * area / 1000.0)})
    out["latitude"] = lat
    print("\n|b|        n_rmse  N4 flags  med max(S)   pre(raw)  pre(M5)  "
          "pre(M6)   x_before  x_M5   x_M6")
    for r in lat:
        print("  %-7s %7d   %6.1f%%     %6.3f    %7d  %7d  %7d   %7.2f %6.2f %6.2f"
              % (r["band"], r["n_rmse"], 100 * r["n4_flag_frac_of_rmse"],
                 r["median_maxS"] or float("nan"), r["previsual_raw"],
                 r["previsual_m5"], r["previsual_m6"], r["x_before"],
                 r["x_after_m5"], r["x_after_m6"]))

    # what N4 ADDS beyond N1|N2 -- the number that says whether it is a new axis
    v = d[d["morph_ok"]]
    n1 = v["n1_flag"].astype(bool)
    n2 = v["n2_flag"].astype(bool)
    n4 = v["n4_flag"].astype(bool)
    out["overlap"] = {
        "n_valid": int(len(v)),
        "n1_only": int((n1 & ~n2 & ~n4).sum()),
        "n2_only": int((~n1 & n2 & ~n4).sum()),
        "n4_only": int((~n1 & ~n2 & n4).sum()),
        "n1_and_n4": int((n1 & n4).sum()), "n2_and_n4": int((n2 & n4).sum()),
        "any_of_three": int((n1 | n2 | n4).sum()),
        "n1_or_n2": int((n1 | n2).sum()),
        "n4_share_of_flagged": float(n4.mean()),
        "n4_new_rejections": int((n4 & ~(n1 | n2)).sum()),
        "n4_new_rejections_frac_of_rmse": float((n4 & ~(n1 | n2)).mean())}
    o = out["overlap"]
    print("\nWhat N4 adds beyond N1|N2, on the %d survivors with a valid "
          "cutout:" % o["n_valid"])
    print("  N1|N2 flags %d; adding N4 takes it to %d; N4's OWN new "
          "rejections: %d (%.1f%% of the RMSE survivors)"
          % (o["n1_or_n2"], o["any_of_three"], o["n4_new_rejections"],
             100 * o["n4_new_rejections_frac_of_rmse"]))
    print("  N4-only %d | N1-only %d | N2-only %d | N1&N4 %d | N2&N4 %d"
          % (o["n4_only"], o["n1_only"], o["n2_only"], o["n1_and_n4"],
             o["n2_and_n4"]))

    # PR-1 validation (a) 7/7, (c) sensitivity band
    cand = pd.read_csv(OUT / "m6_morph_flags_candidates.csv")
    out["validation_7of7"] = {
        "n_labelled": int(len(cand)),
        "n4_flagged": int(cand["n4_flag"].fillna(False).sum()),
        "flagged_labels": list(cand.loc[cand["n4_flag"].fillna(False), "label"]),
        "scores": {str(r["label"]): float(r["n4_score"])
                   for _, r in cand.iterrows()},
        "published_seven_preserved": bool(
            cand[cand["label"].isin(list("ABCDEFG"))]["n4_flag"]
            .fillna(False).sum() == 0)}
    sens = {}
    for q in SENSITIVITY:
        k = ~(d["neb_m5"].astype(bool) | d[f"n4_flag_{q}"].astype(bool))
        sens[str(q)] = int((k & extra & snr).sum())
    out["sensitivity_previsual_counts"] = sens
    print("\nPR-1 (a): %d of %d labelled objects flagged by N4 %s; the seven "
          "published candidates preserved: %s"
          % (out["validation_7of7"]["n4_flagged"], len(cand),
             out["validation_7of7"]["flagged_labels"],
             out["validation_7of7"]["published_seven_preserved"]))
    print("PR-1 (c) sensitivity, pre-visual survivors with N1|N2|N4 at "
          "0.95/0.99/0.999: %s" % sens)
    (OUT / "m6_funnel_morph.json").write_text(json.dumps(out, indent=2))
    print("\n-> out/m6_funnel_morph.json")


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("funnel")
    for name in ("coadd", "stats", "apply"):
        p = sub.add_parser(name)
        p.add_argument("--what", default="rmse",
                       choices=["calib", "rmse", "previsual", "candidates"])
        p.add_argument("--refresh", action="store_true")
        p.add_argument("--part", type=int, default=0)
        p.add_argument("--nparts", type=int, default=1)
    sub.add_parser("calibrate")
    a = ap.parse_args()
    {"coadd": cmd_coadd, "stats": cmd_stats, "calibrate": cmd_calibrate,
     "apply": cmd_apply, "funnel": cmd_funnel}[a.cmd](a)


if __name__ == "__main__":
    main()
