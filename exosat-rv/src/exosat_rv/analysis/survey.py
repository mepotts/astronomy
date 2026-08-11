"""M7 -- apply the Hoy et al. feasibility test to every directly imaged companion.

The target sample is **Lazzoni et al. 2022's Table 1** (arXiv:2207.07569), the 38 companions
their detectability study used, plus CD-35 2722 B itself.

That addition is not cosmetic. **CD-35 2722 B is absent from Lazzoni et al.'s sample** --
checked, not assumed -- even though Hoy et al. cite that paper (their reference [11]) for
the claim that "it has been calculated that, given the existence of satellites orbiting
CD-35 B, the radial velocity method would be relatively likely to find them". The
calculation was about the *class*, not this object. The first exosatellite was found on a
target the predictive study never evaluated, which is worth knowing before trusting any
ranking -- including this one.

The ranking here differs from Lazzoni's in one deliberate way: their detection threshold
is a *forecast* (100 m/s at K = 13.5), and this one is anchored on the *achievement*
(31.44 m/s at K = 12.01). See ``satellites.hoy_calibrated_threshold_ms``.
"""

from __future__ import annotations

from typing import Any

from .satellites import (
    DEUTERIUM_CLIFF_MJUP,
    activity_amplitude_ms,
    domingos_stability_limit_au,
    expected_sat_mass_mearth,
    hoy_calibrated_threshold_ms,
    lazzoni_threshold_ms,
    min_detectable_sat_mearth,
    roche_limit_au,
    satellite_period_d,
)

# name, age_Myr, K_companion_mag, separation_au, M_star_Msun, M_companion_MJup
# Transcribed from Lazzoni et al. 2022 Table 1 (columns: Age, Kp, a, M*, Mp).
LAZZONI_TABLE1: tuple[tuple[str, float, float, float, float, float], ...] = (
    ("1RXS J160929.1-210524 b", 10.0, 16.9, 309.4, 0.85, 8.0),
    ("2M1207 b", 8.0, 15.6, 42.0, 0.03, 5.0),
    ("51 Eri b", 24.0, 21.0, 11.2, 1.75, 3.6),
    ("AB Pic b", 45.0, 15.1, 270.6, 0.86, 14.0),
    ("beta Pic b", 16.0, 14.9, 8.9, 1.64, 12.8),
    ("CT Cha b", 1.4, 14.8, 514.0, 0.80, 15.0),
    ("DH Tau B", 1.4, 14.7, 318.1, 0.10, 10.6),
    ("eta Tel B", 24.0, 13.2, 199.4, 2.18, 47.0),
    ("GJ504 b", 4000.0, 21.0, 43.8, 1.18, 23.0),
    ("GQ Lup b", 3.5, 13.5, 117.0, 1.03, 30.0),
    ("HD1160 c", 50.0, 14.2, 97.3, 2.00, 66.0),
    ("HD4747 B", 2300.0, 13.6, 11.4, 0.86, 70.0),
    ("HD19467 B", 8000.0, 14.2, 44.1, 0.95, 74.0),
    ("HD72946 B", 1600.0, 13.5, 6.5, 0.99, 72.4),
    ("HD95086 b", 12.0, 21.0, 58.0, 1.60, 4.5),
    ("HR2562 B", 750.0, 17.4, 21.8, 1.37, 29.0),
    ("HR3549 B", 125.0, 16.8, 81.1, 2.00, 48.0),
    ("HR8799 b", 42.0, 20.6, 72.2, 1.52, 5.8),
    ("HR8799 c", 42.0, 18.2, 41.6, 1.52, 7.6),
    ("HR8799 d", 42.0, 16.9, 26.9, 1.52, 9.2),
    ("HR8799 e", 42.0, 18.2, 16.3, 1.52, 7.6),
    ("HIP64892 B", 16.0, 16.3, 159.1, 2.35, 33.0),
    ("HIP65426 b", 14.0, 21.0, 115.0, 1.96, 8.0),
    ("HIP74865 B", 15.0, 15.7, 24.8, 1.72, 46.0),
    ("HIP78530 B", 11.0, 18.4, 573.8, 2.75, 20.0),
    ("HIP79098 B", 10.0, 14.7, 345.2, 4.00, 20.0),
    ("HIP107412 B", 700.0, 17.6, 12.8, 1.32, 25.0),
    ("k And b", 47.0, 13.9, 103.6, 2.70, 20.0),
    ("PDS 70 b", 5.4, 15.2, 20.1, 0.98, 7.9),
    ("PDS 70 c", 5.4, 15.2, 33.2, 0.98, 7.8),
    ("PZ Tel B", 24.0, 13.0, 70.9, 0.90, 52.0),
    ("TYC 7084-794-1 B", 140.0, 15.3, 67.0, 0.50, 32.0),
    ("TYC 8047-232-1 B", 42.0, 16.4, 277.0, 0.82, 13.8),
    ("TYC 8998-760-1 b", 17.0, 18.2, 162.0, 1.00, 14.0),
    ("TYC 8998-760-1 c", 17.0, 21.0, 320.0, 1.00, 6.0),
    ("TYC 8984-2245-1 b", 13.9, 21.0, 115.0, 1.10, 6.3),
    ("GSC 6214-210 B", 10.0, 14.8, 240.0, 0.90, 14.0),
)

CD35 = ("CD-35 2722 B", 100.0, 12.01, 222.0, 0.40, 37.0)
"""Hoy et al.'s target, absent from Lazzoni's Table 1. K = 12.01 MKO from Wahhaj et al.
2011; a = 222 au is the semi-major axis implied by P ~ 5000 yr, not the 62.6 au projected
separation -- the distinction that M0 got wrong and M1 retracted."""

CD35_ECC = 0.94
"""Companion orbital eccentricity. The published value is ">0.9"; 0.94 is what reproduces
the paper's own 1.07 au stability limit (M1 section 1.1)."""


def run_survey(threshold: str = "hoy") -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Rank companions by the smallest satellite the method could find around each."""
    thr_fn = hoy_calibrated_threshold_ms if threshold == "hoy" else lazzoni_threshold_ms
    label = (
        "3-sigma on Hoy et al.'s achieved 31.44 m/s at K=12.01"
        if threshold == "hoy"
        else "Lazzoni et al. 2022 forecast, 100 m/s at K=13.5"
    )

    rows: list[dict[str, Any]] = []
    for name, age, kmag, sep_au, mstar, mhost in (*LAZZONI_TABLE1, CD35):
        ecc = CD35_ECC if name == CD35[0] else 0.0
        sigma = thr_fn(kmag)
        stab = domingos_stability_limit_au(mhost, mstar, sep_au, ecc)
        # Radius ~1.2 R_Jup for a young substellar object; the Roche limit is insensitive
        # to it next to the stability limit, which spans four decades across this sample.
        roche = roche_limit_au(mhost, 1.2, rho_sat_cgs=3.0)
        # Evaluate at 0.4 x the stability limit: inside the stable zone, and near the
        # median of Lazzoni's own recovered semi-major axes.
        a_probe = max(min(0.4 * stab, stab), roche * 1.5)
        m_min = min_detectable_sat_mearth(mhost, a_probe, sigma)
        p_sat = satellite_period_d(a_probe, mhost)

        # Name the *class* of satellite the method could reach, rather than pass/fail
        # against an arbitrary bar. Lazzoni et al. 2022's central conclusion is that only
        # their "binary-like" population is reachable at all, and this reproduces it --
        # so a table of 38 FAILs would be hiding the actual result rather than stating it.
        if kmag >= 21.0:
            verdict = "no measured K -- upper limit only, unrankable"
        elif mhost < DEUTERIUM_CLIFF_MJUP and kmag > 17.0:
            verdict = "below D-burning cliff and faint -- out of reach"
        elif m_min <= 30.0:
            verdict = "planet-like (Galilean/Titan class) reachable"
        elif m_min <= 317.8:
            verdict = "sub-Jovian reachable"
        elif m_min <= 3178.0:
            verdict = "binary-like only (1-10 M_Jup)"
        else:
            verdict = "nothing physical reachable"

        rows.append({
            "name": name,
            "age_myr": age,
            "k_mag": kmag,
            "separation_au": sep_au,
            "m_star_msun": mstar,
            "m_host_mjup": mhost,
            "threshold_ms": sigma,
            "stability_au": stab,
            "roche_au": roche,
            "probe_sma_au": a_probe,
            "probe_period_d": p_sat,
            "min_sat_mearth": m_min,
            "min_sat_mass_ratio": m_min / (mhost * 317.828),
            "cpd_expectation_mearth": expected_sat_mass_mearth(mhost),
            "activity_floor_ms": activity_amplitude_ms(10.0),
            "in_lazzoni_sample": name != CD35[0],
            "verdict": verdict,
        })

    rows.sort(key=lambda r: r["min_sat_mearth"])
    meta = {
        "threshold": threshold,
        "threshold_label": label,
        "n_pass": sum("planet-like" in r["verdict"] for r in rows),
        "n_marginal": sum("sub-Jovian" in r["verdict"] for r in rows),
        "n_fail": sum(
            "binary-like" in r["verdict"] or "out of reach" in r["verdict"]
            or "unrankable" in r["verdict"] or "nothing physical" in r["verdict"]
            for r in rows
        ),
        "note": (
            "CD-35 2722 B is NOT in Lazzoni et al. 2022's sample -- the first exosatellite "
            "was found on a target their detectability study never evaluated."
        ),
    }
    return rows, meta
