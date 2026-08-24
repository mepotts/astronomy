# DR3 → DR4 table/column mapping (release-day patch list)

*Every rename the `queries/*.sql` files assume, so 2026-12-02 is a patch, not a rewrite.
DR4 side sourced from the **draft** DR4 data model, issue D rev 0, dated 2026-05-20,
distributed 2026-06-26 ([zip](https://anonftp.cosmos.esa.int/pub/GAIA_PUBLIC_DATA/Gaia_DR4/dr4-prerelease/gaia-dr4-prerelease-draft-data-model_2026-06-26.zip),
local copy `data/draft-data-model/gaia-dr4-prerelease-draft-data-model.pdf`, 1231 pp).
The draft warns the final model "is subject to change ... without any public notification" —
re-verify this whole file against the live archive schema (`TAP_SCHEMA.columns`) on release day.
Shared artifact with [`../../IDEAS/gaia-dr4-diff-auditor.md`](../../IDEAS/gaia-dr4-diff-auditor.md).*

## Schema prefix

| assumption | status |
|---|---|
| `gaiadr4.` as the TAP schema prefix (by analogy with `gaiadr3.`) | **UNSOURCED** — the draft data model gives table names only, no schema prefix; check on day one |

## Identity: source_id MAY change DR3 → DR4 (resolve anyway; the M1 "proof" was wrong)

**CORRECTED 2026-08-16 (M2).** M1 recorded "Gaia BH3 is `4318465066420528896` in DR3
(Panuzzo et al. 2024) but `4318465066420528000` in the pre-release file" — that is false.
Panuzzo et al. 2024 ([A&A 686, L2](https://doi.org/10.1051/0004-6361/202449763)) prints
`Gaia DR3 4318465066420528000` (verified in the arXiv:2404.10486 LaTeX source, line 174);
`...000` is live in `gaiadr3.gaia_source` and SIMBAD; `...896` does not exist in DR3.
In fact **all 12 pre-release sources carry their DR3 source_ids unchanged** (verified by
TAP id + cone-search match, 2026-08-16).

What survives: DR4 rebuilds the source list, so ids CAN change, and ESA ships the
crosswalk `dr3_neighbourhood` (draft data model §7.3: `source_id` (DR4), `dr3_source_id`,
`angular_distance` [mas], `magnitude_difference`, `probable_match`) precisely because of
that. **Resolving stored DR3 ids through the crosswalk on day one remains the practice**
(cheap insurance) — but no observed renumbering exists yet, and no code should *depend*
on ids changing either.

## Tables the queries touch

| DR3 (validated live 2026-08-14) | DR4 draft | notes |
|---|---|---|
| `gaiadr3.gaia_source` | `gaia_source` (§1.1, 370 cols) | kept; many new cols (see below) |
| `gaiadr3.nss_two_body_orbit` | `nss_two_body_orbit` (§10.8) | kept; Campbell elements + `mass_function` now published directly |
| — (none) | `nss_masses` (§10.3) | NEW: m1/m2 16–84% posteriors, `fluxratio`, `exoplanet_candidate_hrd_proba`, `lowmass_candidate_hrd_proba` |
| — | `nss_multiple_orbits`, `nss_multiplicity`, `nss_resolved_pair`, `nss_epoch_flags`, `optical_pair` (§10.x) | NEW NSS family members |
| `gaiadr2.dr2_neighbourhood`-style | `dr3_neighbourhood` (§7.3) | the DR3→DR4 id crosswalk |
| — (DR3 has no epoch astrometry) | `epoch_astrometry` (§3.1) — **[DataLink], NOT TAP** | "not available through the main archive TAP interface"; astroquery `retrieval_type='EPOCH_ASTROMETRY'`; discover via `has_epoch_astrometry` flag (in both `gaia_source` and `all_source_flags`) |
| — | `bright_source_epoch_astrometry` (§6.2), `crowded_field_epoch_astrometry` (§8.2) | separate epoch-astrometry products for special regimes |
| — | `all_source_astrometry`, `all_source_flags`, `all_source_photometry`, `all_source_rvs`, `all_source_match` (§2.x) | NEW "all 2.8B processed sources" family (gaia_source is the ~2B subset) |

## Column renames / removals assumed by the queries

### nss_two_body_orbit

| DR3 | DR4 draft | queries affected |
|---|---|---|
| `nss_solution_type` | `solution_type` | 01 |
| `goodness_of_fit` | `gof` | 01 |
| derive a0 from `a_thiele_innes,b,f,g` | `semi_major_axis` (+ `_error`) published directly; A/B/F/G still present | 01 (keep the Thiele-Innes formula as fallback) |
| — | NEW: `inclination`, `arg_periastron`, `pos_ascending_node`, `mass_function`, `mass_ratio`, `astrometric_jitter`, `bic`, `tuwe`, `subtype`, `bootstrap_probability` | 01 |
| solution types incl. `OrbitalTargetedSearch`, `OrbitalTargetedSearchValidated`, `OrbitalAlternativeValidated` | draft list has `Orbital`, `OrbitalPoorlyConstrained` (significance < 5), `OrbitalAlternative`, `AstroSpectroSB1`, **`AstroSpectroSB2`** (new), `VIMO`, SB/eclipsing types; no `*TargetedSearch*` variants | 01 (solution-type list is a parameter) |

### gaia_source

| DR3 | DR4 draft | queries affected |
|---|---|---|
| `astrometric_params_solved` | `astrometric_params` (short; bit meaning re-documented) | none directly (recorded for diff-auditor) |
| `astrometric_excess_noise_sig` | **REMOVED** (only `astrometric_excess_noise` remains) | 02 — Marchetti's `≤ 2` cut has no DR4 equivalent; replaced by `astrometric_gof_al` + `ruwe` |
| `phot_bp_rp_excess_factor` | **REMOVED** from gaia_source (per-band flux statistics columns appear instead) | none of ours; noted for diff-auditor |
| `ref_epoch` = 2016.0 | `ref_epoch` kept; DR4 reference epoch = **J2017.5 TCB** (ESA BH3 notebook `DR4_REFERENCE_EPOCH`; pre-release VOTable TIMESYS timeorigin JD 2455197.5 TCB for epoch data) | any epoch math |
| `radial_velocity` | kept, plus NEW `radial_velocity_single`, `radial_velocity_sys`, robust rv_* statistics family | 02 unaffected |
| — | NEW: `has_epoch_astrometry`, `non_single_star` (kept), `source_ids_sharing_transits`, `astrometric_primary_flag`, ... | 03 |

### Columns verified present & same-named in DR4 draft gaia_source
`parallax`, `parallax_error`, `parallax_over_error`, `pmra`, `pmdec` (+errors), `ruwe`,
`astrometric_excess_noise`, `astrometric_gof_al`, `phot_g_mean_mag`, `phot_bp_mean_mag`,
`phot_rp_mean_mag`, `bp_rp`, `radial_velocity`, `radial_velocity_error`, `rv_nb_transits`,
`grvs_mag`, `rv_expected_sig_to_noise`, `ipd_frac_multi_peak`, `ipd_gof_harmonic_amplitude`,
`visibility_periods_used`, `duplicated_source`, `l`, `b`, `ref_epoch`, `designation`.

## Epoch-astrometry record format (pre-release ground truth)

The pre-release VOTable (`Gaia DR4_RC3` tag) has one row per source×FoV-transit with per-CCD
arrays; 36 fields: `solution_id, source_id, transit_id, ra0, dec0, agis_source_excess_noise,
obs_time_tcb, obs_time_bary_corr, scan_pos_angle, zeta, parallax_factor_al/ac,
colour_factor_al/ac, nu_eff_used_in_astrometry, nu_eff_error, centroid_pos_al/ac,
calculated_pos_ac, centroid_pos_error_al/ac, used_by_agis_al/ac, transit_acq_flags,
transit_proc_flags, ccd_proc_flags, multipeak, blended, ipd_error_al/ac, g_mag, g_class,
gates, source_dist_to_last_ci, ac_rate, sub_pixel_coord, mu`.
`gaiasupdate.epoch_astrometry.GaiaEpochAstrometryArchive` consumes exactly this layout.

## Parallax zero-point inputs (added M8, 2026-08-24)

`scripts/m8_zeropoint.py` needs FIVE `gaia_source` columns, and the day-one arm cannot
apply the Lindegren+2021 correction without all five. **Diff them on the day** -- they are
not otherwise in this map, and `astrometric_params_solved` is already flagged above as a
likely rename:

| DR3 column | DR4 status (read off the draft data model PDF, M8) | note |
|---|---|---|
| `phot_g_mean_mag` | present | |
| `nu_eff_used_in_astrometry` | **present** (draft pp. 18, 25, 75, 76, ...) | 5-parameter solutions |
| `pseudocolour` | **present** (draft pp. 18, 19, 22, 27, 76, 77, ...) | 6-parameter solutions |
| `ecl_lat` | **present** (draft pp. 16, 55, 67, 87, ...) | |
| `astrometric_params_solved` | **RENAMED to `astrometric_params`** (draft p. 19: "Bitwise code describing which astrometric parameters are provided (short)") | the 31/95 guard reads this; get it wrong and `zpt.get_zpt` **RAISES** rather than returning NaN. **Confirm the bit encoding too** -- the draft describes a bitwise code, not DR3's 3/31/95 integers |

**AND DR4 SHIPS ITS OWN CORRECTION -- PREFER IT.** The draft data model declares, in both
`gaia_source` (p. 20) and `all_source_astrometry` (p. 74):

> `tentative_parallax_bias` : Parallax bias correction (double, Angle[mas]). "This is the
> parallax bias correction computed based on the recipe in [the DR4 astrometry paper].
> **This correction is to be subtracted from `parallax` to get the corrected parallax.**"

Same convention as Lindegren+2021. Pull it in Phase 0, use it in preference to the L21
recipe, and keep L21 as the cross-check -- see DR4-DAY-RUNBOOK Phase 3.4. The name carries
"tentative" and the model is a draft, so verify it exists and is non-null before relying
on it.

## Day-one checklist

1. `SELECT schema_name FROM TAP_SCHEMA.schemas` — pin the real prefix.
2. Diff this file against `TAP_SCHEMA.columns` for the four tables above.
3. Patch the three DR4 `.sql` files; re-run their DR3 twins as regression.
4. Resolve every stored DR3 source_id through `dr3_neighbourhood` before use.
