#!/usr/bin/env python
"""M8 task 3: a SYNTHETIC verdict store at December scale.

M7's own lesson was that three pre-registered commands did not run until
somebody ran them.  The rest of the pre-registration has still never been
executed, because executing it needs verdicts that do not exist.  This
manufactures them -- under a DECLARED null and a DECLARED effect, at the
sample sizes December is projected to deliver -- so that every pre-registered
analysis path can be run end to end while finding a broken rule is still
free.

WHERE IT WRITES, AND WHY THAT MATTERS.  Never into out/verdicts/.  The
pre-registered December command is `--verdicts all`, and `all` means "every
CSV in out/verdicts/"; a synthetic file dropped there would silently join
December's real analysis.  Everything here goes to
out/verdicts_synth/<scenario>/, which `load_store` expands by exactly the
same directory code path as `all` -- so the rehearsal exercises the real
expansion logic without ever putting a fabricated verdict where a real one
lives.

THE GENERATIVE MODEL, DECLARED IN ADVANCE (this is the whole point; a
synthetic store whose truth is chosen after seeing the p-value tests
nothing):

  population   the 981 real day-one queue members.  Real source_ids, so the
               joins to the triage frame, the DR3 activity columns and the
               eROSITA footprint all behave exactly as they will in
               December.  Fabricated ids would make every test read NOT
               TESTABLE for the wrong reason.

  null         verdict is independent of every metric.  P(SPURIOUS) fixed by
               the scenario's ratio, assignment by a seeded permutation.

  effect       verdict is tilted on ONE declared driver metric to a declared
               target effect size, which is the effect the pre-registration
               names for that test:
                 D1  in-footprint X-ray detection rate 0.154 (spurious) vs
                     0.000 (confirmed) -- constructed exactly, by drawing
                     the spurious group's detected members first
                 D2  AUC(spurious > confirmed) on dAmp_G = 0.659
                 D3  AUC(spurious > confirmed) on astrometric_gof_al = 0.344
                 D4  flag_astrom_quiet marking rate 0.30 (spurious) vs
                     0.075 (confirmed)
               A numeric target AUC is hit by a logistic tilt on the
               driver's normalised rank, with the slope found by bisection
               until the REALISED AUC matches the target to 0.002.  The
               realised value is recorded in the scenario manifest, so the
               store's truth is a measured number and not an intention.

  reversal     the same tilt with the sign of the slope flipped: a
               significant effect OPPOSITE to the pre-registered direction,
               which is the only way to exercise DIRECTION REVERSAL.

  thin         5 confirmed + 4 spurious: the NOT TESTABLE arm.

  no_coverage  full sample size, but every driver value blanked -- the OTHER
               NOT TESTABLE arm (zero rows survive the join), which is what
               M5 family A actually returned for activityindex_espcs.

  ratios       three, exactly the three the pre-registration's power table
               uses: 1:1 (490+490), the EB26 split 1.83:1 (633+347), and the
               M6 pre-release harness split 0.33:1 (245+735).

Every record is a schema-valid day1_verdict.v1 record with
verdict_source='epoch_vet_harness', verdict_scope='orbit_reality',
verdict_basis='epoch_astrometry_f2', and a run_id that names the scenario
and the seed, so a synthetic record can never be mistaken for a real one.

Run:
  .venv/Scripts/python.exe scripts/m8_synthetic_store.py --build-all
"""
import argparse
import json
import os
import shutil
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import verdict_schema as vs                                      # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")
DATA = os.path.join(BASE, "data")
SYNTH_DIR = os.path.join(OUT, "verdicts_synth")
QUEUE = os.path.join(OUT, "epoch_vet_day1_queue.v2.csv")
ACT = os.path.join(DATA, "dr3_activity_columns.parquet")

SEED = 20261202
RATIOS = {"eb26": (633, 347), "even": (490, 490), "harness": (245, 735)}

SYNTH_SOURCE = "epoch_vet_harness"
SYNTH_SCOPE = "orbit_reality"


# ======================================================================
def _amp_proxy(n_obs, foe):
    """M5's Belokurov+2017 eq. 2 amplitude proxy, imported rather than
    re-derived so the driver is the metric the test will actually use."""
    import m5_activity_discriminator as M5
    return M5.amp_proxy(n_obs, foe)


def driver_frame():
    """The real metric values the tilt is applied to."""
    q = pd.read_csv(QUEUE)
    q["source_id"] = q["source_id"].astype("int64")
    act = pd.read_parquet(ACT)
    act["source_id"] = act["source_id"].astype("int64")
    d = q.merge(act, on="source_id", how="left", suffixes=("", "_act"))
    assert len(d) == len(q), f"join fanned out: {len(d)} vs {len(q)}"
    tri = pd.read_parquet(os.path.join(DATA, "dr3_amrf_triage.parquet"),
                          columns=["source_id", "nss_solution_type", "l",
                                   "b"]).drop_duplicates("source_id")
    tri["source_id"] = tri["source_id"].astype("int64")
    d = d.merge(tri[["source_id", "l", "b"]], on="source_id", how="left")
    assert len(d) == len(q), f"triage join fanned out: {len(d)} vs {len(q)}"
    d["amp_g"] = _amp_proxy(d["phot_g_n_obs"], d["phot_g_mean_flux_over_error"])
    import m5_activity_discriminator as M5
    base = M5.rolling_median_baseline(
        d["phot_g_mean_mag_act"].values, d["amp_g"].values,
        d["phot_g_mean_mag_act"].values)
    d["damp_g"] = d["amp_g"].values - base
    return d


def _no_coverage_frame(seed, n_max=588):
    """Class-III sources that have NO row in the activity pull: the genuine
    zero-coverage population.  Real ids, real orbits, present in the triage
    frame; nothing M5 measures exists for them."""
    act = pd.read_parquet(ACT, columns=["source_id"])
    tri = pd.read_parquet(
        os.path.join(DATA, "dr3_amrf_triage.parquet"),
        columns=["source_id", "nss_solution_type", "period", "significance",
                 "class_det", "l", "b"])
    tri["source_id"] = tri["source_id"].astype("int64")
    c3 = tri[tri["class_det"] == 3].drop_duplicates("source_id")
    out = c3[~c3["source_id"].isin(act["source_id"].astype("int64"))]
    out = out.sample(n=min(n_max, len(out)), random_state=seed).copy()
    out = out.reset_index(drop=True)
    for c, v in [("queue_bin", "not_in_queue"), ("rank", -1),
                 ("flag_alias_1yr", False), ("flag_low_lat", False),
                 ("flag_hi_sigma_ti2", False), ("flag_xray_active", False),
                 ("flag_dust_unresolved_south", False),
                 ("flag_dust_sigma_fragile", False),
                 ("flag_astrom_quiet", False), ("damp_g", np.nan),
                 ("astrometric_gof_al", np.nan)]:
        out[c] = v
    return out


DRIVERS = {
    "D1": ("flag_xray_active", "rate", (0.154, 0.000)),
    "D2": ("damp_g", "auc", 0.659),
    "D3": ("astrometric_gof_al", "auc", 0.344),
    "D4": ("flag_astrom_quiet", "rate", (0.30, 0.075)),
}


def _auc(x_conf, x_spur):
    from scipy.stats import mannwhitneyu
    x_conf = np.asarray(x_conf, float)
    x_spur = np.asarray(x_spur, float)
    x_conf = x_conf[np.isfinite(x_conf)]
    x_spur = x_spur[np.isfinite(x_spur)]
    if not len(x_conf) or not len(x_spur):
        return np.nan
    u = mannwhitneyu(x_spur, x_conf, alternative="two-sided").statistic
    return float(u / (len(x_conf) * len(x_spur)))


def tilt_auc(values, n_conf, n_spur, target_auc, rng, tol=0.002,
             iters=60):
    """Choose which rows are SPURIOUS so the realised AUC(spur>conf) hits
    `target_auc`.  Logistic tilt on the normalised rank; bisection on the
    slope.  Rows with a missing driver value are assigned last, at random,
    so they cannot bias the AUC."""
    v = np.asarray(values, float)
    n = len(v)
    ok = np.isfinite(v)
    r = np.full(n, np.nan)
    r[ok] = (pd.Series(v[ok]).rank(pct=True).values - 0.5)

    def realise(beta):
        w = np.zeros(n)
        w[ok] = 1.0 / (1.0 + np.exp(-beta * r[ok]))
        w[~ok] = 0.5
        w = w / w.sum()
        spur_idx = rng.choice(n, size=n_spur, replace=False, p=w)
        mask = np.zeros(n, bool)
        mask[spur_idx] = True
        return mask, _auc(v[~mask], v[mask])

    lo, hi = -40.0, 40.0
    best = None
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        mask, a = realise(mid)
        if best is None or abs(a - target_auc) < abs(best[1] - target_auc):
            best = (mask, a, mid)
        if not np.isfinite(a):
            break
        if abs(a - target_auc) <= tol:
            return mask, a, mid
        if a < target_auc:
            lo = mid
        else:
            hi = mid
    return best


def tilt_rate(flags, n_conf, n_spur, p_spur, p_conf, rng, eligible=None):
    """SUBSAMPLE the population so the marked FRACTION is p_spur among
    spurious and p_conf among confirmed, exactly.

    The first attempt partitioned all N rows and could not work: whatever is
    not chosen as spurious becomes confirmed, so the confirmed group inherits
    every marked row the spurious group did not take and its rate is set by
    arithmetic rather than by the target (D4 came out at 0.2385 against a
    target of 0.075).  The fix is to CHOOSE both groups from the pool and
    drop the remainder, shrinking the sample to whatever the marked pool can
    support.  The realised size is recorded, because a rehearsal that
    quietly changes n is a rehearsal of the wrong experiment.

    `eligible` is the sub-population the RATE IS MEASURED ON -- for D1 the
    eROSITA-DE footprint, which is only ~half the sky.  Rows outside it are
    added afterwards at the same conf:spur ratio: they belong in the store
    (December's will contain them) and they cannot move the in-footprint
    rate.
    """
    f = np.asarray(flags).astype(bool)
    n = len(f)
    elig = np.ones(n, bool) if eligible is None else np.asarray(eligible,
                                                                bool)
    marked = np.where(f & elig)[0]
    unmarked = np.where((~f) & elig)[0]
    other = np.where(~elig)[0]
    rho = n_spur / float(n_conf + n_spur)
    frac_marked = rho * p_spur + (1.0 - rho) * p_conf
    frac_unmarked = 1.0 - frac_marked
    cap = [n_conf + n_spur]
    if frac_marked > 0:
        cap.append(len(marked) / frac_marked)
    if frac_unmarked > 0:
        cap.append(len(unmarked) / frac_unmarked)
    n_e = int(np.floor(min(cap)))
    ns_e = int(round(rho * n_e))
    nc_e = n_e - ns_e
    k_s = int(round(p_spur * ns_e))
    k_c = int(round(p_conf * nc_e))
    k_s = min(k_s, len(marked))
    k_c = min(k_c, len(marked) - k_s)
    pm = list(rng.permutation(marked))
    pu = list(rng.permutation(unmarked))
    spur = pm[:k_s] + pu[:ns_e - k_s]
    conf = pm[k_s:k_s + k_c] + pu[ns_e - k_s:ns_e - k_s + nc_e - k_c]
    # top the store back up with rows the rate is not measured on
    po = list(rng.permutation(other))
    n_extra = min(len(po), (n_conf + n_spur) - (len(conf) + len(spur)))
    ns_x = int(round(rho * n_extra))
    spur += po[:ns_x]
    conf += po[ns_x:n_extra]
    spur = np.asarray(spur, int)
    conf = np.asarray(conf, int)
    realised = (float(f[spur[elig[spur]]].mean()) if elig[spur].any()
                else np.nan,
                float(f[conf[elig[conf]]].mean()) if elig[conf].any()
                else np.nan)
    return conf, spur, realised, {"n_eligible_used": int(n_e),
                                  "n_marked_pool": int(len(marked)),
                                  "n_unmarked_pool": int(len(unmarked)),
                                  "n_ineligible_added": int(n_extra)}


# ======================================================================
def build_scenario(name, test, mode, ratio="eb26", seed=SEED, verbose=True):
    """One synthetic store.  Returns (frame, manifest)."""
    rng = np.random.default_rng(seed)
    d = driver_frame()
    n_conf, n_spur = RATIOS[ratio]
    manifest = {"scenario": name, "test": test, "mode": mode,
                "ratio": ratio, "seed": seed,
                "n_conf_target": n_conf, "n_spur_target": n_spur}

    if mode == "thin":
        n_conf, n_spur = 5, 4
        manifest.update(n_conf_target=n_conf, n_spur_target=n_spur)

    col, kind, target = DRIVERS[test]

    if mode == "no_coverage":
        # FIRST ATTEMPT WAS WRONG, and it is worth recording why: it blanked
        # the driver column INSIDE THE STORE.  The store carries source_ids
        # and verdicts; M5 reads `astrometric_gof_al` from
        # data/dr3_activity_columns.parquet, so blanking a column in the
        # store changes nothing the test looks at and the scenario would
        # have quietly tested the null instead of zero coverage.
        # The honest way to manufacture zero coverage is to use sources for
        # which the metric's data GENUINELY does not exist -- which is
        # exactly M5 family A's situation with activityindex_espcs.  The 604
        # class-III sources outside the 1,199-row activity pull are that
        # population: real ids, present in the triage frame (so M4's sky
        # join works), absent from every M5 metric.
        d = _no_coverage_frame(seed)
        n_conf = int(round(len(d) * n_conf / (n_conf + n_spur)))
        n_spur = len(d) - n_conf
        manifest.update(n_conf_target=n_conf, n_spur_target=n_spur)
        mask = np.zeros(len(d), bool)
        mask[rng.choice(len(d), size=n_spur, replace=False)] = True
        manifest["realised"] = (
            f"{len(d)} class-III sources with NO row in "
            f"data/dr3_activity_columns.parquet -- the metric's data does "
            f"not exist for them")
    elif mode in ("null", "thin"):
        n_take = n_conf + n_spur
        if n_take > len(d):
            raise ValueError(f"{n_take} > {len(d)} queue rows")
        d = d.sample(n=n_take, random_state=seed).reset_index(drop=True)
        mask = np.zeros(len(d), bool)
        mask[rng.choice(len(d), size=n_spur, replace=False)] = True
        manifest["realised"] = "independent of every metric"
    elif mode in ("effect", "reversal") and kind == "auc":
        n_take = n_conf + n_spur
        d = d.sample(n=n_take, random_state=seed).reset_index(drop=True)
        tgt = target if mode == "effect" else (1.0 - target)
        mask, realised, beta = tilt_auc(d[col].values, n_conf, n_spur,
                                        tgt, rng)
        manifest.update(target_auc=tgt, realised_auc=realised,
                        tilt_beta=beta)
    elif mode in ("effect", "reversal"):
        ps, pc = target
        if mode == "reversal":
            ps, pc = pc, ps
        elig = None
        if test == "D1":
            # D1's rate is measured IN THE eROSITA-DE FOOTPRINT only
            # (179.94 < l < 359.94, M4's own definition), which is ~half the
            # sky.  Tilting on the whole queue would dilute the induced rate
            # by exactly the footprint fraction.
            import m4_eb26_erosita_test as M4
            elig = ((d["l"] > M4.L_LO) & (d["l"] < M4.L_HI)).values \
                if "l" in d.columns else None
        idx_c, idx_s, realised, info = tilt_rate(
            d[col].fillna(False).values, n_conf, n_spur, ps, pc, rng,
            eligible=elig)
        keep = np.concatenate([idx_c, idx_s])
        mask = np.concatenate([np.zeros(len(idx_c), bool),
                               np.ones(len(idx_s), bool)])
        d = d.iloc[keep].reset_index(drop=True)
        manifest.update(target_rates=[ps, pc], realised_rates=list(realised),
                        **info)
    else:
        raise ValueError(mode)

    verdict = np.where(mask, "SPURIOUS", "CONFIRMED")
    manifest["n_conf"] = int((verdict == "CONFIRMED").sum())
    manifest["n_spur"] = int((verdict == "SPURIOUS").sum())

    rec = vs.empty_frame()
    rows = []
    run_id = f"m8_synth_{name}_seed{seed}"
    for i in range(len(d)):
        f2 = float(rng.normal(12.0, 4.0)) if verdict[i] == "CONFIRMED" \
            else float(rng.normal(1.5, 1.2))
        rows.append({
            "source_id": int(d["source_id"].to_numpy(dtype="int64")[i]),
            "release": "SYNTHETIC (M8 rehearsal, not a real release)",
            "source_id_dr3": int(d["source_id"].to_numpy(dtype="int64")[i]),
            "nss_solution_type": d["nss_solution_type"].iloc[i],
            "orbit_source": "gaiadr3.nss_two_body_orbit",
            "orbit_period_d": float(d["period"].iloc[i]),
            "orbit_significance": float(d["significance"].iloc[i]),
            "orbit_a0_mas": np.nan,
            "queue_bin": d["queue_bin"].iloc[i],
            "queue_rank": int(d["rank"].iloc[i]),
            "n_transits_fetched": 60, "n_transits_used": 500,
            "f2_single_star": round(f2, 4),
            "parallax_mas": np.nan, "excess_noise_mas": np.nan,
            "fit_model": "SYNTHETIC", "fit_seconds": 0.0,
            "verdict": verdict[i], "verdict_scope": SYNTH_SCOPE,
            "verdict_basis": "epoch_astrometry_f2",
            "verdict_confidence": "HIGH" if abs(f2) >= 10 or abs(f2) <= 2.5
            else "MEDIUM",
            "verdict_confidence_basis": "synthetic",
            "flag_alias_1yr": bool(d["flag_alias_1yr"].iloc[i]),
            "flag_low_lat": bool(d["flag_low_lat"].iloc[i]),
            "flag_hi_sigma_ti2": bool(d["flag_hi_sigma_ti2"].iloc[i]),
            "flag_xray_active": bool(d["flag_xray_active"].iloc[i]),
            "flag_dust_unresolved_south":
                bool(d["flag_dust_unresolved_south"].iloc[i]),
            "flag_dust_sigma_fragile":
                bool(d["flag_dust_sigma_fragile"].iloc[i]),
            "flag_astrom_quiet": bool(d["flag_astrom_quiet"].iloc[i]),
            "schema_version": vs.SCHEMA_VERSION,
            "verdict_source": SYNTH_SOURCE,
            "verdict_source_version":
                f"M8 SYNTHETIC rehearsal store ({name}); NOT a measurement",
            "config_version": 5,
            "epoch_data_release": "SYNTHETIC",
            "epoch_data_structure": "SYNTHETIC",
            "gaiasupdate_version": "SYNTHETIC",
            "produced_utc": vs.utcnow(), "run_id": run_id,
            "notes": f"synthetic {mode} store, scenario {name}",
        })
    rec = pd.concat([rec, pd.DataFrame(rows)], ignore_index=True)
    rec = vs.coerce(rec)
    vs.validate(rec)
    return rec, manifest


SCENARIOS = [
    # name,               test, mode,          ratio
    ("null_eb26",         "D2", "null",        "eb26"),
    ("null_even",         "D2", "null",        "even"),
    ("null_harness",      "D2", "null",        "harness"),
    ("d1_effect",         "D1", "effect",      "eb26"),
    ("d2_effect",         "D2", "effect",      "eb26"),
    ("d3_effect",         "D3", "effect",      "eb26"),
    ("d4_effect",         "D4", "effect",      "eb26"),
    ("d3_reversal",       "D3", "reversal",    "eb26"),
    ("d2_reversal",       "D2", "reversal",    "eb26"),
    ("thin",              "D2", "thin",        "eb26"),
    ("no_coverage",       "D3", "no_coverage", "eb26"),
]


def build_all(force=False, verbose=True):
    os.makedirs(SYNTH_DIR, exist_ok=True)
    manifests = []
    for name, test, mode, ratio in SCENARIOS:
        sd = os.path.join(SYNTH_DIR, name)
        if os.path.isdir(sd) and force:
            shutil.rmtree(sd)
        os.makedirs(sd, exist_ok=True)
        if mode == "thin":
            rec, man = build_scenario(name, test, "thin", ratio)
        else:
            rec, man = build_scenario(name, test, mode, ratio)
        p = os.path.join(sd, "harness_synth.v1.csv")
        vs.write_store(rec, p, verbose=False)
        # the pooled arm needs the real EB26 file alongside it, and the
        # pre-registered command reads a DIRECTORY, so a copy lives here.
        shutil.copyfile(os.path.join(vs.STORE_DIR, "eb26.v1.csv"),
                        os.path.join(sd, "eb26.v1.csv"))
        man["path"] = os.path.relpath(p, BASE)
        man["dir"] = os.path.relpath(sd, BASE)
        manifests.append(man)
        if verbose:
            extra = ""
            if "realised_auc" in man:
                extra = (f"  target AUC {man['target_auc']:.3f} -> realised "
                         f"{man['realised_auc']:.4f}")
            elif "realised_rates" in man:
                extra = (f"  target rates {man['target_rates']} -> realised "
                         f"({man['realised_rates'][0]:.4f}, "
                         f"{man['realised_rates'][1]:.4f})")
            print(f"  {name:<14s} {mode:<12s} {man['n_conf']:>4d} conf / "
                  f"{man['n_spur']:>4d} spur{extra}")
    with open(os.path.join(SYNTH_DIR, "MANIFEST.json"), "w",
              newline="\n") as fh:
        json.dump({"seed": SEED, "scenarios": manifests,
                   "produced_utc": vs.utcnow(),
                   "warning": "SYNTHETIC verdicts. Never copy into "
                              "out/verdicts/ -- the December command "
                              "`--verdicts all` reads that directory."},
                  fh, indent=2)
    print(f"\nwrote {len(manifests)} scenarios to "
          f"{os.path.relpath(SYNTH_DIR, BASE)}")
    return manifests


def axis_correlation(out_path=None):
    """Are D1 and D2 independent axes?  The pre-registration corrects with
    Holm WITHIN each family and explicitly NOT across families, on the stated
    ground that "the families ask different questions of different data".
    That premise is testable on the queue itself, with no verdicts involved,
    and it is worth testing before December rather than after two families
    come back positive and get reported as two findings.
    """
    from scipy.stats import mannwhitneyu
    import m4_eb26_erosita_test as M4
    d = driver_frame()
    foot = (d["l"] > M4.L_LO) & (d["l"] < M4.L_HI)
    sub = d[foot]
    xs = sub["flag_xray_active"].fillna(False).astype(bool)
    lines = ["M8 -- ARE THE DISCRIMINATOR AXES INDEPENDENT?",
             "measured on the 981-row day-one queue itself; NO verdicts "
             "involved, so this",
             "is a property of the data and not of any test.",
             f"in the eROSITA-DE footprint: {len(sub)} queue rows, "
             f"{int(xs.sum())} X-ray detected", ""]
    for col, fam in [("damp_g", "D2 primary metric (dAmp_G)"),
                     ("astrometric_gof_al", "D3 primary metric")]:
        a_ = sub.loc[xs, col].dropna()
        b_ = sub.loc[~xs, col].dropna()
        if len(a_) < 3 or len(b_) < 3:
            lines.append(f"  {fam}: too few")
            continue
        u = mannwhitneyu(a_, b_, alternative="two-sided")
        auc = u.statistic / (len(a_) * len(b_))
        lines.append(f"  {fam:<34s} AUC(X-ray detected > not) = {auc:.3f}"
                     f"   p = {u.pvalue:.2e}   n = {len(a_)} vs {len(b_)}")
    lines += [
        "",
        "READING: D1 (X-ray) and D2 (photometric variability) are STRONGLY",
        "correlated on this sample -- both are activity proxies, and that is",
        "astrophysically expected.  D3 (astrometric quality) is not.",
        "CONSEQUENCE for December: if D1 and D2 both come back POSITIVE that",
        "is ONE finding reported twice, not two independent confirmations.",
        "The pre-registration's 'no correction across families' is still the",
        "right rule for keeping December's p-values comparable with the frozen",
        "ones -- but the INTERPRETATION must say the axes are not independent.",
        "Proposed as a declared variant for Matthew; not applied here.",
    ]
    txt = "\n".join(lines) + "\n"
    out_path = out_path or os.path.join(OUT, "m8_axis_correlation.txt")
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)
    return txt


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--build-all", action="store_true")
    ap.add_argument("--axis-correlation", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    if a.build_all:
        build_all(force=a.force)
    if a.axis_correlation:
        axis_correlation()
    if a.build_all or a.axis_correlation:
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
