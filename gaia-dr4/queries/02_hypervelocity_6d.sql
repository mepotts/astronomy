-- =====================================================================
-- 02 6D hypervelocity-star input (Gaia DR4, day-one; workstream W5)
-- =====================================================================
-- PURPOSE  : Select the full 6D sample (positions, parallax, PM, RV) with
--            quality columns for a Marchetti-style total-velocity computation
--            offline (Galactocentric transform + distance posterior are NOT
--            done in ADQL). The ADQL pre-filter keeps candidates whose
--            *tangential* or *radial* velocity alone is already extreme,
--            plus loose-quality columns so the spurious-astrometry killer
--            (DR4 epoch astrometry, via 03_epoch_astrometry_fetch.sql) can be
--            applied to every survivor.
-- CUTS FROM: Marchetti, Rossi & Brown 2019, MNRAS 490, 157 (Gaia DR2 6D
--            catalogue: parallax_over_error >= 5 for the clean sample);
--            Marchetti et al. 2022, MNRAS 515, 767 (Gaia DR3 in 6D rerun). Their
--            astrometric_excess_noise_sig cut has NO DR4 equivalent (column
--            removed) -> replaced by astrometric_gof_al + ruwe, both present
--            in the draft DR4 gaia_source (data model 2026-06-26, sec 1.1).
-- DR4 SCHEMA SOURCE: draft DR4 data model 2026-06-26, sec 1.1 gaia_source
--            (all columns below verified present in the draft PDF).
--            'gaiadr4.' prefix is an assumption; see dr3-to-dr4-tables.md.
-- VALIDATED ON DR3: yes, 2026-08-14, anonymous TAP sync TOP 10 via twin file
--            02_hypervelocity_6d.dr3-validation.sql (identical column names
--            in DR3 except the DR4-removed astrometric_excess_noise_sig,
--            which the DR3 twin still applies as in Marchetti 2019).
-- DIFF-AUDITOR OVERLAP: none beyond the shared TAP client + schema map.
-- PARAMETERS: {PLX_OVER_ERR_MIN}=5   -- Marchetti clean-sample cut
--             {VTAN_MIN}=300         -- km/s, 4.74047*pm/plx pre-filter
--             {RV_ABS_MIN}=300       -- km/s, OR-branch for radial outliers
--             {RUWE_MAX}=1.4         -- spurious-solution guard
-- =====================================================================
SELECT TOP 100000
  g.source_id,
  g.ra, g.dec, g.l, g.b, g.ref_epoch,
  g.parallax, g.parallax_error, g.parallax_over_error,
  g.pmra, g.pmra_error, g.pmdec, g.pmdec_error,
  g.radial_velocity, g.radial_velocity_error, g.rv_nb_transits,
  g.grvs_mag, g.rv_expected_sig_to_noise,
  g.phot_g_mean_mag, g.bp_rp,
  g.ruwe, g.astrometric_gof_al, g.astrometric_excess_noise,
  g.ipd_frac_multi_peak, g.visibility_periods_used,
  g.duplicated_source, g.non_single_star,
  g.has_epoch_astrometry,                    -- feeds the FP-killer fetch
  4.74047 * SQRT(g.pmra*g.pmra + g.pmdec*g.pmdec) / g.parallax AS vtan_kms
FROM gaiadr4.gaia_source AS g
WHERE g.radial_velocity IS NOT NULL
  AND g.parallax > 0
  AND g.parallax_over_error >= 5             -- {PLX_OVER_ERR_MIN}
  AND g.ruwe < 1.4                           -- {RUWE_MAX}
  AND ( 4.74047 * SQRT(g.pmra*g.pmra + g.pmdec*g.pmdec) / g.parallax >= 300
        OR ABS(g.radial_velocity) >= 300 )   -- {VTAN_MIN} / {RV_ABS_MIN}
