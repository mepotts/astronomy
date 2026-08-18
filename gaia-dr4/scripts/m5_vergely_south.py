#!/usr/bin/env python
"""M5 task 2: close the southern dust ambiguity with Vergely+2022.

M4 arbitrated 13 dust-ambiguous far-star rows with Bayestar19 and resolved
9 alive; **4 sit south of the B19 footprint (dec < -30)** and stayed
bracketed with `flag_dust_unresolved_south`.  Vergely, Lallement & Cox 2022
is an ALL-SKY Cartesian inversion -- it has no declination edge, only a box
edge -- so it can reach them.

MAP AND UNITS, sourced
----------------------
Product: CDS J/A+A/664/A174 (Vergely J.L., Lallement R., Cox N.L.J. 2022,
A&A 664, A174 = 2022A&A...664A.174V), fetched over anonymous FTP by
scripts/m5_fetch_vergely2022.py; ReadMe + list.dat kept next to the cubes.

  ReadMe, Description: "3D distribution of extinction density at 550nm in a
  6kpc by 6kpc by 0.8kpc volume around the Sun.  The map is in Cartesian
  coordinates with the Sun at centre X,Y,Z=0,0,0.  The X axis is directed
  to the Galactic Centre, the Y axis is along the direction of rotation,
  and the Z axis points to the Northern Galactic Pole.  Distances X, Y, Z
  units are parsecs."
  ReadMe, Caution: "read the article for assumptions during the inversion
  (especially the resolution) and errors at large distances or beyond very
  dense structures."

  FITS headers (self-describing, read 2026-08-18):
    explore_cube_density_values_025pc_v2.fits  601x601x81
        STEP=10 pc  RESOL=25 pc  UNIT='A0(550nm)/parsec'
        SUN_POSX/Y=300.5  SUN_POSZ=40.5
    explore_cube_density_values_050pc_v2.fits  501x501x41
        STEP=20 pc  RESOL=50 pc  UNIT='A0(550nm)/parsec'
        SUN_POSX/Y=250.5  SUN_POSZ=20.5
    explore_cube_density_errors_050pc_v2.fits  (same grid, the map's own
        1-sigma density uncertainty)
  NOTE the FITS cubes are already in mag/pc; the ReadMe's "nanomagnitude
  per parsec" describes the ASCII `cube_ext.dat` (integer) version of the
  same data, which we do not download (7.5 GB).

  The quantity is A0, the MONOCHROMATIC extinction at 550 nm:
  arXiv:2205.09087 (3DINTERCAL.tex) source line 162: "The photometric
  catalogue provides monochromatic extinctions A$_{0}$ at 550~nm, while the
  spectroscopic catalogues estimate A$_V$, the extinction in the V band.
  Both quantities are very similar."

UNIT CHAIN into the house scale (one link, the same curve the house already
uses -- so the arbitration compares MAPS, not coefficient conventions,
exactly as M4 required of Bayestar19):

  E(ZGR23)_equivalent = A0(550 nm) / R_ZGR23(550 nm),  R_ZGR23(550) = 2.6798
  [ZGR23 extinction curve, data/papers/zgr23_curve/extinction_curve.txt,
   Zenodo 7692680/7811871, linearly interpolated at 550 nm -- the same
   table that supplies R_G/R_BP/R_RP/R_V to dust3d.zgr23_band_coefficients]
  then Gaia bands via the ZGR23 ratios, i.e. A_G = R_G * E, exactly as the
  Edenhofer and SFD tiers.

  Cross-check chain (published, independent), run in parallel as M4 did:
  treat A0(550) as A_V (the paper says the two are "very similar"), convert
  to E(B-V) with SF11's A_V = 2.742 E(B-V), and use El-Badry+2026's
  A_G = 2.66 E(B-V), E(BP-RP) = 1.33 E(B-V) (arXiv:2608.06453 src lines
  169-172).  A movement verdict counts only if BOTH chains agree.

PRE-REGISTERED GEOMETRY GATE (written before running; the reader is new
code and a swapped axis would silently produce plausible numbers):
  G1 The declared convention X = d cos b cos l, Y = d cos b sin l,
     Z = d sin b, index = coord/STEP + (SUN_POS - 0.5), must beat all
     three plausible corruptions (X<->Y swap, X sign flip, Y sign flip) on
     Spearman rho against the Edenhofer 2023 3D map over >= 2000 randomly
     drawn candidate sightlines with 200 <= d <= 1250 pc (inside BOTH maps'
     volumes), by a margin of at least 0.2 in rho.  If it does not, the
     reader is wrong and NOTHING is written.
  G2 On the same sample the median ratio E_V22 / E_Edenhofer must lie in
     [0.5, 2.0] (two independent inversions of different input catalogues
     at different resolutions; a factor-2 window is generous but a unit
     error would blow straight through it).
  G3 The 025 pc and 050 pc cubes must agree with each other to a median
     ratio within [0.8, 1.25] on the same sample.

ARBITRATION (M4's policy, unchanged):
  best estimate = max(E_V22 integrated to the star, E_Edenhofer floor);
  class from dust_retriage.compute_dusted_class; the SFD full column stays
  the pessimistic ceiling.  A row is RESOLVED only if the house chain and
  the EB26 chain agree, AND the verdict is unchanged when the V22 value is
  moved by +-1 sigma of the map's own error cube.  Rays that leave the box
  before reaching the star are flagged (the integral is then a lower bound
  and the row stays bracketed).

Scope: all 13 dust-ambiguous v2 rows -- the 4 southern ones are the target,
the 9 Bayestar19 already resolved are the CONTROL: V22 must reproduce B19's
verdict on them or the southern result is not credible.

Output: out/m5_vergely_dust_south.csv, out/m5_vergely_geometry_gate.txt
Run   : .venv/Scripts/python.exe scripts/m5_vergely_south.py
"""

import os
import sys

import numpy as np
import pandas as pd
from astropy.io import fits
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dust3d import Edenhofer3D, ZGR23_CURVE, zgr23_band_coefficients
from dust_retriage import compute_dusted_class, SF11_AV_PER_EBV

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V22_DIR = os.path.join(BASE, "data", "dustmaps", "vergely2022")
OUT_DIR = os.path.join(BASE, "out")

CUBE_025 = os.path.join(V22_DIR, "explore_cube_density_values_025pc_v2.fits")
CUBE_050 = os.path.join(V22_DIR, "explore_cube_density_values_050pc_v2.fits")
ERR_050 = os.path.join(V22_DIR, "explore_cube_density_errors_050pc_v2.fits")

EB26_AG_PER_EBV = 2.66
EB26_EBPRP_PER_EBV = 1.33
SEED = 20261202

# geometry-gate thresholds, pre-registered
GATE_RHO_MARGIN = 0.20
GATE_RATIO_EDEN = (0.5, 2.0)
GATE_RATIO_CUBES = (0.8, 1.25)
GATE_N_MIN = 2000


def r_zgr23_at(wavelength_nm):
    tab = np.loadtxt(ZGR23_CURVE, skiprows=1)
    return float(np.interp(wavelength_nm, tab[:, 0], tab[:, 1]))


class Vergely2022Cube:
    """Line-of-sight integrator for the Vergely+2022 Cartesian density cubes.

    Returns A0(550 nm) in mag, integrated from the Sun to distance d.
    """

    def __init__(self, path):
        with fits.open(path) as h:
            hdr = h[0].header
            self.data = np.asarray(h[0].data, dtype=np.float64)  # (Z, Y, X)
            self.step = float(hdr["STEP"])
            self.resol = float(hdr["RESOL"])
            self.unit = str(hdr["UNIT"]).strip()
            # SUN_POS* are 1-based-pixel-edge coordinates: the Sun sits at
            # the CENTRE of 0-based index SUN_POS - 0.5 (verified: 601-pixel
            # axis, SUN=300.5 -> index 300 = the exact middle pixel).
            self.sun = np.array([float(hdr["SUN_POSX"]) - 0.5,
                                 float(hdr["SUN_POSY"]) - 0.5,
                                 float(hdr["SUN_POSZ"]) - 0.5])
        assert self.unit == "A0(550nm)/parsec", f"unexpected UNIT {self.unit}"
        self.nx = self.data.shape[2]
        self.ny = self.data.shape[1]
        self.nz = self.data.shape[0]

    def _sample(self, x, y, z):
        """Trilinear sample of the density [mag/pc] at Cartesian (x,y,z) pc.
        Points outside the box return NaN."""
        fi = x / self.step + self.sun[0]
        fj = y / self.step + self.sun[1]
        fk = z / self.step + self.sun[2]
        inside = ((fi >= 0) & (fi <= self.nx - 1) & (fj >= 0)
                  & (fj <= self.ny - 1) & (fk >= 0) & (fk <= self.nz - 1))
        out = np.full(np.shape(x), np.nan, dtype=float)
        if not np.any(inside):
            return out, inside
        i0 = np.floor(fi[inside]).astype(int)
        j0 = np.floor(fj[inside]).astype(int)
        k0 = np.floor(fk[inside]).astype(int)
        i1 = np.minimum(i0 + 1, self.nx - 1)
        j1 = np.minimum(j0 + 1, self.ny - 1)
        k1 = np.minimum(k0 + 1, self.nz - 1)
        di = fi[inside] - i0
        dj = fj[inside] - j0
        dk = fk[inside] - k0
        d = self.data
        v = (d[k0, j0, i0] * (1-di)*(1-dj)*(1-dk)
             + d[k0, j0, i1] * di*(1-dj)*(1-dk)
             + d[k0, j1, i0] * (1-di)*dj*(1-dk)
             + d[k0, j1, i1] * di*dj*(1-dk)
             + d[k1, j0, i0] * (1-di)*(1-dj)*dk
             + d[k1, j0, i1] * di*(1-dj)*dk
             + d[k1, j1, i0] * (1-di)*dj*dk
             + d[k1, j1, i1] * di*dj*dk)
        out[inside] = v
        return out, inside

    def integrate(self, l_deg, b_deg, d_pc, convention="declared",
                  n_sub=2):
        """Integrated A0(550nm) [mag] from the Sun to d along (l, b).

        `convention` selects the axis mapping; only "declared" is the
        ReadMe's.  The others exist so the pre-registered geometry gate can
        show the declared one wins.
        Returns (A0, frac_inside): frac_inside < 1 means the ray left the
        box, so A0 is a LOWER bound.
        """
        l = np.radians(np.atleast_1d(np.asarray(l_deg, float)))
        b = np.radians(np.atleast_1d(np.asarray(b_deg, float)))
        d = np.atleast_1d(np.asarray(d_pc, float))
        ds = self.step / float(n_sub)
        nmax = int(np.ceil(np.nanmax(d) / ds)) + 1
        s = (np.arange(nmax) + 0.5) * ds                  # midpoint rule
        # (n_targets, n_steps)
        S = s[None, :]
        active = S <= d[:, None]
        x = S * (np.cos(b) * np.cos(l))[:, None]
        y = S * (np.cos(b) * np.sin(l))[:, None]
        z = S * np.sin(b)[:, None]
        if convention == "swap_xy":
            x, y = y, x
        elif convention == "flip_x":
            x = -x
        elif convention == "flip_y":
            y = -y
        elif convention != "declared":
            raise ValueError(convention)
        rho, inside = self._sample(x, y, z)
        good = active & inside & np.isfinite(rho)
        A0 = np.nansum(np.where(good, rho, 0.0), axis=1) * ds
        frac = (good.sum(axis=1)
                / np.maximum(active.sum(axis=1), 1)).astype(float)
        return A0, frac


def main():
    co = zgr23_band_coefficients()
    r_g, r_bp, r_rp, r_v = co["R_G"], co["R_BP"], co["R_RP"], co["R_V"]
    R550 = r_zgr23_at(550.0)
    print(f"unit chain: 1 mag A0(550nm) = {1.0/R550:.4f} E(ZGR23) "
          f"[R_ZGR23(550) = {R550:.4f}]  ->  A_G = {r_g:.4f} E; "
          f"A_G per mag A0 = {r_g/R550:.4f}")
    print(f"EB26 cross-chain: A_G per mag A0 = "
          f"{EB26_AG_PER_EBV/SF11_AV_PER_EBV:.4f}")

    print("\nloading Vergely+2022 cubes...", flush=True)
    c25 = Vergely2022Cube(CUBE_025)
    c50 = Vergely2022Cube(CUBE_050)
    e50 = Vergely2022Cube(ERR_050)
    print(f"  025pc: {c25.nx}x{c25.ny}x{c25.nz} step {c25.step} pc "
          f"resol {c25.resol} pc, unit {c25.unit!r}")
    print(f"  050pc: {c50.nx}x{c50.ny}x{c50.nz} step {c50.step} pc "
          f"resol {c50.resol} pc")

    # ---------------- pre-registered geometry gate ------------------------
    gate_lines = []

    def g(s=""):
        gate_lines.append(s)
        print(s)

    g("M5 Vergely+2022 reader -- pre-registered geometry gate (2026-08-18)")
    g("=" * 72)
    dust = pd.read_csv(os.path.join(OUT_DIR, "dust_retriage.csv"))
    samp = dust[(dust["d_pc"] >= 200) & (dust["d_pc"] <= 1250)]
    rng = np.random.default_rng(SEED)
    n = min(4000, len(samp))
    idx = rng.choice(len(samp), size=n, replace=False)
    samp = samp.iloc[idx].reset_index(drop=True)
    g(f"\nvalidation sightlines: {len(samp)} drawn (seed {SEED}) from "
      f"dust_retriage rows with 200 <= d <= 1250 pc "
      f"(inside BOTH map volumes); required >= {GATE_N_MIN}")
    assert len(samp) >= GATE_N_MIN, "not enough validation sightlines"

    eden = Edenhofer3D()
    E_ed, _ = eden.query_integrated(samp["l"].values, samp["b"].values,
                                    samp["d_pc"].values)
    g("\nG1 -- axis convention vs Edenhofer 2023 (Spearman rho):")
    rhos = {}
    for conv in ("declared", "swap_xy", "flip_x", "flip_y"):
        A0, frac = c25.integrate(samp["l"].values, samp["b"].values,
                                 samp["d_pc"].values, convention=conv)
        ok = np.isfinite(A0) & np.isfinite(E_ed) & (frac > 0.999)
        rho = spearmanr(A0[ok], E_ed[ok]).statistic
        rhos[conv] = rho
        g(f"  {conv:9s}: rho = {rho:+.4f}  (n = {int(ok.sum())})")
    margin = rhos["declared"] - max(v for k, v in rhos.items()
                                    if k != "declared")
    g(f"  margin of declared over the best corruption: {margin:+.4f} "
      f"(required >= {GATE_RHO_MARGIN})")
    assert margin >= GATE_RHO_MARGIN, "GEOMETRY GATE G1 FAILED -- reader wrong"

    A0_25, frac25 = c25.integrate(samp["l"].values, samp["b"].values,
                                  samp["d_pc"].values)
    A0_50, frac50 = c50.integrate(samp["l"].values, samp["b"].values,
                                  samp["d_pc"].values)
    E_v25 = A0_25 / R550
    E_v50 = A0_50 / R550
    ok = (frac25 > 0.999) & (frac50 > 0.999) & (E_ed > 1e-4)
    ratio_ed = np.median(E_v25[ok] / E_ed[ok])
    p10, p90 = np.percentile(E_v25[ok] / E_ed[ok], [10, 90])
    g(f"\nG2 -- E_V22(025pc) / E_Edenhofer: median {ratio_ed:.3f} "
      f"(10-90%: {p10:.3f}-{p90:.3f}); required in "
      f"[{GATE_RATIO_EDEN[0]}, {GATE_RATIO_EDEN[1]}]")
    assert GATE_RATIO_EDEN[0] <= ratio_ed <= GATE_RATIO_EDEN[1], \
        "GEOMETRY GATE G2 FAILED"

    ok2 = ok & (E_v50 > 1e-4)
    ratio_cubes = np.median(E_v25[ok2] / E_v50[ok2])
    g(f"G3 -- E_V22(025pc) / E_V22(050pc): median {ratio_cubes:.3f}; "
      f"required in [{GATE_RATIO_CUBES[0]}, {GATE_RATIO_CUBES[1]}]")
    assert GATE_RATIO_CUBES[0] <= ratio_cubes <= GATE_RATIO_CUBES[1], \
        "GEOMETRY GATE G3 FAILED"
    g(f"\nGEOMETRY GATE: PASS -- the reader may be used.")

    # ---------------- the 13 dust-ambiguous rows --------------------------
    v2 = pd.read_csv(os.path.join(OUT_DIR, "amrf_class3_candidates_v2.csv"))
    amb = v2[v2["class_det_dust_upper"] != 3].copy()
    doz = pd.read_csv(os.path.join(OUT_DIR, "m4_bayestar_dozen.csv"))
    key = ["source_id", "nss_solution_type"]
    tri = pd.read_parquet(os.path.join(BASE, "data",
                                       "dr3_amrf_triage.parquet"))
    scope = amb[key].merge(tri, on=key, how="left").reset_index(drop=True)
    scope = scope.merge(dust[key + ["E_zgr23_eden", "ebv_sfd_raw", "d_pc",
                                    "dust_tier"]], on=key, how="left")
    scope = scope.merge(doz[key + ["verdict", "E_b19_zgr_equiv",
                                   "b19_in_footprint"]].rename(
        columns={"verdict": "b19_verdict"}), on=key, how="left")
    print(f"\ndust-ambiguous rows: {len(scope)} "
          f"({int((~scope['b19_in_footprint']).sum())} south of the B19 "
          f"footprint)")

    l, b, d = scope["l"].values, scope["b"].values, scope["d_pc"].values
    A0_25, f25 = c25.integrate(l, b, d)
    A0_50, f50 = c50.integrate(l, b, d)
    # error cube: integrating a 1-sigma density field along the ray treats
    # the per-cell errors as fully correlated -> a deliberately CONSERVATIVE
    # (maximal) 1-sigma band on the integrated column.
    S0_50, _ = e50.integrate(l, b, d)

    E_v25 = A0_25 / R550
    E_v50 = A0_50 / R550
    E_sig = S0_50 / R550
    E_eden = scope["E_zgr23_eden"].values
    E_sfd = SF11_AV_PER_EBV * scope["ebv_sfd_raw"].values / r_v

    in_box = f25 > 0.999
    # primary = the finest cube that fully contains the ray; else the 50 pc
    E_v22 = np.where(in_box, E_v25, np.where(f50 > 0.999, E_v50, np.nan))
    cube_used = np.where(in_box, "025pc", np.where(f50 > 0.999, "050pc",
                                                   "OUT_OF_BOX"))
    E_arb = np.maximum(E_v22, E_eden)
    tension = np.isfinite(E_v22) & (E_v22 < E_eden)

    def classify(E, chain):
        if chain == "house":
            ag = r_g * E
            ebprp = (r_bp - r_rp) * E
        else:  # EB26 chain: E(ZGR23) -> A_V -> E(B-V) -> their coefficients
            ebv = E * r_v / SF11_AV_PER_EBV
            ag = EB26_AG_PER_EBV * ebv
            ebprp = EB26_EBPRP_PER_EBV * ebv
        m1, src, cls, marg, _ = compute_dusted_class(
            scope, np.where(np.isfinite(ag), ag, 0.0),
            np.where(np.isfinite(ebprp), ebprp, 0.0))
        return m1, src, cls, marg

    m1_h, src_h, cls_h, marg_h = classify(E_arb, "house")
    _, _, cls_e, _ = classify(E_arb, "eb26")
    # +-1 sigma robustness (the map's own error, conservatively integrated)
    _, _, cls_hi, _ = classify(np.maximum(E_v22 + E_sig, E_eden), "house")
    _, _, cls_lo, _ = classify(np.maximum(E_v22 - E_sig, E_eden), "house")

    has = np.isfinite(E_arb)
    cls_h = np.where(has, cls_h, -1)
    cls_e = np.where(has, cls_e, -1)
    stable = has & (cls_hi == cls_h) & (cls_lo == cls_h)

    verdict = np.select(
        [~has,
         (cls_h == 3) & (cls_e == 3) & stable,
         (cls_h != 3) & (cls_e != 3) & stable,
         ~stable],
        ["UNRESOLVED_outside_box", "SURVIVES_v22", "DIES_v22",
         "UNRESOLVED_sigma_flips_verdict"],
        default="CHAIN_DEPENDENT")

    out = scope[key + ["l", "b", "d_pc", "dust_tier", "phot_g_mean_mag",
                       "bp_rp", "significance"]].copy()
    out["dec"] = scope["dec"].values
    out["E_eden_floor_zgr"] = E_eden
    out["E_sfd_upper_zgr"] = E_sfd
    out["A0_550_v22_025pc_mag"] = A0_25
    out["A0_550_v22_050pc_mag"] = A0_50
    out["A0_550_v22_sigma_mag"] = S0_50
    out["frac_ray_in_box_025"] = f25
    out["frac_ray_in_box_050"] = f50
    out["cube_used"] = cube_used
    out["E_v22_zgr_equiv"] = E_v22
    out["E_v22_sigma_zgr"] = E_sig
    out["E_arb_zgr"] = E_arb
    out["v22_below_eden_floor"] = tension
    out["class_v22_house"] = cls_h
    out["class_v22_eb26chain"] = cls_e
    out["class_v22_plus1sig"] = cls_hi
    out["class_v22_minus1sig"] = cls_lo
    out["m1_v22_house"] = m1_h
    out["margin_v22_house"] = marg_h
    out["b19_verdict"] = scope["b19_verdict"].values
    out["E_b19_zgr_equiv"] = scope["E_b19_zgr_equiv"].values
    out["verdict"] = verdict
    out = out.sort_values(["b19_verdict", "source_id"])
    out.to_csv(os.path.join(OUT_DIR, "m5_vergely_dust_south.csv"),
               index=False, lineterminator="\n")

    print("\nper-row arbitration (E in ZGR23-equivalent units):")
    show = out[["source_id", "dec", "d_pc", "E_eden_floor_zgr",
                "E_b19_zgr_equiv", "E_v22_zgr_equiv", "E_v22_sigma_zgr",
                "E_sfd_upper_zgr", "cube_used", "class_v22_house",
                "class_v22_eb26chain", "b19_verdict", "verdict"]]
    print(show.to_string(index=False))

    # ---- the control: does V22 reproduce B19 where both exist? -----------
    both = out[out["b19_verdict"] == "SURVIVES_b19"]
    central = int(((both["class_v22_house"] == 3)
                   & (both["class_v22_eb26chain"] == 3)).sum())
    agree = int((both["verdict"] == "SURVIVES_v22").sum())
    g("")
    g("CONTROL -- V22 vs Bayestar19 on the 9 rows B19 already arbitrated:")
    g(f"  at the CENTRAL value, V22 reproduces B19's class-III verdict on "
      f"{central} of {len(both)} (both chains)")
    g(f"  after the +-1 sigma robustness test (which M4's B19 pass did not "
      f"apply): {agree} of {len(both)} stay clean")
    r = both["E_v22_zgr_equiv"] / both["E_b19_zgr_equiv"]
    g(f"  median E_V22 / E_B19 = {np.median(r):.3f} "
      f"(range {np.min(r):.3f}-{np.max(r):.3f})")

    south = out[out["b19_verdict"] == "UNRESOLVED_south_of_footprint"]
    g("")
    g(f"SOUTH -- the 4 rows M4 could not reach: "
      f"{south['verdict'].value_counts().to_dict()}")
    for _, rr in south.iterrows():
        g(f"  {int(rr['source_id'])}  dec {rr['dec']:+.1f}  "
          f"d {rr['d_pc']:.0f} pc  E_eden {rr['E_eden_floor_zgr']:.3f}  "
          f"E_V22 {rr['E_v22_zgr_equiv']:.3f} +- {rr['E_v22_sigma_zgr']:.3f}"
          f"  E_SFD {rr['E_sfd_upper_zgr']:.3f}  -> class "
          f"{int(rr['class_v22_house'])}/{int(rr['class_v22_eb26chain'])}  "
          f"{rr['verdict']}")

    g("")
    g(f"summary over all {len(out)}: "
      f"{out['verdict'].value_counts().to_dict()}")
    g(f"V22 below the Edenhofer floor (map tension, clamped): "
      f"{int(tension.sum())}")

    with open(os.path.join(OUT_DIR, "m5_vergely_geometry_gate.txt"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(gate_lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
