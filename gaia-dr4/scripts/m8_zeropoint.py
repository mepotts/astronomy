#!/usr/bin/env python
"""M8 task 2: the Gaia DR3 parallax ZERO-POINT, applied the house way.

WHY THIS EXISTS.  M7 measured the refit arm's dominant systematic and could
only name it: all three trio parallaxes came out 5-41 uas BELOW the published
values, and the photocentre mass function goes as parallax^-3, so a -0.9 %
parallax is +2.7 % on the companion mass.  That, and not a discrepant orbit,
is the whole of the arm's +2.4 sigma offset from Panuzzo's published M_BH
(M7 doc section 2e-ii).  A named systematic is not a bounded one.

THE HOUSE PATTERN.  This repository already applies Lindegren+2021 correctly,
in the sibling project seti-ellipsoid-broker
(src/seti_ellipsoid_broker/zeropoint.py, documented in its DATA-SOURCES.md
section 2a).  The pattern is reproduced here rather than reinvented:

    from zero_point import zpt
    zpt.load_tables()
    corrected = parallax - zpt.get_zpt(phot_g_mean_mag,
                                       nu_eff_used_in_astrometry,
                                       pseudocolour, ecl_lat,
                                       astrometric_params_solved)

and the four load-bearing details that go with it, each of which the sibling
project pays for in code and which are reproduced verbatim in intent:

  1. SIGN.  `corrected = parallax - Z`.  Z is typically negative (the DR3
     global mean is -17 uas), so the corrected parallax is LARGER and the
     star is CLOSER.
  2. ORDER.  The correction is applied BEFORE anything inverts or cubes the
     parallax.  Here that means before the mass function, which is where a
     0.9 % parallax error becomes a 2.7 % mass error.
  3. GUARD.  zpt.get_zpt() RAISES if any astrometric_params_solved is not
     31 (5p) or 95 (6p), so 2-parameter solutions must be masked out BEFORE
     the call, not filtered after.  The validity box is 6 < G < 21,
     1.1 < nu_eff < 1.9 (5p), 1.24 < pseudocolour < 1.72 (6p); outside it
     the package returns NaN with `_warnings=False`, and the house rule is
     to FALL BACK TO THE UNCORRECTED PARALLAX rather than drop the source --
     but to count and report how many fell back.
  4. NEP-50.  gaiadr3-zeropoint 0.1.0's scalar path calls
     np.can_cast(python_scalar, float), which numpy >= 2 forbids.  Passing
     ndarrays takes the package's array branch and skips the check.  Always
     pass arrays.

PROVENANCE QUIRK, carried from the sibling project: the dist-info says
version 0.1.0 while zero_point.__version__ says "0.0.1".  Stamp provenance
from the dist metadata, never from the module attribute.

CITATION.  Lindegren, L., Bastian, U., Biermann, M., et al. 2021,
"Gaia Early Data Release 3: Parallax bias versus magnitude, colour, and
position", A&A 649, A4.  Package: gaiadr3-zeropoint (Pau Ramos),
https://gitlab.com/icc-ub/public/gaiadr3_zeropoint

Run:
  .venv/Scripts/python.exe scripts/m8_zeropoint.py --pull
  .venv/Scripts/python.exe scripts/m8_zeropoint.py --selftest
"""
import argparse
import hashlib
import os
import sys
import time
import warnings
from datetime import datetime, timezone

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PARQUET = os.path.join(BASE, "data", "dr3_zeropoint_columns.parquet")
OUT_NOTE = os.path.join(BASE, "data", "dr3_zeropoint_columns.NOTE.md")

# DR3 global mean zero-point, Lindegren+2021 -- the fallback scale, quoted
# for orientation only.  It is NEVER applied as a scalar here.
GAIA_DR3_MEAN_ZEROPOINT_MAS = -0.017
SOLVED_5P, SOLVED_6P = 31, 95

ZP_COLS = ["source_id", "phot_g_mean_mag", "nu_eff_used_in_astrometry",
           "pseudocolour", "ecl_lat", "astrometric_params_solved",
           "parallax", "parallax_error"]

_TABLES_LOADED = False


def _zpt():
    """Import zero_point.zpt and load its coefficient tables once."""
    global _TABLES_LOADED
    try:
        from zero_point import zpt
    except ImportError as exc:                        # pragma: no cover
        raise ImportError(
            "the Lindegren+2021 correction needs the 'gaiadr3-zeropoint' "
            "package (import name 'zero_point'): "
            "pip install gaiadr3-zeropoint") from exc
    if not _TABLES_LOADED:
        zpt.load_tables()
        _TABLES_LOADED = True
    return zpt


def zpt_package_version():
    """Version from the DIST metadata -- zero_point.__version__ lies."""
    try:
        from importlib.metadata import version
        return version("gaiadr3-zeropoint")
    except Exception:                                 # noqa: BLE001
        return "UNSOURCED"


def _arr(x):
    return np.atleast_1d(np.asarray(x, dtype=float))


def parallax_zeropoint(phot_g_mean_mag, nu_eff_used_in_astrometry,
                       pseudocolour, ecl_lat, astrometric_params_solved):
    """Z [mas] per source, NaN where the correction is not defined.

    Masks non-(31,95) solutions BEFORE the call -- get_zpt raises on them.
    """
    zpt = _zpt()
    g = _arr(phot_g_mean_mag)
    nu = _arr(nu_eff_used_in_astrometry)
    pc = _arr(pseudocolour)
    ecl = _arr(ecl_lat)
    solved = _arr(astrometric_params_solved)
    shapes = {a.shape for a in (g, nu, pc, ecl, solved)}
    if len(shapes) != 1:
        raise ValueError(f"inputs must share one shape; got {sorted(shapes)}")
    out = np.full(g.shape, np.nan, dtype=float)
    ok = (solved == SOLVED_5P) | (solved == SOLVED_6P)
    if np.any(ok):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            z = zpt.get_zpt(g[ok], nu[ok], pc[ok], ecl[ok],
                            solved[ok].astype(int), _warnings=False)
        out[ok] = np.asarray(z, dtype=float)
    return out


def apply_zeropoint(parallax_mas, phot_g_mean_mag, nu_eff_used_in_astrometry,
                    pseudocolour, ecl_lat, astrometric_params_solved,
                    fallback_to_uncorrected=True):
    """(corrected_parallax, Z, applied_mask).  corrected = parallax - Z."""
    plx = _arr(parallax_mas)
    z = parallax_zeropoint(phot_g_mean_mag, nu_eff_used_in_astrometry,
                           pseudocolour, ecl_lat, astrometric_params_solved)
    corrected = plx - z
    applied = np.isfinite(z)
    if fallback_to_uncorrected:
        corrected = np.where(applied, corrected, plx)
    return corrected, z, applied


def zeropoint_frame(df, plx_col="parallax"):
    """Add zp_mas / parallax_zp_corrected / zp_applied to a frame in place-ish.

    `df` must carry the five ZP inputs plus `plx_col`.  Returns a COPY.
    """
    d = df.copy()
    corrected, z, applied = apply_zeropoint(
        d[plx_col].values, d["phot_g_mean_mag"].values,
        d["nu_eff_used_in_astrometry"].values, d["pseudocolour"].values,
        d["ecl_lat"].values, d["astrometric_params_solved"].values)
    d["zp_mas"] = z
    d["zp_applied"] = applied
    d[plx_col + "_zp"] = corrected
    return d


# ======================================================================
# the pull
# ======================================================================
def _id_universe():
    """Every source this milestone needs a zero-point for, with provenance."""
    import pyarrow.parquet as pq
    prov = {}

    def add(ids, tag):
        for s in ids:
            prov.setdefault(int(s), set()).add(tag)

    q = pd.read_csv(os.path.join(BASE, "out", "epoch_vet_day1_queue.v2.csv"))
    add(q["source_id"].astype("int64").tolist(), "day1_queue_v2")

    tri = pd.read_parquet(os.path.join(BASE, "data", "dr3_amrf_triage.parquet"),
                          columns=["source_id", "class_det"])
    add(tri.loc[tri["class_det"] == 3, "source_id"].astype("int64").tolist(),
        "class3")

    nss = pd.read_parquet(os.path.join(BASE, "data",
                                       "dr3_nss_amrf_input.parquet"),
                          columns=["source_id"])
    vc = nss["source_id"].value_counts()
    add(vc[vc > 1].index.astype("int64").tolist(), "dual_solution")

    # the M7 trio: BH3 has no NSS row at all, so it is not in any of the above
    add([4318465066420528000, 3937211745905473024, 1457486023639239296],
        "m7_trio")

    ids = sorted(prov)
    tags = ["|".join(sorted(prov[i])) for i in ids]
    return ids, tags


def pull(force=False):
    import m5_pull_activity_columns as P
    if os.path.exists(OUT_PARQUET) and not force:
        print(f"{OUT_PARQUET} exists -- use --force to re-pull")
        return pd.read_parquet(OUT_PARQUET)
    ids, tags = _id_universe()
    print(f"zero-point columns for {len(ids)} sources")
    t0 = time.time()
    name, url = P.pick_endpoint()
    served = set()
    gs = P.pull(url, "gaiadr3.gaia_source", ZP_COLS, ids, served=served)
    dt = time.time() - t0
    out = pd.DataFrame({"source_id": np.asarray(ids, dtype=np.int64),
                        "id_provenance": tags})
    out = out.merge(gs, on="source_id", how="left")
    assert len(out) == len(ids), f"join fanned out: {len(out)} vs {len(ids)}"
    out.to_parquet(OUT_PARQUET, index=False)
    sha = hashlib.sha256(open(OUT_PARQUET, "rb").read()).hexdigest()
    got = int(out["phot_g_mean_mag"].notna().sum())
    with open(OUT_NOTE, "w", encoding="utf-8") as fh:
        fh.write(
            "# dr3_zeropoint_columns.parquet\n\n"
            f"- pulled: {datetime.now(timezone.utc).isoformat()} "
            f"(sync CSV chunks of <= {P.CHUNK} ids; {dt:.0f}s)\n"
            f"- endpoint chosen by probe: **{name}** ({url}) -- anonymous\n"
            f"- endpoint host(s) that served chunks: {', '.join(sorted(served))}\n"
            f"- rows: {len(out)} (one per source_id); gaia_source matched "
            f"{got}\n"
            "- id-list provenance: day-one queue v2, class-III, the 98 "
            "dual-solution NSS sources, the M7 trio\n"
            "- columns: the five Lindegren+2021 inputs "
            "(phot_g_mean_mag, nu_eff_used_in_astrometry, pseudocolour, "
            "ecl_lat, astrometric_params_solved) + gaia_source parallax\n"
            f"- sha256: {sha}\n")
    print(f"wrote {OUT_PARQUET} ({len(out)} rows, {dt:.0f}s)\n  sha256 {sha}")
    return out


def load():
    if not os.path.exists(OUT_PARQUET):
        raise FileNotFoundError(
            f"{OUT_PARQUET} missing -- run m8_zeropoint.py --pull")
    return pd.read_parquet(OUT_PARQUET)


# ======================================================================
def selftest():
    """Reproduce the sibling project's pinned anchor, then the DR3 mean."""
    ok = True
    z = parallax_zeropoint(18.5, 1.6, np.nan, -66.0, 31)
    print(f"anchor  G=18.5 nu=1.6 pc=nan ecl=-66 solved=5p -> Z = {z[0]:.6f} "
          "mas   (seti-ellipsoid-broker pins -0.028661)")
    if abs(z[0] - (-0.028661)) > 5e-6:
        print("  MISMATCH against the sibling project's pinned value")
        ok = False
    z2 = parallax_zeropoint([18.5, 15.0, 12.0], [1.6, 1.5, 1.4],
                            [np.nan] * 3, [-66.0, 10.0, 45.0], [31, 31, 31])
    print(f"vector  -> {np.round(z2, 6)}")
    z3 = parallax_zeropoint([10.0], [1.5], [np.nan], [0.0], [3])
    print(f"2-parameter solution (solved=3) -> {z3[0]} (must be nan)")
    if np.isfinite(z3[0]):
        print("  the 31/95 guard is not working")
        ok = False
    z4 = parallax_zeropoint([5.0], [1.5], [np.nan], [0.0], [31])
    print(f"out of the validity box (G=5) -> {z4[0]} (must be nan)")
    if np.isfinite(z4[0]):
        print("  the validity box is not being honoured")
        ok = False
    c, zz, ap = apply_zeropoint([1.0], [5.0], [1.5], [np.nan], [0.0], [31])
    print(f"fallback: parallax 1.0 outside the box -> {c[0]} "
          f"(must be 1.0, applied={ap[0]})")
    if abs(c[0] - 1.0) > 0 or ap[0]:
        print("  the fallback is not working")
        ok = False
    print(f"\ngaiadr3-zeropoint dist version: {zpt_package_version()}  "
          f"(module __version__ lies -- do not use it)")
    print("SELFTEST", "PASS" if ok else "FAIL")
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pull", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return 0 if selftest() else 1
    if a.pull:
        pull(force=a.force)
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
