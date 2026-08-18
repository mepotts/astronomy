"""W2(b): hot-DOG / red-background-galaxy chance-alignment odds at the
candidate positions, under every published surface density, with unit
conversions re-derived from the primary statements.

Densities (each traced to its exact sentence):
  [S24]  Suazo et al. 2024 (arXiv:2405.02927) Sec 3.1: galaxies with W4 flux
         >= candidates' and 2.84 < W3-W4 < 3.25: ~15,000 sr^-1
         -> their contamination rate 1.1e-5 per star inside r=3.25" (33 as^2),
         applied to ~2e5 stars with W3/W4 SNR>=3.5 -> ~2 expected.
  [R24]  Ren et al. 2024 (arXiv:2405.14921) Sec III: "Hot DOGs also have a
         surface density of approximately 1 per 31 square degrees (Assef et
         al. 2015), which translates to about 9e-6 per square arcsecond."
         NOTE: 1/31 deg^-2 = 2.49e-9 arcsec^-2, not 9e-6 arcsec^-2.
         0.032258 deg^-2 / 3600 = 8.96e-6 = "9e-6" -- i.e. the stated number
         is per square ARCMINUTE, mislabelled arcsecond (factor 3600).
         Both versions are computed below to show the consequence.
  [Z26]  Zackrisson et al. 2026 (arXiv:2607.09460) Sec 5.1: Assef et al. 2015
         z=2-4 Hot DOGs 0.032 deg^-2; z<0.5 Hot DOGs 0.0024 deg^-2 (their
         ref 32); required density to explain 7 candidates within 3.25" of
         5e6 stars: >=0.5 deg^-2 (>=6 deg^-2 within 1").

Geometry: P(>=1 within r) = 1 - exp(-rho * pi * r^2)  (Poisson).

Output: out/w2_chance_alignment.csv + stdout table.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
OUT.mkdir(exist_ok=True)

ARCSEC2_PER_DEG2 = 3600.0 ** 2          # 1.296e7
DEG2_PER_SR = (180.0 / np.pi) ** 2      # 3282.80635

DENSITIES = {  # name -> per arcsec^2
    "S24 red-gal 15000/sr": 15000.0 / DEG2_PER_SR / ARCSEC2_PER_DEG2,
    "R24 as stated 9e-6/as2": 9e-6,
    "R24 corrected (1/31 deg2)": (1.0 / 31.0) / ARCSEC2_PER_DEG2,
    "Assef15 HotDOG 0.032/deg2": 0.032 / ARCSEC2_PER_DEG2,
    "z<0.5 HotDOG 0.0024/deg2": 0.0024 / ARCSEC2_PER_DEG2,
}

# measured W3 centroid offsets (this work, w2_centroids.py) as the per-source
# effective radius, plus the 3.25" (W3 PSF half-width) convention radius.
CAND_RADII = {  # label -> arcsec
    "C(control) r=W3 offset": 3.72,
    "D r=W3 offset": 1.41,
    "D r=JWST gal sep": 1.0,   # Zackrisson+26: background galaxy at ~1"
    "I r=W3 offset": 2.64,
    "any r=3.25 (W3 PSF halfwidth)": 3.25,
    "any r=1.0": 1.0,
}

N_FULL = 5.0e6    # Hephaistos II parent sample
N_SNR = 2.0e5     # Hephaistos II stars with W3/W4 SNR>=3.5 (their Sec 3.1)


def main() -> None:
    rows = []
    for dname, rho_as2 in DENSITIES.items():
        for rname, r in CAND_RADII.items():
            p1 = 1.0 - np.exp(-rho_as2 * np.pi * r * r)
            rows.append(dict(
                density=dname, rho_per_arcsec2=rho_as2, radius_arcsec=r,
                p_per_star=p1,
                expected_in_5e6=p1 * N_FULL,
                expected_in_2e5_snrcut=p1 * N_SNR,
            ))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "w2_chance_alignment.csv", index=False)

    pd.set_option("display.float_format", lambda v: f"{v:.3g}")
    print("Chance-alignment expectations, P(>=1 red bg source within r):\n")
    print(df.to_string(index=False))

    print("\nKey checks:")
    r24_stated = 9e-6
    r24_correct = (1.0 / 31.0) / ARCSEC2_PER_DEG2
    print(f"  1/31 deg^-2 = {r24_correct:.3e} arcsec^-2 "
          f"(Ren24 states {r24_stated:.0e}; ratio {r24_stated / r24_correct:.0f}x"
          f" -- the stated value is per arcmin^2, mislabelled)")
    p325 = 1 - np.exp(-DENSITIES['S24 red-gal 15000/sr'] * np.pi * 3.25 ** 2)
    print(f"  S24 15000/sr inside 3.25\": p = {p325:.2e} "
          f"(S24 quote: 1.1e-5) -> x2e5 = {p325 * N_SNR:.1f} (S24 quote ~2); "
          f"x5e6 = {p325 * N_FULL:.0f} (Z26 quote ~60)")
    req_325 = 7 / (N_FULL * np.pi * 3.25 ** 2) * ARCSEC2_PER_DEG2
    req_10 = 7 / (N_FULL * np.pi * 1.0 ** 2) * ARCSEC2_PER_DEG2
    print(f"  density needed for 7 candidates: {req_325:.2f} deg^-2 (r=3.25\") "
          f"or {req_10:.1f} deg^-2 (r=1\")  [Z26 quotes >=0.5 / >=6]")


if __name__ == "__main__":
    main()
