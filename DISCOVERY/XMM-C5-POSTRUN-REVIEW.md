# C5 independent post-run receipt and aggregate audit

September 12, 2026. **Diagnostic execution accepted; current pn-plus-MOS1
source-region support evidence is not established.** This is not a burst
recovery or discovery result.

The parent reports execution after freeze `9cef69c` and one subsequent
successful numerical replay. This independent review inspected only saved
receipts, aggregate summaries, source/protocol bindings and retained header
hashes. It did not decode another map, hash a FITS product, perform a new WCS
fit or access network data. The parent's numerical replay is distinct from
this receipt/aggregate audit; this review does not independently rederive
actual pixel classifications.

## Integrity and execution scope

Verified the supplied [outcome](XMM-C5-2026-09-12-data/outcome.json) SHA-256:
`58d8526abdaeb0347cecb252b740fcbd8b5f6956bf89a661b08eb5210d892a36`.
It records exit zero, completed parent assessment, both maps OK, all 20 fixed
regions summarized, and `STATIC_SUPPORT_APPROXIMATION_NOT_COVERAGE`.
MOS2 remains `UNAVAILABLE`; coordinate/WCS persistence remains false.

Read-only checks passed:

- Eight outcome artifact hashes, seven worker artifact hashes and six pinned
  dependency hashes: 21 checks, plus the supplied outcome hash. Exact artifact
  name closure was checked, not only a matching subset.
- Six additional source/test/protocol/prior-outcome/header hash checks and
  the worker-start binding hash. The fixed counts-definition hash remains
  `7a3e6b99da0a11f547ed43373cb179f90257d9e01a2a2fbdf643cb85bec53c4e`.
- Worker/parent ledgers, map byte totals and validation-pass counters agree.
  The two start markers are ordered at approximately 0.141 and 0.563 seconds,
  within the prospective 60-second limit. Reported worker and parent monitored
  peaks are each 78,749,696 bytes, below 500,000,000 bytes.
- JSON accounting matches 74,135 bytes before worker/outcome receipts,
  75,388 before outcome and 77,712 total, below the fixed cap.
- All 20 label/kind entries occur in the fixed order. All 40 resolution
  summaries and 200 category groups satisfy the checked count/area/fraction
  arithmetic, category partition, sampled-parent-pixel count bounds and
  reported analytical-area difference identities.

| Execution binding | SHA-256 |
| --- | --- |
| Runtime | `5e7af10b0d8ac5ea8272229efb8a618a392c92d802e6efc401e6b3a54cb5a05b` |
| Runtime tests | `51fa37948ea7fcb9a5fd41d1d232a835f7cf04027a6b9d385752b35aac9c3007` |
| Protocol snapshot | `7bed41ff48eaaee04761f49a924ac3dedd14611d41156b4b1048aa41d416b062` |
| pn map result | `b64e0ea2e0ec32f06ac8a899c1b55247e3fc552c5ad063ba4cec94563a9186df` |
| MOS1 map result | `5f984bcfea5e2052723f16a15edc84d20004a9ebdf78e48151b8517ac2b4e6f2` |

The source hash is unchanged from the [accepted runtime review](XMM-C5-REVIEW.md).
Thus its selected-header contract remains primary CDELT-only RA/DEC TAN,
degree units, verified legacy FK5/equinox2000 explicitly mapped to RADESYS,
`fix=False`, and no imported alternate linear WCS. Fixed centres use the
prospectively adopted ICRS convention followed by FK5/J2000 conversion. This
is not independent astrometric calibration or a justification for changing
the centre after seeing the zeros.

Only the two approved 648-by-648 big-endian float32 primary payloads were
eligible under the bound reader: 1,679,616 bytes each, 3,359,232 per full pass.
The worker and parent validation passes are separately recorded. Including
the parent's reported subsequent replay, there are **three known passes,
10,077,696 decoded bytes**, not one supposedly cost-free verification pass.
Hash/header reads are separate. This review adds no fourth decoding pass.
Zero compressed/expanded storage reported in the C5 directory does not mean
zero input reads.

## Both fixed-resolution results

Entries below are **estimated percentage of sampled spherical region area
assigned to finite-positive accumulated map pixels**, not exposure percentage
or live-time fraction. Four/eight are subpixels per axis; eight was frozen as
nominal. All sampled nonpositive area here belongs to the zero category:
negative, nonfinite and out-of-image categories are zero at both resolutions
for every region. That statement is about these sampled regions, not every
pixel in either whole map.

| Region | pn, 4 | pn, 8 | MOS1, 4 | MOS1, 8 |
| --- | ---: | ---: | ---: | ---: |
| Published circle | 100.0000 | 100.0000 | 0.0000 | 0.0000 |
| Published annulus | 95.3732 | 95.3370 | 0.0000 | 0.0000 |
| North circle | 100.0000 | 100.0000 | 0.0000 | 0.0000 |
| North annulus | 100.0000 | 100.0000 | 32.8453 | 32.8269 |
| East circle | 100.0000 | 100.0000 | 51.0757 | 50.9640 |
| East annulus | 99.1437 | 99.1441 | 50.3467 | 50.3244 |
| South circle | 84.4745 | 84.5863 | 0.0000 | 0.0000 |
| South annulus | 96.9785 | 96.9689 | 0.0000 | 0.0000 |
| West circle | 100.0000 | 99.9801 | 0.0000 | 0.0000 |
| West annulus | 96.7532 | 96.7490 | 0.0000 | 0.0000 |

Source receipts: [pn](XMM-C5-2026-09-12-data/map-1-result.json) and
[MOS1](XMM-C5-2026-09-12-data/map-2-result.json). Circle/annulus radii remain
20 and 60–90 arcseconds; cardinal negative centres remain 120 arcseconds away.
No poorly supported region was replaced or discarded.

The pn source circle is positive at all selected subpixels at both
resolutions; the source annulus has nominal zero-area fraction
0.04662972098054731. The pn south circle has nominal zero fraction
0.15413686790568357. MOS1's source circle **and** annulus are entirely
zero-classified at both resolutions, while the east circle is only
0.5096401117490299 positive at the nominal resolution. Neither the source
deficit nor the spatial negative results can be hidden by reporting pn alone.

The largest absolute 4-versus-8 positive-fraction difference is
0.0011179437420825167, or approximately 0.111794 percentage points. The
largest absolute fine-grid total-area difference relative to analytical
spherical area is approximately 0.087833%. These are comparisons between
the fixed quadratures and analytic full area, **not certified discretization
error bounds**, uncertainties on coverage, or grounds to choose a favorable
resolution.

## Concrete warning against a clean-region interpretation

The pn west circle illustrates why the predeclared proximity limitations
matter. Its coarse result selects zero zero-valued subpixels, but its fine
result selects **one**, yielding nominal zero fraction
0.00019908415441912368. Meanwhile its nearest unsupported **pixel centre**
is 22.393491592187438 arcseconds away, giving a positive centre-distance
margin of 2.393491592187438 arcseconds beyond the 20-arcsecond radius.

That positive centre margin does not exclude overlap with the unsupported
pixel's finite area. Choosing the coarse result or interpreting the margin
as a guaranteed edge clearance would incorrectly erase observed fine-grid
unsupported sampling. Similarly, annulus proximity may refer to a pixel in
the central hole; it is not itself an annulus-intersection measurement.

## Scientific disposition

The diagnostic ran successfully but does not establish the current intended
pn-plus-MOS1 source-region support evidence. A wholly zero sampled MOS1
source aperture/annulus in this specific accumulated product cannot be used
as affirmative simultaneous support for the stronger recovery draft.
MOS2 remains unavailable in this stage, so it cannot be silently counted as
the missing confirming camera.

Conversely, these zeros do **not** prove that MOS1 had no exposure at every
time, identify a physical chip/window/bad-pixel cause, establish the absence
of photons, or demonstrate an astrophysical disappearance. Product band/FLAG
selection, unavailable GTI references and the limits of accumulated-map
semantics remain unresolved for per-bin exposure. The sampled C4 attitude
diagnostic cannot repair that gap or certify continuous geometry.

The stronger recovery gate therefore remains unmet. Any subsequent MOS2
metadata/acquisition or a narrower descriptive photon screen must be
separately authorized/frozen, preserve all original camera/control outcomes,
and state its unmet exposure, contamination and confirmation requirements.
Do not change apertures, offsets, resolution or coordinate convention in this
frozen result to manufacture support. No new requests, photon processing,
physical-cause diagnosis, recovery claim or discovery claim accompanied this
audit.
