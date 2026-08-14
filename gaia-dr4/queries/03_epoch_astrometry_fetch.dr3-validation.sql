-- =====================================================================
-- 03 (DR3 VALIDATION TWIN) named-source-list fetch pattern
-- =====================================================================
-- PURPOSE  : Validate the IN-list source fetch of 03_epoch_astrometry_fetch.sql
--            on DR3, using Gaia BH1 and BH2 as the named list (same rows are
--            the W2 fixtures). DR3 has no has_epoch_astrometry and no public
--            epoch astrometry, so only the fetch pattern is validatable today;
--            DR3's DataLink equivalent (retrieval_type='EPOCH_PHOTOMETRY')
--            proves the transport we will use for EPOCH_ASTROMETRY.
-- IDS FROM : mission brief / Gaia BH1: El-Badry et al. 2023, MNRAS 518, 1057
--            (source_id 4373465352415301632); Gaia BH2: El-Badry et al. 2023,
--            MNRAS 521, 4323 (source_id 5870569352746779008).
-- VALIDATED ON DR3: yes, 2026-08-14, anonymous TAP sync, HTTP 200, 2 rows.
-- ENDPOINT : https://gea.esac.esa.int/tap-server/tap/sync
-- =====================================================================
SELECT
  g.source_id,
  g.designation,
  g.ra, g.dec, g.ref_epoch,
  g.parallax, g.parallax_error,
  g.pmra, g.pmdec,
  g.phot_g_mean_mag, g.bp_rp,
  g.ruwe, g.astrometric_excess_noise,
  g.non_single_star
FROM gaiadr3.gaia_source AS g
WHERE g.source_id IN ( 4373465352415301632, 5870569352746779008 )
