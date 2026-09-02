"""M2 step 5 (M2-01 A6): the same rubric and the same evidence, applied to the
FIXED filter's output.

Population: out/m2_candidates_recent.csv (37 objects).  Because 37 > 25, a random
sample of 25 was drawn with seed 20260825 under the identical procedure, exactly
as A6 pre-registered.  Classifications were made from out/vet/m2list_sheet*.png
against the rubric of M2-01 A3, first rule that fires wins.

Reports the pre-registered precision (numerator = plausible_transient only) AND,
separately and never inside it, the known_cv_outburst sub-tally A0 promised: a
real astrophysical outburst that the filter found and correctly flagged, but on an
object that already has a designation and therefore must not be filed as an AT
report.

usage: python m2_precision_final.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cache_contract import load_proved_output  # noqa: E402
from m2_precision import run as run_m1, wilson  # noqa: E402
from tnscommon import OUT, write_text  # noqa: E402

VETTING_M2 = [
 ("ZTF18abimytv", "known_variable", "R2b",
  "VSX YSO at 0.16 arcsec AND Gaia DR3 vclassre YSO at 0.13 arcsec; 366 alerts, "
  "continuously detected 16-19 for seven years with repeated comparable-amplitude "
  "excursions and no quiescent floor. A genuine young stellar object."),
 ("ZTF19aaocygn", "known_variable", "R2c",
  "red-variable trap: J-K=2.70, BP-RP=2.82, multi-hundred-day timescales; VSX YSO "
  "at 0.25 arcsec and Gaia vclassre YSO at 0.24 arcsec; 298 alerts, persistent, "
  "no floor, so R2b fires as well."),
 ("ZTF24abuzrht", "plausible_transient", "R3",
  "faint but centred positive source in the difference, no dipole and no residual "
  "structure; no VSX / ATLAS-VS / Gaia-variability match at all; 9 alerts over 30 "
  "days at 19.1-20.2 against a reference at ~21.5, a 2.6 mag excursion from a "
  "definable baseline. CAVEAT recorded at vetting time: |b| = -79.5 deg, so far "
  "out of the plane that a faint supernova is at least as likely as a CV."),
 ("ZTF19adhngbf", "known_variable", "R2b",
  "80 alerts at 19.2-20.2 in clusters across five years with no quiescent floor. "
  "Two strong bipolar residuals elsewhere in the stamp but nothing visible at the "
  "position itself, so R3a would also have failed."),
 ("ZTF18abvosgm", "known_variable", "R2b",
  "the position sits on the disc of a resolved edge-on galaxy visible in both the "
  "science and template stamps; 30 alerts at 18.8-19.6 spread over six years with "
  "no floor. The VSX UG match is 4.79 arcsec away and does not plausibly belong "
  "to this source."),
 ("ZTF24abuztdc", "undecidable", "R4",
  "no clean PSF visible in the difference stamp at mag 19.8 with sigma=6.9, so "
  "R3a cannot be confirmed; 7 alerts over 350 days is too few for R2b. Evidence "
  "insufficient either way."),
 ("ZTF18acvmvpg", "known_cv_outburst", "R2-subtally",
  "VSX type UG at 0.81 arcsec, a catalogued U Gem dwarf nova. 63 alerts showing "
  "textbook repeated outbursts to 15.9-16.5 with quiescent gaps between, and it "
  "is erupting again now, 3.8 mag above quiescence. A real event, correctly found "
  "and correctly flagged known_cv, but not a new object."),
 ("ZTF19acbplek", "plausible_transient", "R3",
  "the object the M2-02 vetting also identified, re-vetted independently here on "
  "the current episode: compact positive source, no VSX / ATLAS-VS / Gaia-var "
  "match, no Gaia DR3 counterpart at all, PS1 reference magnitude 21.8, episodic "
  "clusters at 17.7-19.9 over seven years returning to non-detection between "
  "them, 3.69 mag above quiescence. Uncatalogued dwarf nova."),
 ("ZTF18abzvuub", "known_cv_outburst", "R2-subtally",
  "VSX type UG at 0.07 arcsec. 26 alerts in three clean outburst clusters "
  "(MJD 60520, 60850, 61265) reaching 16.4-16.7 with nothing in between: a "
  "textbook dwarf nova, already catalogued."),
 ("ZTF23aajtssy", "known_variable", "R2b",
  "313 alerts, continuously detected from MJD 60100, rising 20.5 to 19.1 and "
  "staying there, with repeated excursions and no quiescent floor; BP-RP=0.07 "
  "(very blue), no significant parallax, |b| = -27.5 deg. AGN-shaped."),
 ("ZTF19aarylmv", "artifact", "R1a",
  "positive lobe at the position with a deep adjacent negative lobe immediately "
  "to its right, plus a large bipolar complex up-right and another below. VSX "
  "type UG: at 0.15 arcsec, so also a catalogued CV, but the difference stamp at "
  "the trigger epoch is a subtraction residual."),
 ("ZTF19aafohks", "known_cv_outburst", "R2-subtally",
  "VSX type UG at 0.04 arcsec AND Gaia DR3 vclassre CV at 0.03 arcsec. 56 alerts "
  "in outburst clusters at 18.9-20.5 across seven years. Channel D, |b| = 14.2 "
  "deg. Real, catalogued, not new."),
 ("ZTF21abfxngg", "known_variable", "R2b",
  "262 alerts, continuously detected at 19.3-20.3 for six years with no quiescent "
  "floor; BP-RP=0.45, parallax consistent with zero, |b| = -58.6 deg. AGN-shaped, "
  "though nothing catalogues it."),
 ("ZTF18abmirqr", "artifact", "R1a",
  "positive core at the position with a deep negative lobe directly above and a "
  "second dipole up-right. VSX type UG at 0.06 arcsec, and the light curve is "
  "continuously detected at 18.0-20.5 for seven years rather than episodic, i.e. "
  "nova-like / Z Cam behaviour, not an isolated outburst."),
 ("ZTF20ackoxkt", "known_variable", "R2b",
  "Gaia DR3 vclassre AGN at 0.16 arcsec; 43 alerts at 19.8-20.8 over six years "
  "with no quiescent floor; parallax consistent with zero, |b| = -76.1 deg."),
 ("ZTF20abmkdhu", "known_variable", "R2b",
  "Gaia DR3 vclassre AGN at 0.37 arcsec; 37 alerts at 19.7-20.4 over six years, "
  "no floor; |b| = -51.2 deg."),
 ("ZTF21abjznrj", "known_variable", "R2b",
  "Gaia DR3 vclassre AGN at 0.19 arcsec; 260 alerts, persistent 19.0-20.3 over "
  "six years, no floor; BP-RP=0.53, |b| = -37.1 deg."),
 ("ZTF19abdrtby", "known_variable", "R2b",
  "Gaia DR3 vclassre AGN at 0.18 arcsec; 567 alerts of classic stochastic "
  "wandering between 18.7 and 20.0 over six years with no floor."),
 ("ZTF20abmrpsq", "known_variable", "R2b",
  "Gaia DR3 vclassre AGN at 0.27 arcsec; 251 alerts, persistent 18.8-20.4 over "
  "six years, no floor. The same object the M2-02 vetting classed as an AGN, "
  "reached independently here."),
 ("ZTF18aafeggh", "known_cv_outburst", "R2-subtally",
  "VSX type UG at 0.08 arcsec AND Gaia DR3 vclassre CV at 0.1 arcsec. Only 4 "
  "alerts, ALL from MJD 61274.5-61275.5: a fresh outburst caught in the act at "
  "3.8 mag above a reference at 21.1, on the night the pass was run. Exactly what "
  "the outburst enumerator was built to find. Catalogued, so not an AT report."),
 ("ZTF18abmipkc", "known_cv_outburst", "R2-subtally",
  "VSX type NL at 0.59 arcsec (nova-like) AND Gaia vclassre CV at 0.27 arcsec; "
  "680 alerts, persistent 17-20 over seven years."),
 ("ZTF18abifuem", "known_cv_outburst", "R2-subtally",
  "VSX type ZAND at 0.19 arcsec (symbiotic) AND Gaia vclassre SYST at 0.1 arcsec "
  "AND an ATLAS-VS counterpart at 0.12 arcsec; BP-RP=4.03, J-K=1.82; 686 alerts "
  "of huge repeated 15-20 mag cycles. A catalogued symbiotic star."),
 ("ZTF18adodmcb", "known_cv_outburst", "R2-subtally",
  "VSX type UG at 0.15 arcsec; 65 alerts showing repeated clean dwarf-nova "
  "outbursts between 17.5 and 20 with quiescent gaps."),
 ("ZTF18abcgnpe", "artifact", "R1c",
  "the difference source is a bloated blob many times the width of the other "
  "point sources in the stamp: a bright-star residual, not a PSF, on a star at "
  "r = 12-14. Independently a long-period variable (VSX ZAND at 0.16 arcsec, "
  "ATLAS-VS LPV at 0.08 arcsec, Gaia vclassre LPV at 0.06 arcsec, BP-RP=3.21, "
  "J-K=1.52), so R2c would have fired next."),
 ("ZTF18absgnqy", "known_cv_outburst", "R2-subtally",
  "VSX type AM at 0.13 arcsec (AM Her polar) AND Gaia vclassre CV at 0.1 arcsec; "
  "638 alerts switching between a 16.5-17 high state and a 19-19.5 low state. "
  "A catalogued magnetic CV."),
]


def run_m2() -> dict:
    v = pd.DataFrame(VETTING_M2, columns=["oid", "vet_class", "rule", "evidence"])
    candidate_path = OUT / "m2_candidates_recent.csv"
    proof = load_proved_output(
        candidate_path,
        candidate_path.with_suffix(".json"),
        kind="m2_candidate_output",
    )
    cand = pd.read_csv(candidate_path)
    if len(cand) != int(proof["row_count"]):
        raise RuntimeError(f"candidate output row-count mismatch: {candidate_path}")
    v = v.merge(cand[["oid", "rank_score", "channel", "gal_b", "mag_at_pass",
                      "amp", "ptp_band", "flag_known_cv", "arm", "ra", "dec"]],
                on="oid", how="left")
    v.to_csv(OUT / "m2_vetting_final.csv", index=False, lineterminator="\n")
    N, n = len(cand), len(v)
    k = int((v["vet_class"] == "plausible_transient").sum())
    n_und = int((v["vet_class"] == "undecidable").sum())
    n_cv = int((v["vet_class"] == "known_cv_outburst").sum())
    p_s, lo_s, hi_s = wilson(k, n)
    p_l, lo_l, hi_l = wilson(k, n - n_und)
    p_e, lo_e, hi_e = wilson(k + n_cv, n)
    return {
        "population": N, "n_vetted": n, "sample_seed": 20260825,
        "class_counts": v["vet_class"].value_counts().to_dict(),
        "rule_counts": v["rule"].value_counts().to_dict(),
        "strict": {"precision": round(p_s, 5),
                   "wilson95": [round(lo_s, 5), round(hi_s, 5)]},
        "lenient": {"precision": round(p_l, 5),
                    "wilson95": [round(lo_l, 5), round(hi_l, 5)]},
        "real_event_rate": {
            "k": k + n_cv, "n": n, "rate": round(p_e, 5),
            "wilson95": [round(lo_e, 5), round(hi_e, 5)],
            "note": "plausible_transient + known_cv_outburst. A real "
                    "astrophysical outburst was found and correctly "
                    "characterised, but the known_cv part is NOT a new object "
                    "and must not be filed as an AT report. Reported separately "
                    "and never inside precision, exactly as M2-01 A0 required."},
        "plausible": v.loc[v["vet_class"] == "plausible_transient", "oid"].tolist(),
    }


def main() -> None:
    res = {"M1_list": run_m1("m1list"), "M2_list": run_m2()}
    write_text(OUT / "m2_precision.json", json.dumps(res, indent=2))
    m, o = res["M2_list"], res["M1_list"]
    print("M1 list  strict precision:", o["strict"]["precision"],
          o["strict"]["stratified_wilson_95"])
    print("M2 list  strict precision:", m["strict"]["precision"],
          m["strict"]["wilson95"])
    print("M2 list  lenient         :", m["lenient"]["precision"],
          m["lenient"]["wilson95"])
    print("M2 real-event rate       :", m["real_event_rate"]["rate"],
          m["real_event_rate"]["wilson95"])
    print("M1 classes:", o["class_counts"])
    print("M2 classes:", m["class_counts"])
    print("plausible :", m["plausible"])


if __name__ == "__main__":
    main()
