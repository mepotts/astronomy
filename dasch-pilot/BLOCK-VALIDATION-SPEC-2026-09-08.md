# Separate bracketed-block detector validation - September 8

This is a **new, outcome-informed development design**, not a rescue or amendment
of the failed [real-event transfer test](REAL-CONTROLS-SPEC-2026-09-08.md). Its
three giant-star DR7 curves have been seen and cannot be called held-outs. The
old detector, protocol and results remain unchanged. Freeze this design before
running the new algorithm and before retrieving the separate real-event holdout.

## Estimand and algorithm

Search for discrete 10-, 20-, or 40-year excursions **bracketed by comparable
observations on both sides**, not century-long monotonic evolution. Starts every
five years from 1880, requiring block end <=1990: 55 correlated block trials per
source (21 ten-year, 19 twenty-year, 15 forty-year).

Use September 7's unchanged cleaning and quarantine exposure joins, unique clean
imaging keys and catalogue/row accounting. For each in-block observation find
same-series, colour-term-distance <=0.10 comparison detections **strictly before
start-1 or at/after end+1**. Require >=10 on EACH side. Sort each side by colour
distance then JD and take at most 25 per side. Together these must cover >=5
distinct integer years. Subtract the median magnitude of the combined comparison
set. No event-block detections can enter any baseline for that block.

As before, require >=10 matched event detections spanning >=1 year, and >=2 plate
series each with >=5 matched points. A flag needs median residual >=0.5 mag in
at least two series (dimming), or <=-0.5 in at least two (brightening). Keep every
eligible and ineligible block and both signs. Do not minimize the threshold,
optimize a boundary on a light curve, or convert correlated flags to sigma/FAP.

Source-level coverage remains >=100 joined rows, >=30-year span, <=2% exposure
conflicts, >=1 eligible block. APASS variable flags are **reported, not vetoed**
in this validation: historical characterization of known variables is scientifically
useful, but a known name or event can never count as a new discovery. No replacement
unknown population or catalogue magnitude/colour cuts are selected here.

## Development and instrumental controls (offline first)

1. Reuse all three public Tang 2010 giant bundles, with unchanged identity joins.
   Display their new block results as development only. Require at least one
   dimming flag with its full block contained in 1930..1955 for J0754 or J0736
   as an engineering gate; J0830's secular trend is out of this discrete-event
   estimand. No post-outcome parameter iteration in this experiment.
2. Reuse all four usable September 7 SPSS held-outs (44,104,113,120), now explicitly
   **reused instrumental controls**, not freshly blinded negatives. Require no
   unmodified flags over the entire 55-block family on any of them.
3. For each, inject +/-1 mag separately into 1930..1950 and 1950..1970 at existing
   detections and score the exact injected 20-year block. Require >=6 eligible
   signed injections across >=3 stars, >=80% recovered. Report unmodified
   counterparts; no detection completeness or century-long stability claim.

If any gate fails: `STOP_BLOCK_DEVELOPMENT`; retain results, make no holdout
requests, no broader search. All inputs are cached and byte-verified.

## Prospective astrophysical holdout (only if development passes)

Exactly **DASCH J075731.1+201735**, RA=119.37958333333333,
Dec=20.293055555555558 (J2000 published coordinate name), a previously published
1942-to-1950s brightening, from [Tang et al. 2012](https://arxiv.org/abs/1110.0019).
This control was selected from the primary abstract before its new DR7 curves;
not selected by this algorithm's outputs. It shares the Harvard archive and
research group with the development paper, not an independent instrument.

Three requests maximum: APASS 30-arcsec querycat, unique match <=5 arcsec, its
lightcurve and its own centre queryexps. Same nine-request archive mechanism but
enforce a tighter three-attempt cap; sequential, >=1 sec apart, <=16 MiB each,
30-second socket timeout, no automatic retries, cache hashes and exact request
bodies, failed responses stop. Match ambiguity means `STOP_BLOCK_HOLDOUT`.

Recovery requires source coverage and a negative flag in the 1940..1950 OR
1945..1955 ten-year block. All other blocks remain reported but earn no recovery
credit. Result is `PASS_BLOCK_TRANSFER_ONLY` or `STOP_BLOCK_HOLDOUT`.
Even a pass demonstrates just one selected real-event recovery, not discovery
precision. Do not retrieve an unknown sample in this validation experiment.

Only public known-control identities are written or transmitted. No candidate
coordinate disclosure, paper upload, registry report, correspondence, or new
scheduler. A broader search would need prospectively fixed source selection and
near-neighbour/systematics controls; no automatic sample growth until a flag.
