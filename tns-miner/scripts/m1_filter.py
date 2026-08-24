"""M1 filter: pre-registered thresholds, fixed BEFORE any candidate was counted.

See M1-filter-design.md for the rule that fixed each number.  Nothing in this file
may be re-tuned after looking at candidate counts; if a threshold changes, the
change and its justification go in the M-doc and the run is re-labelled.

Input: a per-object table of ZTF alert packets as served by Fink
(https://api.ztf.fink-portal.org/api/v1/objects), one row per detection, with the
raw `i:` alert fields and Fink's `d:` cross-match columns.

The filter is deliberately the INVERSE of the survey auto-reporters on two axes:
they demand a resolved host (sgscore1 low, distpsnr1 large) because they hunt
supernovae.  Novae and CVs are stellar and often sit on their own quiescent
progenitor, so those cuts structurally discard our targets.  That inversion is
the whole thesis of this project.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# PRE-REGISTERED THRESHOLDS  (frozen 2026-08-24, before any candidate was counted)
# ---------------------------------------------------------------------------
# Rule that fixed each value, in priority order:
#   (i)   the value used by the published ZTF / AMPEL / ZTF-BTS "real transient"
#         recipes for that same alert field;
#   (ii)  a boundary this project's own README names (mag 19.0-20.6, M31/M81);
#   (iii) the loosest value that excludes an artifact class by construction.
# No threshold was chosen by looking at how many candidates it yields.

DRB_MIN = 0.90            # (i) ZTF deep real-bogus; 0.9 is the standard high-purity cut
RB_MIN = 0.55             # (i) legacy real-bogus, for alerts predating drb
NBAD_MAX = 0              # (iii) any bad pixel in the stamp -> reject by construction
FWHM_MAX = 5.0            # (i) ZTF standard
ELONG_MAX = 1.4           # (i) ZTF standard
MAGDIFF_MAX = 0.5         # (i) ZTF standard is 0.1; loosened to 0.5 because faint
                          #     (mag ~20) PSF-vs-aperture scatter alone exceeds 0.1
N_DET_MIN = 2             # (i) detection multiplicity, the classic moving-object kill
DT_MIN_DAYS = 0.02083     # (iii) 30 min: shorter than this an asteroid has not moved
SSDIST_MAX_ARCSEC = 5.0   # (i) ZTF ssdistnr match radius for known minor planets

# --- v2, 2026-08-24: revised BEFORE any candidate was counted, on evidence from
#     the positive control and the measured gap.  v1 values kept for the record.
# MAG_BRIGHT was 16.0 ("brighter than this is ASAS-SN / ZTF-BTS territory").
# MEASURED, and the reason for the change: the DCAP reports we are trying to
# reproduce run 12.53-20.58 mag with a MEDIAN of 18.74, and 7.8% of them are
# brighter than 16.0.  A 16.0 floor structurally excludes the target class.  The
# new floor sits just below DCAP's brightest report and at ZTF's saturation.
MAG_BRIGHT = 12.0
MAG_FAINT = 20.6          # (ii) 20.6 is ZTF's practical single-epoch floor
FAINT_RESIDUE_MIN = 19.0  # (ii) README's faint-residue band starts at 19.0

# nuclear / TDE rejection -- the mission says avoid these
NUCLEAR_SGSCORE_MAX = 0.30   # (i) sgscore1 <= 0.3 == PS1 says "galaxy"
NUCLEAR_SEP_ARCSEC = 1.0     # (i) within 1" of a galaxy centroid == nuclear

# channel A1: outburst on a catalogued point source (CV / dwarf nova)
# v1 used A1_SEP_ARCSEC = 1.5 with A2 starting at 3.0, which left a DEAD ZONE at
# 1.5-3.0": objects there matched no channel and fell through to the faint-residue
# channel, which requires mag >= 19, so every bright plane object with a 2"
# association was silently dropped (AT 2026stb, a real nova, sits at 2.19").  That
# was a partition bug, not a threshold.  A1 and A2 now tile the axis at one radius.
A1_SEP_ARCSEC = 3.0       # (i) 3" -- the cross-match radius TNS itself uses for duplicates
A1_SGSCORE_MIN = 0.50     # (i) PS1 star/galaxy score >= 0.5 == star-like.  ZTF writes
                          #     0.5 when PS1 has no opinion, and for our class the
                          #     no-opinion side is the side to keep.
# channel A2: new star where PS1 shows nothing (classical nova candidate)
A2_SEP_ARCSEC = 3.0       # same radius: > 3" means nothing plausibly associated
A2_FAINT_HOST_MAG = 21.0  # (iii) PS1 3-pi single-epoch depth; fainter == effectively absent

# channel B: the two resolved-nova fields the README calls out
M31 = (10.6847, 41.2687, 1.5)   # RA, Dec, radius deg -- D25 semi-major axis ~1.6 deg
M81 = (148.8882, 69.0653, 0.5)  # RA, Dec, radius deg -- M81/M82 group core
GAL_PLANE_ABS_B = 15.0    # (ii) |b| < 15 deg == the galactic-plane sub-channel

TNS_MATCH_ARCSEC = 3.0    # (i) TNS's own duplicate-report matching radius

# SIMBAD classes that mean "already known to vary in a way we are not adding to"
KNOWN_VARIABLE_SIMBAD = {
    "RRLyr", "RRLyrae", "Mira", "LongPeriodV*", "LPV*", "EclBin", "EB*",
    "Cepheid", "delSctV*", "RSCVnV*", "BYDraV*", "Variable*", "Star",
    "PulsV*", "SB*", "EllipVar", "RotV*", "gammaDorV*", "alf2CVnV*",
    "AGN", "QSO", "Blazar", "BLLac", "Seyfert", "Seyfert_1", "Seyfert_2",
    "Galaxy", "GinCl", "GinGroup", "GinPair", "EmG", "StarburstG", "LINER",
    "Radio", "X",
}
# ...but these SIMBAD classes are the target, not a veto:
TARGET_SIMBAD = {"CataclyV*", "Nova", "DwarfNova", "Symbiotic*", "CV*",
                 "Nova_Candidate", "CataclyV*_Candidate"}


# ---------------------------------------------------------------------------

def _f(row, key, default=np.nan) -> float:
    v = row.get(key, default)
    try:
        f = float(v)
    except (TypeError, ValueError):
        return float(default) if default is not np.nan else np.nan
    return f


def _isnull(v) -> bool:
    """True for "this cross-match returned nothing".

    Fink stamps a failed cross-match call as the literal string "Fail 502" /
    "Fail 500" in the d: columns.  That is a service error, NOT a catalogue hit --
    treating it as a hit silently vetoes real candidates, so it counts as null.
    """
    if v is None:
        return True
    if isinstance(v, float) and np.isnan(v):
        return True
    s = str(v).strip().lower()
    if s.startswith("fail"):
        return True
    return s in ("", "nan", "none", "null", "-99.0", "-99", "unknown")


def gal_b(ra_deg: float, dec_deg: float) -> float:
    """Galactic latitude, degrees.  Closed-form, no astropy dependency in the hot loop."""
    ra, dec = np.radians(ra_deg), np.radians(dec_deg)
    ra_ngp, dec_ngp = np.radians(192.85948), np.radians(27.12825)
    sb = (np.sin(dec) * np.sin(dec_ngp)
          + np.cos(dec) * np.cos(dec_ngp) * np.cos(ra - ra_ngp))
    return float(np.degrees(np.arcsin(np.clip(sb, -1, 1))))


def _sep_deg(ra1, dec1, ra2, dec2) -> float:
    r1, d1, r2, d2 = map(np.radians, (ra1, dec1, ra2, dec2))
    c = np.sin(d1) * np.sin(d2) + np.cos(d1) * np.cos(d2) * np.cos(r1 - r2)
    return float(np.degrees(np.arccos(np.clip(c, -1, 1))))


def detection_is_clean(row) -> tuple[bool, str]:
    """Universal hygiene gate, applied per detection.  Cuts 1-3 of the design doc."""
    isdiffpos = str(row.get("i:isdiffpos", "")).strip()
    if isdiffpos not in ("t", "1", "T", "true", "True"):
        return False, "isdiffpos: negative subtraction (fading, not brightening)"

    drb = _f(row, "i:drb")
    rb = _f(row, "i:rb")
    if not np.isnan(drb):
        if drb < DRB_MIN:
            return False, f"drb {drb:.3f} < {DRB_MIN}"
    elif not np.isnan(rb):
        if rb < RB_MIN:
            return False, f"rb {rb:.3f} < {RB_MIN} (no drb available)"
    else:
        return False, "no real-bogus score"

    nbad = _f(row, "i:nbad", 0)
    if not np.isnan(nbad) and nbad > NBAD_MAX:
        return False, f"nbad {nbad:.0f} > {NBAD_MAX}"
    fwhm = _f(row, "i:fwhm")
    if not np.isnan(fwhm) and fwhm > FWHM_MAX:
        return False, f"fwhm {fwhm:.2f} > {FWHM_MAX}"
    elong = _f(row, "i:elong")
    if not np.isnan(elong) and elong > ELONG_MAX:
        return False, f"elong {elong:.2f} > {ELONG_MAX}"
    magdiff = _f(row, "i:magdiff")
    if not np.isnan(magdiff) and abs(magdiff) > MAGDIFF_MAX:
        return False, f"|magdiff| {abs(magdiff):.2f} > {MAGDIFF_MAX}"

    mag = _f(row, "i:magpsf")
    if np.isnan(mag) or not (MAG_BRIGHT <= mag <= MAG_FAINT):
        return False, f"magpsf {mag} outside [{MAG_BRIGHT}, {MAG_FAINT}]"

    ssdist = _f(row, "i:ssdistnr", -999)
    if not np.isnan(ssdist) and 0 <= ssdist <= SSDIST_MAX_ARCSEC:
        return False, f"known minor planet {ssdist:.1f}\" away (ssdistnr)"
    roid = _f(row, "d:roid", 0)
    if roid in (2.0, 3.0):
        return False, f"Fink roid={roid:.0f} (solar-system candidate / MPC match)"
    return True, "clean"


def classify_channel(row) -> tuple[str | None, str]:
    """Which target channel does this detection belong to?  None == not a target."""
    ra, dec = _f(row, "i:ra"), _f(row, "i:dec")
    sg1 = _f(row, "i:sgscore1")
    sep1 = _f(row, "i:distpsnr1", 999)
    sgmag1 = _f(row, "i:sgmag1", 99)
    mag = _f(row, "i:magpsf")

    # nuclear / TDE veto first -- the mission says avoid these
    if (not np.isnan(sg1) and sg1 <= NUCLEAR_SGSCORE_MAX
            and not np.isnan(sep1) and sep1 <= NUCLEAR_SEP_ARCSEC):
        return None, "nuclear: on a PS1 galaxy centroid (TDE/AGN territory, out of scope)"

    # B: M31 / M81 fields
    for name, (r0, d0, rad) in (("M31", M31), ("M81", M81)):
        if not np.isnan(ra) and _sep_deg(ra, dec, r0, d0) <= rad:
            return f"B_{name}", f"inside the {name} field ({rad} deg)"

    b = gal_b(ra, dec) if not np.isnan(ra) else np.nan
    in_plane = (not np.isnan(b)) and abs(b) < GAL_PLANE_ABS_B
    plane = " [galactic plane]" if in_plane else ""

    # A2: nothing catalogued here -> classical nova candidate
    if (np.isnan(sep1) or sep1 > A2_SEP_ARCSEC
            or (sgmag1 > A2_FAINT_HOST_MAG and sep1 > A1_SEP_ARCSEC)):
        return "A2_nova_like", f"no PS1 source within {A2_SEP_ARCSEC}\"{plane}"

    # A1: outburst on a catalogued point source -> CV / dwarf nova
    if sep1 <= A1_SEP_ARCSEC and (np.isnan(sg1) or sg1 >= A1_SGSCORE_MIN):
        return "A1_cv_outburst", f"outburst on a PS1 point source {sep1:.2f}\" away{plane}"

    # D: galactic plane.  Promoted to its own channel by the measured gap: only
    # 5.8% of all TNS reports in the last 12 months are at |b| < 15 deg, but 55%
    # of DCAP's and 68% of XOSS's are.  The plane is where the survey pipelines
    # structurally do not report, at any magnitude.
    if in_plane:
        return "D_galactic_plane", f"|b| = {abs(b):.1f} deg, extended association {sep1:.2f}\""

    # C: faint residue
    if FAINT_RESIDUE_MIN <= mag <= MAG_FAINT:
        return "C_faint_residue", f"faint residue at mag {mag:.2f}"

    return None, "no channel: bright, off-plane, extended non-stellar association"


def catalogue_veto(rows: pd.DataFrame) -> tuple[bool, str]:
    """Cuts 6 and 7: already-catalogued variable, or already in TNS.

    Fink attaches VSX, GCVS, SIMBAD and TNS cross-matches to every alert, so this
    is a column read, not a network call."""
    for col, label in (("d:vsx", "VSX"), ("d:gcvs", "GCVS")):
        if col in rows.columns:
            vals = [v for v in rows[col].tolist() if not _isnull(v)]
            if vals:
                return False, f"already catalogued in {label}: {vals[0]}"
    if "d:tns" in rows.columns:
        vals = [v for v in rows["d:tns"].tolist() if not _isnull(v)]
        if vals:
            return False, f"already in TNS: {vals[0]}"
    if "d:cdsxmatch" in rows.columns:
        vals = [str(v).strip() for v in rows["d:cdsxmatch"].tolist() if not _isnull(v)]
        for v in vals:
            if v in TARGET_SIMBAD:
                continue
            if v in KNOWN_VARIABLE_SIMBAD:
                return False, f"SIMBAD says {v} (already-known variable or host)"
    return True, "no catalogue veto"


def evaluate(rows: pd.DataFrame, jd_cutoff: float | None = None,
             jd_floor: float | None = None) -> dict:
    """Run the whole filter on one object's alert history.

    jd_cutoff: only alerts with i:jd <= cutoff are visible.  This is the rewind
    used by the positive control -- the filter never sees the future.
    jd_floor:  optionally also hide alerts older than this, so the "first pass"
    epoch is measured within one outburst episode rather than being dragged back
    to an eruption years earlier (CVs recur; the lead time for THIS event is the
    honest number to quote alongside the all-time one).
    """
    out = {"passed": False, "channel": None, "reason": "", "first_pass_jd": None,
           "n_clean": 0, "n_alerts": 0, "mag_at_pass": None, "band_at_pass": None}
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

    ok, why = catalogue_veto(rows)
    if not ok:
        out["reason"] = why
        return out

    clean = []
    for _, r in rows.iterrows():
        good, why_d = detection_is_clean(r)
        if good:
            clean.append(r)
    out["n_clean"] = len(clean)
    if len(clean) < N_DET_MIN:
        out["reason"] = f"only {len(clean)} clean detection(s), need {N_DET_MIN}"
        return out

    # detection multiplicity with a real time baseline (cut 4)
    jds = [float(r["i:jd"]) for r in clean]
    if max(jds) - min(jds) < DT_MIN_DAYS:
        out["reason"] = (f"clean detections span {max(jds)-min(jds):.4f} d "
                         f"< {DT_MIN_DAYS} d -- cannot exclude a mover")
        return out

    # the object passes at the epoch of the SECOND clean detection that also
    # satisfies the time baseline: that is the first moment a filter running live
    # could have fired.
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
        # try the brightest clean detection too -- association can be epoch-noisy
        bright = min(clean, key=lambda r: _f(r, "i:magpsf", 99))
        chan, why_c = classify_channel(bright)
        if chan is None:
            out["reason"] = why_c
            return out
        trigger = bright

    out.update({
        "passed": True,
        "channel": chan,
        "reason": why_c,
        "first_pass_jd": float(trigger["i:jd"]),
        "mag_at_pass": _f(trigger, "i:magpsf"),
        "band_at_pass": {1: "g", 2: "r", 3: "i"}.get(int(_f(trigger, "i:fid", 0)), "?"),
        "ra": _f(trigger, "i:ra"),
        "dec": _f(trigger, "i:dec"),
        "drb": _f(trigger, "i:drb"),
        "sgscore1": _f(trigger, "i:sgscore1"),
        "distpsnr1": _f(trigger, "i:distpsnr1"),
        "distnr": _f(trigger, "i:distnr"),
        "magnr": _f(trigger, "i:magnr"),
        "gal_b": gal_b(_f(trigger, "i:ra"), _f(trigger, "i:dec")),
        "simbad": trigger.get("d:cdsxmatch"),
    })
    return out
