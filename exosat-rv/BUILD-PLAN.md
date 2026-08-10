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

### M1 — Spectra in hand
Download the 17 usable products and **open one**. Characterise: order structure, SNR per
order, wavelength solution as delivered, whether telluric lines survive the pipeline's
processing. Read the actual arXiv PDF (poppler under WSL) and promote the `[SUMM]` config
fields to `[v1]`.
*Kill condition:* if the ESO products are order-merged or resampled in a way that destroys
the per-order wavelength solution, `viper` cannot use them and the project reverts to
building cr2res for all 20 nights — a different, much larger project. **This is the real
remaining risk and M1 exists to retire it.**

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

### M4 — The harmonic test
The project's sharpest question. Is the 87.46 d signal a second satellite, or the first
harmonic of an eccentric 169 d orbit? 169.45/2 = 84.7 d sits 4.34σ from it, and the paper's
Δlog Z = 2.6 (Bayes factor ~14) is positive, not decisive.
Method: inject single eccentric Keplerians at the recovered 169 d orbit into the real
observing cadence, recover, and measure how often a spurious ~87 d signal appears at
Δlog Z ≥ 2.6. Optionally add the two 2023 J-band epochs (M0 §3) for baseline leverage.

### M5 — Analogue survey
Build the substellar-companion target list — wide (slit-resolvable), bright (H ≲ 16), with
public CRIRES+ holdings — and apply the M2/M3 pipeline. **The expected deliverable is upper
limits, not detections**, and limits are reported as the result.
Blocked on nothing; can be built in parallel with M1–M4.

---

## 4. Standing constraints

- **Reproduces arXiv v1, not Nature.** The frames that changed the accepted paper are
  embargoed until Dec 2026 – May 2027. Never state a v1 result as agreeing with *Nature*.
- **No `[SUMM]` field may back an assertion.** See M0 §4.2.
- **Minimum masses only.** RV gives m·sin(i); every mass reported here is a lower bound,
  exactly as the paper's are.
- **No discovery claims, no submissions.** The output is a reproduction verdict, a harmonic
  test, and limits.
