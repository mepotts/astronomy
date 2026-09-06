# DASCH Plate-Archaeology Pilot

This directory contains an account-free, narrow M0 feasibility audit for century-scale
photographic-plate work with DASCH Data Release 7. It reproduces a published
positive control, the 1938--1945 high state of T CrB, and compares it with a
deterministically selected nearby field control. It does **not** run a blind
anomaly search or claim a discovery.

## Result

**September 6 extension:** six independently labelled standards all pass the
bounded coverage gate (10,096 clean detections). A flagged Feige 66 year mixes
red/blue plates with a 1.128-mag same-epoch discrepancy. See
[the result and limits](STABLE-RESULTS-2026-09-06.md). This supports emulsion-aware
calibration work, not a blind search or a measured century-scale false-positive rate.

The targeted workflow passes this pilot's frozen light-curve/API gate. After the current documented DASCH
quality flags and a 15-arcsec astrometric cut, the T CrB median brightening is
1.103 mag (367 baseline and 348 high-state measurements). The nearby field
control shifts by only 0.015 mag (23 and 33 measurements), leaving a 1.089-mag
differential signal. All frozen acceptance checks pass.

See [M0-RESULTS-2026-09-02.md](M0-RESULTS-2026-09-02.md) for the interpretation
and limitations. The result establishes that targeted, scripted DASCH work is
practical; it does not establish that a blind survey would have an acceptable
false-positive rate.

The original M0 was completed to a decision on **2026-09-05**. R Cnc (a verified
Mira) passed; the faint/crowded V404 Cyg control had only five clean detections
and failed the three-position coverage gate. Nine official plate cutouts were
retrieved and inspected, including an explicitly exploratory same-series
recovery of V404 Cyg's published 1938 eruption against deeper adjacent epochs.
The nearest-epoch image selection failed first and remains recorded as a failure.

The outcome stops unconditional faint-field/broker annotation. Only a separate
brightness/coverage-limited, externally vetted stable-star false-positive study
is a supported next option. In particular, `class=0, v_flag=0` is not a reliable
stable-star label: the known Mira itself has these catalog flags. No unknown
source was searched. See [the full closeout](M0-EXTENSION-RESULTS-2026-09-05.md).

## Reproduce

The five small public M0 responses (health, two catalog queries, and two known
control light curves) are tracked in Git. Their roles, request bodies, byte
counts, SHA-256 digests, and source endpoints are bound by
`data/provenance.json` so the pilot remains reproducible if the API changes.

```powershell
python scripts/m0_dasch_pilot.py --output out/m0-results-20260902.json
python -m unittest discover -s tests -v
```

The extension's exact known-control responses are retained in a 10.77 MB gzip
bundle under `data/m0-extension-20260905/`, with a per-response manifest. From
the repository root, `python dasch-pilot/scripts/m0_extension.py analyze` verifies
and analyzes this bundle without network access. Rendering the three review
figures also requires Astropy, NumPy, and Matplotlib; use the `render` mode.
The public `fetch`, `images`, and `recovery` modes are for rebuilding the fixed
known-control experiment, not expanding to new targets. Existing cached inputs
are immutable and verified before reuse.

The analysis uses only Python's standard library. It verifies every stored raw
artifact and every effective command-line input both before and after analysis,
checks the catalog/light-curve identity pairs, and rejects detected rows with
missing quality flags. The output contains aggregate statistics only and states
explicitly that no discovery scan ran.

## Sources

- [DASCH DR7 Web API Reference](https://dasch.cfa.harvard.edu/dr7/web-apis/)
- [DASCH DR7 Lightcurve Reduction Guide](https://dasch.cfa.harvard.edu/dr7/reduce-lightcurve/)
- [DASCH DR7 Lightcurve Columns](https://dasch.cfa.harvard.edu/dr7/lightcurve-columns/)
- [daschlab photometry documentation](https://daschlab.readthedocs.io/en/latest/api/daschlab.photometry.Photometry.html)
- [Luna et al. (2020), published positive control](https://arxiv.org/abs/2009.11902)

## Scope and release gate

Any future unknown-source scan must stay private until the multi-control model,
plate-image review, catalog/literature cross-match, and an explicit human
release decision are complete. Publication and outward submission are outside
this pilot.
