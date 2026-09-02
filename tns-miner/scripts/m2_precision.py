"""M2 step 2: record the hand-vetting classifications and compute precision.

The classifications below were made by reading the evidence sheets in out/vet/
against the rubric frozen in M2-01-preregistration.md Part A3, one object at a
time, first-rule-that-fires-wins.  The rule that fired and the evidence are
recorded per object so any human can re-check the call.

Statistics are exactly those pre-registered in M2-01 A4:
  * per-stratum Wilson 95%;
  * whole-list stratified estimate with a finite-population correction
    (tiers A and B are censuses, so they contribute no sampling variance);
  * strict (undecidable = not a transient) and lenient (undecidable dropped).

usage: python m2_precision.py [tag]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cache_contract import validated_tag  # noqa: E402
from tnscommon import OUT, write_text  # noqa: E402

Z = 1.959964

# oid, class, rule, evidence note  ------------------------------------------- #
# classes: plausible_transient | known_variable | artifact | undecidable
VETTING = [
 ("ZTF19acbplek", "plausible_transient", "R3",
  "compact clean positive PSF in the difference, no dipole; NO Gaia DR3 source "
  "within 3 arcsec and no VSX/ATLAS-VS/Gaia-var match at all; PS1 point source at "
  "0.11 arcsec with magnr=21.88, so quiescence is below Gaia's limit; episodic "
  "detections at 17.7-19.6 in clusters separated by months-to-years, returning to "
  "non-detection between them. Textbook uncatalogued dwarf nova."),
 ("ZTF20abmrpsq", "known_variable", "R2b",
  "251 alerts, continuously detected 18.8-20.4 for six years with no quiescent "
  "floor and repeated comparable-amplitude excursions; Gaia DR3 vclassre says AGN "
  "at 0.19 arcsec; blue (BP-RP=0.45), |b|=45 deg."),
 ("ZTF18abobdzu", "known_variable", "R2c",
  "Mira trap, all three conditions: 2MASS J-K=1.69 (>1.0), Gaia BP-RP=5.18 (>2.0), "
  "slow undulation on multi-hundred-day timescales. 700 alerts continuously "
  "detected for seven years, no quiescent floor (R2b also fires). ATLAS-VS "
  "counterpart at 0.39 arcsec. G=12.70. M1's single best candidate is a red LPV."),
 ("ZTF19aaxsbas", "known_variable", "R2c",
  "Mira trap: J-K=1.26, BP-RP=2.64, hundred-day timescales; 226 alerts, "
  "persistent, no floor (R2b also fires); ATLAS-VS at 0.44 arcsec."),
 ("ZTF18abbsyyw", "artifact", "R1a",
  "difference stamp shows a large positive lobe with an adjacent deep negative "
  "lobe just below-left of the position -- a classic astrometric/PSF subtraction "
  "dipole on a bright star; a second dipole bottom-right. Independently also a red "
  "variable (VSX type VAR at 4.24 arcsec, BP-RP=4.32, J-K=1.67)."),
 ("ZTF18abutckp", "known_variable", "R2b",
  "535 alerts, dense, repeated ~1.5 mag cycles on a several-hundred-day period "
  "over seven years, never returning to a quiescent floor; ATLAS-VS at 0.32 arcsec."),
 ("ZTF18abbdqqd", "artifact", "R1a",
  "the position sits on the edge of a saturated-star mask; the difference stamp is "
  "a field of strong bipolar residuals with the saturation block in the middle. "
  "The light curve also shows a single-epoch vertical stripe of alerts at MJD "
  "60500 spanning 1.3 mag, a second artifact signature."),
 ("ZTF20abvccny", "artifact", "R1a",
  "positive source at the position with a deep adjacent negative lobe immediately "
  "below -- bipolar residual off the bright neighbour 2 arcsec away. Underlying "
  "star is a nearby M dwarf (Gaia Plx=5.96 mas, BP-RP=3.03); only 4 alerts."),
 ("ZTF22aaqkjgl", "plausible_transient", "R3",
  "compact clean positive PSF, no dipole; no VSX/ATLAS-VS/Gaia-var match; single "
  "monotonic ~2 mag rise over ~400 d from 20.5 to 18.5 then a plateau -- a genuine "
  "excursion from a definable baseline, not repeated. CAVEAT recorded at vetting "
  "time: a 400-day rise is not nova-shaped; AGN turn-on or a slow symbiotic are "
  "live alternatives, and R2b does not fire only because the rise is not repeated."),
 ("ZTF18abigckz", "artifact", "R1a",
  "positive core with a deep negative lobe directly below at the position; a "
  "saturated blob at the top of the stamp and a second strong dipole at right. "
  "Also red (BP-RP=3.91, J-K=1.67) with an ATLAS-VS match at 0.95 arcsec."),
 ("ZTF18absvftl", "artifact", "R1a",
  "textbook dipole: positive lobe at the position, deep negative lobe immediately "
  "below-left. 259 alerts, persistent, no floor."),
 ("ZTF18aazlttw", "artifact", "R1a",
  "positive at the position with an adjacent negative lobe above-left. Also a red "
  "LPV by colour (BP-RP=3.74, J-K=1.50), so R2c would have fired next."),
 ("ZTF19aarybaz", "artifact", "R1a",
  "positive core with a negative lobe immediately left; more dipoles bottom-right. "
  "ATLAS-VS class IRR at 0.67 arcsec; persistent light curve with no floor."),
 ("ZTF18abcjbfn", "artifact", "R1a",
  "large positive lobe with an adjacent deep negative blob directly below at the "
  "position, plus a second dipole to the left -- bad subtraction on a bright star. "
  "ATLAS-VS at 0.49 arcsec, 292 alerts, persistent."),
 ("ZTF20aawakdv", "known_variable", "R2b",
  "209 alerts, continuously detected for six years, wandering by ~2 mag with "
  "repeated comparable-amplitude excursions and no quiescent floor; Gaia Plx=8.77 "
  "mas -- a nearby star ~115 pc away, i.e. a long-period/irregular variable, not a "
  "transient. ATLAS-VS at 0.79 arcsec."),
 ("ZTF21aamxwne", "known_variable", "R2b",
  "step up in 2024 then 900 days of continuous detection at 19.7-20.2 with "
  "repeated ~0.5 mag excursions and no return to the pre-rise level; blue "
  "(BP-RP=0.73), Plx~0, sits ~2 arcsec off a resolved galaxy visible in the "
  "science and template stamps. No clean PSF is visible in the difference stamp "
  "either, so R3a would also have failed."),
 ("ZTF20aarepnp", "artifact", "R1c",
  "the difference source is not a clean positive PSF: a negative core ringed by a "
  "positive halo -- a PSF-mismatch residual. 1233 alerts, continuous for seven "
  "years, no floor."),
 ("ZTF19aadtsew", "artifact", "R1a",
  "strong positive lobe with a deep negative lobe below-left at the position, and a "
  "large negative blob at the top of the stamp. Light curve also brightens "
  "monotonically from 18 to 16 over six years -- a slow variable, not an event."),
 ("ZTF23aagepgc", "known_variable", "R2b",
  "230 alerts, continuously detected across four seasons at 19.6-20.4 with "
  "repeated ~0.6 mag excursions and no quiescent floor; M1 amplitude is -0.35, "
  "i.e. the variation is fainter than the star it sits on."),
 ("ZTF19abbuwnp", "known_variable", "R2b",
  "283 alerts, continuous over five years, r 18.8-19.3 and g 19.3-19.8, no floor; "
  "strong dipoles elsewhere in the stamp but not at the position."),
 ("ZTF18abeaikl", "known_variable", "R2b",
  "381 alerts, repeated smooth ~1.4 mag cycles over six years with no floor; Gaia "
  "DR3 vclassre says AGN at 0.48 arcsec; ATLAS-VS at 0.48 arcsec."),
 ("ZTF20acpbjsv", "known_variable", "R2b",
  "130 alerts, continuously detected at 19.3-20.2 over five years, no floor; "
  "M1 amplitude -0.50."),
 ("ZTF23abiabmy", "known_variable", "R2b",
  "140 alerts, dense over three seasons at 17.0-18.7 with no quiescent floor; "
  "ATLAS-VS at 0.35 arcsec; Gaia Plx=1.22 mas."),
 ("ZTF18abdjpfo", "known_variable", "R2b",
  "1602 alerts -- one of the most-observed objects in the list -- continuously "
  "detected for seven years with no floor; ATLAS-VS class IRR at 0.36 arcsec."),
 ("ZTF20acxmvxu", "known_variable", "R2b",
  "239 alerts, slow persistent brightening 19.5 -> 18.5 over 1500 d with repeated "
  "excursions and no floor; no clean PSF visible in the difference stamp either."),
 ("ZTF19abrqdjs", "artifact", "R1a",
  "positive lobe at the position with a deep negative lobe immediately to its "
  "right; two further dipoles in the same stamp."),
 ("ZTF21aapnhfv", "known_variable", "R2b",
  "the difference source is ~2 mag FAINTER than the quiescent star it sits on "
  "(magnr=17.22 vs magpsf~19.5), i.e. a ~0.14 mag total brightening; 300 days of "
  "continuous detection with ~0.6 mag scatter and no floor. Low-amplitude "
  "variability, not an outburst -- R3c fails outright."),
 ("ZTF19abiiveh", "known_variable", "R2b",
  "38 sparse alerts wandering 18.5-20.4 over seven years with no floor; magnr=17.35 "
  "so the excursion is ~0.18 mag on the underlying star. R3c fails."),
 ("ZTF18abbslas", "artifact", "R1c",
  "the difference source is a bloated positive blob ringed with negative, several "
  "times the width of the other point sources in the stamp, with saturation masks "
  "in the corners -- a bright-star residual, not a PSF. ATLAS-VS class IRR at "
  "0.32 arcsec; 331 alerts, persistent."),
 ("ZTF19aauabwo", "known_variable", "R2b",
  "113 alerts, sparse then 300 days of dense continuous detection at 18.3-19.7 "
  "with no floor; magnr=16.53, so the excursion is ~0.2 mag on the star."),
 ("ZTF22aaolizp", "known_variable", "R2b",
  "94 alerts, continuously detected at 19.0-19.6 over 1500 d, no floor; "
  "magnr=17.41, M1 amplitude -1.42."),
 ("ZTF18abifvxf", "known_variable", "R2c",
  "Mira trap: J-K=1.89, BP-RP=5.59, variation over years; 74 r-band alerts "
  "wandering 17.8-19.0 across seven years. |b|=2.3 deg."),
 ("ZTF18ablpbnm", "known_variable", "R2c",
  "Mira trap: J-K=1.75, BP-RP=5.18, multi-hundred-day timescales; 159 alerts "
  "continuous for seven years; ATLAS-VS at 0.47 arcsec; |b|=3.0 deg."),
 ("ZTF22abwkjwg", "known_variable", "R2b",
  "160 alerts pinned at 18.6-19.0 for 1300 d with no floor, plus a single-epoch "
  "vertical stripe of alerts at MJD 60500 spanning 0.8 mag."),
 ("ZTF19aattoit", "known_variable", "R2c",
  "Mira trap: J-K=1.78, BP-RP=5.05; 43 alerts scattered 18.0-19.5 over seven "
  "years. |b|=3.4 deg. No clean difference source visible either."),
 ("ZTF20abgcjru", "artifact", "R1a",
  "deep negative blob immediately left of the position with the positive lobe at "
  "the position -- bipolar residual; a second dipole below-right."),
 ("ZTF18ababkvk", "artifact", "R1a",
  "positive at the position with a deep negative lobe directly below; further "
  "dipoles up-right. 323 alerts, persistent."),
 ("ZTF18ablohbh", "artifact", "R1a",
  "a dipole sits on the position and the whole stamp is peppered with bipolar "
  "residuals -- a globally bad subtraction; a saturation mask in the corner."),
 ("ZTF19abhhdhc", "undecidable", "R4",
  "no clean PSF visible in the difference stamp, so R3a cannot be confirmed; only "
  "11 alerts over five years, too few for R2b; magnr=17.36 against a difference "
  "magnitude of ~19.5, i.e. a ~0.15 mag excursion, so R3c fails as well. The "
  "template shows a blended blob at the position. Evidence insufficient either way."),
 ("ZTF18aaxykvr", "artifact", "R1a",
  "large positive lobe with a deep negative lobe immediately to its left, plus a "
  "very large bipolar complex at the top-left of the stamp. ATLAS-VS at 0.43 "
  "arcsec; BP-RP=2.75, J-K=1.27."),
]


def wilson(k: int, n: int) -> tuple[float, float, float]:
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    p = k / n
    den = 1 + Z * Z / n
    ctr = (p + Z * Z / (2 * n)) / den
    half = Z * np.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / den
    return p, max(0.0, ctr - half), min(1.0, ctr + half)


def run(tag: str = "m1list") -> dict:
    tag = validated_tag(tag)
    sample = pd.read_csv(OUT / "m2_vet_sample.csv") if tag == "m1list" else None
    v = pd.DataFrame(VETTING, columns=["oid", "vet_class", "rule", "evidence"])
    if sample is not None:
        v = v.merge(sample[["oid", "stratum", "channel", "gal_b", "mag_at_pass",
                            "outburst_amp", "ptp_mag_60d", "ra", "dec"]],
                    on="oid", how="left")
    v.to_csv(OUT / "m2_vetting.csv", index=False, lineterminator="\n")

    N = {"A": 3, "B": 5, "C": 176}
    Ntot = sum(N.values())
    out = {"population": Ntot, "n_vetted": len(v),
           "class_counts": v["vet_class"].value_counts().to_dict(),
           "rule_counts": v["rule"].value_counts().to_dict(), "strata": {}}

    strat = {}
    for h in ("A", "B", "C"):
        g = v[v["stratum"] == h]
        n_all = len(g)
        k = int((g["vet_class"] == "plausible_transient").sum())
        n_und = int((g["vet_class"] == "undecidable").sum())
        p_s, lo_s, hi_s = wilson(k, n_all)                    # strict
        p_l, lo_l, hi_l = wilson(k, n_all - n_und)            # lenient
        strat[h] = {"N": N[h], "n": n_all, "n_plausible": k, "n_undecidable": n_und,
                    "census": n_all == N[h],
                    "counts": g["vet_class"].value_counts().to_dict(),
                    "strict": {"p": p_s, "wilson95": [lo_s, hi_s]},
                    "lenient": {"p": p_l, "wilson95": [lo_l, hi_l]}}
    out["strata"] = strat

    for mode in ("strict", "lenient"):
        P = var = 0.0
        lo_b = hi_b = 0.0
        for h, s in strat.items():
            w = s["N"] / Ntot
            p = s[mode]["p"]
            n = s["n"] - (s["n_undecidable"] if mode == "lenient" else 0)
            P += w * p
            if not s["census"]:
                fpc = 1 - n / s["N"]
                var += w * w * (p * (1 - p) / n) * fpc
                lo_b += w * s[mode]["wilson95"][0]
                hi_b += w * s[mode]["wilson95"][1]
            else:
                lo_b += w * p
                hi_b += w * p
        sd = float(np.sqrt(var))
        out[mode] = {
            "precision": round(P, 5),
            "stratified_normal_95": [round(max(0.0, P - Z * sd), 5),
                                     round(min(1.0, P + Z * sd), 5)],
            "stratified_wilson_95": [round(max(0.0, lo_b), 5),
                                     round(min(1.0, hi_b), 5)],
            "sd": round(sd, 5),
        }

    # pre-registered decision rules (M2-01 A5)
    out["decision_A5_list"] = (
        "NOT SUBMITTABLE" if out["strict"]["stratified_wilson_95"][1] < 0.20
        else "submittable-as-a-list not ruled out")
    ab = v[v["stratum"].isin(["A", "B"])]
    n_ab = int((ab["vet_class"] == "plausible_transient").sum())
    out["decision_A5_triage"] = {
        "n_plausible_in_tiers_AB": n_ab,
        "verdict": "M1-05 triage NOT WORKING" if n_ab < 2 else "triage holds"}
    return out


def main() -> None:
    tag = validated_tag(sys.argv[1] if len(sys.argv) > 1 else "m1list")
    res = run(tag)
    write_text(OUT / "m2_precision.json", json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
