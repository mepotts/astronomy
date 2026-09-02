# SPHEREx M0 — a warm-tail feasibility kill check

Date fixed: 2026-09-02

## Question

Can public SPHEREx QR2 spectrophotometry add a scientifically useful constraint to the
existing high-latitude extreme-mid-IR-excess screen **now**?

The test is deliberately narrower than the old prospectus premise. Forced photometry is not
novel: IRSA now provides a research-ready Spectrophotometry Tool that uses the Tractor, the QR2
PSF and variance products, and fixed user-supplied positions/morphologies. SPHEREx covers only
0.75–5 microns, while the screen's fitted 100–300 K excesses peak longward of that range. The
only live hypothesis is therefore:

> A very small warm-tail subset may have enough model-predicted 4.8-micron excess for the
> official tool to test the photosphere-plus-single-blackbody fit; the rest of the 223-row
> catalogue should not be processed.

This is a feasibility statement, not a candidate claim.

## Frozen inputs and selection

- Target pool: `../dyson-revet/catalog/dyson-revet_highlat_extreme_IR_excess_v3.csv`.
- Stellar luminosity interpolation: the frozen Pecaut–Mamajek table already used by
  `dyson-revet`, `../dyson-revet/data/EEM_dwarf_UBVIJHK_colors_Teff.txt`.
- Empirical noise check: the two existing QR2 aperture extractions
  `dyson-revet/out/w3_spherex_D_sed.csv` and
  `dyson-revet/out/w3_spherex_I_sed.csv`, restricted to wavelength >= 4.4 microns and
  pixels whose only set flag may be SOURCE (bit 21). Their exact byte counts and SHA-256
  digests are part of the tracked result input contract and are rechecked after use.
- Control pool: the existing Gaia–AllWISE parent harvest under
  `../dyson-revet/data/w4/aip/cells/`. A control must be point-like and astrometrically clean,
  have clean AllWISE flags, W1-W2 consistent with a photosphere, and match the target in W2
  brightness (within 0.25 mag) and sky position (0.1–2 degrees). W3 is deliberately not required:
  these are 0.75–5 micron SPHEREx controls, and demanding a significant photospheric W3 detection
  would remove the faint, high-ecliptic-latitude matches. Controls are pipeline/systematics
  controls, not evidence about any individual object.

For each catalogue row, predict the 4.8-micron excess flux from the catalogue's fitted
temperature, covering fraction, distance, and interpolated stellar luminosity using the same
bolometric blackbody normalization as the original screen. Rank before any SPHEREx query. The
live coverage probe uses the top three rows and one independently selected nearby photospheric
control per row. The exact six-row outbound payload and matched-control identities stay in a
gitignored manifest; tracked results contain aggregates only. The target identities are not
secret: readers can reproduce their ranking from the pre-existing tracked catalog and the
tracked formula in this pilot.

## Live access test

Use anonymous official services only:

1. IRSA TAP `spherex.plane` joined to `spherex.artifact`, counting public science images by
   detector at each blinded position. Count distinct plane IDs (not joined artifact rows), require
   calibration level 2, and restrict to the QR2 pipeline versions observed and frozen on
   2026-09-02 (`6.4`, `6.5.3`--`6.5.7`); a new version requires a dated protocol update.
   A coordinate-free distinct-version TAP response proves those values were live; its
   query, exact stored bytes, and SHA-256 are recorded in the tracked result.
2. The current IRSA mission and Spectrophotometry Tool documentation, preserved byte-for-byte
   in the ignored raw cache and named by SHA-256 in the tracked result.
3. An anonymous AWS S3 ListObjectsV2 response for `nasa-irsa-spherex/qr2/level2/`, likewise
   preserved and hashed, to prove that the public cloud route is alive without downloading a
   bulk FITS product.

Every live response is written by atomic replacement, then hashed from the stored file and
reverified before the aggregate result is atomically replaced. A partial or changed cache
cannot support a completed result.

IRSA's own runtime approximation, `hours = 0.000463 * n_images + 0.013`, is reported separately
for all bands and for the warm-window D5+D6 images. It is an estimate, not a measured runtime.

## Decision gates fixed before the live coverage probe

- **GO**: at least 10 catalogue rows exceed the conservative empirical 5-sigma warm-window
  floor, all three target probe rows have all six detectors, their median D5+D6 estimated
  runtime is <= 6 hours, and every paired control has D5+D6 coverage within 6 hours.
- **NARROW/PIVOT**: exactly one row exceeds that floor, the leading row has all six
  detectors, and the exact three-row experiment—leading row, its paired photospheric
  control, and the fixed second-ranked subthreshold falsifier—has D5+D6 coverage within
  6 hours per row. The next experiment is only those three rows through the official
  Spectrophotometry Tool.
- **KILL**: no row exceeds the floor, the leading row lacks D5/D6 coverage, or a successful
  coverage query shows that any row required by the fixed GO/NARROW experiment lacks its
  required detector/runtime coverage. Do not run forced photometry for this use case.
- **BLOCKED**: the official anonymous schema/coverage routes cannot be verified, or two
  to nine rows exceed the floor so the fixed second-ranked target is no longer the
  required subthreshold falsifier. That latter case requires a newly frozen manifest and
  protocol; it must not silently reuse pair 2.

Sending the exact position list to an external cone/TAP service is an outward action. If that
payload is not explicitly authorized, only the coordinate-free public schema/docs/AWS
probe may run and the positional-coverage gate is **BLOCKED**; all-sky mission language is not a
substitute for measuring the selected positions.

The empirical floor is five times the worse of the two inverse-variance stacked errors from the
two existing warm-window extractions. It is intentionally conservative because those were simple
aperture measurements; a future Tractor gain is something the pilot must demonstrate, not assume.

## Non-claims and gates

- No new coordinate, source identifier, per-object flux, or ranked name enters a tracked artifact;
  the upstream catalog remains the public, reproducible source of the target ranking.
- No coordinate-bearing payload is sent to IRSA or any other external service without explicit approval
  for that exact six-row target/control payload. The coordinate-bearing command additionally
  requires its exact private-manifest SHA-256 as an authorization argument and refuses a missing
  or mismatched digest before making any network request.
- No blind all-sky/source-discovery scan is permitted by this M0.
- No publication, public candidate disclosure, proposal, message, account creation, or submission
  is authorized.
- Any official-tool spectrum must be downloaded immediately, hashed, kept private, and graded
  against its paired controls, flags, `fit_ql`, and `flux_bkg` before interpretation.
