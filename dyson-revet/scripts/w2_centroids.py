"""W2(a): centroid-offset test on candidates D and I, with C as the control.

Method (per Ren et al. 2026, arXiv:2607.03619 Sec 2-3):
  1. Fetch 1x1 arcmin AllWISE Atlas intensity cutouts (W1-W4) from IRSA IBE
     (account-free), plus unWISE full-depth coadd cutouts (unwise.me) as a
     second imaging basis.
  2. Propagate the Gaia DR3 position (epoch J2016.0) back to the AllWISE
     per-band mean epoch using Gaia proper motions.
  3. Measure the MIR emission centroid near the star: background-subtracted
     flux-weighted first moments inside a box centred on the brightest pixel
     within 10 arcsec of the propagated position (Ren used SEP where the SNR
     allowed and scipy.ndimage.center_of_mass for low-SNR W3/W4; the moment
     centroid below is equivalent to the latter).
  4. Report offset (arcsec) and centroiding uncertainty FWHM/(2.355*SNR)
     (Ren eq. 1), with SNR measured in a 3-pixel-radius aperture.

Validation targets (Ren 2026 Tables 5-6, offsets in arcsec):
  C: W1 0.82  W2 0.76  W3 3.67+-0.25  W4 4.98+-2.15   <- published refutation
  D: W1 0.53  W2 0.46  W3 0.75+-0.22  W4 1.80+-1.80   <- "cleanest" candidate
  I: W1 0.24  W2 0.40  W3 2.10+-0.62  W4 3.22+-2.15   <- low-SNR stripe in W3

Outputs: out/w2_centroid_offsets.csv, out/w2_cutout_{label}.png,
         data/cutouts/*.fits (gitignored)
"""

from __future__ import annotations

import io
import sys
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from astropy.wcs import WCS

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
CUT = ROOT / "data" / "cutouts"
OUT = ROOT / "out"
CUT.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

IBE_SEARCH = "https://irsa.ipac.caltech.edu/ibe/search/wise/allwise/p3am_cdd"
IBE_DATA = "https://irsa.ipac.caltech.edu/ibe/data/wise/allwise/p3am_cdd"

# label: gaia_id, ra/dec J2016 (deg), pmra/pmdec (mas/yr)  [Ren 2026 Table 1]
TARGETS = {
    "C": dict(sid=4649396037451459712, ra=74.01205, dec=-74.17051,
              pmra=39.525, pmdec=-19.288),
    "D": dict(sid=2660349163149053824, ra=351.96373, dec=5.10726,
              pmra=-30.674, pmdec=-21.611),
    "I": dict(sid=3854090071297359616, ra=144.97633, dec=7.00774,
              pmra=-4.744, pmdec=-14.760),
}
# AllWISE Atlas W1/W2 include the 3-band+NEOWISE cryo phases; per-band mean
# epochs below are the candidate w?mjd_mean values pulled by w1_fetch (fallback
# to Ren Table 1 epochs if the fetch has not run yet).
REN_EPOCHS = {  # (W1/W2 epoch, W3/W4 epoch), Julian years, Ren 2026 Table 1
    "C": (2010.78, 2010.29), "D": (2010.46, 2010.46), "I": (2010.36, 2010.35),
}
PSF_FWHM = {1: 6.1, 2: 6.4, 3: 6.5, 4: 12.0}  # arcsec, Ren 2026 / WISE docs


def ibe_find_tile(ra: float, dec: float) -> str:
    r = None
    for attempt in range(3):
        try:
            r = requests.get(IBE_SEARCH, params={"POS": f"{ra},{dec}"},
                             timeout=180)
            r.raise_for_status()
            break
        except requests.RequestException as e:
            print(f"  IBE search retry {attempt + 1}: {e}")
    if r is None:
        raise RuntimeError("IBE search failed after 3 attempts")
    rows = [ln for ln in r.text.splitlines() if ln and not ln.startswith(("\\", "|"))]
    # IPAC table: coadd_id is 1st data column
    cols = None
    for ln in r.text.splitlines():
        if ln.startswith("|"):
            cols = [c.strip() for c in ln.strip("|").split("|")]
            break
    idx = cols.index("coadd_id")
    best = rows[0].split()[idx]
    return best


def fetch_cutout(label: str, coadd_id: str, band: int, ra: float, dec: float,
                 size_arcsec: int = 90) -> Path:
    dest = CUT / f"{label}_w{band}_allwise.fits"
    if dest.exists():
        return dest
    url = (f"{IBE_DATA}/{coadd_id[:2]}/{coadd_id[:4]}/{coadd_id}/"
           f"{coadd_id}-w{band}-int-3.fits"
           f"?center={ra},{dec}&size={size_arcsec}arcsec")
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    dest.write_bytes(r.content)
    return dest


def fetch_unwise(label: str, ra: float, dec: float) -> Path | None:
    """unWISE full-depth (allwise version) W3/W4 cutouts, account-free."""
    dest = CUT / f"{label}_unwise.tgz"
    if dest.exists():
        return dest
    url = ("http://unwise.me/cutout_fits?version=allwise"
           f"&ra={ra}&dec={dec}&size=40&bands=34")
    try:
        r = requests.get(url, timeout=300)
        r.raise_for_status()
        dest.write_bytes(r.content)
        return dest
    except Exception as e:  # noqa: BLE001 - record and continue
        print(f"  unwise.me failed for {label}: {e}")
        return None


def propagate(t: dict, epoch_jyr: float) -> tuple[float, float]:
    """Gaia J2016.0 -> epoch, using PM (mas/yr). Returns (ra, dec) deg."""
    dt = epoch_jyr - 2016.0
    dec = t["dec"] + t["pmdec"] * dt / 3.6e6
    ra = t["ra"] + t["pmra"] * dt / 3.6e6 / np.cos(np.radians(t["dec"]))
    return ra, dec


def measure_centroid(path: Path, ra_exp: float, dec_exp: float, band: int
                     ) -> dict:
    """Flux-weighted centroid of the emission near (ra_exp, dec_exp)."""
    with fits.open(path) as hdul:
        img = hdul[0].data.astype(float)
        wcs = WCS(hdul[0].header)
    mean, med, std = sigma_clipped_stats(img, sigma=3.0)
    sub = img - med
    px_scale = np.abs(wcs.proj_plane_pixel_scales()[0].to_value("arcsec"))
    x_exp, y_exp = wcs.world_to_pixel_values(ra_exp, dec_exp)

    # search box: brightest pixel within 10 arcsec of expected position
    r_search = int(round(10.0 / px_scale))
    yy, xx = np.mgrid[0:sub.shape[0], 0:sub.shape[1]]
    mask_search = (xx - x_exp) ** 2 + (yy - y_exp) ** 2 <= r_search ** 2
    peak_idx = np.nanargmax(np.where(mask_search, sub, -np.inf))
    py, px = np.unravel_index(peak_idx, sub.shape)

    # centroid box: +-1 PSF FWHM around the peak (moments over positive flux)
    r_box = max(2, int(round(PSF_FWHM[band] / px_scale)))
    y0, y1 = max(0, py - r_box), min(sub.shape[0], py + r_box + 1)
    x0, x1 = max(0, px - r_box), min(sub.shape[1], px + r_box + 1)
    box = np.clip(sub[y0:y1, x0:x1], 0, None)
    tot = box.sum()
    cy = (np.arange(y0, y1)[:, None] * box).sum() / tot
    cx = (np.arange(x0, x1)[None, :] * box).sum() / tot

    # aperture SNR at the centroid (r = 1 FWHM aperture). Noise = scatter of
    # the same aperture placed at random source-free positions, which captures
    # the correlated noise of the interpolated Atlas coadds (a per-pixel
    # std*sqrt(Npix) estimate overstates SNR by ~5-10x there).
    r_ap = PSF_FWHM[band] / px_scale
    ap_mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= r_ap ** 2
    flux = sub[ap_mask].sum()
    rng = np.random.default_rng(42)
    bg_fluxes = []
    h, w = sub.shape
    for _ in range(600):
        rx = rng.uniform(r_ap, w - r_ap)
        ry = rng.uniform(r_ap, h - r_ap)
        if np.hypot(rx - cx, ry - cy) < 3 * r_ap:
            continue
        m = (xx - rx) ** 2 + (yy - ry) ** 2 <= r_ap ** 2
        val = sub[m]
        if np.nanmax(val) > 5 * std:  # avoid real sources
            continue
        bg_fluxes.append(np.nansum(val))
        if len(bg_fluxes) >= 200:
            break
    noise = np.std(bg_fluxes) if len(bg_fluxes) > 20 else std * np.sqrt(ap_mask.sum())
    snr = flux / noise

    ra_c, dec_c = wcs.pixel_to_world_values(cx, cy)
    off = angsep(ra_c, dec_c, ra_exp, dec_exp)
    sig_pos = PSF_FWHM[band] / (2.355 * max(snr, 0.1))
    return dict(ra_centroid=float(ra_c), dec_centroid=float(dec_c),
                offset_arcsec=float(off), snr=float(snr),
                sigma_pos_arcsec=float(sig_pos),
                peak_ra=float(wcs.pixel_to_world_values(px, py)[0]),
                peak_dec=float(wcs.pixel_to_world_values(px, py)[1]))


def angsep(ra1, dec1, ra2, dec2) -> float:
    """Angular separation in arcsec (small-angle, fine at <1 arcmin)."""
    dra = (ra1 - ra2) * np.cos(np.radians(0.5 * (dec1 + dec2)))
    ddec = dec1 - dec2
    return float(np.hypot(dra, ddec) * 3600.0)


def measure_unwise(label: str, t: dict) -> list[dict]:
    """Second imaging basis: unWISE full-depth W3/W4 coadds (Lang 2014;
    'allwise' version, unwise.me cutouts). Same 2010 epochs as AllWISE."""
    import gzip
    import tarfile
    out = []
    tgz = CUT / f"{label}_unwise.tgz"
    if not tgz.exists():
        return out
    with tarfile.open(tgz) as tf:
        for m in tf.getmembers():
            if m.name.endswith("-img-m.fits"):
                band = 3 if "-w3-" in m.name else 4
                dest = CUT / f"{label}_w{band}_unwise.fits"
                if not dest.exists():
                    dest.write_bytes(tf.extractfile(m).read())
                ep = REN_EPOCHS[label][1]
                ra_e, dec_e = propagate(t, ep)
                r = measure_centroid(dest, ra_e, dec_e, band)
                r.update(label=label, band=f"W{band}u", epoch=ep,
                         basis="unWISE")
                out.append(r)
                print(f"  unWISE W{band}: offset {r['offset_arcsec']:.2f}\" "
                      f"+- {r['sigma_pos_arcsec']:.2f}\" (ap SNR {r['snr']:.1f})")
    return out


def main() -> None:
    rows = []
    for label, t in TARGETS.items():
        print(f"== candidate {label}")
        have_all = all((CUT / f"{label}_w{b}_allwise.fits").exists()
                       for b in (1, 2, 3, 4))
        tile = None if have_all else ibe_find_tile(t["ra"], t["dec"])
        print(f"  AllWISE tile {tile or '(cutouts cached)'}")
        fetch_unwise(label, t["ra"], t["dec"])
        fig, axes = plt.subplots(1, 4, figsize=(16, 4.2))
        for band in (1, 2, 3, 4):
            path = fetch_cutout(label, tile, band, t["ra"], t["dec"])
            ep = REN_EPOCHS[label][0 if band <= 2 else 1]
            ra_e, dec_e = propagate(t, ep)
            m = measure_centroid(path, ra_e, dec_e, band)
            m.update(label=label, band=f"W{band}", epoch=ep)
            rows.append(m)
            print(f"  W{band}: offset {m['offset_arcsec']:.2f}\" "
                  f"+- {m['sigma_pos_arcsec']:.2f}\"  (ap SNR {m['snr']:.1f})")
            # panel
            with fits.open(path) as hdul:
                img = hdul[0].data.astype(float)
                wcs = WCS(hdul[0].header)
            _, med, std = sigma_clipped_stats(img, sigma=3.0)
            ax = axes[band - 1]
            ax.imshow(img - med, origin="lower", cmap="gray_r",
                      vmin=-1 * std, vmax=8 * std)
            xs, ys = wcs.world_to_pixel_values(ra_e, dec_e)
            xc, yc = wcs.world_to_pixel_values(m["ra_centroid"], m["dec_centroid"])
            ax.plot(xs, ys, "r*", ms=12, mew=0.5, label="Gaia (propagated)")
            ax.plot(xc, yc, "g+", ms=14, mew=2, label="MIR centroid")
            ax.set_title(f"{label} W{band}  off={m['offset_arcsec']:.2f}\"")
            ax.set_xticks([])
            ax.set_yticks([])
            if band == 1:
                ax.legend(loc="lower right", fontsize=8)
        rows.extend(measure_unwise(label, t))
        fig.suptitle(f"Candidate {label}: AllWISE atlas 90\" cutouts "
                     f"(Gaia J2016 propagated to ~2010.4)")
        fig.tight_layout()
        fig.savefig(OUT / f"w2_cutout_{label}.png", dpi=130)
        plt.close(fig)

    df = pd.DataFrame(rows)
    ren = {  # published offsets for comparison (Ren 2026 Tables 5-6)
        ("C", "W1"): 0.82, ("C", "W2"): 0.76, ("C", "W3"): 3.67, ("C", "W4"): 4.98,
        ("D", "W1"): 0.53, ("D", "W2"): 0.46, ("D", "W3"): 0.75, ("D", "W4"): 1.80,
        ("I", "W1"): 0.24, ("I", "W2"): 0.40, ("I", "W3"): 2.10, ("I", "W4"): 3.22,
    }
    df["ren2026_offset"] = [ren.get((r.label, r.band)) for r in df.itertuples()]
    cols = ["label", "band", "epoch", "offset_arcsec", "sigma_pos_arcsec",
            "snr", "ren2026_offset", "ra_centroid", "dec_centroid"]
    df[cols].to_csv(OUT / "w2_centroid_offsets.csv", index=False)
    print(df[cols].to_string(index=False))


if __name__ == "__main__":
    main()
