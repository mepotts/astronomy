# M0 preregistration: Catalog 2 activity-period feasibility

Date frozen for future reruns: 2026-09-02
Scientific state at freeze: known-source method development completed; no unknown-source scan performed

## Question

Can the public CHIME/FRB Catalog 2 release support a discovery-grade, population-wide search for multi-day repeating-source activity cycles without access to private telescope operations data?

M0 is a feasibility and positive-control milestone, not a discovery analysis. It must stop before any unknown-source periodogram if the released observing-window information cannot support calibrated null simulations.

## Fixed inputs

- Event table: the canonical CANFAR `chimefrbcat2.csv` under data DOI `10.11570/25.0066`.
- Exposure product: the canonical CANFAR `chimefrbcat2_exposure.h5` under the same DOI.
- Exact byte lengths and SHA-256 digests: `data/provenance.json`.
- Catalog definition and flags: Abbott et al., journal DOI `10.3847/1538-4365/ae3828`.
- Positive control: FRB 20180916B, published activity period `16.35 +/- 0.15` days.

Raw files are immutable inputs. A changed digest is a new dataset version and requires a new dated manifest and rerun note.

## Unit of analysis and quality cuts

The released table has one row per fitted sub-burst, not one row per FRB event. Group rows by `event_id`, require event-level names and flags to agree across sub-bursts, and assign the event the earliest finite `mjd_inf` among its sub-bursts. Multiple bursts on the same UTC day collapse to one day for the M0 positive-control smoke test only. UTC flooring is not a physical CHIME transit definition and is forbidden for a future unknown-source analysis; M1 must derive authenticated transit identifiers or midpoints from the resolved observing-window product.

An event is clean only when all of these are zero:

- `excluded_flag`
- `sidelobe_flag`
- `citizen_science_flag`

The M0 control does not turn `intrachan_flag` or `catalog1_param_flag` into exclusion rules because they concern morphology/parameter provenance rather than whether a burst occurred.

## Ordered kill gates

1. **Provenance.** Both inputs exist and exactly match their frozen sizes and SHA-256 digests.
2. **Catalog integrity.** The parser sees the frozen 60-column schema and reproduces 5,045 sub-burst rows, 4,539 events, 3,641 sources, 83 repeaters, and 981 repeater events.
3. **Positive control.** On clean, day-collapsed FRB 20180916B events, a Rayleigh `Z1^2` scan from 2 to 100 days with frequency spacing `1 / (10 * baseline)` must place the strongest grid point within 0.5 day of 16.35 days. This is only a method smoke test; no p-value is valid without the observing window.
4. **Window product.** The public exposure archive must contain an explicit time coordinate and operational/sensitivity samples, not only a map integrated across the survey dates.
5. **Unknown-source scan.** Never run in M0. If gates 1–4 pass, record only that the window input is ready for M1 design. A separate complete, committed M1 preregistration is still required; otherwise emit no prospective source identifiers or period candidates.

## M1 design outline — not a complete preregistration

This section constrains a future M1 but does not authorize it. M0 can at most establish that a window input is usable. Before any unknown period is inspected, a new dated, committed preregistration must freeze the null event-rate/clustering model, full statistic and harmonic/variant family, global alpha and correction, Monte Carlo/tail estimator, numeric alias widths, and minimum baseline/cycle rule. The current threshold cohort includes sources with baselines too short for an unrestricted 300-day search, so event count alone cannot qualify a source.

- Search sources with at least 12 clean events and at least 10 independent clean active days.
- Search periods from 2 to 300 days on a frequency grid oversampled by 10 relative to the full baseline.
- Use authenticated CHIME transit identifiers/midpoints as the clustering unit; do not use UTC-day flooring and do not count sub-bursts as independent evidence.
- Simulate null events only within each source's actual time-resolved exposure, including outages and non-nominal sensitivity intervals.
- Precompute the solar/sidereal-day, lunar-month, annual, and window-spectrum aliases and veto their resolution-width neighborhoods.
- Correct across every tested source, period, harmonic, and analysis variant. A source-level p-value alone is insufficient.
- Keep source identifiers blinded or private until the window-conditioned analysis, independent rerun, and prior-art review all pass.
- No TNS notice, email, preprint, repository candidate disclosure, or journal submission without a separate human gate.

## Method-development disclosure

Before this document was committed, the known public control source was used to verify that the simple Rayleigh implementation could recover the established activity period. No periodogram was calculated for any unknown prospective source. The implementation and tolerance above are frozen before any future unknown-source scan.
