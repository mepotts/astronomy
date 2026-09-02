#!/usr/bin/env python
"""Minimal Edenhofer et al. 2023/2024 3D dust-map reader (mean, integrated).

Why not `dustmaps`: dustmaps hard-depends on healpy, which has no Windows
build (verified 2026-08-16: no wheel, source build fails).  This module
replicates the reference implementation dustmaps 1.0.14
`dustmaps/edenhofer2023.py` (loader `_get_sphere` + `_interp_hpxr2lbd`,
`integrated=True` path) with `astropy_healpix` supplying the same 4-pixel
bilinear weights healpy's `get_interp_weights` would.

Data file: data/dustmaps/edenhofer_2023/mean_and_std_healpix.fits
(Zenodo 8187943, md5-verified on download against the dustmaps-pinned
hash).  Layout verified 2026-08-16: MEAN (516, 786432) f4 NEST nside=256,
units 'E of Zhang, Green, and Rix (2023)' per pc; radial pixel centers
(516) 69.1..1244 pc; boundaries (517); 'MEAN OF INTEGRATED INNER 68.8 PC'
(786432) = the integrated column inside the innermost shell, which the
reference adds to bin 0 before cumulative integration.

Units out: integrated E (ZGR23).  Conversions (see dust_retriage.py):
  A_V   = 2.8  * E   [Edenhofer et al. 2024, A&A 685 A82, arXiv:2308.01295
                      main.tex line 591: "multiplied the unitless ZGR23
                      extinction by a factor of 2.8" (V at 540 nm)]
  A_lam = R(lam) * E [ZGR23 extinction curve, extinction_curve.txt from
                      Zenodo 7692680/7811871, local copy
                      data/papers/zgr23_curve/; NOTE the dustmaps 1.0.14
                      docstring cites DOI 10.5281/zenodo.6674521 for the
                      curve, which resolves to GaiaXPy -- wrong DOI]
"""

import os

import numpy as np
import astropy.units as u
from astropy.io import fits
from astropy_healpix import bilinear_interpolation_weights

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDEN_FITS = os.path.join(BASE, "data", "dustmaps", "edenhofer_2023",
                         "mean_and_std_healpix.fits")
ZGR23_CURVE = os.path.join(BASE, "data", "papers", "zgr23_curve",
                           "extinction_curve.txt")


class Edenhofer3D:
    """Integrated mean extinction E(ZGR23) to distance d along (l, b)."""

    def __init__(self, path=EDEN_FITS):
        with fits.open(path, memmap=True) as hdul:
            mean = np.asarray(hdul["MEAN"].data, dtype=np.float32)
            self.nside = int(hdul["MEAN"].header["NSIDE"])
            assert hdul["MEAN"].header["ORDERING"].lower().startswith("nest")
            self.radii = np.asarray(
                hdul["RADIAL PIXEL CENTERS"].data["radial pixel centers"],
                dtype=np.float64)
            bounds = np.asarray(
                hdul["RADIAL PIXEL BOUNDARIES"].data["radial pixel boundaries"],
                dtype=np.float64)
            inner = np.asarray(
                hdul["MEAN OF INTEGRATED INNER 68.8 PC"].data,
                dtype=np.float32)
        # density [E/pc] * radial bin width [pc] -> E per shell; + inner
        # column; cumulative sum -> integrated E out to each bin center
        # (reference implementation order of operations, dustmaps 1.0.14)
        dvol = np.diff(bounds).astype(np.float32)
        mean *= dvol[:, None]
        mean[0, :] += inner
        np.cumsum(mean, axis=0, out=mean)
        # reference interpolates in log space
        with np.errstate(divide="ignore"):
            self.logdata = np.log(mean, out=mean)

    def query_integrated(self, l_deg, b_deg, d_pc):
        """Integrated E(ZGR23) at galactic (l, b) [deg] and distance [pc].
        Returns (E, tier) with tier one of:
          'edenhofer'        69 <= d <= 1250 pc (in 3D coverage)
          'edenhofer_inner'  d < 69 pc: linear ramp of the innermost column
                             (approximation; extinction here is ~0 anyway)
          'edenhofer_floor'  d > 1250 pc: integrated to the map edge --
                             a LOWER bound on the true column
        """
        l_deg = np.atleast_1d(np.asarray(l_deg, dtype=float))
        b_deg = np.atleast_1d(np.asarray(b_deg, dtype=float))
        d_pc = np.atleast_1d(np.asarray(d_pc, dtype=float))
        idx, wgt = bilinear_interpolation_weights(
            l_deg * u.deg, b_deg * u.deg, nside=self.nside, order="nested")
        # radial: clamp into [r0, r_last], remember which side we clamped
        r0, r_last = self.radii[0], self.radii[-1]
        tier = np.where(d_pc < r0, "edenhofer_inner",
                        np.where(d_pc > r_last, "edenhofer_floor",
                                 "edenhofer")).astype(object)
        d_eff = np.clip(d_pc, r0, r_last)
        ir = np.searchsorted(self.radii, d_eff).clip(1, len(self.radii) - 1)
        il = ir - 1
        w_hi = (d_eff - self.radii[il]) / (self.radii[ir] - self.radii[il])
        w_lo = 1.0 - w_hi
        # gather: logdata[rbin, pix] at 4 pixels x 2 radial bins
        v_lo = np.einsum("kn,kn->n", wgt,
                         self.logdata[il[None, :], idx])
        v_hi = np.einsum("kn,kn->n", wgt,
                         self.logdata[ir[None, :], idx])
        E = np.exp(w_lo * v_lo + w_hi * v_hi)
        # inner approximation: linear ramp of the innermost integrated column
        near = d_pc < r0
        if near.any():
            E[near] = E[near] * (d_pc[near] / r0)
        return E, tier


def zgr23_band_coefficients():
    """R(lambda) of the ZGR23 extinction curve at the Gaia (E)DR3 pivot
    wavelengths, by linear interpolation of the published curve table.
    Pivots: G 621.79 nm, BP 510.97 nm, RP 776.91 nm (Riello et al. 2021,
    A&A 649, A3, EDR3 passbands).  Point evaluation at the pivot is an
    approximation to the band-integrated coefficient (colour/extinction
    dependence at the few-% level -- documented, not corrected).
    Returns dict with R_G, R_BP, R_RP, R_V (V = 540 nm; sanity vs the
    published 2.8)."""
    tab = np.loadtxt(ZGR23_CURVE, skiprows=1)
    lam, R = tab[:, 0], tab[:, 1]
    out = {
        "R_G": float(np.interp(621.79, lam, R)),
        "R_BP": float(np.interp(510.97, lam, R)),
        "R_RP": float(np.interp(776.91, lam, R)),
        "R_V": float(np.interp(540.0, lam, R)),
    }
    return out


if __name__ == "__main__":
    import time
    t0 = time.time()
    ed = Edenhofer3D()
    print(f"loaded + integrated in {time.time()-t0:.1f}s; "
          f"radii {ed.radii[0]:.1f}..{ed.radii[-1]:.1f} pc")
    co = zgr23_band_coefficients()
    print("ZGR23 curve coefficients:", {k: round(v, 4) for k, v in co.items()},
          "(paper's A_V factor: 2.8)")
    # spot checks: galactic centre direction vs pole, 500 pc
    for (l, b, d) in ((0.0, 0.0, 500.0), (0.0, 90.0, 500.0),
                      (120.0, -5.0, 1000.0)):
        E, tier = ed.query_integrated(l, b, d)
        print(f"  (l={l}, b={b}, d={d} pc): E={E[0]:.4f} "
              f"-> A_V~{2.8*E[0]:.3f}, A_G~{co['R_G']*E[0]:.3f}  [{tier[0]}]")
