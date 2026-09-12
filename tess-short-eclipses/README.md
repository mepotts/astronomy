# TESS short eclipses: control-first discovery route

Started September 12, 2026 under the user's ongoing discovery goal. **No new
candidate or discovery yet.** First stage: recover three published eclipsing
white-dwarf controls from public short-cadence light curves. Then validate pixel
localization, competing-source rejection and false positives before unknowns.

Read [M0 protocol](M0-PROTOCOL-2026-09-12.md). Do not confuse reproducing a published
system with discovery. The novel-search opportunity is conditional: public sectors
or target populations outside prior searches must be established, not assumed.

Initial M0 stopped at a [metadata-selection error](M0-ACQUISITION-RESULT-2026-09-12.md)
before flux analysis. [M0b](M0b-PROTOCOL-2026-09-12.md) corrects single-sector
eligibility uniformly, with identical scientific controls and thresholds.

**M0b completed: 3/3 published periods recovered**, with exact raw-data replay and
independent audit. [Result and limitations](M0b-RESULT-2026-09-12.md): pipeline
crowding corrections and negative flux prevent physical-depth claims. The next
[M1 pixel/background control](M1-PROTOCOL-2026-09-12.md) and its narrow metadata
repair are complete: [M1b results](M1b-RESULT-2026-09-12.md) recover near-target
pixel signals for all three, with exact replay. **Source confusion remains
unresolved**. At M1b, one field had 26 nearby catalogue competitors and two
catalogues were unavailable. Calibrated PRF/negative-control work is still needed;
no unknown scan.

The [next-localization proposal](NEXT-LOCALIZATION-PROPOSAL.md) identifies official
PRF products and an official Gaia mirror. The separately frozen metadata-only
[M1c attempt](M1c-RESULT-2026-09-12.md) stopped after one mirror response triggered
a Windows/Astropy binary null-sentinel parsing error. Its failure reproduces
exactly; numerical catalog parity was not established, and neither missing field
was queried. An offline decoder would be a new stage, not a retry of this run.
No PRF files or unknown-source pixels were acquired by M1c.

The [M1d offline attempt](M1d-RESULT-2026-09-12.md) stopped on an overly narrow
RESOURCE profile. The separately frozen [M1d2 amendment](M1d2-RESULT-2026-09-12.md)
now establishes exact parity for all 1,290 first-field catalogue rows, including
all masks, with independent replay. No new catalogue request or pixel measurement
was needed. The [coordinate audit](PRF-COORDINATE-AUDIT-2026-09-12.md) supports the
SPOC header-to-PRF mapping without an extra 44-column shift, but does not certify
absolute astrometry. The [M1e continuation](M1e-RESULT-2026-09-12.md) has now
retrieved both missing catalogues in exactly two requests, with exact replay.
All three fields have catalogue data: one passes only the coarse consistency
diagnostic, while two retain 26 and two potential competitors within one pixel.
Even the cleaner field has a much brighter star 2.895 pixels away. Catalogue
availability is resolved; PRF/localization and empirical negatives are not.

The separately frozen [M2n real-data phase test](M2n-RESULT-2026-09-12.md) now
passes all 18 fixed off-eclipse diagnostics (36 flux/background channels), with
exact replay and explicit cadence overlap. These within-field windows are usable
under the declared checks; they are not independent population negatives or
validated source localization. PRF/confusion and independent-negative work remain.
The separately frozen [M2a acquisition](M2a-RESULT-2026-09-12.md) now retains all
twelve exact PRF grid products (2,764,800 bytes), with structural validation and
read-only replay. No PRF fit or injection has run; that is the next scientific step.

The portable agent kit named by global instructions is absent at its configured
path on this host. This project uses the scoped AGENTS.md, a prospective protocol,
small tested functions, explicit stop rules and retained provenance instead.

Initial runtime: existing `../dyson-revet/.venv/Scripts/python.exe` (Astropy 8.0.1,
NumPy 2.5.2, SciPy 1.18.0, astroquery 0.4.11). No environment was modified.

## Scientific boundaries

- Positive light-curve recovery alone does not establish on-target eclipses.
- A catalogued WD probability does not prove a companion's nature.
- Multiple sectors share some instrumental risks; agreement is necessary, not
  automatically independent confirmation.
- Unresolved blends require an independent angular-resolution constraint. No
  telescope-free guarantee is made.
- All new candidate products stay local/ignored until private-coordinate and
  publication rules have been satisfied.
