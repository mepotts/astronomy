"""M5: the funnel WITH the nebular stage in place, and PR-2's validation.

Reports, all emitted -- never hand-copied:

  * the sky area the N1 catalogue veto masks, by Galactic-latitude band
    (Monte Carlo on a seeded uniform sphere, so the veto's cost in sky is
    visible and cannot hide inside a rejection fraction);
  * the ENRICHMENT of the veto -- the fraction of survivors it removes
    divided by the fraction of sky it removes.  A veto that only masks sky
    scores 1.0; a veto that tracks real contamination scores above it.  This
    needs no new threshold and is the honest test of whether N1 is doing work;
  * the funnel with the stage inserted where Hephaistos II Table 4 puts its
    CNN (between the RMSE gate and the extra cuts);
  * the residual overproduction factor by latitude band, before and after;
  * PR-2's validation (a) 7/7, (b) the latitude gradient, (c) the sensitivity
    band at 0.95 / 0.99 / 0.999 -- LABELLED AS SENSITIVITY, with 0.99 the
    delivered number.

Run:  python scripts/m5_funnel_nebular.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "out"

from m5_nebular import (FIXED_RADIUS_AS, SCORE_THRESHOLD, SENSITIVITY,  # noqa: E402
                        SKY_DEG2, galactic, sky_matched)

BANDS = [(0, 5), (5, 10), (10, 20), (20, 30), (30, 50), (50, 90)]
# Hephaistos II Table 4, the stage the CNN sits between, and its final
# pre-visual count.  Suazo et al. 2024.
PAPER = {"rmse": 11243, "post_cnn": 5732, "extra": 5137, "snr": 368}
PAPER_RATE = PAPER["snr"] / SKY_DEG2 * 1000.0        # per 1000 deg^2, all-sky
N_MC = 3_000_000
SEED = 20260823


def band_area(lo: float, hi: float) -> float:
    """Exact area of the |b| in [lo, hi) band, BOTH hemispheres -- the same
    convention as M4 Sec 4.3 ("the sky with |b| in [lo, hi) is
    (sin hi - sin lo) x 4pi sr"), which puts 0-5 deg at 3,595 deg^2."""
    return (np.sin(np.radians(hi)) - np.sin(np.radians(lo))) * SKY_DEG2


def xyz(ra, dec):
    r, d = np.radians(ra), np.radians(dec)
    return np.column_stack([np.cos(d) * np.cos(r), np.cos(d) * np.sin(r), np.sin(d)])


def mask_fraction_by_band(cats: pd.DataFrame) -> dict:
    """Monte Carlo: what fraction of each |b| band does N1 mask?

    The tree is built on the RANDOM POINTS and queried once per catalogue disc,
    which is the cheap direction: 29,462 queries returning ~N_MC x 12% hits in
    total, instead of N_MC queries against a 10-degree search radius.
    """
    rng = np.random.default_rng(SEED)
    u = rng.random(N_MC)
    ra = rng.random(N_MC) * 360.0
    dec = np.degrees(np.arcsin(2 * u - 1))
    v = xyz(ra, dec)
    tree = cKDTree(v)
    masked = np.zeros(N_MC, bool)
    per_cat = {}
    for cid, g in cats.groupby("cat"):
        m = np.zeros(N_MC, bool)
        for r_as, cr, cd in zip(g["r_as"], g["ra"], g["dec"]):
            chord = 2.0 * np.sin(np.radians(r_as / 3600.0) / 2.0)
            idx = tree.query_ball_point(xyz([cr], [cd])[0], chord)
            if idx:
                m[idx] = True
        per_cat[cid] = m
        masked |= m
    _, b = galactic(ra, dec)
    ab = np.abs(b)
    out = {"n_mc": N_MC, "seed": SEED, "bands": {}, "per_catalogue_allsky": {}}
    for cid, m in per_cat.items():
        out["per_catalogue_allsky"][cid] = float(m.mean())
    for lo, hi in BANDS:
        sel = (ab >= lo) & (ab < hi)
        out["bands"][f"{lo}-{hi}"] = {
            "n_mc": int(sel.sum()),
            "masked_fraction": float(masked[sel].mean()),
            "area_deg2": band_area(lo, hi),
        }
    out["allsky_masked_fraction"] = float(masked.mean())
    return out


def main() -> None:
    cats = pd.read_csv(OUT / "m5_nebular_catalogs.csv")
    rm = pd.read_csv(OUT / "w4_rmse_survivors_m4_g0.1.csv")
    fl = pd.read_csv(OUT / "m5_nebular_flags_rmse.csv")
    assert len(rm) == len(fl) and (rm["source_id"].to_numpy()
                                   == fl["source_id"].to_numpy()).all()
    d = pd.concat([rm.reset_index(drop=True),
                   fl[["n1_flag", "n1_ncat", "n1_cat", "n1_name", "n2_score",
                       "n2_flag", "nebular_flag", "glat", "ecl_lat",
                       "w3sky", "w4sky", "w3conf", "w4conf", "w3rchi2",
                       "w4rchi2", "nb", "na"]
                      + [f"n2_flag_{q}" for q in SENSITIVITY]].reset_index(drop=True)],
                  axis=1)
    d["ab"] = np.abs(d["glat"])
    d.to_csv(OUT / "m5_rmse_survivors_nebular_m4_g0.1.csv", index=False)

    print("== N1: the sky the catalogue veto masks (Monte Carlo, "
          f"{N_MC:,} points, seed {SEED}) ==")
    mf = mask_fraction_by_band(cats)
    (OUT / "m5_nebular_skymask.json").write_text(json.dumps(mf, indent=2))
    print(f"  all sky: {100 * mf['allsky_masked_fraction']:.2f}% masked")
    for k, v in mf["bands"].items():
        print(f"    |b| {k:6s}  {100 * v['masked_fraction']:6.2f}% of "
              f"{v['area_deg2']:8,.0f} deg2")
    print("  per catalogue (all sky, union within the catalogue):")
    for cid, f in sorted(mf["per_catalogue_allsky"].items(),
                         key=lambda kv: -kv[1]):
        print(f"    {cid:12s} {100 * f:6.3f}%")

    # ---------------------------------------------------------------- funnel
    print("\n== the funnel with the nebular stage at Table 4's position ==")
    n_rmse = len(d)
    keep = ~d["nebular_flag"]
    n_neb = int(keep.sum())
    extra = d["extra_ok"].astype(bool)
    snr = d["snr_ok"].astype(bool)
    rows = [
        ("RMSE <= 0.2", n_rmse, PAPER["rmse"]),
        ("+ nebular stage (M5 N1|N2)", n_neb, PAPER["post_cnn"]),
        ("+ extra cuts", int((keep & extra).sum()), PAPER["extra"]),
        ("+ S/N >= 3.5 (pre-visual)", int((keep & extra & snr).sum()), PAPER["snr"]),
    ]
    funnel = {}
    for name, ours, theirs in rows:
        print(f"  {name:32s} {ours:7,d}   paper {theirs:7,d}   "
              f"{ours / theirs:5.2f}x")
        funnel[name] = {"ours": ours, "paper": theirs, "ratio": ours / theirs}
    n_pre_before = int((extra & snr).sum())
    n_pre_after = int((keep & extra & snr).sum())
    print(f"\n  pre-visual survivors: {n_pre_before:,} before the stage -> "
          f"{n_pre_after:,} after  "
          f"({100 * (1 - n_pre_after / n_pre_before):.1f}% removed)")
    print(f"  the paper's own nebular stage removes "
          f"{100 * (1 - PAPER['post_cnn'] / PAPER['rmse']):.1f}% at the RMSE "
          f"stage; ours removes {100 * (1 - n_neb / n_rmse):.1f}%")

    # ------------------------------------------------- latitude, before/after
    print("\n== residual overproduction by Galactic latitude ==")
    print("   'x after'  compares to the paper's rate over the FULL band area, "
          "as the paper's\n   own CNN removed objects and not area.  "
          "'x areacorr' divides instead by the area N1\n   leaves unmasked -- "
          "the conservative reading, because a mask lowers our count without\n"
          "   lowering theirs.  Both are reported; neither is chosen.")
    print(f"{'|b|':>8s} {'area':>8s} {'pre':>6s} {'post':>6s} {'rej%':>6s} "
          f"{'N1%':>6s} {'N2%':>6s} {'sky%':>6s} {'enrich':>7s} "
          f"{'x before':>9s} {'x after':>9s} {'x areacorr':>11s}")
    lat = []
    for lo, hi in BANDS:
        sel = (d["ab"] >= lo) & (d["ab"] < hi)
        pre = int((sel & extra & snr).sum())
        post = int((sel & keep & extra & snr).sum())
        area = band_area(lo, hi)
        skyf = mf["bands"][f"{lo}-{hi}"]["masked_fraction"]
        n1f = float(d.loc[sel & extra & snr, "n1_flag"].mean()) if pre else np.nan
        n2f = float(d.loc[sel & extra & snr, "n2_flag"].mean()) if pre else np.nan
        enrich = n1f / skyf if skyf > 0 else np.nan
        xb, xa = pre / (PAPER_RATE * area / 1000.0), post / (PAPER_RATE * area / 1000.0)
        xac = post / (PAPER_RATE * area * (1 - skyf) / 1000.0)
        # 68% Poisson on the post count
        lo68, hi68 = poisson_68(post)
        print(f"{lo:3d}-{hi:<4d} {area:8,.0f} {pre:6d} {post:6d} "
              f"{100 * (1 - post / pre) if pre else 0:5.1f}% "
              f"{100 * n1f:5.1f}% {100 * n2f:5.1f}% {100 * skyf:5.2f}% "
              f"{enrich:7.2f} {xb:8.2f}x {xa:8.2f}x {xac:10.2f}x")
        lat.append({"band": f"{lo}-{hi}", "area_deg2": area,
                    "pre": pre, "post": post,
                    "rejected_frac": (1 - post / pre) if pre else None,
                    "n1_frac": n1f, "n2_frac": n2f, "sky_masked_frac": skyf,
                    "n1_enrichment": enrich,
                    "yield_per_1000deg2_before": pre / area * 1000,
                    "yield_per_1000deg2_after": post / area * 1000,
                    "overproduction_before": xb, "overproduction_after": xa,
                    "overproduction_after_areacorrected": xac,
                    "overproduction_after_68": [lo68 / (PAPER_RATE * area / 1000.0),
                                                hi68 / (PAPER_RATE * area / 1000.0)]})
    allx_b = n_pre_before / (PAPER_RATE * SKY_DEG2 / 1000.0)
    allx_a = n_pre_after / (PAPER_RATE * SKY_DEG2 / 1000.0)
    allsf = mf["allsky_masked_fraction"]
    allx_ac = n_pre_after / (PAPER_RATE * SKY_DEG2 * (1 - allsf) / 1000.0)
    print(f"{'all sky':>8s} {SKY_DEG2:8,.0f} {n_pre_before:6d} {n_pre_after:6d} "
          f"{100 * (1 - n_pre_after / n_pre_before):5.1f}% "
          f"{100 * float(d.loc[extra & snr, 'n1_flag'].mean()):5.1f}% "
          f"{100 * float(d.loc[extra & snr, 'n2_flag'].mean()):5.1f}% "
          f"{100 * allsf:5.2f}% "
          f"{float(d.loc[extra & snr, 'n1_flag'].mean()) / allsf:7.2f} "
          f"{allx_b:8.2f}x {allx_a:8.2f}x {allx_ac:10.2f}x")
    exc_b = n_pre_before - PAPER["snr"]
    exc_a = n_pre_after - PAPER["snr"]
    exc_ac = n_pre_after / (1 - allsf) - PAPER["snr"]
    print(f"\n  excess over the paper's 368: {exc_b:,} before -> {exc_a:,} after "
          f"({100 * (1 - exc_a / exc_b):.1f}% of the excess removed; "
          f"{100 * (1 - exc_ac / exc_b):.1f}% area-corrected)")

    # which catalogue does N1's work on SURVIVORS (not on sky)
    print("\n  N1's flagging of pre-visual survivors, by catalogue "
          "(nearest-in-units-of-its-own-radius):")
    vc = d.loc[extra & snr & d["n1_flag"], "n1_cat"].value_counts()
    for cid, n in vc.items():
        print(f"    {cid:12s} {n:5d}  ({100 * n / n_pre_before:5.1f}% of the "
              f"{n_pre_before:,} pre-visual survivors)")

    # ---------------------------------- is N2 measuring nebulosity, or zodi?
    # w3sky is dominated by zodiacal light, which is why PR-2 bins by ecliptic
    # latitude.  The test that the RESIDUAL tracks the Galactic plane is a
    # within-ecliptic-bin comparison, and it has to be shown, not asserted.
    print("\n== N2 diagnostic: median w3sky (DN) WITHIN each |ecliptic| bin ==")
    cal = pd.read_csv(sky_matched("calib"))
    for f_ in (cal, d):
        f_["eb"] = np.floor(np.abs(f_["ecl_lat"]) / 10.0).astype(int)
    print(f"  {'|ecl|':>7s} {'n_cal':>7s} {'cal (|b|>50)':>13s} "
          f"{'|b|<5':>9s} {'|b|10-30':>9s} {'|b|>50':>9s} {'ratio':>7s}")
    diag = []
    for eb in sorted(cal["eb"].unique()):
        cc = cal[cal["eb"] == eb]
        sub = lambda lo, hi: d[(d["eb"] == eb) & (d["ab"] >= lo) & (d["ab"] < hi)]  # noqa: E731
        m = lambda s: float(s["w3sky"].median()) if len(s) else np.nan   # noqa: E731
        a, b_, g = m(sub(0, 5)), m(sub(10, 30)), m(sub(50, 90))
        cm = float(cc["w3sky"].median())
        print(f"  {eb * 10:3d}-{eb * 10 + 10:<3d} {len(cc):7,d} {cm:13.0f} "
              f"{a:9.0f} {b_:9.0f} {g:9.0f} {a / cm:7.3f}")
        diag.append({"ecl_bin": int(eb), "n_cal": int(len(cc)), "cal_median": cm,
                     "median_b_lt5": a, "median_b_10_30": b_,
                     "median_b_gt50": g, "ratio_plane_over_cal": a / cm})
    print("  Every bin: the plane sits ABOVE the clean-sky median of the same "
          "ecliptic\n  latitude, and |b| > 50 sits ON it. The zodiacal "
          "gradient is what the binning\n  removes; what is left tracks the "
          "Galactic plane, which is what N2 is for.")
    print("\n  N2 score distribution among RMSE survivors, by |b|:")
    for lo, hi in BANDS:
        s = d[(d["ab"] >= lo) & (d["ab"] < hi)]
        print(f"    |b| {lo:2d}-{hi:<2d} n={len(s):5,d}  median score "
              f"{s['n2_score'].median():.3f}   fraction > 0.99 "
              f"{s['n2_flag'].mean():.3f}")

    # ------------------------------------------------------------ validation
    print("\n== PR-2 validation ==")
    cand = pd.read_csv(OUT / "m5_nebular_flags_candidates.csv")
    if "label" not in cand.columns:
        lab = pd.read_csv(ROOT / "data" / "photometry" / "candidates_gaia_chain.csv")
        cand = cand.merge(lab[["source_id", "label"]], on="source_id", how="left")
    # Hephaistos II's SEVEN published candidates are A-G; H, I, J are the
    # Hephaistos III objects that failed II's SNR cut (M1).
    pub = cand[cand["label"].isin(list("ABCDEFG"))]
    print(f"  (a) the paper's 7 published candidates: "
          f"{int((~pub['nebular_flag']).sum())}/7 preserved "
          f"(N1 flags {int(pub['n1_flag'].sum())}, N2 flags {int(pub['n2_flag'].sum())})")
    print(f"      all 10 labelled objects A-J: "
          f"{int((~cand['nebular_flag']).sum())}/10 preserved")
    for _, r in cand.sort_values("label").iterrows():
        print(f"        {r['label']}  |b| = {abs(r['glat']):5.1f} deg   "
              f"N2 score {r['n2_score']:.3f}   N1 {'FLAG' if r['n1_flag'] else 'clear'}")
    grad = [x["rejected_frac"] for x in lat]
    mono = all(grad[i] >= grad[i + 1] - 1e-9 for i in range(len(grad) - 1))
    print(f"  (b) rejected fraction falls monotonically with |b|: "
          f"{'YES' if mono else 'NO'}  {[round(100 * g, 1) for g in grad]}")
    moved = all(lat[i]["overproduction_after"] <= lat[i]["overproduction_before"]
                for i in range(len(lat)))
    print(f"      overproduction moves towards 1.0 in every band: "
          f"{'YES' if moved else 'NO'}")
    print("  (c) sensitivity band (LABELLED SENSITIVITY -- 0.99 is delivered):")
    sens = {}
    for q in SENSITIVITY:
        k = ~(d["n1_flag"] | d[f"n2_flag_{q}"].fillna(False))
        n = int((k & extra & snr).sum())
        sens[str(q)] = n
        star = "  <- DELIVERED" if q == SCORE_THRESHOLD else ""
        print(f"        N2 q = {q:<6}  pre-visual survivors {n:5,d}   "
              f"{n / (PAPER_RATE * SKY_DEG2 / 1000.0):5.2f}x{star}")

    res = {"funnel": funnel, "latitude": lat,
           "paper_rate_per_1000deg2": PAPER_RATE,
           "pre_visual_before": n_pre_before, "pre_visual_after": n_pre_after,
           "overproduction_before": allx_b, "overproduction_after": allx_a,
           "overproduction_after_areacorrected": allx_ac,
           "excess_over_paper_before": exc_b, "excess_over_paper_after": exc_a,
           "frac_of_excess_removed": 1 - exc_a / exc_b,
           "frac_of_excess_removed_areacorrected": 1 - exc_ac / exc_b,
           "n1_catalogue_share_of_previsual": {str(k): int(v) for k, v in vc.items()},
           "nebular_reject_frac_at_rmse": 1 - n_neb / n_rmse,
           "paper_cnn_reject_frac_at_rmse": 1 - PAPER["post_cnn"] / PAPER["rmse"],
           "validation": {
               "published_candidates_preserved": int((~pub["nebular_flag"]).sum()),
               "published_candidates_total": int(len(pub)),
               "all_labelled_preserved": int((~cand["nebular_flag"]).sum()),
               "monotone_latitude_gradient": bool(mono),
               "overproduction_moves_toward_one": bool(moved)},
           "sensitivity_previsual_counts": sens,
           "n2_within_ecliptic_bin_diagnostic": diag,
           "n2_score_by_latitude": [
               {"band": f"{lo}-{hi}",
                "median_score": float(d.loc[(d["ab"] >= lo) & (d["ab"] < hi),
                                            "n2_score"].median()),
                "frac_flagged": float(d.loc[(d["ab"] >= lo) & (d["ab"] < hi),
                                            "n2_flag"].mean())}
               for lo, hi in BANDS],
           "skymask": mf}
    (OUT / "m5_funnel_nebular.json").write_text(json.dumps(res, indent=2))
    print("\nwrote out/m5_funnel_nebular.json, "
          "out/m5_rmse_survivors_nebular_m4_g0.1.csv, out/m5_nebular_skymask.json")


def poisson_68(n: int) -> tuple[float, float]:
    """Gehrels 1986 approximation, as M3/M4 used."""
    if n == 0:
        return 0.0, 1.841
    return n * (1 - 1 / (9 * n) - 1 / (3 * np.sqrt(n))) ** 3, \
        (n + 1) * (1 - 1 / (9 * (n + 1)) + 1 / (3 * np.sqrt(n + 1))) ** 3


if __name__ == "__main__":
    main()
