-- =====================================================================
-- 03 Epoch-astrometry fetch template for a named source list (Gaia DR4)
-- =====================================================================
-- PURPOSE  : Given a hand-curated source list (exosat-rv companion hosts,
--            microlensing lens candidates, triage survivors from query 01,
--            HVS survivors from query 02), confirm epoch astrometry exists
--            and pull the source rows that anchor the epoch-level fit.
-- IMPORTANT: DR4 epoch astrometry is NOT a TAP table. Draft data model
--            2026-06-26, sec 3.1 'epoch_astrometry [DataLink]': "this table
--            is not available through the main archive TAP interface. Data
--            are delivered via the Massive Data service indexed by the VO
--            DataLink protocol"; the astroquery retrieval type is
--            EPOCH_ASTROMETRY. So the flow is:
--              (1) run this ADQL to get source_ids with has_epoch_astrometry
--              (2) in Python:
--                    from astroquery.gaia import Gaia
--                    Gaia.load_data(ids=id_list,
--                                   retrieval_type='EPOCH_ASTROMETRY',
--                                   data_release='Gaia DR4')
--              (3) fit with gaiasupdate (see ../scripts/fit_prerelease_*.py,
--                  proven on the June 2026 pre-release sample).
--            Boolean literal note: the draft data model shows both
--            has_epoch_astrometry='true' and ='t'; if the DR4 archive rejects
--            the string form, try the bare boolean - record which works on
--            release day in dr3-to-dr4-tables.md.
-- SOURCE LISTS (fill {SOURCE_ID_LIST}; DR4 source_ids are NOT the DR3 ones -
--            resolve via gaiadr4.dr3_neighbourhood first, see query at bottom):
--            . exosat-rv companion hosts (../exosat-rv/, M20-M24 roster)
--            . microlensing lens candidates (W4, later)
--            . Gaia BH1/BH2 (DR3 ids 4373465352415301632 / 5870569352746779008,
--              fixtures in ../fixtures/)
-- VALIDATED ON DR3: yes, 2026-08-14, anonymous TAP sync: the IN-list fetch
--            pattern ran against gaiadr3.gaia_source with the BH1/BH2 ids
--            (twin file 03_epoch_astrometry_fetch.dr3-validation.sql, 2 rows).
--            has_epoch_astrometry itself cannot be validated before DR4.
-- DIFF-AUDITOR OVERLAP: the dr3_neighbourhood crosswalk below is the same
--            join the diff-auditor needs for every DR3->DR4 comparison; keep
--            the two projects' copies in sync via dr3-to-dr4-tables.md.
-- =====================================================================
SELECT
  g.source_id,
  g.designation,
  g.ra, g.dec, g.ref_epoch,
  g.parallax, g.parallax_error,
  g.pmra, g.pmdec,
  g.phot_g_mean_mag, g.bp_rp,
  g.ruwe, g.astrometric_excess_noise,
  g.has_epoch_astrometry,
  g.non_single_star
FROM gaiadr4.gaia_source AS g
WHERE g.source_id IN ( {SOURCE_ID_LIST} )
  AND g.has_epoch_astrometry = 'true'

-- ---------------------------------------------------------------------
-- Companion query: resolve DR3 source_ids to DR4 source_ids first.
-- The DR4 source list is NEW; ids are not stable across releases (proof:
-- Gaia BH3 is 4318465066420528896 in DR3 [Panuzzo et al. 2024, A&A 686 L2]
-- but 4318465066420528000 in the DR4 pre-release sample file).
-- Draft data model sec 7.3 dr3_neighbourhood [TAP].
-- ---------------------------------------------------------------------
-- SELECT x.dr3_source_id, x.source_id AS dr4_source_id,
--        x.angular_distance, x.magnitude_difference, x.probable_match
-- FROM gaiadr4.dr3_neighbourhood AS x
-- WHERE x.dr3_source_id IN ( {DR3_SOURCE_ID_LIST} )
