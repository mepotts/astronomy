-- =====================================================================
-- 02 (DR3 VALIDATION TWIN) 6D hypervelocity-star input
-- =====================================================================
-- PURPOSE  : Same logic as 02_hypervelocity_6d.sql on Gaia DR3 names.
--            Differences vs the DR4 body (see dr3-to-dr4-tables.md):
--              + astrometric_excess_noise_sig <= 2 restored (exists in DR3;
--                REMOVED in draft DR4 gaia_source - Marchetti 2019's original
--                cut, kept here so the DR3 run matches the published recipe)
--              - has_epoch_astrometry, non_single_star semantics: non_single_star
--                exists in DR3; has_epoch_astrometry does not -> dropped here.
-- CUTS FROM: Marchetti, Rossi & Brown 2019, MNRAS 490, 157;
--            Marchetti et al. 2022, MNRAS 515, 767 (Gaia DR3 in 6D).
-- VALIDATED ON DR3: yes, 2026-08-14, anonymous TAP sync, TOP 10, HTTP 200
--            (rows with vtan_kms >= 300 or |RV| >= 300 returned).
-- ENDPOINT : https://gea.esac.esa.int/tap-server/tap/sync
-- =====================================================================
SELECT TOP 10
  g.source_id,
  g.ra, g.dec, g.l, g.b, g.ref_epoch,
  g.parallax, g.parallax_error, g.parallax_over_error,
  g.pmra, g.pmra_error, g.pmdec, g.pmdec_error,
  g.radial_velocity, g.radial_velocity_error, g.rv_nb_transits,
  g.grvs_mag, g.rv_expected_sig_to_noise,
  g.phot_g_mean_mag, g.bp_rp,
  g.ruwe, g.astrometric_gof_al, g.astrometric_excess_noise,
  g.astrometric_excess_noise_sig,
  g.ipd_frac_multi_peak, g.visibility_periods_used,
  g.duplicated_source, g.non_single_star,
  4.74047 * SQRT(g.pmra*g.pmra + g.pmdec*g.pmdec) / g.parallax AS vtan_kms
FROM gaiadr3.gaia_source AS g
WHERE g.radial_velocity IS NOT NULL
  AND g.parallax > 0
  AND g.parallax_over_error >= 5
  AND g.ruwe < 1.4
  AND g.astrometric_excess_noise_sig <= 2
  AND ( 4.74047 * SQRT(g.pmra*g.pmra + g.pmdec*g.pmdec) / g.parallax >= 300
        OR ABS(g.radial_velocity) >= 300 )
