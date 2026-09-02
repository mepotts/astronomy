"""M2: the single table for the RNAAS-sized note on the Ren et al. (2024)
Hot DOG surface-density unit error.

Every density is traced to the exact sentence in its source; the conversions
are re-derived here rather than quoted. Poisson geometry throughout:
    P(>=1 source within r) = 1 - exp(-rho * pi * r^2)
    N_expected = P * N_stars,  N_stars = 5e6 (Suazo et al. 2024 parent sample)

Output: out/m2_note_table.csv and a LaTeX-ready deluxetable body printed to
stdout (the note is a DRAFT and is NOT submitted anywhere).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"

AS2_PER_DEG2 = 3600.0 ** 2            # 1.296e7 arcsec^2 per deg^2
DEG2_PER_SR = (180.0 / np.pi) ** 2    # 3282.806
N_STARS = 5.0e6
R_W3 = 3.25                            # W3 PSF half-width, Suazo+24 convention
R_JWST = 1.0                           # measured blend separation, Zackrisson+26

ROWS = [
    # (label, rho in arcsec^-2, provenance)
    ("Ren et al. (2024), as printed",
     9.0e-6,
     "\"about $9\\times10^{-6}$ per square arcsecond\""),
    ("Assef et al. (2015) Hot DOGs, corrected",
     (1.0 / 31.0) / AS2_PER_DEG2,
     "1 per 31 deg$^2$ = 0.032 deg$^{-2}$, converted correctly"),
    ("Blain (2024) full WISE Hot DOG sample",
     0.1 / AS2_PER_DEG2,
     "2220 Hot DOGs over 70\\% of the sky = 0.1 deg$^{-2}$"),
    ("Li et al. (2025) $z<0.5$ Hot DOGs",
     0.0024 / AS2_PER_DEG2,
     "0.0024 deg$^{-2}$ (via Zackrisson et al. 2026)"),
    ("Suazo et al. (2024) faint red galaxies",
     15000.0 / DEG2_PER_SR / AS2_PER_DEG2,
     "$\\approx15000$ sr$^{-1}$ with W4 and W3$-$W4 like the candidates'"),
]


def main() -> None:
    recs = []
    for name, rho, prov in ROWS:
        for r in (R_W3, R_JWST):
            p = 1.0 - np.exp(-rho * np.pi * r * r)
            recs.append(dict(population=name, provenance=prov,
                             rho_arcsec2=rho, rho_deg2=rho * AS2_PER_DEG2,
                             radius_arcsec=r, p_per_star=p,
                             n_expected=p * N_STARS))
    df = pd.DataFrame(recs)
    df.to_csv(OUT / "m2_note_table.csv", index=False)

    req325 = 7.0 / (N_STARS * np.pi * R_W3 ** 2) * AS2_PER_DEG2
    req10 = 7.0 / (N_STARS * np.pi * R_JWST ** 2) * AS2_PER_DEG2

    print("== the note's table (N expected among 5e6 stars) ==\n")
    print(f"{'population':44s} {'deg^-2':>10s} "
          f"{'N(3.25\")':>10s} {'N(1.0\")':>10s}")
    for name, rho, _ in ROWS:
        n325 = (1 - np.exp(-rho * np.pi * R_W3 ** 2)) * N_STARS
        n10 = (1 - np.exp(-rho * np.pi * R_JWST ** 2)) * N_STARS
        print(f"{name:44s} {rho * AS2_PER_DEG2:10.4g} "
              f"{n325:10.3g} {n10:10.3g}")
    print(f"\n{'required to produce the 7 candidates':44s} "
          f"{req325:10.3g} {7.0:10.3g}      -- at r=3.25\"")
    print(f"{'':44s} {req10:10.3g} {'':10s} {7.0:10.3g}  -- at r=1.0\"")

    ratio = 9.0e-6 / ((1.0 / 31.0) / AS2_PER_DEG2)
    print(f"\nerror factor: {ratio:.1f}x  "
          f"(1/31 deg^-2 = {(1 / 31) / AS2_PER_DEG2:.3e} arcsec^-2 = "
          f"{(1 / 31) / 3600:.3e} arcmin^-2)")
    n_printed = (1 - np.exp(-9e-6 * np.pi * R_W3 ** 2)) * N_STARS
    n_corr = (1 - np.exp(-((1 / 31) / AS2_PER_DEG2) * np.pi * R_W3 ** 2)) * N_STARS
    print(f"consequence at r=3.25\": {n_printed:.0f} expected as printed vs "
          f"{n_corr:.2f} corrected -- a factor {n_printed / n_corr:.0f}")
    print(f"corrected catalogued Hot DOGs explain {n_corr / 7 * 100:.0f}% of "
          f"the 7 candidates")
    print("\nwrote out/m2_note_table.csv")


if __name__ == "__main__":
    main()
