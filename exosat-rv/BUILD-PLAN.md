# BUILD PLAN — exosat-rv

Desk/data/software-only: no telescope time, no proprietary data, no paid service. See
[`SPEC.md`](SPEC.md) for the thesis, [`DATA-SOURCES.md`](DATA-SOURCES.md) for endpoints, and
[`M0-RESULTS.md`](M0-RESULTS.md) for what M0 actually measured.

---

## 1. Chosen stack (justified)

| Concern | Choice | Why | Alternatives considered |
|---|---|---|---|
| Language | **Python 3.11+** | The whole high-resolution-spectroscopy toolchain (astropy, viper, radvel) is Python; matches sibling projects. | None viable. |
| Packaging | **`pyproject.toml` + hatchling**, `src/` layout | Matches `itf-linker`; src-layout prevents "works because cwd" bugs. | Flat layout (import shadowing). |
| CLI | **`typer`** | Sibling convention; free `--help`. | argparse (boilerplate). |
| Archive access | **`pyvo` TAP** | Direct ADQL against `dbo.raw` *and* `ivoa.ObsCore`. The raw/reduced distinction is the whole of M0 and needs both tables. | `astroquery.eso` (wraps the web form; awkward for ObsCore joins). |
| Time / coords / FITS | **astropy** | `Time` for MJD↔ISO, `SkyCoord` for the M5 cross-match, `io.fits` for the products. | Hand-rolled (no independent check). |
| Periodogram | **`astropy.timeseries.LombScargle`** | Generalised LS is what the paper used; astropy's is the reference implementation and gives analytic FAP. | `scipy.signal.lombscargle` (no floating mean, no FAP). |
| RV extraction | **`viper` as an external tool** | Forward-modelling RV extraction against an empirical template is not credibly reimplemented in a side project, and it is the paper's own tool. Independence is bought at the *inference* stage instead, not here. | Cross-correlation with a template (loses the wavelength-solution refinement that buys the ~10 m/s floor). |
| Keplerian fitting | **`radvel`** (planned, M3) | Deliberately **not** the paper's `EMPEROR`. If two independent samplers on the same RVs give the same orbit, the orbit is not a property of the sampler. | `EMPEROR` (would make the check circular); bare `emcee` (would mean hand-rolling the likelihood). |
| Spectral reduction | **ESO `calib_level=2` products**, esorex/cr2res under WSL only for the 3-night gap | M0 measured that 17 of 20 epochs are already reduced. Building cr2res to recover 3 nights is a late optimisation, not a prerequisite. | Reducing all 20 from raw (weeks of work for +3 epochs). |
| Tests | **pytest**, `network`/`slow` markers | Sibling convention; the live archive assertions must be skippable offline. | unittest (verbose). |

**Deliberately deferred:** no parallelism, no database, no cr2res build. M0 showed the
data volume is tens of spectra, not millions of rows.

---

## 2. Architecture

Implemented in M0:

```
exosat_rv/
  config.py             endpoints, and the published values with PROVENANCE TAGS
  cli.py                typer entry point
  archive/
    inventory.py        pure: frames -> nights -> usable/gap/embargoed. No I/O.
    tap.py              ESO dbo.raw + ivoa.ObsCore, NASA Exoplanet Archive. All I/O here.
  targets/
    feasibility.py      pure: K amplitude, min detectable mass, photon scaling, Hill radius
```

The `inventory.py` / `tap.py` split is load-bearing: deciding which nights are *usable* is
the subtle part, and it is testable offline only because no TAP call reaches it.

---

## 3. Milestones

Each milestone lands an `M{n}-RESULTS.md` recording what was measured — including, and
especially, what failed.

### M0 — Archive kill-check ✅
Is this reproducible, and how much reduction must be redone?
**Result: 17 of 20 epochs already reduced; 3 need esorex.** Also disproved a published-looking
Hill radius and exposed a provenance problem across the whole config. See
[`M0-RESULTS.md`](M0-RESULTS.md).

### M1 — Spectra in hand ✅
**Track A — read the source: DONE.** `pypdf` extracted the PDF that defeated M0's fetch
(27 pages, no poppler/WSL needed). Every config field is now `[v1]` or `[TAP]`; the `[SUMM]`
tier is eliminated. **Two claims M0 published were retracted** — see
[`M1-RESULTS.md`](M1-RESULTS.md) §1.

**Track B — open a product: DONE, and it passes.** `exosat-rv probe` (after ESO's outage
lifted) shows the products are **per-order extractions**: 7 orders x 3 detectors x 2048
native pixels, labelled by `ORDER`/`DETEC`/`XPOS`, curved dispersion within each segment.
`viper` can consume them. **The kill condition did not fire; cr2res is not needed.**
*Now known:* the authors did not use the combined product either — they kept individual
nodding frames, buying 31.44 m/s against 34.49 m/s. Archived products cost ~10% precision by
construction, and M3 must not read that offset as a disagreement.

### M2 — RV extraction
Get `viper` running against the products; extract 17 RVs with uncertainties. Success is
per-epoch precision in the tens of m/s, against the paper's quoted 18–54 m/s.
*Control:* the primary CD-35 2722 A has 300 public CRIRES+ frames from an unrelated
programme. It is a bright, RV-quiet M dwarf observed with the same instrument — the natural
check on whether our extraction has an instrumental floor we are mistaking for signal.

### M3 — Reproduction verdict
GLS periodogram, then `radvel` Keplerian fitting. Does 169.45 d / 0.743 M_Jup fall out of
17 epochs analysed by a different sampler? Report the answer either way; a failure to
reproduce is a result, not a bug to be tuned away.

### M4 — The alias test *(re-scoped by M1)*
**Original scope was redundant.** M0 framed this as "is the 87 d signal a harmonic of an
eccentric 169 d orbit?" — a question the paper asks, fits (e = 0.29, Table 1), and rejects
at Δlog Z = 6.9.

**The live question is the second signal's period.** The paper identifies 14, 70, 88 and
115 d as aliases of one another caused by two observing seasons almost exactly a year apart,
and prefers 88 d by only Δlog Z = 2.6.
Method: compute the spectral window function of the real cadence and confirm it generates
the 14/70/88/115 d family; then inject signals at each candidate period into the real
cadence and measure how often the injected period is recovered as the favourite. If 115 d
injections frequently recover as 88 d, the paper's choice is sampling-driven.
The two public J-band epochs from Jan/Feb 2023 (M0 §3) sit ~9 months before the paper's
first epoch and may offer alias-breaking leverage, at the cost of a cross-setting zero-point.

### M5 — Analogue target list ✅ *(list built; application awaits M2)*
Built **archive-first**, because a catalogue-first list cannot contain CD-35 2722 B at all.
CD-35 2722 B being rediscovered is the control, and it passes. See
[`M5-RESULTS.md`](M5-RESULTS.md).

**Two targets survive the epoch-cadence test**, which frame counts badly mislead on
(beta Pic b's 753 frames are 6 nights):
- **eta Tel B** — 16 usable H-band nights over an **800-day baseline**, wider separation
  (~4.2″) than CD-35 2722 B. The best analogue.
- **GJ 229 B** — 11 usable H-band nights at 5.8 pc, and a **known binary brown dwarf**, so
  it is a *positive control*: a target where a signal is expected. Run it before believing
  any analogue null.

The flux cut in SPEC never got used — the existence of usable CRIRES+ spectra turned out to
be a better feasibility filter than an unsourced magnitude. Applying the M2/M3 pipeline
still waits on M2. **Expected deliverable remains upper limits, not detections.**

---

## 4. Standing constraints

- **Reproduces arXiv v1, not Nature.** The frames that changed the accepted paper are
  embargoed until Dec 2026 – May 2027. Never state a v1 result as agreeing with *Nature*.
- **No `[SUMM]` field may back an assertion.** See M0 §4.2.
- **Minimum masses only.** RV gives m·sin(i); every mass reported here is a lower bound,
  exactly as the paper's are.
- **No discovery claims, no submissions.** The output is a reproduction verdict, a harmonic
  test, and limits.
