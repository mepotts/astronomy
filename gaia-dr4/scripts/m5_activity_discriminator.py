#!/usr/bin/env python
"""M5 task 1: the activity axis WITHOUT the footprint penalty.

M4 asked whether magnetic activity discriminates EB26-confirmed compact
companions from EB26-spurious astrometric solutions, and could only answer
it on the 29 of 65 verdicted targets that fall inside eROSITA-DE's half of
the sky.  Result: direction consistent (2/13 spurious vs 0/16 confirmed
detected), Fisher p = 0.19, UNDERPOWERED -- only a spurious detection rate
>= 0.40 was reachable at 80 % power.

Gaia's own indicators cover ALL 76.  This script re-asks the question with
no footprint penalty at all.

=======================================================================
PRE-REGISTERED DESIGN  (written and committed to file before any
confirmed-vs-spurious split was computed or inspected)
=======================================================================

SAMPLE.  The 76 El-Badry+2026 followed-up astrometric candidates
(fixtures/elbadry2026_astrometric_candidates.csv): 42 CONFIRMED,
23 SPURIOUS, 1 MARGINAL, 2 NOT_CO, 1 OTHER, 7 UNKNOWN.  The primary
comparison is CONFIRMED (42) vs SPURIOUS (23).  The other 11 verdicts are
reported but never enter a test.

THREE FAMILIES, kept separate in the analysis (they measure different
things and family C is not activity at all):

  A -- CHROMOSPHERIC ACTIVITY (Gaia DR3 ESP-CS)
       A1  activityindex_espcs  [gaiadr3.astrophysical_parameters; the
           Ca II IRT chromospheric activity index, DR3 unit nm]
       Coverage is reported FIRST and honestly: ESP-CS runs only on
       RVS-processed sources in its Teff range, so this axis is expected to
       be sparse.  If either side has < 5 finite values the metric is
       declared NOT TESTABLE (not "null").

  B -- PHOTOMETRIC VARIABILITY (available for every source)
       B1  dAmp_G  -- magnitude-detrended photometric variability amplitude
           proxy.  Amp is Belokurov et al. 2017 (MNRAS 466, 4711) eq. 2,
           source arXiv:1611.04614 clouds_and_bridges.tex lines 490-497:
               Amp = log10( sqrt(N_obs) * sigma_Ibar_G / Ibar_G )
           "N_obs is the number of CCD crossings, sigma_Ibar_G is the mean
           G flux error and Ibar_G is the mean G-band flux".
           In DR3 columns: Amp_G = log10(sqrt(phot_g_n_obs) /
           phot_g_mean_flux_over_error).  Belokurov et al. 2020 (MNRAS 496,
           1922; arXiv:2003.05467 ruwe.tex line 800) use the same estimator
           on DR2 and report it "nicely correlates with the peak-to-peak
           light curve amplitude measured by Gaia".
           Amp is strongly magnitude-dependent, so the PRIMARY metric is
           the detrended residual dAmp_G = Amp_G - median(Amp_G | G),
           the baseline being a rolling median over the 1,199-source
           NSS-candidate population pulled alongside (window +-0.75 mag,
           >= 25 stars, else the nearest valid window).  Raw Amp_G is
           reported next to it.
       B2  dAmp_BP        (same construction, phot_bp_*)
       B3  dAmp_RP        (same construction, phot_rp_*)
       B4  phot_variable_flag == 'VARIABLE'   [binary]
       B5  std_dev_mag_g_fov  [gaiadr3.vari_summary, where present]

  C -- ASTROMETRIC / IMAGING QUALITY (NOT activity -- kept separate on
       purpose; these are "was the astrometry clean" indicators)
       C1  ruwe
       C2  ipd_frac_multi_peak
       C3  ipd_gof_harmonic_amplitude
       C4  astrometric_excess_noise_sig
       C5  astrometric_gof_al
       C6  phot_bp_rp_excess_factor

  NEGATIVE CONTROL (outside all families, must NOT discriminate):
       N1  phot_g_n_obs -- scan-law geometry, nothing to do with whether an
           orbit solution is right.  It is a diagnostic on the machinery,
           not a hypothesis, so its threshold is set apart from the
           families and BEFORE the run: N1 at p < 0.01 VOIDS the run (the
           pipeline is manufacturing signal and nothing may be frozen);
           0.01 <= p < 0.05 is reported as a caveat, since a single
           two-sided test is expected to trip at 5 % by construction.

TEST RULES.
  continuous metric : Mann-Whitney U, two-sided, CONFIRMED vs SPURIOUS;
                      requires >= 5 finite values per side, else NOT
                      TESTABLE.  Effect size = AUC (P[spurious > confirmed])
                      and the rank-biserial r_rb = 2*AUC - 1, with a
                      95 % bootstrap CI (10,000 resamples, seed 20261202).
  binary metric     : Fisher exact two-sided + Wilson 95 % CIs; effect size
                      = odds ratio.
  multiplicity      : Holm-Bonferroni WITHIN each family over that family's
                      testable metrics.  alpha = 0.05.
  DISCRIMINATES     : the metric's p survives Holm inside its family.  The
                      direction must be stated.

POWER (stated for every testable metric, at the achieved n).
  continuous : the smallest AUC detectable at 80 % power for a two-sided
               Mann-Whitney at alpha = 0.05 (and at the Holm-worst-case
               alpha/m), by Monte-Carlo over a normal location-shift family
               (5,000 trials per grid point, seed 20261202).
  binary     : the smallest SPURIOUS rate detectable at 80 % power against
               the observed CONFIRMED rate, by exact binomial enumeration
               (the routine M4 used).

CONFOUND GUARD (pre-registered, applied to any metric that discriminates).
  Report CONFIRMED-vs-SPURIOUS medians of G, distance, period, |b| and
  significance.  A discriminating metric must also survive a G-stratified
  check (median split of the 65 on G: the direction must be the same in
  both halves, and reported per half even if underpowered there).

FAMILY VERDICT.
  WORKS         >= 1 metric survives Holm in that family; direction stated.
  DOESN'T       well-powered null: the family's primary metric reaches
                80 % power against AUC <= 0.70 (|r_rb| <= 0.40) and the
                observed effect is consistent with AUC = 0.5.
  UNDERPOWERED  otherwise; the achievable effect is stated.

CONFIG CONSEQUENCE (pre-registered).
  A metric enters queries/dr4-triage-config.v4.json as a caution FLAG /
  ranking tiebreaker -- never a cut, never a selection change -- if and
  only if it DISCRIMINATES, passes the confound guard, and the acceptance
  re-run (BH1 + BH2 present at Pr = 1.0000 and top-2 by M2_min; EB26
  operating point still 39/42 kept and 7/23 passed) PASSES first.
  If nothing discriminates, no v4 is written and the negative result with
  its power numbers is the deliverable.

=======================================================================
AMENDMENT LOG -- everything added AFTER the first run, and why.  None of
it changed the decision rule above; all of it is reported as descriptive
or as an explicitly-labelled post-hoc caveat.
=======================================================================
  before the first run
    * negative-control threshold split out from the family alpha: N1 voids
      the run at p < 0.01, is a caveat at 0.01 <= p < 0.05.  A single
      two-sided test trips at 5 % by construction, so "any p < 0.05 voids
      the run" was a bad rule and was fixed before it could bite.
  after the first run (which reported family C discriminating and the
  confound table showing CONFIRMED vs SPURIOUS differ in G and distance)
    * `significance` and `a0_mas` added to the confound covariate table
      (the first run crashed before printing them -- the EB26 fixture and
      the triage parquet both carry `significance` and the merge suffixed
      them).
    * POST-HOC ROBUSTNESS block: a distance median-split, and a logistic
      regression of P(spurious) on the metric plus z(log significance),
      z(G), z(log d).  Added because the confound table showed the group
      difference in `significance` is enormous (46.1 vs 10.4) and the
      pipeline already ranks on it -- a flag that merely restates it must
      be labelled as such.  Reported as a caveat; the pre-registered
      decision rule (Holm + G-stratified guard) was NOT changed.
    * "WHAT IT WOULD TAKE" sample-size projection and the family-A n = 7
      table + anecdote: descriptive additions, no test attached.
  M6 (2026-08-21) -- SOURCE OF VERDICTS, not behaviour
    * the verdict table is no longer read from the EB26 fixture directly:
      it comes from the day-one VERDICT STORE (scripts/verdict_schema.py,
      out/verdicts/*.csv), of which the EB26 fixture is now one producer
      and the epoch-vet harness is the other.  That is the entire change;
      the test, the rules, the seeds and the metrics are untouched, and
      the acceptance test of the refactor is that the frozen M5 artifacts
      reproduce BYTE-IDENTICALLY through the new path.
    * --verdicts / --scopes / --sources / --out-dir added so December can
      re-ask this question against harness verdicts with no new code.
    * a verdict-provenance block is printed to stdout every run, and
      written into the stats file ONLY when the store carries more than
      one (source, scope) combination -- a single-scope run has nothing to
      disclose, which is why today's output is unchanged.  The moment
      harness verdicts join the store, every consumer must say so: a
      harness `orbit_reality` SPURIOUS and an EB26 `compact_companion`
      SPURIOUS are close cousins, but a harness CONFIRMED is WEAKER than
      an EB26 CONFIRMED, so a pooled run is not the same experiment.

Inputs : data/dr3_activity_columns.parquet (scripts/m5_pull_activity_columns.py)
         out/verdicts/*.csv  (the day-one verdict store; M6)
         data/dr3_amrf_triage.parquet  (covariates)
Outputs: out/m5_activity_eb26_table.csv     (per-target, all 76)
         out/m5_activity_discriminator_stats.txt
Run    : .venv/Scripts/python.exe scripts/m5_activity_discriminator.py
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact, mannwhitneyu, norm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verdict_schema as vs  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "out")
SEED = 20261202
ALPHA = 0.05
POWER_TARGET = 0.80
N_BOOT = 10000
N_POWER_TRIALS = 5000


# ----------------------------------------------------------------- helpers
def wilson_ci(k, n, z=1.959964):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    den = 1.0 + z * z / n
    ctr = (p + z * z / (2 * n)) / den
    hw = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, ctr - hw), min(1.0, ctr + hw))


def auc_of(x_conf, x_spur):
    """P(spurious > confirmed) + 0.5 P(tie) -- the Mann-Whitney AUC."""
    n1, n2 = len(x_conf), len(x_spur)
    if n1 == 0 or n2 == 0:
        return np.nan
    u, _ = mannwhitneyu(x_spur, x_conf, alternative="two-sided")
    return u / (n1 * n2)


def boot_auc_ci(x_conf, x_spur, rng, n=N_BOOT):
    a = np.empty(n)
    for i in range(n):
        c = rng.choice(x_conf, size=len(x_conf), replace=True)
        s = rng.choice(x_spur, size=len(x_spur), replace=True)
        a[i] = auc_of(c, s)
    return np.nanpercentile(a, [2.5, 97.5])


def mwu_power(n1, n2, auc, rng, alpha=ALPHA, trials=N_POWER_TRIALS):
    """MC power of a two-sided MWU at alpha for a normal location shift
    giving the requested AUC (delta = sqrt(2) * Phi^-1(AUC))."""
    if auc <= 0.5:
        return 0.0
    delta = np.sqrt(2.0) * norm.ppf(auc)
    hits = 0
    for _ in range(trials):
        a = rng.normal(0.0, 1.0, n1)
        b = rng.normal(delta, 1.0, n2)
        if mannwhitneyu(b, a, alternative="two-sided").pvalue < alpha:
            hits += 1
    return hits / trials


def min_detectable_auc(n1, n2, rng, alpha=ALPHA):
    for auc in np.arange(0.55, 1.0001, 0.025):
        if mwu_power(n1, n2, float(auc), rng, alpha) >= POWER_TARGET:
            return float(auc)
    return None


def fisher_power(n1, p1, n2, p2, alpha=ALPHA):
    """Exact power of the two-sided Fisher test (M4's routine)."""
    from scipy.stats import binom
    pw = 0.0
    for k1 in range(n1 + 1):
        w1 = binom.pmf(k1, n1, p1)
        if w1 < 1e-12:
            continue
        for k2 in range(n2 + 1):
            w2 = binom.pmf(k2, n2, p2)
            if w2 < 1e-12:
                continue
            if fisher_exact([[k1, n1 - k1], [k2, n2 - k2]])[1] < alpha:
                pw += w1 * w2
    return pw


def min_detectable_rate(n1, p0, n2, alpha=ALPHA):
    for p1 in np.arange(0.0, 1.0001, 0.05):
        if p1 <= p0:
            continue
        if fisher_power(n1, p0, n2, float(p1), alpha) >= POWER_TARGET:
            return float(p1)
    return None


def holm(pvals):
    """Holm-Bonferroni: returns the adjusted p-values in input order."""
    idx = np.argsort(pvals)
    m = len(pvals)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(idx):
        val = (m - rank) * pvals[i]
        running = max(running, val)
        adj[i] = min(1.0, running)
    return adj


def rolling_median_baseline(g_ref, y_ref, g_query, halfwin=0.75, nmin=25):
    """median(y | G) from a reference population, +-halfwin mag windows."""
    out = np.full(len(g_query), np.nan)
    ok = np.isfinite(g_ref) & np.isfinite(y_ref)
    gr, yr = g_ref[ok], y_ref[ok]
    order = np.argsort(gr)
    gr, yr = gr[order], yr[order]
    for i, g0 in enumerate(g_query):
        if not np.isfinite(g0):
            continue
        w = halfwin
        for _ in range(6):
            lo, hi = np.searchsorted(gr, [g0 - w, g0 + w])
            if hi - lo >= nmin:
                out[i] = np.median(yr[lo:hi])
                break
            w *= 1.6
        else:
            lo, hi = np.searchsorted(gr, [g0 - w, g0 + w])
            if hi > lo:
                out[i] = np.median(yr[lo:hi])
    return out


def logit_irls(X, y, max_iter=200, tol=1e-9):
    """Plain IRLS logistic regression (no statsmodels in the venv).
    Returns (beta, se, wald_p) with an intercept prepended to X."""
    from scipy.stats import chi2
    X = np.column_stack([np.ones(len(y)), np.asarray(X, float)])
    b = np.zeros(X.shape[1])
    for _ in range(max_iter):
        eta = X @ b
        p = 1.0 / (1.0 + np.exp(-np.clip(eta, -30, 30)))
        w = np.clip(p * (1 - p), 1e-9, None)
        z = eta + (y - p) / w
        XtW = X.T * w
        try:
            bn = np.linalg.solve(XtW @ X, XtW @ z)
        except np.linalg.LinAlgError:
            return None, None, None
        if np.max(np.abs(bn - b)) < tol:
            b = bn
            break
        b = bn
    eta = X @ b
    p = 1.0 / (1.0 + np.exp(-np.clip(eta, -30, 30)))
    w = np.clip(p * (1 - p), 1e-9, None)
    try:
        cov = np.linalg.inv((X.T * w) @ X)
    except np.linalg.LinAlgError:
        return b, None, None
    se = np.sqrt(np.diag(cov))
    wald = (b / se) ** 2
    return b, se, chi2.sf(wald, 1)


def zscore(v):
    v = np.asarray(v, float)
    s = np.nanstd(v)
    return (v - np.nanmean(v)) / (s if s > 0 else 1.0)


def amp_proxy(n_obs, flux_over_error):
    """Belokurov+2017 eq. 2: log10(sqrt(N_obs) * sigma_F / F)."""
    n = np.asarray(n_obs, float)
    foe = np.asarray(flux_over_error, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        v = np.log10(np.sqrt(n) / foe)
    return np.where(np.isfinite(v), v, np.nan)


# ------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--verdicts", nargs="*", default=None,
                    help="verdict-store CSV(s); default out/verdicts/eb26.v1.csv")
    ap.add_argument("--scopes", nargs="*", default=None,
                    help="keep only these verdict_scope values")
    ap.add_argument("--sources", nargs="*", default=None,
                    help="keep only these verdict_source values")
    ap.add_argument("--out-dir", default=OUT_DIR)
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    out_dir = a.out_dir
    os.makedirs(out_dir, exist_ok=True)

    rng = np.random.default_rng(SEED)
    lines = []

    def say(s=""):
        lines.append(s)
        print(s)

    act = pd.read_parquet(os.path.join(BASE, "data",
                                       "dr3_activity_columns.parquet"))
    # M6: verdicts come from the verdict STORE, not from the fixture.  The
    # compatibility frame hands back exactly the column names this test
    # already used, which is what makes this a change of source and not of
    # behaviour (see scripts/verdict_schema.py).
    store_paths = a.verdicts or [os.path.join(vs.STORE_DIR, "eb26.v1.csv")]
    store = vs.load_store(store_paths, scopes=a.scopes, sources=a.sources)
    eb = vs.eb26_compatible_frame(store)
    prov = vs.scope_composition_string(store)
    n_combo = store.groupby(["verdict_source", "verdict_scope"]).ngroups
    print(f"VERDICT PROVENANCE: {len(store)} records from "
          f"{[os.path.basename(p) for p in store_paths]}")
    print(f"  scope composition: {prov}")
    eb = eb.drop(columns=["verdict_source", "verdict_scope",
                          "verdict_confidence"])
    tri = pd.read_parquet(
        os.path.join(BASE, "data", "dr3_amrf_triage.parquet"),
        columns=["source_id", "nss_solution_type", "l", "b",
                 "nss_parallax", "period", "significance", "a0_mas",
                 "class_det", "cuts_eb26", "sigma_ti2", "flag_alias_1yr"])
    tri = tri.drop_duplicates("source_id")
    # the EB26 fixture ALSO carries `significance` and `period_d`; keep the
    # archive's values and avoid a silent _x/_y suffix collision
    tri = tri.rename(columns={"significance": "significance_archive"})

    # ---- the magnitude-detrending baseline uses the FULL pulled population
    for band in ("g", "bp", "rp"):
        act[f"amp_{band}"] = amp_proxy(act[f"phot_{band}_n_obs"],
                                       act[f"phot_{band}_mean_flux_over_error"])
    for band in ("g", "bp", "rp"):
        base = rolling_median_baseline(act["phot_g_mean_mag"].values,
                                       act[f"amp_{band}"].values,
                                       act["phot_g_mean_mag"].values)
        act[f"damp_{band}"] = act[f"amp_{band}"].values - base
        act[f"amp_{band}_baseline"] = base

    t = eb.merge(act, on="source_id", how="left") \
          .merge(tri, on="source_id", how="left")
    # M7: same fix as m4_eb26_erosita_test.py -- the invariant is no fan-out,
    # not a store of exactly 76.  `--verdicts all` (and therefore the
    # runbook's pooled command) crashed here the moment the store held a
    # second producer.  Rows with no gaia_source row cannot be tested and are
    # dropped with a count, never silently.
    assert len(t) == len(eb), f"verdict join fanned out: {len(t)} vs {len(eb)}"
    n_unjoined = int(t["ruwe"].isna().sum())
    if n_unjoined:
        print(f"  {n_unjoined} of {len(t)} verdict rows have no "
              f"gaia_source row in the pulled columns -- DROPPED")
        t = t[t["ruwe"].notna()].reset_index(drop=True)
    if len(t) == 0:
        # M7: an empty testable set is a COVERAGE RESULT, not a crash.  The
        # pre-registered scope-pure primary run selects harness verdicts
        # only, and on 2026-08-23 the only harness verdicts in existence are
        # the 12 pre-release demo sources, none of which are in the pulled
        # gaia_source columns.  Raising an AssertionError there says
        # "something broke"; nothing broke, there is nothing to test.
        print("\nNOT TESTABLE: 0 of the selected verdict rows have a "
              "gaia_source row in the pulled columns.")
        print("  This is a coverage result, not a failure. Report the "
              "coverage; claim nothing.")
        return 2

    t["is_variable"] = t["phot_variable_flag"].astype(str) == "VARIABLE"
    t["d_pc"] = 1000.0 / t["nss_parallax"]

    say("M5 activity-vs-spuriousness test -- EB26 x Gaia DR3 all-sky "
        "(2026-08-18)")
    say("=" * 74)
    say("Rules pre-registered in this script's docstring before any "
        "confirmed/spurious split was computed.")
    if n_combo > 1:
        # MANDATORY disclosure: this run pools verdicts of more than one
        # provenance/scope, and a harness `orbit_reality` CONFIRMED is a
        # weaker statement than an EB26 `compact_companion` CONFIRMED.
        say("VERDICT PROVENANCE (more than one source/scope in this run -- "
            "read the asymmetry note in scripts/verdict_schema.py):")
        say(f"  {prov}")
    say("")
    say(f"sample: {len(t)} EB26 targets; verdicts "
        f"{t['verdict'].value_counts().to_dict()}")
    say("FOOTPRINT: 76 of 76 (100 %) have Gaia DR3 gaia_source rows -- "
        "this is the point of the test.")
    say(f"  (M4's X-ray axis could see {29} of the {65} verdicted targets: "
        f"16 confirmed + 13 spurious.)")

    conf = t[t["verdict"] == "CONFIRMED"]
    spur = t[t["verdict"] == "SPURIOUS"]
    other = t[~t["verdict"].isin(["CONFIRMED", "SPURIOUS"])]
    say(f"  primary comparison: CONFIRMED n={len(conf)} vs SPURIOUS "
        f"n={len(spur)}; {len(other)} other verdicts reported only")

    # ---- coverage ---------------------------------------------------------
    say("")
    say("COVERAGE (honest, per family) " + "-" * 44)
    cov_rows = []
    for label, col, kind in [
            ("A1 activityindex_espcs", "activityindex_espcs", "num"),
            ("B1 dAmp_G", "damp_g", "num"),
            ("B2 dAmp_BP", "damp_bp", "num"),
            ("B3 dAmp_RP", "damp_rp", "num"),
            ("B4 phot_variable_flag", "phot_variable_flag", "str"),
            ("B5 std_dev_mag_g_fov", "std_dev_mag_g_fov", "num"),
            ("C1 ruwe", "ruwe", "num"),
            ("C2 ipd_frac_multi_peak", "ipd_frac_multi_peak", "num"),
            ("C3 ipd_gof_harmonic_amplitude", "ipd_gof_harmonic_amplitude",
             "num"),
            ("C4 astrometric_excess_noise_sig", "astrometric_excess_noise_sig",
             "num"),
            ("C5 astrometric_gof_al", "astrometric_gof_al", "num"),
            ("C6 phot_bp_rp_excess_factor", "phot_bp_rp_excess_factor", "num"),
            ("N1 phot_g_n_obs (neg. control)", "phot_g_n_obs", "num")]:
        if kind == "num":
            n_all = int(pd.to_numeric(t[col], errors="coerce").notna().sum())
            n_c = int(pd.to_numeric(conf[col], errors="coerce").notna().sum())
            n_s = int(pd.to_numeric(spur[col], errors="coerce").notna().sum())
        else:
            n_all = int(t[col].notna().sum())
            n_c, n_s = int(conf[col].notna().sum()), int(spur[col].notna().sum())
        cov_rows.append((label, n_all, n_c, n_s))
        say(f"  {label:32s} {n_all:3d}/76 total   "
            f"{n_c:2d}/{len(conf)} confirmed   {n_s:2d}/{len(spur)} spurious")
    say(f"  in vari_summary at all: {int(t['in_vari_summary'].sum())}/76 "
        f"({int(conf['in_vari_summary'].sum())} conf / "
        f"{int(spur['in_vari_summary'].sum())} spur)")
    say(f"  phot_variable_flag values: "
        f"{t['phot_variable_flag'].value_counts().to_dict()}")
    say(f"  activityindex_espcs_input values: "
        f"{t['activityindex_espcs_input'].value_counts(dropna=False).to_dict()}")

    # ---- the tests --------------------------------------------------------
    FAMILIES = {
        "A (chromospheric activity, ESP-CS)": [
            ("A1 activityindex_espcs", "activityindex_espcs", "num")],
        "B (photometric variability)": [
            ("B1 dAmp_G", "damp_g", "num"),
            ("B2 dAmp_BP", "damp_bp", "num"),
            ("B3 dAmp_RP", "damp_rp", "num"),
            ("B4 phot_variable_flag==VARIABLE", "is_variable", "bin"),
            ("B5 std_dev_mag_g_fov", "std_dev_mag_g_fov", "num")],
        "C (astrometric/imaging quality -- NOT activity)": [
            ("C1 ruwe", "ruwe", "num"),
            ("C2 ipd_frac_multi_peak", "ipd_frac_multi_peak", "num"),
            ("C3 ipd_gof_harmonic_amplitude", "ipd_gof_harmonic_amplitude",
             "num"),
            ("C4 astrometric_excess_noise_sig", "astrometric_excess_noise_sig",
             "num"),
            ("C5 astrometric_gof_al", "astrometric_gof_al", "num"),
            ("C6 phot_bp_rp_excess_factor", "phot_bp_rp_excess_factor",
             "num")],
        "NEGATIVE CONTROL (must not discriminate)": [
            ("N1 phot_g_n_obs", "phot_g_n_obs", "num")],
    }

    results = []
    for fam, metrics in FAMILIES.items():
        say("")
        say(f"FAMILY {fam} " + "-" * max(4, 60 - len(fam)))
        fam_res = []
        for label, col, kind in metrics:
            if kind == "bin":
                k1, n1 = int(conf[col].sum()), len(conf)
                k2, n2 = int(spur[col].sum()), len(spur)
                lo1, hi1 = wilson_ci(k1, n1)
                lo2, hi2 = wilson_ci(k2, n2)
                orr, p = fisher_exact([[k2, n2 - k2], [k1, n1 - k1]])
                mdr = min_detectable_rate(n1, k1 / n1 if n1 else 0.0, n2)
                say(f"  {label}")
                say(f"    CONFIRMED {k1}/{n1} = {k1/max(n1,1):.3f} "
                    f"(95% {lo1:.3f}-{hi1:.3f});  SPURIOUS {k2}/{n2} = "
                    f"{k2/max(n2,1):.3f} (95% {lo2:.3f}-{hi2:.3f})")
                say(f"    Fisher two-sided p = {p:.4f}, odds ratio "
                    f"{orr:.2f}")
                say(f"    power: smallest SPURIOUS rate detectable at 80% "
                    f"vs CONFIRMED {k1/max(n1,1):.3f} = "
                    f"{('%.2f' % mdr) if mdr is not None else 'NONE <= 1.0'}")
                fam_res.append({"family": fam, "metric": label, "kind": "bin",
                                "n_conf": n1, "n_spur": n2, "p": p,
                                "effect": orr, "eff_lo": np.nan,
                                "eff_hi": np.nan,
                                "min_detectable": mdr, "testable": True})
                continue

            xc = pd.to_numeric(conf[col], errors="coerce").dropna().values
            xs = pd.to_numeric(spur[col], errors="coerce").dropna().values
            if len(xc) < 5 or len(xs) < 5:
                say(f"  {label}: NOT TESTABLE "
                    f"(confirmed n={len(xc)}, spurious n={len(xs)}; "
                    f"pre-registered minimum 5 per side)")
                fam_res.append({"family": fam, "metric": label, "kind": "num",
                                "n_conf": len(xc), "n_spur": len(xs),
                                "p": np.nan, "effect": np.nan,
                                "eff_lo": np.nan, "eff_hi": np.nan,
                                "min_detectable": np.nan, "testable": False})
                continue
            u, p = mannwhitneyu(xs, xc, alternative="two-sided")
            auc = u / (len(xc) * len(xs))
            lo, hi = boot_auc_ci(xc, xs, rng)
            mda = min_detectable_auc(len(xc), len(xs), rng)
            say(f"  {label}  (n {len(xc)} conf / {len(xs)} spur)")
            say(f"    medians: CONFIRMED {np.median(xc):+.4g}   "
                f"SPURIOUS {np.median(xs):+.4g}   "
                f"(HL shift {np.median(xs)-np.median(xc):+.4g})")
            say(f"    Mann-Whitney two-sided p = {p:.4f};  "
                f"AUC(spur>conf) = {auc:.3f} [95% boot {lo:.3f}-{hi:.3f}];  "
                f"r_rb = {2*auc-1:+.3f} [{2*lo-1:+.3f}, {2*hi-1:+.3f}]")
            say(f"    power: smallest AUC detectable at 80% power = "
                f"{('%.3f' % mda) if mda is not None else 'NONE < 1.0'} "
                f"(r_rb {('%.2f' % (2*mda-1)) if mda is not None else '--'})")
            fam_res.append({"family": fam, "metric": label, "kind": "num",
                            "n_conf": len(xc), "n_spur": len(xs), "p": p,
                            "effect": auc, "eff_lo": lo, "eff_hi": hi,
                            "min_detectable": mda, "testable": True})

        testable = [r for r in fam_res if r["testable"]]
        if testable:
            adj = holm(np.array([r["p"] for r in testable]))
            for r, a in zip(testable, adj):
                r["p_holm"] = a
            say(f"  Holm-Bonferroni within family (m = {len(testable)}):")
            for r in testable:
                mark = "**DISCRIMINATES**" if r["p_holm"] < ALPHA else "ns"
                say(f"    {r['metric']:34s} p = {r['p']:.4f} -> "
                    f"p_holm = {r['p_holm']:.4f}  {mark}")
        results.extend(fam_res)

    res = pd.DataFrame(results)

    # ---- confound covariates ---------------------------------------------
    say("")
    say("CONFOUND COVARIATES (pre-registered, medians) " + "-" * 28)
    for lab, col in (("G mag", "phot_g_mean_mag"), ("d [pc]", "d_pc"),
                     ("period [d]", "period"), ("|b| [deg]", "b"),
                     ("significance", "significance_archive"),
                     ("a0 [mas]", "a0_mas"), ("bp_rp", "bp_rp")):
        a = pd.to_numeric(conf[col], errors="coerce")
        b_ = pd.to_numeric(spur[col], errors="coerce")
        if col == "b":
            a, b_ = a.abs(), b_.abs()
        _, pc = mannwhitneyu(b_.dropna(), a.dropna(),
                             alternative="two-sided")
        say(f"  {lab:14s} CONFIRMED {a.median():8.3f}   SPURIOUS "
            f"{b_.median():8.3f}   (MWU p = {pc:.3f})")

    # ---- G-stratified check for anything that discriminated --------------
    disc = res[(res["testable"]) & (res.get("p_holm", 1.0) < ALPHA)
               & (~res["family"].str.startswith("NEGATIVE"))]
    if len(disc):
        gmed = np.nanmedian(t.loc[t["verdict"].isin(["CONFIRMED", "SPURIOUS"]),
                                  "phot_g_mean_mag"])
        say("")
        say(f"G-STRATIFIED CHECK (median split at G = {gmed:.2f}) "
            + "-" * 20)
        for _, r in disc.iterrows():
            col = dict((lab, c) for fam in FAMILIES.values()
                       for lab, c, _k in fam)[r["metric"]]
            for half, sel in (("bright", t["phot_g_mean_mag"] <= gmed),
                              ("faint", t["phot_g_mean_mag"] > gmed)):
                cc = pd.to_numeric(
                    t.loc[sel & (t["verdict"] == "CONFIRMED"), col],
                    errors="coerce").dropna().values
                ss = pd.to_numeric(
                    t.loc[sel & (t["verdict"] == "SPURIOUS"), col],
                    errors="coerce").dropna().values
                if len(cc) >= 3 and len(ss) >= 3:
                    a = auc_of(cc, ss)
                    _, pp = mannwhitneyu(ss, cc, alternative="two-sided")
                    say(f"  {r['metric']:32s} {half:6s}: n {len(cc)}/"
                        f"{len(ss)}  medians {np.median(cc):+.4g} vs "
                        f"{np.median(ss):+.4g}  AUC {a:.3f}  p {pp:.3f}")
                else:
                    say(f"  {r['metric']:32s} {half:6s}: n {len(cc)}/"
                        f"{len(ss)} -- too few")
        # ---- POST-HOC robustness (NOT part of the pre-registered rule) ---
        say("")
        say("POST-HOC ROBUSTNESS (added after the confound table showed "
            "CONFIRMED and SPURIOUS")
        say("differ in G and in distance; reported as caveats, NOT as part "
            "of the pre-registered decision rule)")
        dmed = np.nanmedian(
            t.loc[t["verdict"].isin(["CONFIRMED", "SPURIOUS"]), "d_pc"])
        for _, r in disc.iterrows():
            col = dict((lab, c) for fam in FAMILIES.values()
                       for lab, c, _k in fam)[r["metric"]]
            say(f"  --- {r['metric']}")
            for half, sel in (("near", t["d_pc"] <= dmed),
                              ("far", t["d_pc"] > dmed)):
                cc = pd.to_numeric(
                    t.loc[sel & (t["verdict"] == "CONFIRMED"), col],
                    errors="coerce").dropna().values
                ss = pd.to_numeric(
                    t.loc[sel & (t["verdict"] == "SPURIOUS"), col],
                    errors="coerce").dropna().values
                if len(cc) >= 3 and len(ss) >= 3:
                    _, pp = mannwhitneyu(ss, cc, alternative="two-sided")
                    say(f"      distance split at {dmed:.0f} pc, {half:4s}: "
                        f"n {len(cc)}/{len(ss)}  AUC {auc_of(cc, ss):.3f}  "
                        f"p {pp:.3f}")
                else:
                    say(f"      distance split, {half:4s}: n {len(cc)}/"
                        f"{len(ss)} -- too few")
            # does it add anything beyond what the pipeline already ranks on?
            m = t[t["verdict"].isin(["CONFIRMED", "SPURIOUS"])].copy()
            m["y"] = (m["verdict"] == "SPURIOUS").astype(float)
            xm = pd.to_numeric(m[col], errors="coerce")
            use = (np.isfinite(xm) & np.isfinite(m["significance_archive"])
                   & np.isfinite(m["phot_g_mean_mag"])
                   & np.isfinite(m["d_pc"]))
            mm = m[use]
            X = np.column_stack([
                zscore(np.log10(np.clip(
                    pd.to_numeric(mm[col], errors="coerce"), 1e-6, None))),
                zscore(np.log10(np.clip(mm["significance_archive"], 1e-6,
                                        None))),
                zscore(mm["phot_g_mean_mag"]),
                zscore(np.log10(mm["d_pc"]))])
            b, se, pw = logit_irls(X, mm["y"].values)
            if b is not None and pw is not None:
                say(f"      logistic P(spurious) ~ z(log {col}) + "
                    f"z(log significance) + z(G) + z(log d), n={len(mm)}:")
                for nm, bi, pi in zip([col, "log significance", "G", "log d"],
                                      b[1:], pw[1:]):
                    say(f"        beta[{nm:22s}] = {bi:+7.3f}   "
                        f"Wald p = {pi:.4f}")
                say(f"      -> the metric's own contribution beyond the "
                    f"pipeline's existing ranking variables: "
                    f"p = {pw[1]:.4f}")
            else:
                say("      logistic fit did not converge (separation) -- "
                    "reported as such")
    else:
        say("")
        say("G-STRATIFIED CHECK: not run (nothing discriminated).")

    # ---- how big would the sample have to be? -----------------------------
    say("")
    say("WHAT IT WOULD TAKE (forward-looking; the observed effect held "
        "fixed, the 42:23")
    say("ratio held fixed, 80 % power at alpha = 0.05 uncorrected) "
        + "-" * 8)
    for fam, metrics in FAMILIES.items():
        sub = res[(res["family"] == fam) & res["testable"]
                  & (res["kind"] == "num")]
        if not len(sub):
            continue
        r = sub.loc[sub["p"].idxmin()]
        auc = float(r["effect"])
        auc_eff = auc if auc > 0.5 else 1.0 - auc
        need = None
        for scale in (1, 2, 3, 4, 6, 8, 12, 16, 24, 32):
            n1, n2 = 42 * scale, 23 * scale
            if mwu_power(n1, n2, auc_eff, rng, trials=1500) >= POWER_TARGET:
                need = (n1, n2, scale)
                break
        say(f"  {r['metric']:32s} observed AUC {auc:.3f} -> needs about "
            + (f"{need[0]} confirmed + {need[1]} spurious "
               f"({need[2]}x today's sample)" if need
               else "> 32x today's sample"))
    say("  (the epoch-vet loop is the sample factory: it adjudicates "
        "hundreds of")
    say("   candidates in 72 h, so re-running this test on day-one "
        "verdicts is the")
    say("   cheapest way to reach these numbers -- wired into the "
        "first-24h bulletin.)")

    # ---- the ESP-CS anecdote (n = 1, stated as such) ---------------------
    esp = t[t["activityindex_espcs"].notna()][
        ["source_id", "verdict", "activityindex_espcs",
         "activityindex_espcs_uncertainty", "phot_g_mean_mag"]]
    if len(esp):
        say("")
        say("FAMILY A, the whole of it (n = 7) -- reported because the "
            "coverage IS the result:")
        say(esp.sort_values("activityindex_espcs", ascending=False)
               .to_string(index=False))
        sp = esp[esp["verdict"] == "SPURIOUS"]
        if len(sp) == 1:
            rank = int((esp["activityindex_espcs"]
                        > float(sp["activityindex_espcs"].iloc[0])).sum()) + 1
            say(f"  ANECDOTE, n = 1, no test claimed: the single "
                f"EB26-SPURIOUS target with an ESP-CS value "
                f"({int(sp['source_id'].iloc[0])}) is rank {rank} of "
                f"{len(esp)} in chromospheric activity -- and it is also "
                f"one of M4's two X-ray detections. Suggestive, "
                f"unfalsifiable at this n.")

    # ---- family verdicts --------------------------------------------------
    say("")
    say("=" * 74)
    for fam in FAMILIES:
        sub = res[res["family"] == fam]
        tst = sub[sub["testable"]]
        if not len(tst):
            say(f"FAMILY {fam}: NOT TESTABLE at this coverage.")
            continue
        wins = tst[tst["p_holm"] < ALPHA]
        prim = tst.iloc[0]
        if len(wins):
            say(f"FAMILY {fam}: **WORKS** -- "
                f"{', '.join(wins['metric'])} survive(s) Holm.")
        else:
            mdet = prim["min_detectable"]
            wellpowered = (prim["kind"] == "num" and mdet is not None
                           and np.isfinite(mdet) and mdet <= 0.70)
            if wellpowered:
                say(f"FAMILY {fam}: **DOESN'T** (well-powered null) -- "
                    f"the primary metric could have detected AUC "
                    f"{mdet:.2f} at 80 % power and the observed AUC is "
                    f"{prim['effect']:.3f} "
                    f"[{prim['eff_lo']:.3f}-{prim['eff_hi']:.3f}].")
            else:
                say(f"FAMILY {fam}: **UNDERPOWERED** -- nothing survives "
                    f"Holm; smallest detectable effect for the primary "
                    f"metric: "
                    f"{('AUC %.2f' % mdet) if (mdet is not None and np.isfinite(mdet)) else 'not reachable at n<=1'}"
                    f"; observed {prim['effect']:.3f}.")
    say("=" * 74)

    # ---- per-target artifact ---------------------------------------------
    keep = ["source_id", "verdict", "phot_g_mean_mag", "bp_rp", "d_pc",
            "period", "significance", "l", "b",
            "activityindex_espcs", "activityindex_espcs_uncertainty",
            "activityindex_espcs_input",
            "amp_g", "amp_g_baseline", "damp_g", "amp_bp", "damp_bp",
            "amp_rp", "damp_rp", "phot_variable_flag", "in_vari_summary",
            "std_dev_mag_g_fov", "range_mag_g_fov", "stetson_mag_g_fov",
            "in_vari_rotation_modulation",
            "ruwe", "ipd_frac_multi_peak", "ipd_gof_harmonic_amplitude",
            "astrometric_excess_noise", "astrometric_excess_noise_sig",
            "astrometric_gof_al", "phot_bp_rp_excess_factor",
            "phot_g_n_obs", "visibility_periods_used", "notes"]
    keep = [c for c in keep if c in t.columns]
    t[keep].to_csv(os.path.join(out_dir, "m5_activity_eb26_table.csv"),
                   index=False, lineterminator="\n")
    res.to_csv(os.path.join(out_dir, "m5_activity_metric_results.csv"),
               index=False, lineterminator="\n")
    with open(os.path.join(out_dir,
                           "m5_activity_discriminator_stats.txt"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    # M7: print the REAL directory.  This line hard-coded "out/" while the
    # files went wherever --out-dir pointed, so a pooled December run would
    # have announced that it had just overwritten the frozen M5 artifacts
    # when it had not.  A log line that lies about a path is a log line that
    # will be believed at 3 a.m. on release day.
    print(f"\nwrote {os.path.relpath(out_dir, BASE)}/"
          f"m5_activity_eb26_table.csv, m5_activity_metric_results.csv, "
          f"m5_activity_discriminator_stats.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
