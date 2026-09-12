# Full-parent-plane calibration result, 2026-09-12

**CALIBRATION_FEASIBILITY: 12 selected comparison candidates, all 12 measurable
in all three independent observing epochs.** The unchanged minimum was five.
The fixed larger reference footprint addresses the small-cutout calibration
failure. It does not erase that failed experiment, validate a discovery pipeline,
or establish variability of the known target.

## Exactly what changed

The [new protocol](FULL-PLANE-PROTOCOL.md) fixed the natural parent-plane footprint
of the same QL2.1/3.1/4.1 observations before new pixels. No new field, epoch or
unknown candidate selection. Source thresholds, reference selection, target
position, beam-template photometry and null positions are unchanged. Existing
pilot.py, original protocols and result receipts remain byte-identical.

The new [driver](full_plane.py) uses the audited, hash-pinned Dyson tree-aware
timeout helper for network workers. Before network access, tests exercised both
mocked exact tree termination and a real Windows venv launcher with a live child;
the owned descendant was reaped. Access-denied is explicitly not accepted as proof
of process exit. This addresses the earlier transport limitation for these new
requests without claiming the earlier timeout's lifecycle was retrospectively proved.

Execution-context limit: parent independent testing found that the real Windows
cleanup regression can error at `communicate(timeout=10)` under a restricted
sandbox token. The owner-context rerun passed, including actual child cleanup.
All science acquisitions here used that verified owner execution context. Do not
claim cleanup works under every restricted token; future acquisition must use the
same verified context, and an inaccessible worker is not assumed terminated.

Metadata advertised all six sizes before download. All six full science/RMS files
matched the expected bytes: **332,792,640 new bytes**. Including the retained prior
inputs gives **383,028,223 bytes**, under the 500,000,000-byte ceiling. All six
requests succeeded with no retries; acquisition hashes, exact URLs and HTTP headers
are retained in full-plane-acquisition.json. Full FITS remain ignored locally.

## Measured calibration diagnostics

All three pairs pass unchanged field/campaign/date, Jy/beam, beam/grid/WCS and
finite-coverage checks. Each image is 3722 x 3722 with 100% finite science and
positive finite RMS pixels. QL3.1 alone selected the 12 comparison positions;
cross-epoch fluxes did not alter that list and no ratios were pruned.

| Epoch | Common comparisons | Median comparison ratio to QL3.1 | Scaled MAD of ratios | Locally scaled target ratio |
|---|---:|---:|---:|---:|
| QL2.1 | 12 | 0.937962 | 0.056689 | 1.028657 |
| QL3.1 | 12 | 1.000000 | 0.000000 | 1.000000 |
| QL4.1 | 12 | 0.929304 | 0.092570 | 1.080345 |

QL3.1's zero scatter is a self-ratio identity, **not a measurement of calibration
precision**. These are candidate references, not certified invariant calibrators;
intrinsic variability, resolution and residual image systematics can contribute.
Individual reference ratios span 0.827--1.135 (QL2.1) and 0.771--1.251 (QL4.1).
Every selected reference and its full per-epoch measurement is retained in
full-plane-measurement.json, including its fit residual and localization diagnostic.

Target amplitudes are unchanged from the retained small cutouts within floating
point precision: 0.9665, 1.0017 and 1.0057 mJy. Their noise proxies are 0.1874,
0.1555 and 0.1692 mJy. The target recovery gate passes all epochs, with peak
offsets 0.30--0.32 arcsec. The maximum absolute response among the unchanged 24
fixed-null measurements remains 1.992 noise units.

The target's ~3% and ~8% provisional scaled changes must not be interpreted as
detected variability. The noise proxies alone are substantially larger; native
beams differ, no absolute calibration is established, and no common-beam or
population false-positive validation has been completed. No historical fading
rate or physical classification is measured here.

## Verification

**31 tests pass**, including cumulative byte-cap preflight, absolute worker paths,
helper/source identity, a real Windows child-tree timeout, prior numerical/identity
tests, report receipts and small-cutout/full-plane target consistency. Ruff passes.
Both original small-cutout and new full-plane raw-data replays pass. The new report
binds protocol, driver, unchanged pilot, audited helper and acquisition hashes.
The local .gitattributes preserves exact LF source/protocol and CRLF receipt bytes.

```powershell
dyson-revet/.venv/Scripts/python.exe -m unittest discover -s vlass-pilot/tests -v
dasch-pilot/.venv/Scripts/ruff.exe check --no-cache vlass-pilot/full_plane.py vlass-pilot/pilot.py vlass-pilot/tests
dyson-revet/.venv/Scripts/python.exe vlass-pilot/pilot.py replay --followup
dyson-revet/.venv/Scripts/python.exe vlass-pilot/full_plane.py replay
```

Full replays need retained ignored FITS; they are not cold-checkout CI promises.
No further acquisition or expansion was performed.

## Remaining gates

Independent review of the native-beam measurements and comparison morphology;
common-beam/empirical-null validation on independently selected controls;
separation of real source variability from instrumental and selection effects;
an explicit prospectively defined unknown-search population and novelty audit.
These are substantive method gates, not date waits. Any future candidate still
needs independent observing evidence and defensible interpretation. Publication
and submissions remain human-gated.

A [same-data next-validation proposal](NEXT-VALIDATION-PROPOSAL.md) specifies the
minimal common-beam, morphology and correlated-noise/selection-bias checks. It is
not executed and does not authorize an unknown-source scan.
