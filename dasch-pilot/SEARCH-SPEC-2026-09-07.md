# Bounded exploratory search, after matched-colour gate

The quarantine validation passed four held-out coverage controls and recovered
16/16 eligible signed injections with no unmodified held-out flags. This is
conditional sensitivity, not century-long negative truth or a discovery FAP.

Freeze before field catalogues or unknown curves: two fields centered on public
known controls Feige34 (159.90308333333334,43.10256944444445) and G146-76 (from
the held-out SPSS table). These provide a development and a held-out field with
substantial historical sampling. Query APASS box half-size 1800 arcseconds.
Exclude the central SPSS control within 30 arcseconds, require finite catalogue
B magnitude 9..13.5, colour -0.3..1.5, num_matches>=500, v_flag=mag_flag=0.
Sort by integer ref_number and take first 32 per field, without replacement.
No outcome-based re-ranking, threshold tuning, or expansion in this screen.

Reuse the exact field-center exposure lists. This intentionally restricts the
search to exposures indexed at both target and field center; lost joins remain
explicitly counted and are not nondetections. Apply the quarantine algorithm
and exact fixed windows/thresholds from the calibration experiment. Require
100 joined clean detections spanning 30 years, conflicts<=2% of clean rows,
and >=1 eligible window. All selected targets remain in the denominator.

At most two querycat and 64 lightcurve requests, each <=16 MiB, 30-second socket
timeout, sequential requests, no service-limit bypass. Retain all exact raw
responses with SHA256 and spec hash. Failed responses never become empty curves.
No bulk catalogue completeness, absent-object, or population-rate claims.

Outputs containing newly screened identities or coordinates remain in ignored
`data/search-20260907/`; track only aggregate counts. A coherent flag is a local
lead, not a discovery. Before promotion it needs independent known-variable and
literature crossmatch, nearby same-plate response controls, source/blend/image
checks, independent recovery and an accountable outward submission. Do not send
candidate-coordinate queries without the existing exact-payload approval gate.
Zero flags ends this fixed sample, not the broader scientific hypothesis.
