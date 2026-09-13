# Photon-blind screening decision for the pending control

September 12 parent decision: use **FLAG == 0** in all three cameras for the
eventual single-band published-control experiment, alongside the draft's
pn PATTERN <= 4, MOS PATTERN <= 12 and strict 200 < PI < 12000 numeric-eV cuts.
This is a prospective conservative choice, not a change selected from counts.
No photon values have been read and the complete counts protocol is not frozen.

HEASARC's standard imaging guide distinguishes its usual canned MOS/pn flag
masks from the stricter zero-flag selection. Flags encode conditions such as
hot-pixel proximity and out-of-field events. The guide's routine MOS selection
does not require zero flags; choosing it here is an explicit engineering
tradeoff in favor of more conservative screening, potentially losing valid
counts. It does not establish complete absence of detector artifacts.
[HEASARC XMM imaging guide, section 7.2](https://heasarc.gsfc.nasa.gov/docs/xmm/abc/node9.html).

Retained C1 EVENTS header inspection (no arrays) finds the same MOS1/MOS2
FLAG data-subspace value `b000x00xxx0x0x0x0x0xxxxxxxxxxxxx`. That is not a
statement that every retained event already has FLAG zero. The pn EVENTS
header has no corresponding FLAG data-subspace entry. Apply and account for
the adopted selection explicitly rather than assume pipeline filtering did it.

The C3 maps' exact FLAG provenance is still unknown. A broader map mask can
have positive accumulated exposure where zero-flag acceptance is not known;
positive map support alone cannot establish compatibility with this choice.
The geometry adjudication must expose that distinction before a reliable
relative-exposure claim. Do not loosen FLAG or recenter apertures after looking
at a light curve. Remaining detector/row diagnostic criteria belong in the
final counts protocol and are not replaced by FLAG zero.

A separate ESA filtering-page URL failed to load; the primary guide above was
the successful documentation source. No claim relies on that failed fetch.
