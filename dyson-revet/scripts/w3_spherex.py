"""W3: SPHEREx QR2 forced aperture spectrophotometry at candidates D and I.

Route (all account-free, discovered from the IRSA SPHEREx docs/tutorials,
https://caltech-ipac.github.io/irsa-tutorials/spherex-cutouts/):
  1. IRSA TAP (https://irsa.ipac.caltech.edu/TAP):
       spherex.plane JOIN spherex.artifact -> science image URIs overlapping
       the target position (QR2 level-2 spectral image MEFs, 71.6 MB each).
  2. Server-side cutout: https://irsa.ipac.caltech.edu/{uri}?center={ra},{dec}d
       &size=120arcsec  (~20x20 px of the 6.15 arcsec detector pixels).
  3. Per cutout: wavelength at the target pixel from the WCS-WAVE extension
       (WCS key "W"); flux = background-subtracted aperture sum over the
       IMAGE extension (MJy/sr -> Jy via pixel solid angle); error from the
       VARIANCE extension; central-pixel FLAGS recorded.

Honesty notes (documented in M1 doc):
  - Aperture r = 2 px (~12.3 arcsec) with sigma-clipped annulus background
    (r = 4..7 px); NO aperture correction and no PSF weighting -> absolute
    scale is approximate; the deliverable is the SED *shape* vs wavelength.
  - SPHEREx PSF FWHM ~6 arcsec: the star and any arcsec-scale contaminant are
    BLENDED, exactly as in WISE W1/W2. What SPHEREx adds is 0.75-5 um
    *continuous spectral* coverage between Gaia/2MASS and WISE W3/W4.
  - Gaia position used at J2016 (proper motion to 2025.5 is <0.4 arcsec for
    both targets, negligible vs the 6.15 arcsec pixels).

Outputs: data/spherex/{label}_planes.csv, data/spherex/cut_* (cache),
         out/w3_spherex_{label}_sed.csv, out/w3_spherex_seds.png
"""

from __future__ import annotations

import io
import sys
import time
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyvo
import requests
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from astropy.wcs import WCS

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
SPX = ROOT / "data" / "spherex"
OUT = ROOT / "out"
SPX.mkdir(parents=True, exist_ok=True)

IRSA_TAP = "https://irsa.ipac.caltech.edu/TAP"
IRSA_BASE = "https://irsa.ipac.caltech.edu/"

TARGETS = {
    "D": dict(ra=351.96373, dec=5.10726),
    "I": dict(ra=144.97633, dec=7.00774),
}

# comparison photometry (Vega mag -> Jy), from w1_fetch outputs; zps as in
# w1_selection.py (Cohen+03, Jarrett+11)
ZP_JY = {"J": 1594.0, "H": 1024.0, "Ks": 666.8,
         "W1": 309.540, "W2": 171.787, "W3": 31.674, "W4": 8.363}
LAM_UM = {"J": 1.235, "H": 1.662, "Ks": 2.159,
          "W1": 3.3526, "W2": 4.6028, "W3": 11.5608, "W4": 22.0883}


def list_planes(label: str, ra: float, dec: float) -> pd.DataFrame:
    cache = SPX / f"{label}_planes.csv"
    if cache.exists():
        return pd.read_csv(cache)
    svc = pyvo.dal.TAPService(IRSA_TAP)
    q = f"""
    SELECT a.uri, p.energy_bandpassname AS band,
           p.time_bounds_lower AS mjd, p.obsid
    FROM spherex.plane p JOIN spherex.artifact a ON a.planeid = p.planeid
    WHERE CONTAINS(POINT('ICRS', {ra}, {dec}), p.poly) = 1
      AND p.dataproducttype = 'image' AND a.producttype = 'science'
    """
    df = svc.search(q).to_table().to_pandas()
    df.to_csv(cache, index=False)
    return df


def extract_one(uri: str, ra: float, dec: float, cache_key: Path) -> dict | None:
    if cache_key.exists():
        data = np.load(cache_key, allow_pickle=True)
        return dict(data["rec"].item())
    url = f"{IRSA_BASE}{uri}?center={ra},{dec}d&size=120arcsec"
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=180)
            r.raise_for_status()
            break
        except requests.RequestException:
            if attempt == 2:
                return None
            time.sleep(3)
    try:
        hdul = fits.open(io.BytesIO(r.content))
        img_h = hdul["IMAGE"]
        img = img_h.data.astype(float)
        var = hdul["VARIANCE"].data.astype(float)
        flags = hdul["FLAGS"].data
        w = WCS(img_h.header)
        x, y = w.world_to_pixel_values(ra, dec)
        x, y = float(x), float(y)
        ny, nx = img.shape
        if not (2 <= x <= nx - 3 and 2 <= y <= ny - 3):
            return None  # target too close to cutout/detector edge

        sw = WCS(img_h.header, fobj=hdul, key="W")
        sw.sip = None
        lam, bw = sw.pixel_to_world(x, y)

        yy, xx = np.mgrid[0:ny, 0:nx]
        rr = np.hypot(xx - x, yy - y)
        ap = rr <= 2.0
        ann = (rr >= 4.0) & (rr <= 7.0)
        good = np.isfinite(img)
        if not good[ap & good].size:
            return None
        _, bg, _ = sigma_clipped_stats(img[ann & good], sigma=3.0)
        npix = int((ap & good).sum())
        flux_sr = np.nansum(img[ap & good] - bg)          # MJy/sr * px
        pix_sr = w.proj_plane_pixel_area().to_value("sr")
        flux_jy = flux_sr * pix_sr * 1e6
        err_jy = float(np.sqrt(np.nansum(var[ap & good])) * pix_sr * 1e6)
        cflag = int(flags[int(round(y)), int(round(x))])
        rec = dict(lam_um=float(lam.to_value("um")),
                   bw_um=float(bw.to_value("um")),
                   flux_jy=float(flux_jy), err_jy=err_jy,
                   npix=npix, center_flag=cflag)
        np.savez_compressed(cache_key, rec=rec)
        return rec
    except Exception:  # noqa: BLE001 - malformed cutouts are skipped, counted
        return None


def run_target(label: str, ra: float, dec: float) -> pd.DataFrame:
    planes = list_planes(label, ra, dec)
    print(f"{label}: {len(planes)} science planes")
    rows, fails = [], 0
    for i, p in planes.iterrows():
        key = SPX / ("cut_" + Path(str(p["uri"])).stem + f"_{label}.npz")
        rec = extract_one(str(p["uri"]), ra, dec, key)
        if rec is None:
            fails += 1
            continue
        rec.update(band=p["band"], mjd=p["mjd"], uri=p["uri"])
        rows.append(rec)
        if (i + 1) % 25 == 0:
            print(f"  {label}: {i + 1}/{len(planes)} done ({fails} skipped)")
    df = pd.DataFrame(rows)
    df.to_csv(OUT / f"w3_spherex_{label}_sed.csv", index=False)
    print(f"{label}: extracted {len(df)} spectrophotometric points "
          f"({fails} skipped)")
    return df


def plot(seds: dict[str, pd.DataFrame]) -> None:
    phot = {}
    gc = pd.read_csv(ROOT / "data" / "photometry" / "candidates_gaia_chain.csv")
    for lab in seds:
        r = gc[gc["label"] == lab].iloc[0]
        mags = {"J": r["j_m"], "H": r["h_m"], "Ks": r["ks_m"],
                "W1": r["w1mpro"], "W2": r["w2mpro"],
                "W3": r["w3mpro"], "W4": r["w4mpro"]}
        phot[lab] = {b: ZP_JY[b] * 10 ** (-0.4 * m) for b, m in mags.items()}

    fig, axes = plt.subplots(1, len(seds), figsize=(7 * len(seds), 5.2))
    axes = np.atleast_1d(axes)
    for ax, (lab, df) in zip(axes, seds.items()):
        # bit 21 (2097152) is set on essentially every pixel incl. clean field
        # pixels (302/311 in the D cutouts) -> informational, not a defect;
        # exact bit meanings: SPHEREx Explanatory Supplement Sec 3.2.4 (IRSA).
        ok = (df["center_flag"].astype(np.int64) & ~np.int64(1 << 21)) == 0
        d = df[ok].copy()
        # robust display: drop >5-sigma flux outliers within 0.1-um bins
        d["_bin"] = (d["lam_um"] / 0.1).round()
        med = d.groupby("_bin")["flux_jy"].transform("median")
        mad = (d.groupby("_bin")["flux_jy"]
               .transform(lambda v: 1.4826 * np.median(np.abs(v - np.median(v)))
                          + 1e-6))
        d = d[np.abs(d["flux_jy"] - med) < 5 * mad]
        # global guard for isolated-bin artifacts (transients/bad pixels)
        cont = d[(d["lam_um"] > 1.0) & (d["lam_um"] < 3.0)]["flux_jy"].median()
        d = d[(d["flux_jy"] < 10 * cont) & (d["flux_jy"] > -2 * cont)]
        ax.errorbar(d["lam_um"], d["flux_jy"] * 1e3, yerr=d["err_jy"] * 1e3,
                    fmt=".", ms=4, alpha=0.45, lw=0.6, color="#3466a4",
                    label=f"SPHEREx QR2 ({len(d)} exposures)")
        for b, f in phot[lab].items():
            ax.plot(LAM_UM[b], f * 1e3, "s", ms=8, color="#c23b22", zorder=5)
            ax.annotate(b, (LAM_UM[b], f * 1e3), textcoords="offset points",
                        xytext=(4, 6), fontsize=8, color="#c23b22")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("wavelength [um]")
        ax.set_ylabel("flux density [mJy]")
        ax.set_title(f"Candidate {lab}: SPHEREx 0.75-5 um + catalog photometry")
        ax.legend(fontsize=9)
        ax.grid(alpha=0.25, which="both")
    fig.tight_layout()
    fig.savefig(OUT / "w3_spherex_seds.png", dpi=130)
    print("wrote out/w3_spherex_seds.png")


def main() -> None:
    seds = {}
    for lab, t in TARGETS.items():
        seds[lab] = run_target(lab, t["ra"], t["dec"])
    plot(seds)


if __name__ == "__main__":
    main()
