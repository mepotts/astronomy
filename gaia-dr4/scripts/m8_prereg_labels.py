#!/usr/bin/env python
"""M8 task 3: make the pre-registration's outcome labels EXECUTABLE.

PREREG-2026-08-23-december-discriminators.md section 5 assigns each test
exactly one of six labels and says "the label follows mechanically from the
numbers; there is no residual judgement".  Nothing in this repository
computed one.  M4 prints WORKS / UNDERPOWERED / NOT TESTABLE; M5 prints
WORKS / DOESN'T / UNDERPOWERED / NOT TESTABLE; M6 prints KEEP / REMOVE /
CARRY.  None of those is the pre-registered vocabulary, none of them knows
about the pre-registered DIRECTION, and none of them knows whether it is
running the scope-pure primary or the pooled secondary.  A rule that no code
executes is a rule that gets executed by a human at 3 a.m. on release day.

This module is the missing translator.  It does NOT change any rule: it
reads section 5 and section 2.2 and turns them into one total function.

  POSITIVE                        Holm p < 0.05 AND pre-registered direction
                                  AND DECISIVE
  POSITIVE (conservative, pooled) as POSITIVE but from the pooled secondary
  NULL                            not significant AND DECISIVE
  UNDERPOWERED                    not significant AND not DECISIVE
  DIRECTION REVERSAL              significant but opposite to the
                                  pre-registered direction
  NOT TESTABLE                    < 5 rows on either side, or zero rows
                                  survive the join

DECISIVE (section 4): the smallest effect detectable at 80 % power at the
achieved n is at least as small as the effect under test.

FOUR GAPS IN THE FROZEN REGISTRATION, FOUND BY WRITING THIS AND BY RUNNING
IT, REPORTED RATHER THAN PATCHED (the file is frozen; only Matthew may
amend it).  GAP-4 is documented on is_decisive() below.

  GAP-1  "significant, right direction, but NOT decisive" has no label.
         POSITIVE requires DECISIVE; NULL and UNDERPOWERED both require
         "not significant"; DIRECTION REVERSAL requires the wrong
         direction; NOT TESTABLE requires n < 5.  A small, loud sample --
         say 8 + 8 with AUC 0.95 -- satisfies none of the six.  The six
         labels are not exhaustive.
         WHAT THIS MODULE DOES: emits `POSITIVE (not decisive)` and sets
         `defect='GAP-1'`, so the case is loud instead of silent.  This is
         a PLACEHOLDER pending an amendment, not a seventh pre-registered
         label.

  GAP-2  section 5 says every test gets "exactly one of these six labels",
         but section 2.2 mandates that a pooled NON-significant result "must
         be reported as 'pooled: uninterpretable'" and "must never be quoted
         as a null".  That outcome is not one of the six.  Applying the six
         literally to a pooled run would force NULL or UNDERPOWERED, both of
         which section 2.2 forbids.
         WHAT THIS MODULE DOES: emits `POOLED: UNINTERPRETABLE (diluted)`
         for that case -- which is section 2.2's own words -- and sets
         `defect='GAP-2'`.  Section 2.2 wins over section 5's arithmetic
         because it is the more specific rule and because it is the one
         that protects against the error.

  GAP-3  a pooled result that is significant in the WRONG direction is
         covered by neither section.  Section 2.2 permits only the positive
         to be interpreted; section 5's DIRECTION REVERSAL carries no scope
         qualifier.
         WHAT THIS MODULE DOES: emits `DIRECTION REVERSAL (pooled, not
         interpretable)` and sets `defect='GAP-3'`.

THE NEGATIVE-CONTROL VETO (section 3, "N") is also implemented here,
because no consumer implements it: if `phot_g_n_obs` reaches p < 0.05, every
D1-D4 POSITIVE in the same run is re-labelled `POSITIVE (VETOED by the
negative control)` and the run is flagged.  The registration gives that rule
teeth; this gives it a code path.
"""
import numpy as np

ALPHA = 0.05
MIN_PER_SIDE = 5

# Pre-registered directions, section 3.  For AUC metrics the direction is
# expressed as AUC(spurious > confirmed) vs 0.5; for rate metrics as
# rate(spurious) vs rate(confirmed).
PREREG = {
    "D1": {"name": "X-ray activity (eROSITA-DE)", "family_m": 3,
           "kind": "rate", "direction": "spurious_higher",
           "effect_under_test": (0.154, 0.000),
           "primary_metric": "in-footprint detection rate"},
    "D2": {"name": "photometric variability", "family_m": 5,
           "kind": "auc", "direction": "auc_above_half",
           "effect_under_test": 0.659, "primary_metric": "dAmp_G"},
    "D3": {"name": "astrometric quality", "family_m": 6,
           "kind": "auc", "direction": "auc_below_half",
           "effect_under_test": 0.344, "primary_metric": "astrometric_gof_al"},
    "D4": {"name": "flag_astrom_quiet, thresholded", "family_m": 1,
           "kind": "rate", "direction": "spurious_higher",
           "effect_under_test": (0.30, 0.075),
           "primary_metric": "flagged fraction"},
}

SIX = ["POSITIVE", "POSITIVE (conservative, pooled)", "NULL",
       "UNDERPOWERED", "DIRECTION REVERSAL", "NOT TESTABLE"]
BEYOND_SIX = ["POSITIVE (not decisive)",
              "POOLED: UNINTERPRETABLE (diluted)",
              "DIRECTION REVERSAL (pooled, not interpretable)"]


def effect_magnitude(kind, effect_under_test):
    """The effect under test on the scale `min_detectable` is measured on."""
    if kind == "auc":
        a = float(effect_under_test)
        return a if a > 0.5 else 1.0 - a
    return float(effect_under_test[0])


def is_decisive(test, min_detectable):
    """Section 4, read LITERALLY: decisive iff the smallest detectable effect
    at 80 % power is at least as small as the effect under test.

    GAP-4, and it only shows up at scale.  For the two RATE tests the effect
    under test is a PAIR -- D1 "0.154 vs 0.000", D4 "0.30 vs 0.075" -- while
    `min_detectable_rate(n1, p0, n2)` returns the smallest detectable
    SPURIOUS rate against the OBSERVED confirmed rate p0.  The two numbers
    are only on the same scale when the observed baseline happens to equal
    the pre-registered one.  On a store where the observed confirmed marking
    rate came out at 0.22 instead of the pre-registered 0.075, the literal
    comparison (min_detectable 0.35 vs effect 0.30) says NOT DECISIVE for a
    test that in fact has ample power for a 0.225-wide difference.  The
    registration does not say which reading it means.  `decisive_by_diff()`
    below implements the other reading -- the pre-registered DIFFERENCE
    applied to the observed baseline -- and the caller reports GAP-4 when the
    two readings disagree.
    """
    if min_detectable is None or not np.isfinite(min_detectable):
        return False
    spec = PREREG[test]
    if spec["kind"] == "auc":
        return float(min_detectable) <= effect_magnitude(
            "auc", spec["effect_under_test"])
    return float(min_detectable) <= float(spec["effect_under_test"][0])


def decisive_by_diff(test, n_conf, n_spur, rate_conf):
    """The second reading of section 4 for a rate test: could this n have
    detected the pre-registered DIFFERENCE at the observed baseline?"""
    spec = PREREG[test]
    if spec["kind"] != "rate":
        return None
    if rate_conf is None or not np.isfinite(rate_conf):
        return None
    p_s, p_c = spec["effect_under_test"]
    p1 = min(1.0, max(0.0, float(rate_conf) + (p_s - p_c)))
    try:
        import m5_activity_discriminator as M5
        return bool(M5.fisher_power(int(n_conf), float(rate_conf),
                                    int(n_spur), p1) >= 0.80)
    except Exception:                                     # noqa: BLE001
        return None


def direction_ok(test, observed):
    """Is the observed effect in the pre-registered direction?"""
    spec = PREREG[test]
    if observed is None or not np.isfinite(observed):
        return None
    if spec["direction"] == "auc_above_half":
        return float(observed) > 0.5
    if spec["direction"] == "auc_below_half":
        return float(observed) < 0.5
    return float(observed) > 0.0        # rate difference, spurious - confirmed


def assign_label(test, analysis, n_conf, n_spur, p_holm, observed_effect,
                 min_detectable, joined_rows=None, rate_conf=None):
    """The one total function.  Returns a dict, never raises, never None.

    analysis : 'primary' | 'regression' | 'pooled'
    observed_effect : AUC for kind='auc'; rate(spurious) - rate(confirmed)
                      for kind='rate'
    """
    spec = PREREG[test]
    out = {"test": test, "analysis": analysis, "n_conf": int(n_conf or 0),
           "n_spur": int(n_spur or 0), "p_holm": p_holm,
           "effect": observed_effect, "min_detectable": min_detectable,
           "decisive": False, "direction_ok": None, "defect": "",
           "label": None, "reason": ""}

    if joined_rows is not None and int(joined_rows) == 0:
        out.update(label="NOT TESTABLE",
                   reason="zero rows survive the join to the metric's data")
        return out
    if (n_conf or 0) < MIN_PER_SIDE or (n_spur or 0) < MIN_PER_SIDE:
        out.update(label="NOT TESTABLE",
                   reason=f"fewer than {MIN_PER_SIDE} rows on a side "
                          f"({n_conf} confirmed / {n_spur} spurious)")
        return out

    dec = is_decisive(test, min_detectable)
    dok = direction_ok(test, observed_effect)
    dec_diff = decisive_by_diff(test, n_conf, n_spur, rate_conf)
    out["decisive"] = bool(dec)
    out["decisive_by_diff"] = dec_diff
    out["direction_ok"] = dok
    if dec_diff is not None and bool(dec_diff) != bool(dec):
        out["defect"] = "GAP-4"

    def _add(gap):
        """Defects accumulate: a pooled non-significant rate test can carry
        both GAP-2 and GAP-4, and losing one of them loses a real finding."""
        out["defect"] = (out["defect"] + "+" + gap) if out["defect"] else gap
        return out["defect"]
    sig = (p_holm is not None and np.isfinite(p_holm)
           and float(p_holm) < ALPHA)
    eff = effect_magnitude(spec["kind"], spec["effect_under_test"])

    if not sig:
        if analysis == "pooled":
            out.update(label="POOLED: UNINTERPRETABLE (diluted)",
                       defect=_add("GAP-2"),
                       reason="section 2.2: pooled non-significance is "
                              "dilution, never a null.  Section 5 has no "
                              "label for it.")
            return out
        if dec:
            out.update(label="NULL",
                       reason=f"not significant (Holm p {p_holm:.4f}) and "
                              f"DECISIVE: smallest detectable "
                              f"{min_detectable:.3f} <= effect under test "
                              f"{eff:.3f}")
        else:
            md = ("not reachable" if min_detectable is None
                  or not np.isfinite(min_detectable)
                  else f"{min_detectable:.3f}")
            out.update(label="UNDERPOWERED",
                       reason=f"not significant (Holm p "
                              f"{p_holm if p_holm is None else float(p_holm):.4f})"
                              f" and NOT decisive: smallest detectable {md} "
                              f"> effect under test {eff:.3f}")
        return out

    # significant
    if dok is False:
        if analysis == "pooled":
            out.update(label="DIRECTION REVERSAL (pooled, not interpretable)",
                       defect=_add("GAP-3"),
                       reason="significant in the opposite direction, in the "
                              "pooled secondary; neither section 2.2 nor "
                              "section 5 covers this combination")
        else:
            out.update(label="DIRECTION REVERSAL",
                       reason=f"Holm p {float(p_holm):.4f} but the effect "
                              f"({observed_effect}) is opposite to the "
                              f"pre-registered direction "
                              f"({spec['direction']})")
        return out

    if analysis == "pooled":
        out.update(label="POSITIVE (conservative, pooled)",
                   reason="significant in the pooled secondary: a "
                          "conservative positive, it survived dilution")
        return out
    if dec:
        out.update(label="POSITIVE",
                   reason=f"Holm p {float(p_holm):.4f}, pre-registered "
                          f"direction, DECISIVE")
    else:
        md = ("not reachable" if min_detectable is None
              or not np.isfinite(min_detectable)
              else f"{min_detectable:.3f}")
        out.update(label="POSITIVE (not decisive)", defect=_add("GAP-1"),
                   reason=f"Holm p {float(p_holm):.4f} in the pre-registered "
                          f"direction, but NOT decisive (smallest detectable "
                          f"{md} > effect under test {eff:.3f}).  Section 5 "
                          f"has no label for this combination.")
    return out


def apply_negative_control_veto(labels, control_p):
    """Section 3 'N': if phot_g_n_obs reaches p < 0.05, no D1-D4 positive
    may be reported as a finding until the control is explained."""
    vetoed = (control_p is not None and np.isfinite(control_p)
              and float(control_p) < ALPHA)
    if not vetoed:
        return labels, False
    for r in labels:
        if r["label"].startswith("POSITIVE"):
            r["label"] = r["label"] + " -- VETOED by the negative control"
            r["reason"] += (f"  [negative control phot_g_n_obs p="
                            f"{float(control_p):.4f} < 0.05: section 3 "
                            f"forbids reporting this as a finding]")
    return labels, True


def format_label(r):
    p = r["p_holm"]
    ps = "  --  " if p is None or not np.isfinite(p) else f"{float(p):.4f}"
    md = r["min_detectable"]
    ms = " -- " if md is None or not np.isfinite(md) else f"{float(md):.3f}"
    ef = r["effect"]
    es = " -- " if ef is None or not np.isfinite(ef) else f"{float(ef):+.3f}"
    return (f"  {r['test']}  {r['analysis']:<10s} "
            f"n={r['n_conf']:>4d}+{r['n_spur']:<4d}  p_holm={ps}  "
            f"eff={es}  min_det={ms}  dec={'Y' if r['decisive'] else 'n'}"
            f"  ->  {r['label']}")


# ======================================================================
def selftest(verbose=True):
    """TOTALITY: every label the registration names, plus every case it does
    NOT name, produced from a hand-built input.  The scenario rehearsal
    proves the labels are reachable from real numbers; this proves the
    function is total and deterministic, which is a different claim and the
    one that has to hold on a day nobody expected.
    """
    cases = [
        ("POSITIVE", dict(test="D2", analysis="primary", n_conf=633,
                          n_spur=347, p_holm=0.001, observed_effect=0.66,
                          min_detectable=0.575)),
        ("POSITIVE (conservative, pooled)",
         dict(test="D2", analysis="pooled", n_conf=633, n_spur=347,
              p_holm=0.001, observed_effect=0.66, min_detectable=0.575)),
        ("NULL", dict(test="D2", analysis="primary", n_conf=633, n_spur=347,
                      p_holm=0.9, observed_effect=0.50,
                      min_detectable=0.575)),
        ("UNDERPOWERED", dict(test="D2", analysis="primary", n_conf=40,
                              n_spur=20, p_holm=0.9, observed_effect=0.52,
                              min_detectable=0.78)),
        ("DIRECTION REVERSAL",
         dict(test="D2", analysis="primary", n_conf=633, n_spur=347,
              p_holm=0.001, observed_effect=0.33, min_detectable=0.575)),
        ("NOT TESTABLE", dict(test="D2", analysis="primary", n_conf=5,
                              n_spur=4, p_holm=np.nan,
                              observed_effect=np.nan,
                              min_detectable=np.nan)),
        ("NOT TESTABLE", dict(test="D3", analysis="primary", n_conf=300,
                              n_spur=200, p_holm=np.nan,
                              observed_effect=np.nan, min_detectable=np.nan,
                              joined_rows=0)),
        ("POSITIVE (not decisive)",
         dict(test="D2", analysis="primary", n_conf=8, n_spur=8,
              p_holm=0.01, observed_effect=0.95, min_detectable=0.90)),
        ("POOLED: UNINTERPRETABLE (diluted)",
         dict(test="D3", analysis="pooled", n_conf=633, n_spur=347,
              p_holm=0.4, observed_effect=0.49, min_detectable=0.575)),
        ("DIRECTION REVERSAL (pooled, not interpretable)",
         dict(test="D3", analysis="pooled", n_conf=633, n_spur=347,
              p_holm=0.001, observed_effect=0.66, min_detectable=0.575)),
    ]
    ok = True
    for want, kw in cases:
        got = assign_label(**kw)
        good = got["label"] == want
        ok &= good
        if verbose:
            print(f"  {'OK ' if good else 'FAIL'}  expected {want:<46s} "
                  f"got {got['label']}"
                  + (f"  [{got['defect']}]" if got["defect"] else ""))
    # the veto
    labs = [assign_label(test="D2", analysis="primary", n_conf=633,
                         n_spur=347, p_holm=0.001, observed_effect=0.66,
                         min_detectable=0.575)]
    labs, vetoed = apply_negative_control_veto(labs, 0.01)
    v_ok = vetoed and "VETOED" in labs[0]["label"]
    ok &= v_ok
    if verbose:
        print(f"  {'OK ' if v_ok else 'FAIL'}  negative-control veto: "
              f"{labs[0]['label']}")
    # determinism
    a = assign_label(test="D4", analysis="primary", n_conf=554, n_spur=304,
                     p_holm=0.001, observed_effect=0.22,
                     min_detectable=0.35, rate_conf=0.076)
    b = assign_label(test="D4", analysis="primary", n_conf=554, n_spur=304,
                     p_holm=0.001, observed_effect=0.22,
                     min_detectable=0.35, rate_conf=0.076)
    d_ok = a == b
    ok &= d_ok
    if verbose:
        print(f"  {'OK ' if d_ok else 'FAIL'}  deterministic on repeat "
              f"({a['label']}"
              + (f", {a['defect']}" if a["defect"] else "") + ")")
    print("SELFTEST", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
