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
[M1 pixel/background control](M1-PROTOCOL-2026-09-12.md) is separately specified;
no unknown-target scan is authorized by period recovery alone.

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
