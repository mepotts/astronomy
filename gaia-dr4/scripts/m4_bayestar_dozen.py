#!/usr/bin/env python
"""M4 task 2: arbitrate the dust-ambiguous rows with Bayestar19, on a
fully-sourced unit chain.

M3 rejected Bayestar because its Gaia-band coefficient chain had an
unsourced link.  That link is now pinned from the papers (local copies in
data/papers/1905.02734/ and data/papers/1012.4804/):

  1 Bayestar19 unit E  ->  E(gP1-rP1) = 0.901 mag
     [Green, Schlafly, Finkbeiner et al. 2019, ApJ 887, 93
      (arXiv:1905.02734): source line 399 "requiring ... that
      E(gP1-rP1) = 0.901 mag when E = 1 mag. The latter choice puts our
      measure of reddening on a similar scale as SFD"; the explicit
      conversion Egr = (0.901 mag) E at source lines 1007-1009; extinction
      vector table (source lines 331-338): R_gP1 = 3.518, R_rP1 = 2.617,
      difference 0.901.]
  1 E(B-V)_SFD        ->  E(gP1-rP1) = 3.172 - 2.271 = 0.901 mag
     [Schlafly & Finkbeiner 2011, ApJ 737, 103 (arXiv:1012.4804), Table 6
      "F99 Reddening in Different Bandpasses", R_V = 3.1 column, rows
      "PS1 g" = 3.172 and "PS1 r" = 2.271.]
  =>  1 Bayestar19 unit = 1.000 x E(B-V)_SFD-scale, EXACT in the g-r
      colour the map is calibrated on (equality by construction: Green19
      chose the 0.901 normalization to match the SFD scale).
  ->  A_V = 2.742 x E(B-V)  [SF11 Table 6, Landolt V, R_V = 3.1 -- the
      constant the M3 SFD tier already uses]
  ->  Gaia bands via the ZGR23-curve ratios at the Gaia EDR3 pivots
      (house chain, M3): A_G = A_V x R_G/R_V etc., i.e. the Bayestar19
      value enters compute_dusted_class through the SAME conversion as the
      SFD tier -- map differences are then map differences, not
      coefficient differences.

  Cross-check chain (published, independent): El-Badry et al. 2026
  (arXiv:2608.06453, source lines 169-172) treat the Green19 map value as
  E(B-V) and adopt A_G = 2.66 E(B-V), E(BP-RP) = 1.33 E(B-V) ("appropriate
  for typical sources in the sample with Teff ~ 6000 K").  Both chains are
  run; a movement verdict is only called robust if both agree.

Data: data/dustmaps/bayestar2019.h5 (Harvard Dataverse
doi:10.7910/DVN/2EJ9TX, file id 3424724, md5
ab815d2fd3068d1b81a1bd61fb18a722, verified on download 2026-08-18).
Reader below replicates dustmaps 1.0.14 BayestarQuery (multi-nside nested
lookup; linear DM interpolation; median over the 5 stored samples) with
astropy_healpix instead of healpy (no Windows build -- M3 landmine #4).
The Argonaut web API (api/v2/bayestar2019/query) returns HTTP 500 on both
documented wire formats (2026-08-18) -- new landmine, logged.

Scope: the v2 rows with class_det_dust_upper != 3 -- the rows that survive
the Edenhofer floor but die under the SFD full column.  M3 counted 12
(originally-class-III far rows); the v2 list actually carries 13 such rows
(the 13th, 3344044498533737216, is one of the 6 dust movers-IN, so it was
outside M3's 'was class III' accounting -- counting correction, documented
in M4 doc).  Bayestar19 footprint is dec > -30, so the southern rows stay
bracketed and are reported as unresolved.

Policy: arbitrated best-estimate column for these far rows =
max(E_b19_equiv, E_edenhofer_floor) (the floor is a measured lower bound
inside 1.25 kpc; tension counted, as M3 did for SFD).  Class from
dust_retriage.compute_dusted_class.  DM beyond the pixel's
DM_reliable_max is flagged; a kill that depends on an unreliable-distance
value is reported as such, not silently frozen.

Output: out/m4_bayestar_dozen.csv, stdout report.
Run   : .venv/Scripts/python.exe scripts/m4_bayestar_dozen.py
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dust3d import zgr23_band_coefficients
from dust_retriage import compute_dusted_class, SF11_AV_PER_EBV

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B19_H5 = os.path.join(BASE, "data", "dustmaps", "bayestar2019.h5")
OUT_DIR = os.path.join(BASE, "out")

# the sourced identity: 1 Bayestar19 unit = this many E(B-V)_SFD units
# (0.901 / 0.901; Green19 line 399 + Table extinction-vector; SF11 Table 6
#  PS1 g,r at R_V=3.1)
B19_UNIT_PER_EBV_SFD = 0.901 / (3.172 - 2.271)

# EB26 cross-check chain (arXiv:2608.06453 source lines 171-172)
EB26_AG_PER_EBV = 2.66
EB26_EBPRP_PER_EBV = 1.33


class Bayestar19Local:
    """healpy-free replica of dustmaps BayestarQuery (median + best)."""

    def __init__(self, path=B19_H5):
        import h5py
        from astropy_healpix import HEALPix
        with h5py.File(path, "r") as f:
            self.pix = f["pixel_info"][:]
            self.dm_edges = f["pixel_info"].attrs["DM_bin_edges"]
            self.samples = f["samples"][:]      # (npix, 5, 120)
            self.best = f["best_fit"][:]        # (npix, 120)
        self.nsides = np.unique(self.pix["nside"])
        order = np.argsort(self.pix, order=["nside", "healpix_index"])
        self._hp_sorted, self._data_idx = [], []
        lo = 0
        for ns in self.nsides:
            hi = np.searchsorted(self.pix["nside"], ns, side="right",
                                 sorter=order)
            idx = order[lo:hi]
            self._hp_sorted.append(self.pix["healpix_index"][idx])
            self._data_idx.append(idx)
            lo = hi
        self._hpx = {int(ns): HEALPix(nside=int(ns), order="nested")
                     for ns in self.nsides}

    def _find(self, l_deg, b_deg):
        import astropy.units as u
        out = np.full(len(l_deg), -1, dtype=np.int64)
        for k, ns in enumerate(self.nsides):
            ipix = self._hpx[int(ns)].lonlat_to_healpix(
                np.asarray(l_deg) * u.deg, np.asarray(b_deg) * u.deg)
            pos = np.searchsorted(self._hp_sorted[k], ipix, side="left")
            ok = pos < self._hp_sorted[k].size
            pos[~ok] = 0
            hit = ok & (self._hp_sorted[k][pos] == ipix)
            out[hit] = self._data_idx[k][pos[hit]]
        return out

    def query(self, l_deg, b_deg, d_pc):
        """Returns dict of arrays: E_median, E_best (Bayestar19 units),
        in_footprint, reliable (DM within pixel's reliable range),
        dm, dm_reliable_max."""
        l_deg = np.atleast_1d(np.asarray(l_deg, float))
        b_deg = np.atleast_1d(np.asarray(b_deg, float))
        d_pc = np.atleast_1d(np.asarray(d_pc, float))
        pi = self._find(l_deg, b_deg)
        n = len(l_deg)
        dm = 5.0 * (np.log10(d_pc / 1000.0) + 2.0)
        med = np.full(n, np.nan)
        bst = np.full(n, np.nan)
        rel = np.zeros(n, bool)
        dmmax = np.full(n, np.nan)
        edges = self.dm_edges
        for i in range(n):
            j = pi[i]
            if j < 0:
                continue
            ce = np.searchsorted(edges, dm[i])
            if ce == 0:                      # nearer than first slice
                a = 10.0 ** (0.2 * (dm[i] - edges[0]))
                s = a * self.samples[j, :, 0]
                b = a * self.best[j, 0]
            elif ce == len(edges):           # beyond last slice
                s = self.samples[j, :, -1]
                b = self.best[j, -1]
            else:                            # linear DM interpolation
                a = (edges[ce] - dm[i]) / (edges[ce] - edges[ce - 1])
                s = (1 - a) * self.samples[j, :, ce] \
                    + a * self.samples[j, :, ce - 1]
                b = (1 - a) * self.best[j, ce] + a * self.best[j, ce - 1]
            med[i] = np.median(s)
            bst[i] = b
            lo, hi = self.pix["DM_reliable_min"][j], \
                self.pix["DM_reliable_max"][j]
            rel[i] = np.isfinite(lo) and np.isfinite(hi) \
                and lo <= dm[i] <= hi
            dmmax[i] = hi
        return {"E_median": med, "E_best": bst, "in_footprint": pi >= 0,
                "reliable": rel, "dm": dm, "dm_reliable_max": dmmax}


def main():
    co = zgr23_band_coefficients()
    r_g, r_bp, r_rp, r_v = co["R_G"], co["R_BP"], co["R_RP"], co["R_V"]
    print(f"unit chain: 1 B19 unit = {B19_UNIT_PER_EBV_SFD:.4f} E(B-V)_SFD "
          f"(Green19 0.901 / SF11 {3.172-2.271:.3f}) "
          f"-> A_V = {SF11_AV_PER_EBV} x E(B-V) (SF11 Table 6) "
          f"-> ZGR23 ratios R_G/R_V = {r_g/r_v:.4f}")
    print(f"  => A_G per B19 unit (house chain): "
          f"{B19_UNIT_PER_EBV_SFD*SF11_AV_PER_EBV*r_g/r_v:.4f}; "
          f"EB26 chain: {EB26_AG_PER_EBV}")

    v2 = pd.read_csv(os.path.join(OUT_DIR, "amrf_class3_candidates_v2.csv"))
    amb = v2[v2["class_det_dust_upper"] != 3].copy()
    print(f"\ndust-ambiguous rows in v2 (class_det_dust_upper != 3): "
          f"{len(amb)}  [M3 counted 12: the 13th is dust mover-in "
          f"3344044498533737216 -- counting correction]")

    tri = pd.read_parquet(os.path.join(BASE, "data",
                                       "dr3_amrf_triage.parquet"))
    key = ["source_id", "nss_solution_type"]
    scope = amb[key].merge(tri, on=key, how="left").reset_index(drop=True)
    assert len(scope) == len(amb) and scope["a0_mas"].notna().all()

    dust = pd.read_csv(os.path.join(OUT_DIR, "dust_retriage.csv"))
    scope = scope.merge(dust[key + ["E_zgr23_eden", "ebv_sfd_raw", "d_pc",
                                    "dust_tier"]], on=key, how="left")

    print("loading bayestar2019.h5 (healpy-free reader)...", flush=True)
    b19 = Bayestar19Local()
    q = b19.query(scope["l"].values, scope["b"].values,
                  scope["d_pc"].values)

    # unit chain to E(ZGR23)-equivalent, exactly like the SFD tier
    ebv_equiv = B19_UNIT_PER_EBV_SFD * q["E_median"]
    E_b19_zgr = SF11_AV_PER_EBV * ebv_equiv / r_v
    E_eden = scope["E_zgr23_eden"].values
    E_sfd_zgr = SF11_AV_PER_EBV * scope["ebv_sfd_raw"].values / r_v

    # arbitrated best estimate: never below the measured inner floor
    tension = q["in_footprint"] & (E_b19_zgr < E_eden)
    E_arb = np.where(q["in_footprint"],
                     np.maximum(E_b19_zgr, E_eden), np.nan)

    # ---- house-chain re-triage -------------------------------------------
    ag = r_g * E_arb
    ebprp = (r_bp - r_rp) * E_arb
    m1_a, src_a, cls_a, marg_a, amrf_a = compute_dusted_class(
        scope, np.where(np.isfinite(ag), ag, 0.0),
        np.where(np.isfinite(ebprp), ebprp, 0.0))
    cls_a = np.where(q["in_footprint"], cls_a, -1)  # -1 = no coverage

    # ---- EB26-chain cross-check ------------------------------------------
    ag_e = EB26_AG_PER_EBV * ebv_equiv
    # EB26 keeps the same floor logic in spirit: clamp at the Edenhofer
    # floor converted through the SAME (EB26) coefficients for consistency
    ag_e = np.maximum(ag_e, EB26_AG_PER_EBV * (E_eden * r_v
                                               / SF11_AV_PER_EBV))
    ebprp_e = ag_e * EB26_EBPRP_PER_EBV / EB26_AG_PER_EBV
    m1_e, src_e, cls_e, marg_e, _ = compute_dusted_class(
        scope, np.where(np.isfinite(ag_e), ag_e, 0.0),
        np.where(np.isfinite(ebprp_e), ebprp_e, 0.0))
    cls_e = np.where(q["in_footprint"], cls_e, -1)

    out = scope[key + ["l", "b", "d_pc", "dust_tier", "phot_g_mean_mag",
                       "bp_rp", "significance"]].copy()
    out["E_eden_floor_zgr"] = E_eden
    out["E_sfd_upper_zgr"] = E_sfd_zgr
    out["E_b19_median_units"] = q["E_median"]
    out["E_b19_best_units"] = q["E_best"]
    out["E_b19_zgr_equiv"] = E_b19_zgr
    out["E_arb_zgr"] = E_arb
    out["b19_in_footprint"] = q["in_footprint"]
    out["b19_reliable_dm"] = q["reliable"]
    out["b19_dm"] = q["dm"]
    out["b19_dm_reliable_max"] = q["dm_reliable_max"]
    out["b19_below_eden_floor"] = tension
    out["class_v2_lower"] = 3          # by construction (v2 members)
    out["class_v2_upper"] = amb["class_det_dust_upper"].values
    out["class_b19_house"] = cls_a
    out["m1_b19_house"] = m1_a
    out["m1_source_b19_house"] = src_a
    out["margin_b19_house"] = marg_a
    out["class_b19_eb26chain"] = cls_e
    out["verdict"] = np.select(
        [~q["in_footprint"],
         (cls_a == 3) & (cls_e == 3),
         (cls_a != 3) & (cls_e != 3)],
        ["UNRESOLVED_south_of_footprint",
         "SURVIVES_b19", "DIES_b19"], default="CHAIN_DEPENDENT")
    out.to_csv(os.path.join(OUT_DIR, "m4_bayestar_dozen.csv"), index=False,
               lineterminator="\n")

    print("\nper-row arbitration (E in ZGR23-equivalent units):")
    show = out[["source_id", "d_pc", "b", "E_eden_floor_zgr",
                "E_b19_zgr_equiv", "E_sfd_upper_zgr", "b19_reliable_dm",
                "class_b19_house", "class_b19_eb26chain", "verdict"]]
    print(show.to_string(index=False))
    print(f"\nsummary: {int((out['verdict']=='SURVIVES_b19').sum())} survive, "
          f"{int((out['verdict']=='DIES_b19').sum())} die, "
          f"{int((out['verdict']=='CHAIN_DEPENDENT').sum())} chain-dependent, "
          f"{int((out['verdict']=='UNRESOLVED_south_of_footprint').sum())} "
          f"unresolved (dec < -30)")
    print(f"B19 below Edenhofer floor (map tension, clamped): "
          f"{int(tension.sum())}")
    print(f"B19 value at star distance beyond DM_reliable_max: "
          f"{int((q['in_footprint'] & ~q['reliable']).sum())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
