# Independent source-geometry numerical-core review

September 12, 2026 label. **Scoped GO for this pure numerical core; not a
runtime, real-catalogue execution or clean-sky approval.** Read the complete
implementation plan, geometry proposal, current `xmm_source_geometry.py` and
its tests. No actual source-list, map or event arrays, product hashes, new
catalogue coordinates or network requests were used. Only this review document
was written by the reviewer.

## Finding resolved before execution

The initial implementation returned `source/north/east/south/west`, unlike
the unchanged C5/C7 labels required for joining these separate diagnostics.
The author restored `published/north120/east120/south120/west120` and added
explicit aperture/annulus label-sequence assertions. This changed labels, not
coordinates, numerical thresholds or selection. The final source/tests were
reread and rerun after that correction. No remaining scoped blocker was found.

## Independent synthetic verification

All **13 author tests** independently pass under the existing Python runtime;
root-invoked Ruff 0.16.5 also passes on both files. Author tests cover unique,
absent and multiple associations; invalid corrected rows; displaced/invalid
original positions; invalid and duplicate IDs; duplicate positions with distinct
IDs; contact boundaries; RA wrap, poles and antipodes; field-validity categories;
input schemas, empty lists, JSON privacy and input immutability.

Additional reviewer inline experiments, not extra committed unittest methods:

- **100 deterministic synthetic 151-row catalogues**, seed 267019, compared
  all five centres and all three contact classes with independently constructed
  Astropy `SkyCoord.separation` distances: **1,500 count comparisons passed**.
  Fixtures independently introduce invalid original positions, invalid corrected
  positions and duplicate IDs. Association status, all-row denominators,
  extent-category count closure and finite JSON serialization also pass.
- **Three exact computed-distance association probes** at the float immediately
  below 5 arcseconds, exactly 5, and immediately above 5 pass. A temporary,
  restored in-process distance mock isolates the literal comparison from
  trigonometric roundoff; it does not alter source or a real measurement.
- **Twelve direct threshold-neighbour fixtures** at/below/above 20, 30, 50 and
  120 arcseconds pass for all three contact classes.

There is deliberately no new epsilon or uncertainty-dependent matching radius.
Inclusive comparisons act on computed float64 distances; an exact mathematical
tangency represented through sky coordinates can land on either side through
roundoff. These engineering contact flags are not positive intersection areas.

## Correctness and interpretation

Source IDs remain signed integers, never float-promoted. Nonpositive or
out-of-int32-range IDs and duplicate valid IDs are counted; duplicate coordinates
are not deduplicated. No identity-invalid row is dropped to manufacture a unique
association. All rows remain in each region's catalogue denominator.

Association uses corrected positions and requires complete corrected-coordinate
validity plus valid unique IDs across the entire input. A near match alongside
an invalid corrected row is explicitly incomplete, not unique. Zero or multiple
matches do not trigger nearest/brightest selection. Errors and extents do not
alter the fixed 5-arcsecond rule.

Geometry uses original positions independently. Invalid originals are omitted
only from computable contact counts, with their count and incomplete-screen
status retained. They are not asserted distant or clean. A unique corrected
association can coexist with an original-position mismatch or missing original
position; the reported displacement/within-aperture value then preserves that
distinction. The core does not move the aperture or apply a catalogue correction
to image/event coordinates.

Only the unique control row is exempted from the **published aperture's** two
other-source classes. It is retained in every annulus and every negative
aperture. Unresolved association exempts nothing. Annulus contact uses the fixed
inclusive 30–120-arcsecond interval; aperture centre and disk-contact classes
remain distinct at 20 and 50 arcseconds. Each row contributes at most once to
each class; there is no area union or sum of overlapping disk areas here.

Zero, positive and invalid extents partition each contact count. Extent is not
converted into an enclosing radius, and extent error/positional-error fields
remain separate validity/minimum/maximum diagnostics. Zero model extent or zero
contact is not a negligible-wing, empty-sky or stable-background assertion.

Public returns contain no source IDs, row ordinals, absolute coordinates,
coordinate vectors, WCS or private catalogue cache. The planned scalar distance
of a uniquely associated row's original position is retained as a descriptive
offset, not an absolute coordinate. Invalid diagnostics serialize as counts or
`null`, not NaN/Infinity. The strongest label remains
`SOURCE_GEOMETRY_SCREEN_NOT_CLEAN_SKY`.

## Caller obligations, not established by this review

This pure function accepts 0–151 rows for synthetic tests and has no archive
reader. The future runtime must enforce **exactly all 151 retained rows** and
the selected nine-column schema/units/int32 decoding before invoking it. A
smaller or empty input's internally consistent count is not proof of catalogue
completeness. Exact span bounds, unbuffered reads, provenance, partial-byte
accounting, process limits and immutable replay require separate runtime tests.

The caller must also bind the five fixed centres in their reviewed order and
perform the explicit published ICRS-convention to FK5/J2000 transformation.
The core validates shape and coordinate domains but cannot infer frame, epoch,
fixed offsets or correction provenance from numeric arrays. Original and
corrected columns must not be swapped by the decoder. The preserved limits
include catalogue incompleteness, uncertain contaminant radii and absent
per-region temporal exposure: neither this function nor its tests resolve them.

## Final anchors

| Artifact | SHA-256 |
| --- | --- |
| `xmm_source_geometry.py` | `33f483e69dd78ad64a6b015ecfa02a1e49bf5e2aa8da83f7869f560ecb0059be` |
| `test_xmm_source_geometry.py` | `c013dbc2c7d0599b07b7fb7b76094d26f7ffbc1f7567085d941ed63ae80bf68d` |

These hashes were independently recomputed after the label repair. There was
no scientific input execution or runtime authorization in this review.
