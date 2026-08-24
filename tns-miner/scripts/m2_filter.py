"""M2 filter -- M1's frozen thresholds plus the four fixes of M2-01 Part B.

Nothing from M1-03 is re-tuned.  M2 ADDS cuts and turns two vetoes into flags.
Every added threshold is pre-registered in M2-01-preregistration.md Part B, fixed
under the same rule M1-03 used, before any recall or precision number was recounted.

The fixes are individually switchable so the cost of each can be measured against
the M1-04 positive control one at a time (see m2_positive_control.py):

  fix_a   amplitude (per band!) + flat-residual veto        [M2-01 B1]
  fix_c1  VSX / GCVS: hard veto -> flag, except periodic types  [M2-01 B3 c1]
  fix_c2  SIMBAD generic classes: hard veto -> flag             [M2-01 B3 c2]
  fix_d   negative-subtraction fraction veto                 [M2-02, POST-HOC]

fix_b, the outburst enumerator, is not a filter cut -- it lives in m2_pool.py.

fix_d is flagged POST-HOC throughout because it was identified from the M2-02
vetting sample rather than pre-registered.  Its threshold is still fixed by rule
(iii) and not by yield, and it is validated out-of-sample on the positive control
and on the fresh vetting of M2-04.  That provenance travels with it everywhere.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

import m1_filter as M1
from m1_filter import (_f, _isnull, gal_b, classify_channel,  # noqa: F401
                       detection_is_clean, N_DET_MIN, DT_MIN_DAYS,
                       GAL_PLANE_ABS_B, TNS_MATCH_ARCSEC)

# --------------------------------------------------------------------------- #
# M2 thresholds -- frozen in M2-01 Part B before any recount
# --------------------------------------------------------------------------- #
AMP_MIN = 1.0                 # (ii)+(iii) M1-05's declared tier A/B line; ~5x the
                              #   ZTF single-epoch scatter at mag 20
NEW_SOURCE_MAX_HIST_DAYS = 90.0   # (iii) A2/B have no quiescent source to measure
                              #   against; a position where PS1 shows nothing but
                              #   ZTF has been detecting for years is a reference
                              #   hole by construction.  90 d is the outer edge of
                              #   a classical nova's detectable decline.
FLAT_PTP_MAX = 0.30           # (ii)+(iii) M1-05's declared flat override; below
                              #   ZTF's own per-epoch scatter at mag ~20
FLAT_MIN_ALERTS = 3
FLAT_WINDOW_DAYS = 60.0
NEG_FRAC_MAX = 0.05           # (iii) POST-HOC.  A source genuinely above its
                              #   reference level cannot produce a NEGATIVE
                              #   high-confidence difference detection.  A few are
                              #   reference noise; more than one in twenty means
                              #   the source spends real time BELOW its reference,
                              #   which is variability about a mean, not an
                              #   outburst above quiescence.  See M2-03 for the
                              #   measured insensitivity across 0.02-0.20.

# VSX / GCVS types whose variability is already known and already published.
# Matched on the type string truncated at the first / : + or ( , upper-cased.
PERIODIC_VETO_TYPES = {
    "M", "SR", "SRA", "SRB", "SRC", "SRD", "SRS", "L", "LB", "LC", "LPV",
    "RR", "RRAB", "RRC", "RRD", "CEP", "DCEP", "DCEPS", "CW", "CWA", "CWB",
    "ACEP", "BCEP", "EA", "EB", "EW", "E", "ED", "ESD", "EC", "ELL", "RS",
    "BY", "DSCT", "HADS", "GDOR", "ACV", "SXPHE", "ROT", "SPB", "ZZ", "ZZA",
    "ZZB", "ZZO", "GCAS", "LPB",
}
# ...and the ones that mean "already a catalogued CV": real outbursts, but NOT new
# objects.  Kept, flagged, and warned about -- never silently promoted.
CV_FAMILY_TYPES = {"UG", "UGSU", "UGSS", "UGZ", "UGWZ", "UGER", "NA", "NB", "NC",
                   "NL", "NR", "N", "ZAND", "AM", "DQ", "CV", "IBWD"}

# SIMBAD classes moved from veto to flag by fix c2: a nova erupting on a
# catalogued star is classed "Star" by SIMBAD, so the M1 veto rejected exactly the
# case the project exists to find.
SIMBAD_DEMOTED = {"Star", "Variable*", "PulsV*", "SB*", "Radio", "X"}
# ...everything else in M1's list stays a hard veto: the specific periodic classes,
# and the extragalactic classes, which the mission scope excludes outright.
SIMBAD_HARD_VETO = M1.KNOWN_VARIABLE_SIMBAD - SIMBAD_DEMOTED


def simbad_head(v) -> str:
    """Strip a trailing '_Candidate' before any class comparison.

    fix (c3), a STRUCTURAL SYMMETRY FIX, no threshold.  M1-03 explicitly handled
    the _Candidate suffix on the TARGET side -- "CataclyV*, Nova, DwarfNova,
    Symbiotic* and their _Candidate forms are targets, not vetoes" -- but never on
    the VETO side.  SIMBAD serves 315 classes and the _Candidate form of nearly
    every one of them, so 'AGN' was vetoed while 'AGN_Candidate', 'Blazar_Candidate',
    'QSO_Candidate', 'LongPeriodV*_Candidate', 'Mira_Candidate' and
    'EclBin_Candidate' all sailed through Layer 3.  Two objects in the M2-02
    vetting sample carry a Gaia DR3 variability class of AGN.
    Stripping the suffix once, here, makes both sides symmetric and adds no
    parameter.  It can only ever REMOVE objects, so its cost is measurable on the
    positive control and is reported in M2-03.
    """
    s = str(v).strip()
    for suf in ("_Candidate", "_candidate"):
        if s.endswith(suf):
            return s[: -len(suf)]
    return s


@dataclass(frozen=True)
class Config:
    fix_a: bool = True
    fix_c1: bool = True
    fix_c2: bool = True
    fix_d: bool = True
    fix_c3: bool = True

    @property
    def label(self) -> str:
        on = [n for n, v in (("a", self.fix_a), ("c1", self.fix_c1),
                             ("c2", self.fix_c2), ("c3", self.fix_c3),
                             ("d", self.fix_d)) if v]
        return "M1 + fix " + "+".join(on) if on else "M1 baseline"


M1_BASELINE = Config(False, False, False, False, False)
M2_FULL = Config(True, True, True, True, True)


# --------------------------------------------------------------------------- #
def _type_head(v) -> str:
    """VSX/GCVS type strings look like 'UGSU', 'EA/RS:', 'M+E', 'SR:'."""
    s = str(v).strip().upper()
    for ch in "/:+(|":
        s = s.split(ch)[0]
    return s.strip()


def catalogue_layer(rows: pd.DataFrame, cfg: Config) -> tuple[bool, str, dict]:
    """Layer 3, as amended by fix c1 and c2.  Returns (keep, why, flags)."""
    flags: dict[str, str] = {}

    for col, label in (("d:vsx", "VSX"), ("d:gcvs", "GCVS")):
        if col not in rows.columns:
            continue
        vals = [v for v in rows[col].tolist() if not _isnull(v)]
        if not vals:
            continue
        v = vals[0]
        head = _type_head(v)
        flags[f"flag_{label.lower()}"] = str(v)
        if not cfg.fix_c1:
            return False, f"already catalogued in {label}: {v}", flags
        if head in PERIODIC_VETO_TYPES:
            return False, (f"{label} type {v} is a catalogued periodic variable "
                           f"-- nothing new to claim"), flags
        if head in CV_FAMILY_TYPES:
            flags["flag_known_cv"] = f"{label}:{v}"

    if "d:tns" in rows.columns:
        vals = [v for v in rows["d:tns"].tolist() if not _isnull(v)]
        if vals:
            return False, f"already in TNS: {vals[0]}", flags

    if "d:cdsxmatch" in rows.columns:
        vals = [str(v).strip() for v in rows["d:cdsxmatch"].tolist()
                if not _isnull(v)]
        for v in vals:
            # fix c3: compare on the class with any trailing "_Candidate" removed,
            # so the veto side is as suffix-aware as M1-03 already made the target
            # side.  Off -> M1's literal-string comparison.
            h = simbad_head(v) if cfg.fix_c3 else v
            if h in M1.TARGET_SIMBAD or v in M1.TARGET_SIMBAD:
                flags["flag_simbad_target"] = v
                continue
            if cfg.fix_c2:
                if h in SIMBAD_DEMOTED:
                    flags["flag_simbad"] = v
                    continue
                if h in SIMBAD_HARD_VETO:
                    return False, f"SIMBAD says {v} (known variable or host)", flags
            else:
                if h in M1.KNOWN_VARIABLE_SIMBAD:
                    return False, f"SIMBAD says {v} (known variable or host)", flags
    return True, "no catalogue veto", flags


def per_band_amplitude(clean: list) -> tuple[float, dict]:
    """amp_f = median(magnr | band f) - min(magpsf | band f); amp = max over bands.

    magnr is the reference-image magnitude of the nearest source IN THAT FILTER.
    M1-05 took median(magnr) over all bands minus min(magpsf) over all bands --
    the same mixed-filter trap it documented for peak-to-peak, one column left.
    """
    by: dict[int, list] = {}
    for r in clean:
        f = int(_f(r, "i:fid", 0))
        by.setdefault(f, []).append(r)
    amps = {}
    for f, rs in by.items():
        mn = [_f(r, "i:magnr") for r in rs]
        mn = [x for x in mn if np.isfinite(x) and 0 < x < 30]
        mp = [_f(r, "i:magpsf") for r in rs]
        mp = [x for x in mp if np.isfinite(x)]
        if mn and mp:
            amps[f] = float(np.median(mn) - min(mp))
    if not amps:
        return float("nan"), {}
    return float(max(amps.values())), {f"amp_fid{f}": round(v, 3)
                                       for f, v in amps.items()}


def per_band_ptp(clean: list, jd_hi: float) -> tuple[float, int]:
    """Largest per-band peak-to-peak over the FLAT_WINDOW_DAYS ending at jd_hi,
    and the largest per-band alert count in that window."""
    by: dict[int, list] = {}
    for r in clean:
        jd = _f(r, "i:jd")
        if np.isfinite(jd) and jd >= jd_hi - FLAT_WINDOW_DAYS:
            by.setdefault(int(_f(r, "i:fid", 0)), []).append(_f(r, "i:magpsf"))
    ptps, nmax = [], 0
    for _f_, mags in by.items():
        mags = [m for m in mags if np.isfinite(m)]
        nmax = max(nmax, len(mags))
        if len(mags) >= 2:
            ptps.append(max(mags) - min(mags))
    return (max(ptps) if ptps else float("nan")), nmax


def negative_fraction(rows: pd.DataFrame) -> tuple[float, int, int]:
    """Fraction of HIGH-CONFIDENCE detections that are negative subtractions.

    POST-HOC (M2-02).  A source above its reference level cannot produce a
    negative high-confidence difference detection; one that does is either a
    registration dipole whose sign flips with the seeing, or a variable star
    dipping below its own reference.  Both are rejects.
    """
    if "i:isdiffpos" not in rows.columns:
        return float("nan"), 0, 0
    drb = pd.to_numeric(rows.get("i:drb"), errors="coerce")
    rb = pd.to_numeric(rows.get("i:rb"), errors="coerce")
    conf = drb.fillna(-1) >= M1.DRB_MIN
    conf = conf | (drb.isna() & (rb.fillna(-1) >= M1.RB_MIN))
    sub = rows[conf]
    if not len(sub):
        return float("nan"), 0, 0
    pos = sub["i:isdiffpos"].astype(str).str.strip().isin(
        ["t", "1", "T", "true", "True"])
    n, nneg = len(sub), int((~pos).sum())
    return nneg / n, nneg, n


# --------------------------------------------------------------------------- #
def evaluate(rows: pd.DataFrame, cfg: Config = M2_FULL,
             jd_cutoff: float | None = None, jd_floor: float | None = None) -> dict:
    """M1's evaluate() with the M2 layers.  Same rewind discipline: only alerts
    with i:jd <= jd_cutoff are ever visible."""
    out = {"passed": False, "channel": None, "reason": "", "first_pass_jd": None,
           "n_clean": 0, "n_alerts": 0, "mag_at_pass": None, "band_at_pass": None,
           "amp": None, "ptp_band": None, "neg_frac": None, "flags": {},
           "hist_span_days": None}
    if rows is None or len(rows) == 0:
        out["reason"] = "no alerts"
        return out

    rows = rows.copy()
    rows["i:jd"] = pd.to_numeric(rows["i:jd"], errors="coerce")
    rows = rows.dropna(subset=["i:jd"]).sort_values("i:jd")
    if jd_cutoff is not None:
        rows = rows[rows["i:jd"] <= jd_cutoff]
    if jd_floor is not None:
        rows = rows[rows["i:jd"] >= jd_floor]
    out["n_alerts"] = len(rows)
    if len(rows) == 0:
        out["reason"] = "no alerts before the cutoff"
        return out

    keep, why, flags = catalogue_layer(rows, cfg)
    out["flags"] = flags
    if not keep:
        out["reason"] = why
        return out

    clean = [r for _, r in rows.iterrows() if detection_is_clean(r)[0]]
    out["n_clean"] = len(clean)
    if len(clean) < N_DET_MIN:
        out["reason"] = f"only {len(clean)} clean detection(s), need {N_DET_MIN}"
        return out

    jds = [float(r["i:jd"]) for r in clean]
    if max(jds) - min(jds) < DT_MIN_DAYS:
        out["reason"] = (f"clean detections span {max(jds)-min(jds):.4f} d "
                         f"< {DT_MIN_DAYS} d -- cannot exclude a mover")
        return out

    trigger = None
    for i in range(1, len(clean)):
        if float(clean[i]["i:jd"]) - float(clean[0]["i:jd"]) >= DT_MIN_DAYS:
            trigger = clean[i]
            break
    if trigger is None:
        out["reason"] = "no pair of clean detections with a 30 min baseline"
        return out

    chan, why_c = classify_channel(trigger)
    if chan is None:
        bright = min(clean, key=lambda r: _f(r, "i:magpsf", 99))
        chan, why_c = classify_channel(bright)
        if chan is None:
            out["reason"] = why_c
            return out
        trigger = bright

    # ---- measurements (always computed, so they can be reported even on a fail)
    amp, amp_by = per_band_amplitude(clean)
    jd_trig = float(trigger["i:jd"])
    ptp, n_win = per_band_ptp(clean, jd_trig)
    negf, n_neg, n_conf = negative_fraction(rows)
    jsh = _f(trigger, "i:jdstarthist")
    span = (jd_trig - jsh) if np.isfinite(jsh) else float("nan")
    out.update({"amp": None if not np.isfinite(amp) else round(amp, 3),
                "amp_by_band": amp_by,
                "ptp_band": None if not np.isfinite(ptp) else round(ptp, 3),
                "n_alerts_60d_maxband": n_win,
                "neg_frac": None if not np.isfinite(negf) else round(negf, 4),
                "n_neg": n_neg, "n_conf": n_conf,
                "hist_span_days": None if not np.isfinite(span) else round(span, 2)})

    # ---- fix (d): negative-subtraction veto  [POST-HOC, M2-02]
    if cfg.fix_d and np.isfinite(negf) and negf > NEG_FRAC_MAX:
        out["reason"] = (f"{n_neg}/{n_conf} = {negf:.1%} of high-confidence "
                         f"detections are NEGATIVE subtractions (> {NEG_FRAC_MAX:.0%}) "
                         f"-- dipole or variability about a mean, not an outburst")
        return out

    # ---- fix (a): amplitude / new-source, and the flat-residual veto
    if cfg.fix_a:
        needs_new = chan.startswith("A2") or chan.startswith("B_")
        if needs_new:
            if np.isfinite(span) and span > NEW_SOURCE_MAX_HIST_DAYS:
                out["reason"] = (f"channel {chan} but ZTF has been detecting this "
                                 f"position for {span:.0f} d (> "
                                 f"{NEW_SOURCE_MAX_HIST_DAYS:.0f} d) -- not a new "
                                 f"source, a reference-image hole")
                return out
        else:
            if not np.isfinite(amp):
                out["reason"] = "no per-band amplitude measurable (magnr absent)"
                return out
            if amp < AMP_MIN:
                out["reason"] = (f"per-band amplitude {amp:.2f} mag above quiescence "
                                 f"< {AMP_MIN} -- not an outburst")
                return out
        if (n_win >= FLAT_MIN_ALERTS and np.isfinite(ptp) and ptp < FLAT_PTP_MAX):
            out["reason"] = (f"flat in every band with >= {FLAT_MIN_ALERTS} clean "
                             f"detections in {FLAT_WINDOW_DAYS:.0f} d "
                             f"(ptp {ptp:.2f} < {FLAT_PTP_MAX}) -- a constant "
                             f"difference residual, not a transient")
            return out

    out.update({
        "passed": True, "channel": chan, "reason": why_c,
        "first_pass_jd": jd_trig,
        "mag_at_pass": _f(trigger, "i:magpsf"),
        "band_at_pass": {1: "g", 2: "r", 3: "i"}.get(int(_f(trigger, "i:fid", 0)), "?"),
        "ra": _f(trigger, "i:ra"), "dec": _f(trigger, "i:dec"),
        "drb": _f(trigger, "i:drb"),
        "sgscore1": _f(trigger, "i:sgscore1"),
        "distpsnr1": _f(trigger, "i:distpsnr1"),
        "distnr": _f(trigger, "i:distnr"), "magnr": _f(trigger, "i:magnr"),
        "ndethist": _f(trigger, "i:ndethist"),
        "gal_b": gal_b(_f(trigger, "i:ra"), _f(trigger, "i:dec")),
        "simbad": trigger.get("d:cdsxmatch"),
    })
    return out
