# Discovery contingency: continue XMM

**Decision: continue the same-observation XMM metadata step; do not start a
second science pipeline.** One distinct alternative was considered below. Its
positive-control evidence is strong, but access, search-footprint novelty and
negative-control feasibility are not sufficiently established to justify a
switch. This is a bounded comparison, not an exhaustive search or a discovery
probability estimate.

## Portfolio boundary and current leverage

The [search record](SEARCH-2026-09-12.md),
[direction](DIRECTION-2026-09-06.md),
[closeout](CLOSEOUT-2026-09-05.md), execution record and run3 prospectus were
checked before choosing the comparison. Failed TESS localization and VLASS
calibration gates remain failed; DASCH/CCOR/DR11 outcomes are not fresh leads.
CHIME's time-resolved sensitivity/window dependency is unchanged. ITF's daily
operation is not a new discovery. The prospectus already considers long-period
radio searches, so merely choosing radio would not constitute a new route.

XMM now has a real, reproducible
[three-camera recorded-count measurement](XMM-C9-RESULT-2026-09-12.md):
3,323,958 input rows and 334 chunks per pass, with complete fixed-region/bin
accounting. It is explicitly **not calibrated recovery**. Detector support,
catalogue contamination and relative-exposure/negative-control validation still
limit the scientific claim. The next known control's HEASARC index returned404;
the [same-observation ESA structured metadata proposal](XMM-RXJ-M0-NEXT-2026-09-13.md)
addresses an independently documented archive interface. Neither its success
nor subsequent product availability is assumed here.

## One alternative: ultra-short pulses in public FRB baseband

The experiment would search isolated microsecond-duration dispersed radio
pulses in a **demonstrably unsearched time subset** of the public Breakthrough
Listen GBT recording of the known repeater FRB20121102A/FRB121102. This is
different from the repo's CHIME multi-day periodicity/window experiment and
from slow-pulsar or continuum-image searches. It is not a claim that the pulse
phenomenon or this dataset is new.

Direct prior art is decisive: Snelders et al. reanalysed the first30minutes of
a five-hour 2017 GBT recording, finding49bursts including eight ultra-fast
bursts. Their first30minutes of raw voltages exceed32TB; coherent dedispersion
and sub-microsecond products are central to the analysis. B30 and B43 are
published positive controls. The paper links a Zenodo reproduction package
and a Breakthrough Listen raw-data search portal.
[Primary paper](https://arxiv.org/pdf/2307.02303).

The official [Breakthrough Listen dataset page](https://seti.berkeley.edu/frb121102/)
was accessible and identifies the observation/data tutorial. The
[author reproduction record](https://zenodo.org/records/8112803) timed out in
this check. No file inventory, downloadable control cutout, current raw-file
availability or bounded transfer size was verified. A published public-data
link is not proof that a particular small product is currently retrievable.

The tempting inference that the remaining4.5hours are unsearched is **not
established**. The paper also discusses earlier searches. A 2023 analysis
footprint does not authenticate the complete search history through2026;
recovery of a previously missed pulse would not automatically establish a new
physical population. This coverage/novelty gate must precede any unknown scan.

## What a genuinely short control path would require

If separately adopted later, first inspect only the author-package metadata
for size-bounded, provenance-linked B30/B43 cutouts and accompanying off-burst
samples. Do not retrieve the raw recording to discover whether small controls
exist. Stop if the package does not support a bounded independent reproduction.

A subsequent frozen calibration-only test could compare those known pulses
with same-recording off-burst windows, wrong-dispersion trials and explicit
interference diagnostics. These would be conditional controls, not independent
blank-sky samples or a survey-wide false-alarm law. Retain every predeclared
negative and failed control. No new pulse search, threshold adaptation or
full-recording acquisition follows automatically from source recovery.

This proposed control path is **not yet access-verified**. Its dedicated
radio-processing environment, dispersive/interference calibration and complete
prior-search ledger would all be new work here. By contrast, XMM has already
exercised its actual local decoder, geometry, counts, resource accounting and
replay; its unresolved calibration remains difficult but concrete. That is
present evidence of implementation leverage, not an argument from sunk cost.

## Stop and recommendation

Do not queue a radio implementation now. Keep the single conditional idea in
this note and continue XMM's bounded metadata decision. A later XMM failure
would justify reconsideration, not automatically waive either project's
controls. The existing two-negative and pn-plus-MOS recovery requirements are
unchanged; neither raw counts nor a new archive response is a discovery.

Research accounting: two discovery searches and four primary-page opens:
the paper's Nature landing page failed, Zenodo timed out, the official dataset
page and the paper's arXiv PDF opened successfully. In-document searches added
no source. No archive query, product download, unknown-coordinate request,
account, external message or software implementation was performed. The paper
is prior-art evidence, not an independently reproduced measurement in this repo.

Parent disposition: root read the full note and independently opened the paper
and official dataset page, checking the large raw-data footprint and prior
search history. Adopt no switch and no radio implementation at this point.
M1 subsequently returned package-level entries with a preserved schema STOP;
that does not automatically authorize a new pipeline. Continue the bounded
same-observation archive-access decision, with every existing gate retained.
