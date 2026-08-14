-- =====================================================================
-- 01 (DR3 VALIDATION TWIN) NSS compact-companion triage input
-- =====================================================================
-- PURPOSE  : Same logic as 01_nss_compact_companion_triage.sql, translated to
--            Gaia DR3 table/column names, so the join + math are proven on the
--            live archive today. Renames applied (see dr3-to-dr4-tables.md):
--              DR4 solution_type      -> DR3 nss_solution_type
--              DR4 gof                -> DR3 goodness_of_fit
--              DR4 semi_major_axis    -> derived from Thiele-Innes A,B,F,G:
--                u = (A^2+B^2+F^2+G^2)/2 ; v = A*G - B*F
--                a0 = SQRT(u + SQRT(u*u - v*v))
--                [Halbwachs et al. 2023, A&A, arXiv:2206.05726, "Gaia DR3
--                 astrometric binary star processing", their eq. for a0]
--              DR4 mass_function, nss_masses, has_epoch_astrometry: no DR3
--                equivalent -> dropped here.
--              DR3 solution-type list has OrbitalTargetedSearch(Validated)
--                instead of DR4's OrbitalPoorlyConstrained.
-- VALIDATED ON DR3: yes, 2026-08-14, anonymous TAP sync, TOP 10, HTTP 200,
--            10 rows returned with finite a0_mas and amrf_pieces.
-- ENDPOINT : https://gea.esac.esa.int/tap-server/tap/sync (anonymous,
--            2000 rows / 60 s cap - keep TOP small here)
-- =====================================================================
SELECT TOP 10
  n.source_id,
  n.nss_solution_type,
  n.period, n.period_error,
  n.eccentricity,
  n.a_thiele_innes, n.b_thiele_innes, n.f_thiele_innes, n.g_thiele_innes,
  SQRT(
    (n.a_thiele_innes*n.a_thiele_innes + n.b_thiele_innes*n.b_thiele_innes
     + n.f_thiele_innes*n.f_thiele_innes + n.g_thiele_innes*n.g_thiele_innes)/2.0
    + SQRT(
        POWER((n.a_thiele_innes*n.a_thiele_innes + n.b_thiele_innes*n.b_thiele_innes
               + n.f_thiele_innes*n.f_thiele_innes + n.g_thiele_innes*n.g_thiele_innes)/2.0, 2)
        - POWER(n.a_thiele_innes*n.g_thiele_innes - n.b_thiele_innes*n.f_thiele_innes, 2)
      )
  ) AS a0_mas,
  n.parallax AS nss_parallax,
  n.significance, n.goodness_of_fit, n.efficiency, n.flags,
  g.ra, g.dec,
  g.parallax, g.parallax_over_error,
  g.phot_g_mean_mag, g.bp_rp,
  g.ruwe, g.ipd_frac_multi_peak, g.astrometric_excess_noise
FROM gaiadr3.nss_two_body_orbit AS n
JOIN gaiadr3.gaia_source AS g
  ON g.source_id = n.source_id
WHERE n.nss_solution_type IN ('Orbital', 'OrbitalTargetedSearch',
                              'OrbitalTargetedSearchValidated', 'AstroSpectroSB1')
  AND n.period BETWEEN 10 AND 4000
  AND n.significance >= 0
  AND g.parallax_over_error >= 3
  AND n.parallax > 0
