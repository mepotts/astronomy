#!/usr/bin/env python
"""M2: pull the full Gaia DR3 astrometric-orbit NSS set for the AMRF triage.

One anonymous ASYNC TAP job (M1 verified limits: async 3M rows / 90 min --
this is ~1.7e5 rows, well inside). The uncapped twin of
queries/01_nss_compact_companion_triage.dr3-validation.sql, extended with:
  - all six DR3 astrometric solution types (verified live 2026-08-16):
      Orbital                        134,598
      AstroSpectroSB1                 33,467
      OrbitalAlternative                 619
      OrbitalAlternativeValidated         10
      OrbitalTargetedSearch              345
      OrbitalTargetedSearchValidated     188   -> total 169,227
  - LEFT JOIN gaiadr3.binary_masses (the M1 source used by Shahaf et al. 2023,
    MNRAS 518, 2991: m1_ref='IsocLum'); BH2 has NO row there (verified
    2026-08-16), so the triage carries a photometric M1 fallback.
  - NO quality/period cuts in-query: cuts happen offline so the rejected
    populations stay measurable (El-Badry 2026 lesson).

Output: data/dr3_nss_amrf_input.parquet + data/dr3_nss_amrf_input.NOTE.md
        (row count, sha256, query text, date).

Run   : .venv/Scripts/python.exe scripts/pull_dr3_nss_orbits.py
"""

import datetime
import hashlib
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PARQUET = os.path.join(BASE, "data", "dr3_nss_amrf_input.parquet")
OUT_NOTE = os.path.join(BASE, "data", "dr3_nss_amrf_input.NOTE.md")

QUERY = """
SELECT
  n.source_id,
  n.nss_solution_type,
  n.period, n.period_error,
  n.t_periastron, n.t_periastron_error,
  n.eccentricity, n.eccentricity_error,
  n.a_thiele_innes, n.a_thiele_innes_error,
  n.b_thiele_innes, n.b_thiele_innes_error,
  n.f_thiele_innes, n.f_thiele_innes_error,
  n.g_thiele_innes, n.g_thiele_innes_error,
  n.c_thiele_innes, n.c_thiele_innes_error,
  n.h_thiele_innes, n.h_thiele_innes_error,
  n.parallax      AS nss_parallax,
  n.parallax_error AS nss_parallax_error,
  n.center_of_mass_velocity, n.center_of_mass_velocity_error,
  n.semi_amplitude_primary, n.semi_amplitude_primary_error,
  n.mass_ratio, n.mass_ratio_error,
  n.significance, n.goodness_of_fit, n.efficiency, n.obj_func,
  n.flags, n.bit_index,
  n.astrometric_n_obs_al, n.astrometric_n_good_obs_al,
  n.rv_n_obs_primary, n.rv_n_good_obs_primary,
  n.conf_spectro_period, n.input_period_error, n.astrometric_jitter,
  g.ra, g.dec, g.l, g.b,
  g.parallax, g.parallax_error, g.parallax_over_error,
  g.pmra, g.pmdec,
  g.phot_g_mean_mag, g.phot_bp_mean_mag, g.phot_rp_mean_mag, g.bp_rp,
  g.phot_bp_rp_excess_factor,
  g.ruwe, g.ipd_frac_multi_peak, g.ipd_gof_harmonic_amplitude,
  g.astrometric_excess_noise, g.astrometric_excess_noise_sig,
  g.astrometric_gof_al, g.astrometric_chi2_al,
  g.visibility_periods_used, g.duplicated_source, g.non_single_star,
  g.radial_velocity, g.radial_velocity_error, g.rv_nb_transits,
  m.m1 AS bm_m1, m.m1_lower AS bm_m1_lower, m.m1_upper AS bm_m1_upper,
  m.m2 AS bm_m2, m.m2_lower AS bm_m2_lower, m.m2_upper AS bm_m2_upper,
  m.fluxratio AS bm_fluxratio,
  m.combination_method AS bm_combination_method,
  m.m1_ref AS bm_m1_ref, m.flag AS bm_flag
FROM gaiadr3.nss_two_body_orbit AS n
JOIN gaiadr3.gaia_source AS g
  ON g.source_id = n.source_id
LEFT JOIN gaiadr3.binary_masses AS m
  ON m.source_id = n.source_id
WHERE n.nss_solution_type IN ('Orbital', 'AstroSpectroSB1',
                              'OrbitalAlternative', 'OrbitalAlternativeValidated',
                              'OrbitalTargetedSearch', 'OrbitalTargetedSearchValidated')
"""


def main():
    from astroquery.gaia import Gaia

    print("Launching anonymous ASYNC TAP job (one job, ~169k rows expected)...")
    job = Gaia.launch_job_async(QUERY, verbose=False)
    table = job.get_results()
    print(f"Job done: {len(table)} rows, {len(table.colnames)} columns")

    df = table.to_pandas()
    os.makedirs(os.path.dirname(OUT_PARQUET), exist_ok=True)
    df.to_parquet(OUT_PARQUET, index=False)

    sha = hashlib.sha256()
    with open(OUT_PARQUET, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            sha.update(chunk)
    digest = sha.hexdigest()
    size = os.path.getsize(OUT_PARQUET)

    counts = df["nss_solution_type"].value_counts().to_string()
    with open(OUT_NOTE, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(
            f"# dr3_nss_amrf_input.parquet\n\n"
            f"- pulled: {datetime.datetime.now(datetime.timezone.utc).isoformat()}\n"
            f"- endpoint: anonymous async TAP, https://gea.esac.esa.int/tap-server/tap\n"
            f"- rows: {len(df)}\n- columns: {len(df.columns)}\n"
            f"- file size: {size} bytes\n- sha256: {digest}\n\n"
            f"## rows per nss_solution_type\n\n```\n{counts}\n```\n\n"
            f"## query\n\n```sql\n{QUERY}\n```\n"
        )
    print(f"Wrote {OUT_PARQUET} ({size} B)\nsha256 {digest}")
    print(counts)


if __name__ == "__main__":
    sys.exit(main())
