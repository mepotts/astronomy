"""M3: J0944 finder chart from public image cutouts (account-free).

The position (Dec -71.2) is outside Legacy Surveys DR10 (verified by cutout
probe in m3_j0944_services.py), so the base imagery is:
  - wide panel: DSS2 color via CDS hips2fits (guaranteed coverage);
  - zoom panel: SkyMapper color HiPS (CDS/P/skymapper-color) if available,
    else DSS2 color.
hips2fits (https://alasky.cds.unistra.fr/hips-image-services/hips2fits) returns
a TAN projection centred on the requested position, so pixel<->sky mapping is
analytic; the eROSITA error circle and the catalogued neighbours (Gaia 10.2",
CatWISE 5.2", VHS 10.1") are drawn from their catalog coordinates.

Output: out/j0944_finder.png (committable size).
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import requests
from matplotlib.patches import Circle

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
H2F = "https://alasky.cds.unistra.fr/hips-image-services/hips2fits"
RA, DEC = 146.22033015318507, -71.19802286286726

# markers: (label, ra, dec, color) - coordinates from the M3 service cones
MARKS = [
    ("CatWISE 5.2\" W1=16.7", 146.2239001, -71.1989132, "#ff7f0e"),
    ("Gaia 10.2\" G=16.4", 146.212587, -71.196675, "#2ca02c"),
]


def fetch(hips: str, fov_deg: float, npix: int) -> np.ndarray | None:
    r = requests.get(H2F, params={
        "hips": hips, "ra": RA, "dec": DEC, "fov": fov_deg,
        "width": npix, "height": npix, "projection": "TAN",
        "coordsys": "icrs", "format": "jpg"}, timeout=180)
    if r.status_code != 200:
        print(f"  {hips}: HTTP {r.status_code}")
        return None
    from PIL import Image
    img = np.asarray(Image.open(io.BytesIO(r.content)))
    if img.std() < 1.0:  # blank = outside coverage
        print(f"  {hips}: blank (std={img.std():.2f})")
        return None
    return img


def sky_to_pix(ra, dec, fov_deg, npix):
    """TAN-projection pixel position (matplotlib image convention)."""
    scale = fov_deg / npix  # deg/pix
    dra = (ra - RA) * np.cos(np.radians(DEC))
    ddec = dec - DEC
    x = npix / 2 - dra / scale   # RA increases to the left
    y = npix / 2 - ddec / scale  # row 0 at top (imshow origin='upper'), Dec up
    return x, y


def draw(ax, img, fov_deg, npix, title, circles_arcsec, marks=True):
    ax.imshow(img, origin="upper")
    for r_as, ls, lab in circles_arcsec:
        r_pix = r_as / 3600.0 / (fov_deg / npix)
        ax.add_patch(Circle((npix / 2, npix / 2), r_pix, fill=False,
                            color="#e41a1c", ls=ls, lw=1.4))
        ax.annotate(lab, (npix / 2 + r_pix * 0.72, npix / 2 - r_pix * 0.72),
                    color="#e41a1c", fontsize=8)
    if marks:
        for lab, mra, mdec, col in MARKS:
            x, y = sky_to_pix(mra, mdec, fov_deg, npix)
            if 0 < x < npix and 0 < y < npix:
                ax.plot(x, y, "+", color=col, ms=11, mew=1.6)
                ax.annotate(lab, (x + 6, y - 6), color=col, fontsize=8)
    # scale bar: 30 arcsec
    bar = 30 / 3600.0 / (fov_deg / npix)
    ax.plot([npix * 0.06, npix * 0.06 + bar], [npix * 0.94] * 2, "w-", lw=2)
    ax.annotate("30\"", (npix * 0.06, npix * 0.91), color="w", fontsize=9)
    ax.annotate("N up, E left", (npix * 0.70, npix * 0.94), color="w",
                fontsize=8)
    ax.set_title(title, fontsize=10)
    ax.set_xticks([])
    ax.set_yticks([])


def main() -> None:
    npix = 512
    print("fetching cutouts ...")
    base = None
    base_name = ""
    for hips, name in [("CDS/P/skymapper-color", "SkyMapper color"),
                       ("CDS/P/DSS2/color", "DSS2 color")]:
        wide = fetch(hips, 4 / 60, npix)   # 4 arcmin
        if wide is not None:
            zoom = fetch(hips, 1.2 / 60, npix)  # 1.2 arcmin
            if zoom is not None:
                base, base_name = (wide, zoom), name
                break
    assert base is not None, "no HiPS imagery available"
    wide, zoom = base
    print(f"base imagery: {base_name}")

    fig, axes = plt.subplots(1, 2, figsize=(10.3, 5.4))
    draw(axes[0], wide, 4 / 60, npix,
         f"3eRASS J094452.8-711152  ({base_name}, 4')",
         [(15, "-", "r=15\"")], marks=False)
    draw(axes[1], zoom, 1.2 / 60, npix,
         "zoom 1.2' - eROSITA 3sig error circle r=1.4\" (POS_ERR 0.48\")",
         [(1.44, "-", ""), (10, "--", "r=10\"")], marks=True)
    fig.suptitle("RA 146.22033  Dec -71.19802 (ICRS)   l=288.98 b=-13.57",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "j0944_finder.png", dpi=110)
    size = (OUT / "j0944_finder.png").stat().st_size
    print(f"wrote out/j0944_finder.png ({size / 1024:.0f} KB, base {base_name})")
    meta = {"base_imagery": base_name,
            "service": H2F, "fov_wide_arcmin": 4, "fov_zoom_arcmin": 1.2}
    js = json.load(open(OUT / "j0944_services.json"))
    js["finder_chart"] = meta
    json.dump(js, open(OUT / "j0944_services.json", "w", encoding="utf-8"),
              indent=1)


if __name__ == "__main__":
    main()
