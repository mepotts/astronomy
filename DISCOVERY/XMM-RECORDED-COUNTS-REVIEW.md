# Independent pure recorded-counts review

September 12, 2026 label. **Scoped GO for this pure counter, not C9 execution
or calibrated recovery.** Read the complete recorded-counts plan, source,
tests, retained-schema preparation note and prospective C9 protocol. No real
event values, source-list/map arrays, product contents or network resources
were accessed. The reviewer edits only this report.

## Independent verification

All **13 author tests** independently pass, as does root-invoked Ruff 0.16.5.
Tests cover the fixed grid, empty/maximal chunks, cut priority, exact energy
and pattern boundaries, camera-specific null semantics, header endpoints,
duplicate/unsorted times, supported CCD sets, signed flags, overlapping regions,
missingness diagnostics, forged masks/accounting, configuration changes,
overflow and split-chunk closure.

Additional reviewer inline experiments, not additional committed unittest
methods:

- **2,913 synthetic rows across all three cameras** were packed into synthetic
  FITS row bytes and passed through the actual pure EVENTS decoder before the
  counter. For every one of the 255 fixed edges, fixtures include its immediate
  lower float, exact edge and immediate higher float; they also include both
  camera-header endpoints, adjacent outside values, nonfinite times, explicit
  nulls and mixed cuts. Random seed 135822; no observed counts informed inputs.
- An independent scalar loop applies the written cut order and searches the
  declared half-open intervals directly. It reproduces every rejection count,
  complete circle/annulus histogram, accepted total and per-CCD region vector.
  Decoding/counting the same bytes in chunks of **1 and 37 rows** preserves
  those exact histograms and rejection totals.
- For both supported accumulation shapes, adding one to int64 maximum minus
  one reaches exactly maximum; adding zero to maximum succeeds; adding one to
  maximum fails before arithmetic. Inputs remain unchanged.

These experiments read only synthetic in-memory byte buffers. They do not
benchmark real-event performance or validate the future streaming runtime.

## Selection and binning correctness

The component requires the exact camera configuration and float64 edges
`738530124.914825 + 200*k`, k=-8 through 246, rather than accepting a shifted
or event-derived grid. There are 254 bins. Right-sided edge lookup implements
half-open bin membership: an event exactly on an interior edge belongs only
to the following bin. Inclusive camera-header endpoints are a separate,
explicit plan choice, not a GTI convention or a claim of time calibration.

Rejections are disjoint in the required order: selected-field missingness,
unsupported CCD, outside header interval, outside strict 200<PI<12000,
PATTERN above 4/12, then nonzero FLAG. Earlier rejection wins without deleting
later overlapping field-diagnostic counts. pn PATTERN 13 and PI -32768 remain
nulls, whereas MOS's corresponding scalars have no declared null. Signed
FLAG zero testing and its uint32 bit-view consistency are checked, not inferred
from a threshold on the sign bit.

All fixed camera header intervals lie inside the fixed grid, so a surviving
row outside that grid is not expected under the bound configuration. The
inside/outside totals are still explicit rather than silently discarding rows.
Neither accepted counts nor zero bins establish live exposure.

## Masks, counts and denominators

The counter checks all nine native-endian dtypes, equal lengths, null/nonfinite/
valid masks reconstructed from values and the retained camera null profile,
joint row validity, FLAG bit view, and complete decoder-byte/row accounting.
It rejects forged or inconsistent masks instead of trusting a supplied
`row_valid` Boolean alone. The 10,000-row cap bounds every chunk histogram and
per-CCD sum well below int64 overflow.

Geometry validity cannot include null X/Y and must cover every decoder-row-valid
event. Circle and annulus masks must be false on invalid geometry and cannot
overlap for the same centre. Cross-centre overlap is deliberately allowed;
the sum of all regional counts is not an event partition. The API accepts
either XY-valid or joint-row-valid projection conventions, as separately
approved for the pure core. **C9's current protocol chooses XY-valid projection**;
that runtime must preserve its particular choice.

Returned increments retain every bin and five region columns, plus every
supported CCD including zeros. Accepted plus rejected rows close over input;
CCD accepted and in-grid totals close over camera totals; summed CCD region
vectors close over histogram columns. The raw annuli remain explicitly
unmasked. Field-validity diagnostics may overlap across columns and therefore
must not be summed as an exclusive rejection ledger.

`checked_add_counts` rejects negative counts, dtype/shape mismatches, broadcasting
and int64 overflow before addition. It returns a fresh read-only sum and does
not mutate its inputs. Python scalar ledger accumulation, row/chunk ordering
and camera-complete bounds still belong to the wrapper; the helper is not a
complete aggregate-receipt validator.

## Runtime and scientific boundaries

Boolean masks alone cannot prove they describe the same photons, correct WCS
or fixed centres. Product/header/decoder/geometry provenance, row ordering,
the actual selected-field null profile and interpretation of MOS PI units
must be bound and checked by the runtime, not inferred from these counts.
This review does not inspect actual header values anew or authorize photons.

The outputs contain only histograms, aggregate counts/CCD labels and limitations,
not event coordinates or individual timestamps. Fixed histogram edges are
allowed prospective metadata. The component computes no rate, background
subtraction, source-exclusion area, GTI exposure, significance, top bin,
episode, period or discovery. Generic cuts are not an EXOD-equivalent detector
screen. C8 contacts and C5/C7 static-map caveats must accompany later
interpretation; the stronger recovery requirements remain unmet.

No core blocker was found. C9 still needs independently reviewed streaming,
safe partial read/decode/geometry/accumulation accounting, immutable replay,
artifact closure, synthetic full-size resource checks and a separate frozen
execution authorization.

## Final reviewed anchors

| Artifact | SHA-256 |
| --- | --- |
| Counter | `5094b15b735619c5de25f7c6fe7a4f5207f82c8c7bc64cac6565678f8975090c` |
| Counter tests | `5e5b1bc15646ab12c856582142cad6331019ff9e23455a961761b3e4d374df9c` |
| Recorded-counts plan | `141a6cbb7d987c1d2179391e50af9a9c306b21347275856696bf2ccb7e397812` |

All three hashes were independently recomputed. No author source or test was
changed by this reviewer.
