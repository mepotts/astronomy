# XMM C0d: exact sizes retained; summary acceptance stopped

The frozen five-request metadata stage remains **STOP_SUMMARY_FOOTER**.
Four HEAD requests succeeded, establishing 126982449 advertised compressed
bytes for the selected pn, MOS1, MOS2 and EPIC source-list products. The fifth
request retained the entire 50010-byte summary but rejected its missing outer
HTML closing tag. No scientific-product body was downloaded by C0d.

The [independent post-run audit](XMM-C0d-POSTRUN-AUDIT.md) verified all 23
outcome artifact hashes and the original STOP by offline replay. The
[separate offline interpretation](XMM-C0d-OFFLINE-2026-09-12.md) accounts for
the complete retained page: pn S003 is PrimeFullWindow, both selected MOS
exposures are PrimePartialW3. Their nominal simultaneous interval is 48480
seconds, not verified GTI coverage or effective exposure. Missing metadata
and unit/time-label limitations remain explicit in that note.

The original summary contains coordinates and observer information. It is
immutable and locally retained but exactly ignored by Git, consistent with
the frozen protocol's no-coordinate-upload rule. Its SHA-256 is
`aba0f32242f6d81b65132cdfa167dbc8f4d75c15ef2c5ab69a37d048e4fca837`.
Public notes are non-coordinate derivatives, not replacements for the raw
evidence. Full local replay requires this retained file; a repository-only
checkout does not contain every raw artifact.

The executed source and protocol were frozen before the batch; no validator
was repaired or request repeated to turn the STOP into a pass. Outcome SHA-256:
`7895f2fd39ce85ab745fbff40a291abbf7376086e9f58a2245352b2c348453a3`.

Next is the separately reviewed [C1 known-control acquisition](XMM-C1-2026-09-12.md):
four fixed product GETs with bounded decompression and headers-only inspection.
The [reviewed structural reader](XMM-STRUCTURAL-REVIEW-2026-09-12.md) has 15
passing synthetic tests; this is not yet evidence about the real products.
Scientific recovery, exposure geometry, background calibration and unknown
search readiness remain unestablished. **No discovery.**
