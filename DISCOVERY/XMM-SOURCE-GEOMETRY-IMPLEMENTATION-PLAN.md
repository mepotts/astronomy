# Smallest source-list geometry implementation

Planning only, 2026-09-12 label / 2026-09-13 UTC. No source-list values, map pixels, events, other arrays or remote products were read. No executable source was added. This proposes one next frozen stage, not permission to execute it.

## Decision: association and overlap flags first

Implement the selected **7,852-byte source-list pass**, retaining all 151 rows, followed by deterministic association and fixed-region overlap flags. Do not add a map reread, raster-union extension or supported-area calculation to this first stage. Strongest label: `SOURCE_GEOMETRY_SCREEN_NOT_CLEAN_SKY`.

This is a deliberately smaller implementation of the [geometry proposal](XMM-SOURCE-GEOMETRY-NEXT-2026-09-12.md): it evaluates its association and contact rules, but defers the proposal's optional sampled exclusion-union areas. C5/C7 summaries cannot reconstruct where positive map pixels and source disks overlap. Multiplying an annulus's positive-map fraction by its unmasked-catalogue fraction would invent that joint information. Keep the map and source-list diagnostics separate, joined only by the unchanged region labels.

## Exact reader and provenance

Bind C1 outcome, slot-4 receipt, expanded-product and full-header hashes from the proposal. Header-only validation must confirm PRIMARY/SRCLIST identity, FK5/equinox2000, POSCOROK true and its correction provenance, 151 rows, 1,131-byte rows, 266 columns, zero heap, exact selected column names/types/units/offsets, and the stated absence of selected null/scaling/dimension ambiguity. Derive offsets from all declared TFORM widths rather than trusting a copied offset alone, then compare with the fixed contract before opening values.

At absolute row start `77760 + 1131*i`, read only these five spans:

| Span `(offset, bytes)` | Decoding |
| --- | --- |
| `(0,4)` | `>i`: SRC_NUM |
| `(20,20)` | `>ddf`: original RA, DEC, RADEC_ERR |
| `(596,8)` | `>ff`: EP_EXTENT, EP_EXT_ERR |
| `(1088,16)` | `>dd`: corrected RA, DEC |
| `(1120,4)` | `>f`: SYSERRCC |

Use unbuffered binary access (`buffering=0`) with exactly bounded seeks/reads: 755 span reads, 52 selected bytes per complete row. Whole-file hash I/O is separate byte-only provenance work, not selected-column interpretation. No FITS array loader, buffered read-ahead, entire-row fetch, or access to photometric columns.

Count returned bytes immediately, decoded bytes after successful unpacking and before later storage, completed spans, and completed rows. A short span retains its actual returned count; previously decoded spans in the same incomplete row still count. Never relabel an incomplete row as a complete zero-valued row. Keep integer IDs integer throughout; an independent synthetic NumPy structured-dtype oracle should cross-check the stdlib-struct decoder.

Reuse the reviewed exclusive worker/parent/receipt pattern: one 60-second worker, proposed 268,435,456-byte monitored peak and 1-MiB aggregate JSON with 64-KiB terminal reserve. Verify feasibility synthetically before freeze. The parent performs one explicitly additional selected-byte pass; successful worker plus parent totals 15,704 decoded bytes. Every later numerical replay is another 7,852 bytes. Preserve caught partial validation accounting; an externally interrupted pass without a receipt has unknown counts. No retry, substitute product or additional column follows a STOP.

## Deterministic identity and frame handling

1. Preserve every row ordinal internally. Require positive unique signed-int32 SRC_NUM values; retain duplicate/invalid counts instead of dropping rows. Validate original and corrected position pairs independently: both finite, RA in `[0,360)`, Dec in `[-90,90]`. Invalid scientific values make a complete association/screen unavailable, while their row and validity counts remain in the denominator.
2. Reuse C5/C7's fixed published-position convention and cardinal offsets without any new coordinates or recentering. Transform the predeclared ICRS centres to FK5/J2000 locally. Association uses **corrected** catalogue positions. Original catalogue positions are used for geometry in the **uncorrected** map/event coordinate system. Do not transfer the catalogue astrometric correction to the aperture or map.
3. Count all corrected positions at great-circle distance **<=5 arcsec** from the fixed published centre. Record zero, one or multiple matches. Declare a unique *positional association* only if the identity and complete corrected-coordinate checks also pass. One valid near match plus an invalid corrected row is not a proved unique association: the invalid row might hide another match. Do not choose the nearest/brightest, enlarge the radius, switch coordinates, or use errors as an unannounced new matching criterion.
4. For a unique association, report its original-coordinate distance to the fixed published aperture and the descriptive `original_position_within_20_arcsec` flag. Corrected association does not prove the original detector/image position lies inside the unchanged aperture. If it does not, retain that explicit mismatch and do not move the aperture.

RADEC_ERR, SYSERRCC and extent/error values retain separate validity categories and aggregate diagnostics. No unverified quadrature combination or match-confidence probability. Nonfinite/negative values remain invalid, not zero; zero positional error does not mean perfect astrometry. Do not invent a numerical threshold for a "large" positional error in this stage: report it with the fixed match radius and the uncertainty caveat.

## Fixed region accounting

Compute original-position great-circle distances to the five fixed centres in memory. For each aperture report catalogue-centre counts at distance **<=20 arcsec** and fixed 30-arcsec-disk contact counts at **<=50 arcsec**. For each 60–90-arcsec annulus, report disk-contact counts for **30<=distance<=120 arcsec**. Inclusive tangency is an engineering contact flag, not proof of positive intersection area. These flag endpoints are distinct from any later half-open point-membership convention.

Exempt only the uniquely associated control row from the published aperture's other-source counts. Do not exempt it from negative apertures or any annulus. With unresolved association, exempt nothing and explicitly mark the other-source classification unresolved. Counts from invalid original positions cannot be replaced by "no contact"; report valid-row contact counts plus incompleteness.

For each contact class retain finite-zero extent (point-model), finite-positive extent (extended-model), and invalid/unknown extent counts. Every catalogue row contributes once to a given contact count, irrespective of duplicate coordinates. No extent-likelihood filter, image-pixel conversion, flux/likelihood cut or source-radius estimate is introduced.

Public outputs need only five aperture and five annulus records, association multiplicity/status, all-row validation totals, separate positional-error/extent caveats, and fixed-rule/input hashes. Keep row ordinals/IDs, coordinates, WCS and individual distance arrays local in memory; do not export a new source catalogue. If later photon extraction needs exclusion membership, its separately frozen stage must redecode these same fields or bind an expressly authorized local-only derivative; this plan creates no hidden coordinate cache.

## What cannot be established, and the next action

A 30-arcsec disk is a fixed exclusion recipe, not a validated enclosing radius. The source-list proposal's documented extent is a model scale, not a PSF/extended-wing boundary; even zero fitted extent does not certify that wings vanish outside the disk. Therefore zero contact flags cannot become a clean-sky or usable-background verdict. Unknown valid contaminant radius remains unresolved under the unchanged stronger recovery draft.

After this small stage, the practical decision is whether the published control has an unambiguous positional association and which fixed apertures have explicit catalogue-overlap warnings. If association is absent/multiple/incomplete, stop the association-dependent extraction path rather than search for a preferred row. If it is unique, its masks/flags can inform a separately frozen **descriptive known-control counts** experiment with the original exposure, source-confusion and detector-artifact limitations stated. It cannot promote the intended multi-camera recovery contract to PASS or justify unknown-source discovery.

Only if a subsequent question truly needs catalogue-masked supported area should a new stage authorize the map pixels and a synthetic-tested union-mask extension. That calculation must use the spatial union of all disks at both fixed 4/8 quadratures, never sum overlapping disk areas or multiply independent aggregate fractions. It is not required to execute the first useful 7,852-byte flag screen.

## Minimum regression set before freeze

- Exact five-span allowlist, unbuffered access and byte budget; all selected endian types; short span after prior complete spans; decoded-before-copy failure accounting.
- Positive/duplicate/invalid SRC_NUM; invalid original versus corrected coordinates kept distinct; all 151 rows accounted even when association is incomplete.
- Zero/one/two matches, a valid match plus invalid corrected row, RA wrap/pole geometry, and fixed threshold boundary/below/above cases without a data-tuned tolerance.
- Corrected association versus displaced original position; control exemption only in its own aperture; associated control retained in every annulus/negative check.
- Separate centre/contact tests at 20/50/30/120 arcsec, tangency, duplicate coordinates, invalid/zero/positive extents, and no inferred source radius or clean boolean.
- Full synthetic worker/parent/replay, immutable inputs, exact count/label closure, safe partial failures, nonzero-worker rejection and output/privacy budgets.

Reviewed local plan hashes: geometry proposal `8c68194ee1eff6aaf592ab0f13ee0a9df9c3f61ad6bc55b295c85043b30d870c`; unchanged counts draft `7a3e6b99da0a11f547ed43373cb179f90257d9e01a2a2fbdf643cb85bec53c4e`. Semantic statements above rely on the primary references already documented in that geometry proposal; this implementation plan did not add a literature search or assert version-matched source-code proof.
