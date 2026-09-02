-- =====================================================================
-- 01 NSS compact-companion triage input (Gaia DR4, day-one)
-- =====================================================================
-- PURPOSE  : Pull every DR4 astrometric(-spectroscopic) orbital solution with
--            the host photometry/astrometry needed to compute the AMRF
--            (astrometric mass-ratio function) triage statistic offline, plus
--            the DPAC mass posteriors (nss_masses) as a cross-check.
--            This is the INPUT selection; the triage itself is M2 (validated
--            by recovering Gaia BH1 + BH2 from the DR3 fixtures first).
-- CUTS FROM: Shahaf, Mazeh, Faigler & Holl 2019, MNRAS 487, 5610 (AMRF triage
--              statistic A = (a0/parallax) * M1^(-1/3) * (P/yr)^(-2/3));
--            Shahaf et al. 2023, MNRAS 518, 2991 (triage applied to DR3 orbits);
--            El-Badry et al. 2026, arXiv:2608.06453 "Spectroscopic follow-up of
--              compact object binary candidates from Gaia DR3" (lessons: ~40-50% of DR3
--              candidates spurious; BH3 FAILED DR3 significance cuts, so keep
--              the significance threshold a PARAMETER and keep
--              'OrbitalPoorlyConstrained' retrievable rather than hard-cut).
-- DR4 SCHEMA SOURCE: draft DR4 data model 2026-06-26 (see repo copy in
--            data/draft-data-model/gaia-dr4-prerelease-draft-data-model.pdf),
--            sections 10.8 nss_two_body_orbit, 10.3 nss_masses, 1.1 gaia_source.
--            Table prefix 'gaiadr4.' is an ASSUMPTION until the archive
--            publishes its schema name (see ../dr3-to-dr4-tables.md).
-- VALIDATED ON DR3: yes, 2026-08-14, via anonymous TAP sync TOP 10 against
--            gaiadr3.nss_two_body_orbit + gaiadr3.gaia_source using the twin
--            file 01_nss_compact_companion_triage.dr3-validation.sql
--            (renames applied: solution_type -> nss_solution_type,
--             gof -> goodness_of_fit, semi_major_axis -> Thiele-Innes a0).
-- DIFF-AUDITOR OVERLAP (../../IDEAS/gaia-dr4-diff-auditor.md): the join
--            skeleton nss_two_body_orbit x gaia_source and the
--            dr3_neighbourhood crosswalk are shared plumbing; the DR3->DR4
--            rename map lives in queries/dr3-to-dr4-tables.md (shared file).
-- PARAMETERS (edit before running; ADQL has no host variables):
--            {P_MIN}=10           -- days
--            {P_MAX}=4000         -- days; BH3-like 4200 d only partly covered
--            {PLX_OVER_ERR_MIN}=3 -- keep loose; triage happens offline
--            {SIG_MIN}=0          -- 0 keeps OrbitalPoorlyConstrained (El-Badry)
--            {ROWCAP}=100000      -- raise for the real run (async job)
-- =====================================================================
SELECT TOP 100000
  n.source_id,
  n.solution_type,
  n.subtype,
  n.period, n.period_error,
  n.eccentricity, n.eccentricity_error,
  n.semi_major_axis, n.semi_major_axis_error,      -- photocentre a0 [mas], NEW in DR4
  n.a_thiele_innes, n.b_thiele_innes, n.f_thiele_innes, n.g_thiele_innes,
  n.inclination, n.arg_periastron, n.pos_ascending_node,   -- Campbell, NEW in DR4
  n.parallax     AS nss_parallax,
  n.parallax_error AS nss_parallax_error,
  n.mass_function,                                  -- NEW in DR4
  n.mass_ratio, n.mass_ratio_error,
  n.significance, n.gof, n.efficiency, n.bic,
  n.astrometric_jitter,                             -- NEW in DR4
  n.tuwe, n.flags,
  -- host star, for M1 estimate + photometric vetting
  g.ra, g.dec, g.l, g.b,
  g.parallax, g.parallax_over_error,
  g.phot_g_mean_mag, g.bp_rp,
  g.ruwe, g.ipd_frac_multi_peak, g.astrometric_excess_noise,
  g.has_epoch_astrometry,                           -- feed 03_epoch_astrometry_fetch
  -- DPAC's own mass posteriors as triage cross-check (may be NULL)
  m.m1, m.m1_lower, m.m1_upper,
  m.m2, m.m2_lower, m.m2_upper,
  m.fluxratio, m.combination_method, m.flag AS nss_masses_flag,
  -- AMRF numerator pieces; full A needs M1, computed offline (M2 milestone):
  --   A = (a0_mas / parallax_mas) * POWER(m1, -1.0/3.0) * POWER(period/365.25, -2.0/3.0)
  n.semi_major_axis / n.parallax AS a0_over_plx_au
FROM gaiadr4.nss_two_body_orbit AS n
JOIN gaiadr4.gaia_source AS g
  ON g.source_id = n.source_id
LEFT JOIN gaiadr4.nss_masses AS m
  ON m.source_id = n.source_id
WHERE n.solution_type IN ('Orbital', 'OrbitalPoorlyConstrained',
                          'OrbitalAlternative', 'AstroSpectroSB1')
  AND n.period BETWEEN 10 AND 4000            -- {P_MIN}..{P_MAX}
  AND n.significance >= 0                     -- {SIG_MIN}; keep 0, cut offline
  AND g.parallax_over_error >= 3              -- {PLX_OVER_ERR_MIN}
  AND n.parallax > 0
-- NOTE a 1-yr-alias guard (exclude 330..400 d) is applied OFFLINE, not here,
-- so the alias population stays measurable (El-Badry 2026 lesson: keep the
-- rejected class visible instead of silently pre-cutting it).
