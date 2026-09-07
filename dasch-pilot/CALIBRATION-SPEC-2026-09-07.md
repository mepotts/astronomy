# Matched-colour instrumental validation, 2026-09-07

Frozen before new exposure metadata or holdout curves. The six September 6 SPSS
controls are development diagnostics, never independent long-term negative truth.
Use the next six numeric IDs under the *same* Accepted / no-note (`---` means
missing) / amplitude <=0.010 / declination 0..60 selection as held-out controls.
No replacements for missing sources or coverage. Retain all outcomes.

Retrieve exposure lists for all twelve, and querycat/lightcurve for the six new
controls. At most 24 new requests, 16 MiB each, 30-second timeout. Existing curves
and catalogue must match their September 6 manifest hashes. Responses and request
bodies are retained with SHA256, and this LF-normalized specification is bound
before acquisition. Resumption uses only byte-verified cached responses.

## Fixed algorithm

Keep unchanged standard AFLAGS and 15-arcsecond positional checks. Join imaging
exposures by (series, plate_number, mosaic_number, solution_number), not plate
alone. Conflicting duplicate identities are errors; logbook-only rows are not
imaging joins. Where both exposure numbers are defined they must agree.
Use finite `median_colorterm_apass`, explicitly a plate representative from the
first WCS solution, not an exposure-specific fitted colour term. Thus this is
matched instrumental response, not a full recalibration to an absolute band.

For each of the fixed five-year windows [1880,1885), ..., [1985,1990), match each
in-window detection to out-of-window detections of the **same series**, with
absolute colour-term difference <=0.10. Exclude the window plus one year on each
side from baseline estimation. Require >=20 baseline detections spanning >=5
calendar years. Use the closest 50 in colour term (JD breaks ties), subtracting
their median magnitude. No fitted temporal trend and no interpolation into an
unsupported colour response. Missing support remains missing, not quiet.

An eligible window has >=10 matched detections spanning >=1 year, with >=2 plate
series contributing >=5 each. A flag requires the median residual in at least
two such series to exceed 0.50 mag in the same direction. These are correlated
screening tests, not independent p-values or a calibrated discovery significance.
All contributing series medians and exclusions remain visible.

On each held-out star, inject +1 and -1 mag into each of 1930--34, 1950--54,
1970--74 separately, rerunning exactly the same matcher. This is conditional
photometric sensitivity at actual detections, NOT detection completeness or
upstream plate-pipeline recovery. At least three held-out stars must have an
eligible injected window, >=6 total signed eligible injections must exist, and
>=80% must recover the injected sign. At least four held-out stars must retain
100 colour-joined clean detections spanning 30 years. Any held-out unmodified
coherent multi-series flag pauses expansion for scientific adjudication.

Passing earns only a separately frozen, bounded **exploratory** unknown-source
screen. It does not prove SPSS stars stable over a century, measure a population
false-positive rate, or authorize a discovery claim. Candidate promotion still
requires same-plate field controls, image/blend/astrometry checks, independent
catalogue/prior-art vetoes, and human-gated publication or disclosure.

Sources: [colour terms](https://dasch.cfa.harvard.edu/dr7/colorterms/),
[exposure identity and representative terms](https://dasch.cfa.harvard.edu/dr7/exposurelist-columns/),
[API](https://dasch.cfa.harvard.edu/dr7/web-apis/),
[SPSS table](https://cdsarc.cds.unistra.fr/ftp/J/MNRAS/462/3616/table3.dat).
