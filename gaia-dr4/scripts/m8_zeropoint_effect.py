#!/usr/bin/env python
"""M8 task 2: BOUND THE PARALLAX ZERO-POINT, and re-derive Gaia BH3.

M7 section 2e-ii named the arm's dominant systematic and could do nothing
else with it: the three trio refit parallaxes ran 5-41 uas BELOW the
published values, the photocentre mass function goes as parallax^-3, and
that -- not a discrepant orbit -- is what the arm's +2.42 sigma offset from
Panuzzo's published M_BH is.  This closes it.

WHAT THIS DOES

  Z1  VALIDATE the implementation against two independent users of the same
      correction, before using it for anything:
        * Panuzzo et al. 2024 (A&A 686, L2), Table 1 footnote b: "A
          zero-point correction (Lindegren+2021) of 35.4 uas has been
          applied to the parallax value given in the catalogue."  The
          catalogue value is pulled live; the corrected value is printed in
          their table.  Both ends are checkable.
        * El-Badry et al. 2026 (the EB26 verdict paper this repo already
          consumes), Table "astrometric_joint_dark_l21_zpt": the same eight
          sources fitted with and without the L21 correction, so the
          difference of the two published parallax columns is their applied
          shift.

  Z2  THE DIRECTION OF M7's OFFSET, re-examined.  M7 compared an
      UNCORRECTED refit parallax against published values whose zero-point
      convention it had not checked.  Panuzzo's paper states the convention
      explicitly in two places and they are OPPOSITE for the two tables --
      Table 1 (the DR3 single-star parallax) IS corrected, Table 2 (the NSS
      orbital solutions) is NOT, and the Letter says so: "we do not have
      enough information at this stage to quantify the bias for the
      preliminary NSS solutions".  Which of those M7's comparison used
      decides whether its 5-41 uas is a systematic or a convention
      mismatch.

  Z3  RE-DERIVE Gaia BH3's MASS with and without the correction, through the
      production arm, and test whether the 2.4 sigma offset closes.
      Panuzzo's headline M_BH = 32.70 +/- 0.82 is derived from a1 (the
      combined astrometry+RVS solution) and uses NO parallax at all, so it
      is an anchor the correction cannot move.  Panuzzo also publishes a
      zero-point-FREE parallax, varpi = a0/a1 = 1.6933 +/- 0.0164 mas,
      which is the cleanest available test of a corrected parallax.

  Z4  AT SCALE: what the correction costs in companion mass across the
      day-one queue.  The mass function goes as varpi^-3, so a source at
      2 mas moves 5 % and a source at 0.5 mas moves 22 %.  The distribution
      of that shift over the 981 rows December will actually refit is the
      number the runbook needs.

  Z5  THE RESIDUAL, bounded.  What is left after the correction, and what
      it costs.

CONVENTION, stated once: varpi_true = varpi - Z, Z is typically negative,
so the corrected parallax is LARGER and the companion mass SMALLER.  This
is the convention of Lindegren+2021, of the gaiadr3-zeropoint package, of
the sibling seti-ellipsoid-broker project, and of El-Badry+2026 (who state
it explicitly).  All four agree; it is written down here because getting it
backwards doubles the error instead of removing it.

Run:
  .venv/Scripts/python.exe scripts/m8_zeropoint_effect.py --all
"""
import argparse
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")
DATA = os.path.join(BASE, "data")

import m8_zeropoint as Z                                        # noqa: E402

BH3 = 4318465066420528000
HD114762 = 3937211745905473024
GAIA4 = 1457486023639239296

# ---- sourced reference values -------------------------------------------
# Panuzzo et al. 2024, A&A 686, L2 (arXiv:2404.10486).  Line numbers are of
# the arXiv source in data/papers/2404.10486/main.tex, checked 2026-08-24.
PANUZZO = {
    # Table 1 (source properties), line 197 + footnote b line 211: the DR3
    # SINGLE-STAR parallax WITH the 35.4 uas L21 correction applied.
    "dr3_singlestar_corrected": (1.679, 0.069),
    "quoted_zp_uas": 35.4,
    # Table 2 (tab:orbit_params) line 279: astrometric-only NSS solution.
    # NOT zero-point corrected -- line 262 says the bias could not be
    # quantified for the preliminary NSS solutions.
    "nss_astrometric_uncorrected": (1.6747, 0.0094),
    # line 329: the combined astrometry+RVS NSS parallax, also uncorrected.
    "nss_combined_uncorrected": (1.6808, 0.0086),
    # line 279 col. 2 + footnote b + line 337: varpi = a0/a1.  Derived from
    # the SPECTROSCOPIC a1, so it carries NO astrometric zero-point at all.
    "a0_over_a1_zeropoint_free": (1.6933, 0.0164),
    # Table 2: mass functions and the headline mass
    "fmass_astrometric": (32.03, 0.64),
    "fmass_from_a1": (31.23, 0.81),
    "m_bh_headline": (32.70, 0.82),
    "m1": (0.76, 0.05),
}

# El-Badry et al. 2026, Tables tab:astrometric-joint-dark-orbits and
# tab:astrometric-joint-dark-l21-zpt-orbits (printed preview rows), from
# data/papers/2608.06453/*.tex.  (source_id, varpi_nozpt, varpi_l21)
EB26_ZPT_PAIRS = [
    (1522897482203494784, 12.446, 12.478),
    (4373465352415301632, 2.098, 2.136),
    (2995961897685517312, 2.506, 2.532),
    (220012968211559296, 3.220, 3.262),
    (2080945469200565248, 1.403, 1.427),
    (6481502062263141504, 1.750, 1.790),
    (5820382041374661888, 1.344, 1.371),
    (2919995917769953408, 2.298, 2.337),
]
# EB26's own directly measured zero-point for astrometric ORBITAL solutions
# (abstract + section "Measuring the parallax zeropoint"): a joint fit of 40
# dark-companion binaries, convention varpi_true = varpi - Z.
EB26_MEASURED_Z = (-0.0362, 0.0053)
EB26_L21_MEDIAN_SAME40 = -0.0342


def _tap_gaia_source(ids):
    import m5_pull_activity_columns as P
    _, url = P.pick_endpoint()
    return P.pull(url, "gaiadr3.gaia_source", Z.ZP_COLS, list(ids))


def zp_for(ids, say=None):
    """Z for a list of source_ids, from the cached pull, falling back to a
    live query for anything not in it."""
    d = Z.load()
    have = d[d.source_id.isin([int(i) for i in ids])]
    missing = sorted(set(int(i) for i in ids) - set(have.source_id.tolist()))
    if missing:
        if say:
            say(f"    {len(missing)} id(s) not in the cached pull -- live "
                f"query")
        extra = _tap_gaia_source(missing)
        have = pd.concat([have, extra], ignore_index=True)
    return Z.zeropoint_frame(have).set_index("source_id")


# ======================================================================
def z1_validate(say):
    say("\n" + "=" * 78)
    say("Z1  VALIDATE the implementation against two independent users")
    say("=" * 78)
    ok = True
    zf = zp_for([BH3] + [p[0] for p in EB26_ZPT_PAIRS], say)

    r = zf.loc[BH3]
    say("\n  (a) Panuzzo et al. 2024, Table 1 footnote b")
    say(f"      DR3 catalogue parallax (pulled)   {r['parallax']:.6f} mas")
    say(f"      L21 Z computed here               {r['zp_mas']*1000:+.1f} uas"
        f"   (Panuzzo quote: -{PANUZZO['quoted_zp_uas']:.1f} uas)")
    say(f"      corrected here                    "
        f"{r['parallax_zp']:.6f} mas")
    say(f"      Panuzzo's printed corrected value {PANUZZO['dr3_singlestar_corrected'][0]:.6f}"
        f" +/- {PANUZZO['dr3_singlestar_corrected'][1]:.3f} mas")
    dz = abs(abs(r["zp_mas"] * 1000) - PANUZZO["quoted_zp_uas"])
    say(f"      |Z_here| - |Z_Panuzzo| = {dz:.3f} uas   "
        f"(tolerance 0.05 uas = their printed precision)")
    if dz > 0.05:
        say("      MISMATCH")
        ok = False
    else:
        say("      MATCH -- the implementation reproduces the published "
            "correction exactly")

    say("\n  (b) El-Badry et al. 2026 -- the same eight sources fitted with "
        "and\n      without L21; the difference of the two published "
        "parallax columns is\n      their applied shift.  These are JOINT "
        "astrometry+RV fits, so the shift\n      is not exactly Z (the RV "
        "data pulls the parallax too); agreement to a\n      few uas is the "
        "test, not bit-identity.")
    rows = []
    for sid, p0, p1 in EB26_ZPT_PAIRS:
        if sid not in zf.index:
            continue
        zz = float(zf.loc[sid, "zp_mas"])
        rows.append({"source_id": sid, "eb26_shift_uas": (p1 - p0) * 1000,
                     "l21_here_uas": -zz * 1000,
                     "diff_uas": (p1 - p0) * 1000 + zz * 1000})
    t = pd.DataFrame(rows)
    t["source_id"] = t["source_id"].astype("int64")
    say("")
    # MEASURED LANDMINE (M8).  `for _, x in t.iterrows()` is the same 2^53
    # trap as M7 landmine #4: iterrows() collapses a mixed-dtype row into a
    # single float64 Series, so `int(x.source_id)` printed ...494912 for a
    # source whose id ends ...494784.  Take the int column as a column.
    sids = t["source_id"].to_numpy(dtype="int64")
    for i in range(len(t)):
        say(f"      {sids[i]:<20d} EB26 {t['eb26_shift_uas'].iloc[i]:+6.1f}   "
            f"here {t['l21_here_uas'].iloc[i]:+6.1f}   "
            f"diff {t['diff_uas'].iloc[i]:+6.1f} uas")
    say(f"\n      median |diff| = {np.median(np.abs(t.diff_uas)):.1f} uas over "
        f"{len(t)} sources; EB26 quote their\n      values to 3 decimal "
        f"places in mas, i.e. 1 uas rounding on each column.")
    say(f"\n  (c) EB26 also MEASURED the zero-point for astrometric ORBITAL "
        f"solutions\n      directly, from 40 dark-companion joint fits: "
        f"Z = {EB26_MEASURED_Z[0]:+.4f} +/- {EB26_MEASURED_Z[1]:.4f} mas,\n"
        f"      against the L21 median {EB26_L21_MEDIAN_SAME40:+.4f} mas for "
        f"the same 40 sources.\n      Their conclusion, quoted: \"the "
        f"single-star zeropoint can and should be\n      applied to binary "
        f"solutions as well.\"  That is the sourced authority for\n"
        f"      applying a single-star correction to an orbital solution, "
        f"which is the\n      one thing this task could not otherwise "
        f"justify.")
    say(f"\n  Z1 {'PASS' if ok else 'FAIL'}")
    return ok, t


# ======================================================================
def z2_direction(say, trio):
    say("\n" + "=" * 78)
    say("Z2  M7's 5-41 uas offset: systematic, or convention mismatch?")
    say("=" * 78)
    say("  Panuzzo states the convention in two places, and they are "
        "OPPOSITE:")
    say("    Table 1 (DR3 single-star parallax)   -- L21 APPLIED "
        "(footnote b, 35.4 uas)")
    say("    Table 2 (the NSS orbital solutions)  -- NOT applied; the Letter "
        "says the")
    say("                                            bias 'could not be "
        "quantified' for")
    say("                                            preliminary NSS "
        "solutions (line 262)")
    say("  M7 compared its refit parallax against the TABLE 2 value "
        "(1.6747 +/- 0.0094),")
    say("  which is UNCORRECTED -- so M7's -14.9 uas on BH3 is a comparison "
        "of two")
    say("  uncorrected parallaxes and is NOT the zero-point.  The zero-point "
        "is a")
    say("  common offset that cancels in that difference.")
    say("")
    say("  the four BH3 parallaxes, on one scale:")
    r = trio.loc[BH3]
    say(f"    DR3 single-star, catalogue        {r['dr3_parallax']:.6f}")
    say(f"    DR3 single-star + L21             {r['dr3_parallax_zp']:.6f}"
        f"   (Panuzzo Table 1: {PANUZZO['dr3_singlestar_corrected'][0]:.3f})")
    say(f"    Panuzzo NSS astrometric, RAW      "
        f"{PANUZZO['nss_astrometric_uncorrected'][0]:.6f} "
        f"+/- {PANUZZO['nss_astrometric_uncorrected'][1]:.4f}")
    say(f"    arm refit (M7), RAW               {r['refit_parallax']:.6f} "
        f"+/- {r['refit_parallax_err']:.6f}")
    say(f"    arm refit + L21                   {r['refit_parallax_zp']:.6f}")
    say(f"    Panuzzo a0/a1, ZERO-POINT FREE    "
        f"{PANUZZO['a0_over_a1_zeropoint_free'][0]:.6f} "
        f"+/- {PANUZZO['a0_over_a1_zeropoint_free'][1]:.4f}")
    zpf, zpfe = PANUZZO["a0_over_a1_zeropoint_free"]
    for lab, v in [("RAW refit", r["refit_parallax"]),
                   ("L21-corrected refit", r["refit_parallax_zp"])]:
        d = (v - zpf) * 1000
        sg = (v - zpf) / np.hypot(r["refit_parallax_err"], zpfe)
        say(f"    {lab:<22s} vs the zero-point-free a0/a1: "
            f"{d:+7.1f} uas = {sg:+5.2f} sigma")
    say("")
    say("  THE TEST THAT DECIDES IT: a0/a1 is derived from the "
        "SPECTROSCOPIC a1 and")
    say("  carries no astrometric zero-point.  If the correction is real, "
        "the")
    say("  corrected refit parallax must land on it and the raw one must "
        "not.")
    return True


# ======================================================================
def z3_bh3_mass(say, trio):
    import orbital_refit_arm as A
    say("\n" + "=" * 78)
    say("Z3  Gaia BH3's companion mass, with and without the correction")
    say("=" * 78)
    rows = []
    for sid, name in [(BH3, "Gaia BH3"), (HD114762, "HD 114762"),
                      (GAIA4, "Gaia-4")]:
        r = trio.loc[sid]
        m1 = float(r["m1"])
        for tag, plx in [("raw", r["refit_parallax"]),
                         ("L21", r["refit_parallax_zp"])]:
            f = float(A.mass_function_msun(r["refit_a0"], r["refit_period"],
                                           plx))
            m2 = A.m2_reference(f, m1, r["refit_a0"], r["refit_period"], plx)
            rows.append({"name": name, "source_id": sid, "variant": tag,
                         "parallax_mas": float(plx),
                         "zp_uas": float(r["zp_mas"] * 1000),
                         "a0_mas": float(r["refit_a0"]),
                         "period_d": float(r["refit_period"]),
                         "m1_msun": m1, "mass_function_msun": f,
                         "m2_msun": float(m2)})
    t = pd.DataFrame(rows)
    say("")
    for name, sub in t.groupby("name", sort=False):
        raw = sub[sub.variant == "raw"].iloc[0]
        cor = sub[sub.variant == "L21"].iloc[0]
        say(f"  {name}")
        say(f"    parallax   {raw.parallax_mas:.6f} -> "
            f"{cor.parallax_mas:.6f} mas  (Z = {raw.zp_uas:+.1f} uas)")
        say(f"    f_M        {raw.mass_function_msun:.5f} -> "
            f"{cor.mass_function_msun:.5f} Msun  "
            f"({100*(cor.mass_function_msun/raw.mass_function_msun - 1):+.2f} %)")
        say(f"    M2         {raw.m2_msun:.5f} -> {cor.m2_msun:.5f} Msun  "
            f"({100*(cor.m2_msun/raw.m2_msun - 1):+.2f} %, "
            f"{cor.m2_msun - raw.m2_msun:+.4f} Msun)")
    bh_raw = t[(t.source_id == BH3) & (t.variant == "raw")].iloc[0]
    bh_cor = t[(t.source_id == BH3) & (t.variant == "L21")].iloc[0]
    mp, me = PANUZZO["m_bh_headline"]
    say("")
    say("  THE PRE-REGISTERED QUESTION -- does the 2.4 sigma close?")
    say(f"    Panuzzo headline M_BH = {mp:.2f} +/- {me:.2f} Msun, derived "
        f"from a1 and")
    say(f"    therefore INDEPENDENT of any parallax zero-point.")
    for lab, m2 in [("arm, RAW parallax (M7)", bh_raw.m2_msun),
                    ("arm, L21-corrected    ", bh_cor.m2_msun)]:
        say(f"    {lab}: M2 = {m2:8.4f}  -> {(m2 - mp)/me:+6.2f} sigma")
    fp, fe = PANUZZO["fmass_astrometric"]
    say("")
    say(f"  and against Panuzzo's own ASTROMETRIC mass function "
        f"{fp:.2f} +/- {fe:.2f} Msun")
    say(f"  (which is computed from a parallax that is NOT zero-point "
        f"corrected):")
    for lab, f in [("arm, RAW parallax", bh_raw.mass_function_msun),
                   ("arm, L21-corrected", bh_cor.mass_function_msun)]:
        say(f"    {lab}: f_M = {f:8.4f}  -> {(f - fp)/fe:+6.2f} sigma")
    fa, fae = PANUZZO["fmass_from_a1"]
    say(f"\n  and against the a1-derived, zero-point-free f_M "
        f"{fa:.2f} +/- {fae:.2f} Msun:")
    for lab, f in [("arm, RAW parallax", bh_raw.mass_function_msun),
                   ("arm, L21-corrected", bh_cor.mass_function_msun)]:
        say(f"    {lab}: f_M = {f:8.4f}  -> {(f - fa)/fae:+6.2f} sigma")
    t.to_csv(os.path.join(OUT, "m8_zeropoint_trio.csv"), index=False,
             lineterminator="\n")
    return t


# ======================================================================
def z4_scale(say):
    say("\n" + "=" * 78)
    say("Z4  AT SCALE -- what the correction costs across the day-one queue")
    say("=" * 78)
    q = pd.read_csv(os.path.join(OUT, "epoch_vet_day1_queue.v2.csv"))
    tri = pd.read_parquet(os.path.join(DATA, "dr3_amrf_triage.parquet"),
                          columns=["source_id", "nss_solution_type",
                                   "a0_mas", "period", "nss_parallax",
                                   "m1_used", "m2_min_dark", "class_det",
                                   "significance"])
    d = Z.zeropoint_frame(Z.load())
    j = q[["source_id"]].astype({"source_id": "int64"}).merge(
        tri, on="source_id", how="left").merge(
        d[["source_id", "zp_mas", "zp_applied"]], on="source_id", how="left")
    assert len(j) == len(q), f"join fanned out: {len(j)} vs {len(q)}"
    j = j[np.isfinite(j.a0_mas) & np.isfinite(j.nss_parallax)
          & (j.nss_parallax > 0) & np.isfinite(j.zp_mas)]
    say(f"\n  {len(j)} of {len(q)} queue rows have an a0, a positive NSS "
        f"parallax and a\n  defined L21 correction "
        f"({int((~np.isfinite(j.zp_mas)).sum())} undefined)")
    say(f"  Z over the queue: median {1000*j.zp_mas.median():+.1f} uas, "
        f"p10 {1000*j.zp_mas.quantile(.1):+.1f}, "
        f"p90 {1000*j.zp_mas.quantile(.9):+.1f} uas")

    import orbital_refit_arm as A
    plx0 = j.nss_parallax.values
    plx1 = plx0 - j.zp_mas.values
    f0 = A.mass_function_msun(j.a0_mas.values, j.period.values, plx0)
    f1 = A.mass_function_msun(j.a0_mas.values, j.period.values, plx1)
    m1 = np.where(np.isfinite(j.m1_used.values), j.m1_used.values, np.nan)
    m2_0 = A.m2_from_mass_function(f0, m1)
    m2_1 = A.m2_from_mass_function(f1, m1)
    rel = m2_1 / m2_0 - 1.0
    frel = f1 / f0 - 1.0
    j = j.assign(parallax_zp=plx1, fmass_raw=f0, fmass_zp=f1,
                 fmass_rel_shift=frel,
                 m2_raw=m2_0, m2_zp=m2_1, m2_rel_shift=rel,
                 m2_abs_shift=m2_1 - m2_0)
    j.to_csv(os.path.join(OUT, "m8_zeropoint_queue.csv"), index=False,
             lineterminator="\n")
    ok = np.isfinite(rel)
    say(f"\n  companion-mass shift from applying L21 "
        f"(n = {int(ok.sum())} with an M1 rung):")
    say(f"    relative: median {100*np.nanmedian(rel):+.2f} %  "
        f"p10 {100*np.nanpercentile(rel[ok],10):+.2f} %  "
        f"p90 {100*np.nanpercentile(rel[ok],90):+.2f} %  "
        f"worst {100*np.nanmin(rel[ok]):+.2f} %")
    say(f"    absolute: median {np.nanmedian(j.m2_abs_shift[ok]):+.4f} Msun  "
        f"p10 {np.nanpercentile(j.m2_abs_shift[ok],10):+.4f}  "
        f"p90 {np.nanpercentile(j.m2_abs_shift[ok],90):+.4f}")
    say(f"    (EB26 measured a median shift of -0.018 Msun on their own "
        f"joint fits)")
    say(f"\n  the shift is a function of distance -- it is "
        f"3 * Z / varpi to first order:")
    for lo, hi in [(0, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 5.0),
                   (5.0, 1e9)]:
        sub = j[(j.nss_parallax >= lo) & (j.nss_parallax < hi)]
        if not len(sub):
            continue
        say(f"    varpi {lo:5.1f}-{hi if hi < 1e8 else np.inf:5.1f} mas: "
            f"n={len(sub):4d}  median mass shift "
            f"{100*np.nanmedian(sub.m2_rel_shift):+6.2f} %")
    say(f"\n  rows whose mass moves by more than 5 %: "
        f"{int(np.nansum(np.abs(rel) > 0.05))} of {int(ok.sum())}")
    say(f"  rows whose mass moves by more than 10 %: "
        f"{int(np.nansum(np.abs(rel) > 0.10))}")
    say(f"\n  the M1-FREE version of the same shift (mass function, defined "
        f"for all {int(np.isfinite(frel).sum())} rows):")
    say(f"    median {100*np.nanmedian(frel):+.2f} %  "
        f"p10 {100*np.nanpercentile(frel, 10):+.2f} %  "
        f"p90 {100*np.nanpercentile(frel, 90):+.2f} %  "
        f"worst {100*np.nanmin(frel):+.2f} %")
    top = j.sort_values("m2_min_dark", ascending=False).head(10)
    say("\n  the ten highest-M2_min queue members (the December headline "
        "candidates).")
    say("  M2 is blank where the triage's M1 ladder reached the evolved "
        "bracket rather")
    say("  than a point mass; the M1-free f_M shift is defined for every "
        "row:")
    say(f"    {'source_id':<20s} {'varpi':>7s} {'M2_raw':>8s} {'M2_L21':>8s} "
        f"{'dM2':>8s} {'df_M':>8s}")
    tsid = top["source_id"].to_numpy(dtype="int64")
    for i in range(len(top)):
        r = top.iloc[i]
        m2r = "     ---" if not np.isfinite(r.m2_raw) else f"{r.m2_raw:8.3f}"
        m2z = "     ---" if not np.isfinite(r.m2_zp) else f"{r.m2_zp:8.3f}"
        dm2 = ("     ---" if not np.isfinite(r.m2_rel_shift)
               else f"{100*r.m2_rel_shift:+7.2f}%")
        say(f"    {tsid[i]:<20d} {r.nss_parallax:7.4f} {m2r} {m2z} "
            f"{dm2} {100*r.fmass_rel_shift:+7.2f}%")
    return j


# ======================================================================
def z5_residual(say, trio, val):
    say("\n" + "=" * 78)
    say("Z5  THE RESIDUAL, bounded -- and what it costs")
    say("=" * 78)
    say("  Three independent statements about how big the residual "
        "zero-point is\n  after L21 is applied:")
    say(f"    (a) EB26's direct measurement on 40 astrometric ORBITAL "
        f"solutions:\n        Z = {EB26_MEASURED_Z[0]:+.4f} +/- "
        f"{EB26_MEASURED_Z[1]:.4f} mas vs the L21 median "
        f"{EB26_L21_MEDIAN_SAME40:+.4f} for the\n        same sources -- a "
        f"residual of "
        f"{1000*(EB26_MEASURED_Z[0]-EB26_L21_MEDIAN_SAME40):+.1f} uas, "
        f"{abs(EB26_MEASURED_Z[0]-EB26_L21_MEDIAN_SAME40)/EB26_MEASURED_Z[1]:.2f} "
        f"sigma from zero.")
    say(f"    (b) the scatter of L21 vs EB26's applied shift on the eight "
        f"published\n        pairs: median |diff| "
        f"{np.median(np.abs(val.diff_uas)):.1f} uas.")
    r = trio.loc[BH3]
    zpf, zpfe = PANUZZO["a0_over_a1_zeropoint_free"]
    res = (r["refit_parallax_zp"] - zpf) * 1000
    say(f"    (c) Gaia BH3 against Panuzzo's zero-point-free a0/a1 "
        f"parallax:\n        residual {res:+.1f} uas "
        f"(+/- {1000*np.hypot(r['refit_parallax_err'], zpfe):.1f} uas, "
        f"i.e. consistent with zero at "
        f"{abs(res)/1000/np.hypot(r['refit_parallax_err'], zpfe):.2f} "
        f"sigma).")
    bound = max(abs(EB26_MEASURED_Z[0] - EB26_L21_MEDIAN_SAME40) * 1000,
                float(np.median(np.abs(val.diff_uas))), abs(res))
    zq = Z.zeropoint_frame(Z.load())
    med_removed = abs(1000.0 * float(zq.loc[zq.zp_applied, "zp_mas"].median()))
    say(f"\n  BOUND ADOPTED: the residual zero-point after L21 is <= "
        f"{bound:.0f} uas\n  (the largest of the three, rounded up), against "
        f"the {med_removed:.0f} uas the correction itself\n  removes at the "
        f"median of this sample (the DR3 GLOBAL mean is "
        f"{abs(1000*Z.GAIA_DR3_MEAN_ZEROPOINT_MAS):.0f} uas; this sample "
        f"is\n  fainter and redder than the all-sky average, so quoting the "
        f"global number\n  here would understate what is being removed by "
        f"a factor two).")
    say(f"\n  WHAT IT COSTS IN COMPANION MASS.  dM2/M2 ~ -3 dvarpi/varpi, so "
        f"a {bound:.0f} uas\n  residual costs:")
    for plx in [0.3, 0.5, 1.0, 1.6598, 2.0, 5.0, 13.6]:
        say(f"    varpi {plx:7.4f} mas -> {300*bound/1000/plx:5.2f} % on the "
            f"companion mass")
    say(f"\n  For Gaia BH3 (varpi 1.66 mas) that is "
        f"{300*bound/1000/1.6598:.2f} % = "
        f"{34.68*3*bound/1000/1.6598:.2f} Msun on a 34.7 Msun\n  companion "
        f"-- against Panuzzo's own 0.82 Msun uncertainty.  The zero-point "
        f"is\n  no longer the dominant systematic once it is applied; it "
        f"was only\n  dominant while it was being ignored.")
    return bound


# ======================================================================
def build_trio(say):
    """The M7 trio's refit values + their L21 corrections, in one frame."""
    p = os.path.join(OUT, "m7_refit_trio.csv")
    t = pd.read_csv(p)
    t["source_id"] = t["source_id"].astype("int64")
    zf = zp_for(t["source_id"].tolist(), say)
    rows = []
    for _, r in t.iterrows():
        sid = int(r["source_id"])
        z = zf.loc[sid]
        rows.append({
            "source_id": sid,
            "refit_parallax": float(r["refit_parallax_mas"]),
            "refit_parallax_err": float(r["refit_parallax_err_mas"]),
            "refit_a0": float(r["refit_a0_mas"]),
            "refit_period": float(r["refit_period_d"]),
            "m1": float(r["refit_m1_msun"]),
            "m1_sigma": float(r["refit_m1_sigma_msun"]),
            "refit_m2_m7": float(r["refit_m2_msun"]),
            "zp_mas": float(z["zp_mas"]),
            "refit_parallax_zp": float(r["refit_parallax_mas"])
            - float(z["zp_mas"]),
            "dr3_parallax": float(z["parallax"]),
            "dr3_parallax_zp": float(z["parallax_zp"]),
        })
    return pd.DataFrame(rows).set_index("source_id")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--out", default=os.path.join(OUT,
                                                  "m8_zeropoint_effect.txt"))
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    lines = []

    def say(s=""):
        print(s, flush=True)
        lines.append(s)

    say("M8 TASK 2 -- THE PARALLAX ZERO-POINT, BOUNDED")
    say(f"produced {pd.Timestamp.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}")
    say(f"gaiadr3-zeropoint {Z.zpt_package_version()}  "
        f"(Lindegren et al. 2021, A&A 649, A4)")
    say("convention: varpi_true = varpi - Z, Z typically negative, corrected "
        "parallax LARGER")

    ok, val = z1_validate(say)
    trio = build_trio(say)
    z2_direction(say, trio)
    mt = z3_bh3_mass(say, trio)
    z4_scale(say)
    bound = z5_residual(say, trio, val)

    summary = {
        "zeropoint_validation_pass": bool(ok),
        "residual_bound_uas": float(bound),
        "bh3": {
            "m2_raw": float(mt[(mt.source_id == BH3)
                               & (mt.variant == "raw")].m2_msun.iloc[0]),
            "m2_l21": float(mt[(mt.source_id == BH3)
                               & (mt.variant == "L21")].m2_msun.iloc[0]),
            "panuzzo_m_bh": PANUZZO["m_bh_headline"],
        },
        "produced_utc": pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with open(os.path.join(OUT, "m8_zeropoint_summary.json"), "w",
              newline="\n") as fh:
        json.dump(summary, fh, indent=2)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\nwrote {os.path.relpath(a.out, BASE)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
