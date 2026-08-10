# M0 — Archive kill-check

**Question:** is the Hoy et al. CD-35 2722 B result reproducible from public data at all,
and if so how much of the expensive part (raw → 1-D reduction) has to be redone?

**Answer: yes, and almost none of it.** 17 of the paper's 20 epochs are available as
ESO pipeline-reduced 1-D spectra today. The remaining 3 exist as public raw frames only.

Reproduce with `exosat-rv inventory`; the machine-readable form is
[`data/m0-inventory.json`](data/m0-inventory.json).

---

## 1. The inventory

CRIRES+ H-band nights on CD-35 2722 B, measured 2026-08-09:

| Class | Nights | Meaning |
|---|---:|---|
| **Usable now** | **17** | public *and* `calib_level=2` reduced — M2 can run on these today |
| **Reduction gap** | **3** | public raw, no reduced product — needs esorex/cr2res under WSL |
| Embargoed | 8 | observed, still proprietary |
| **Total in band** | **28** | |

Usable baseline **2023-10-13 → 2025-01-21**. Gap nights: 2024-12-16, 2025-01-08, 2025-01-13.

**17 + 3 = 20, and the preprint claims exactly 20 usable epochs over Oct 2023 → Jan 2025.**
The paper's dataset *is* the set of public H-band nights, with nothing held back. That
identity is asserted as a live test (`test_live_inventory_matches_the_published_epoch_count`)
so it fails loudly when the embargo lifts rather than drifting unnoticed.

Two independent corroborations that we are looking at the right data:

- ObsCore reports the reduced products spanning **1469–1780 nm**, matching the paper's
  stated CRIRES+ H-band coverage exactly. This is the one instrument parameter this project
  has confirmed from the archive rather than from the paper's prose.
- An earlier hand count said 18 reduced nights, not 17. The extra night is 2024-01-03,
  taken in the **K** setting. The band filter drops it correctly; the hand count was wrong.

## 2. The embargo schedule

The 8 embargoed nights are Dec 2025 → May 2026 — precisely the extension that moved the
accepted Nature paper to ~0.9 M_Jup and 23 epochs. They release on a rolling schedule:

`2026-12-19, 2026-12-21, 2027-01-11, 2027-02-09, 2027-02-10, 2027-03-08, 2027-03-24, 2027-04-04`

Consequence for scope: **this project reproduces arXiv v1, not the Nature version.** Any
comparison against the accepted paper's numbers is apples-to-oranges until 2027. Stating a
v1 reproduction as agreeing or disagreeing with *Nature* would be a false claim.

## 3. Two extra nights the paper does not use

Programme 110.23RW took CD-35 2722 B on 2023-01-04 and 2023-02-01, both public, both in the
**J/YJ** setting. They fall outside the paper's Oct 2023 start and outside its H-band
analysis. They are not combinable with H-band RVs without a cross-setting zero-point, but
they would extend the baseline backwards by ~9 months, which is exactly the leverage the
87-day/169-day period discrimination needs. Deferred to M4; recorded here so it is not
rediscovered later.

## 4. Findings that change how the rest of the project is written

### 4.1 A published-looking number that cannot be true

`PUBLISHED.hill_radius_au = 1.07` came from an AI summary of the paper body. It is
inconsistent with the system as imaged:

| Quantity | Value |
|---|---|
| Companion projected separation (2.8″ at 22.36 pc) | 62.6 au |
| Hill radius there, 37 M_Jup inside 0.5 M_sun | **17.9 au** |
| Separation that *would* give a 1.07 au Hill radius | 3.73 au |

A directly imaged companion is not at 3.7 au. The value is wrong, or it means something
other than what the summary said. It is **retained in the config, flagged, and pinned by
a test** (`test_published_hill_radius_is_internally_inconsistent`) rather than deleted, so
that anyone who later reads the actual PDF is forced to resolve the contradiction in the
open. The physics assertions use a self-consistent Hill radius instead.

Both satellite orbits are comfortably stable either way: a = 0.199 au is 1.1% of the true
Hill radius and 2.8% of the 0.4 R_Hill prograde stability edge.

### 4.2 The provenance problem this exposed

The bad value was not an isolated slip — it was one field in a config populated largely
from AI summaries of the paper rather than from the paper. `config.py` now tags every field:

- `[TAP]` — independently confirmed against a queryable archive (coordinates, parallax,
  wavelength coverage, epoch count).
- `[v1]` — transcribed from the arXiv v1 abstract, which was read directly (both satellite
  masses and periods).
- `[SUMM]` — from an AI summary of the body, **unverified**: `bd_mass_mjup`, `bd_vsini_kms`,
  `bd_max_prot_days`, both period uncertainties, both semi-major axes, `resolving_power`,
  the RV error range, `roche_limit_rbd`.

No test may assert against a `[SUMM]` field. **Reading the actual PDF and promoting those
fields is a prerequisite for M3**, because `rv_err_mean_ms` and the period uncertainties are
inputs to the reproduction verdict, not decoration. The PDF did not extract via the fetch
path used in M0 (`pdftoppm` absent, compressed content streams); WSL has poppler available.

## 5. What M0 does not establish

- That the reduced products are of usable quality for 30 m/s RV work. ObsCore says they
  exist; nobody has opened one. **First task of M1.**
- That `viper` runs on ESO-reduced CRIRES+ products without the authors' intermediate
  files. The paper's pipeline consumed its own extraction.
- Anything about analogue targets. The NASA Exoplanet Archive caps companion mass at
  30 M_Jup and therefore **does not contain CD-35 2722 B itself** — a target list built
  from it alone would exclude the object being reproduced. See DATA-SOURCES.md.
