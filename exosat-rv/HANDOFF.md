# HANDOFF — exosat-rv

Picking this up cold? Read in this order:

1. [`SPEC.md`](SPEC.md) — what is being tested and why it is worth testing.
2. [`M0-RESULTS.md`](M0-RESULTS.md) — what the archive actually contains.
3. [`M1-RESULTS.md`](M1-RESULTS.md) — the source read properly, and three corrections to M0.
   **Read this before trusting anything in M0.**
4. [`BUILD-PLAN.md`](BUILD-PLAN.md) — stack, architecture, milestones.
5. [`DATA-SOURCES.md`](DATA-SOURCES.md) — endpoints, and the traps in each.

The rest of this file is the expensive part: claims that turned out false, approaches
measured and rejected, and silent failures that cost data. The code is not the expensive
part.

---

## 1. Claims published here and later found false

### "The paper's Hill radius of 1.07 au cannot be true" (M0) — **FALSE, retracted in M1**

M0 published a disproof of a value in a peer-reviewed paper. The disproof was wrong twice:

1. **Wrong quantity.** 1.07 au is a Domingos et al. (2006) satellite *stability limit*, not
   a Hill radius. The paper computes the Hill radius separately and notes it varies over the
   companion's orbit.
2. **Wrong orbit.** M0 used the projected separation (2.8" = 62.6 au) as a circular
   semi-major axis. The companion has **e > 0.9** and P ~ 5000 yr, so a ~ 222 au, and the
   Domingos eccentricity term collapses the stable zone by more than 10x.

Recomputed with the paper's own parameters, 1.07 au falls out at e_host ~ 0.93–0.94 —
inside the published ">0.9". **The paper was right.** Full working in
[`M1-RESULTS.md`](M1-RESULTS.md) §1.1.

**Root cause, and the lesson that outlives the specific error:** M0 reasoned from an AI
summary of a source it had not read, all the way to a public claim. It *had* tagged the
value unverified — and tagging it did not stop the reasoning. **An unverified value must
not be an input to any conclusion, not merely absent from tests.**

### "The paper's evidence for a second satellite is delta-log-Z = 2.6" (M0) — **FALSE, retracted in M1**

2.6 compares the **88-day model against the 115-day model** — two candidate *periods* for
the second signal. The evidence that a second satellite exists at all is **delta-log-Z =
6.9**, against an eccentric one-satellite alternative. M0 understated the existence
evidence and overstated the period certainty. See M1 §1.3.

## 2. Inherited claims that do not survive checking

### Table 1's log-evidence difference does not match the quoted value — minor, real

Table 1 gives logZ = −122.654 ± 0.952 and −129.295 ± 0.920, differing by **6.641**, while
the text quotes **6.9**. Both are recorded in `config.py` and pinned by
`test_table1_logz_difference_does_not_match_the_quoted_delta`. Small, and noted rather than
made much of — unlike §1, this one was checked against the actual PDF.

## 3. Approaches measured and rejected

| Approach | Why rejected |
|---|---|
| Populating `config.py` from AI summaries of the paper body | Produced three wrong values and one false published claim (§1). The `[SUMM]` tier is now **eliminated**, not merely flagged. |
| Extracting the PDF via WebFetch, then via poppler under WSL | WebFetch returned only compressed streams; poppler is not installed in WSL and would need sudo. **`pypdf` in the project venv did it in one call** — 27 pages, 55,679 chars. Try the pure-Python route first. |
| Framing M4 as "is the 87-day signal a harmonic of the 169-day orbit?" | The paper asks exactly this, fits the eccentric one-satellite model (e = 0.29), and rejects it by delta-log-Z = 6.9. Re-scoped to the **alias structure**, which the paper states openly is unresolved. See M1 §3-4. |
| Assuming ESO's reduced products are what the paper used | They are not. The authors kept **individual nodding frames** rather than the combined spectrum, buying 31.44 m/s against 34.49 m/s. Working from archived products costs ~10% precision by construction. M1 §2. |
| `CONTAINS(POINT(...), CIRCLE(...))` on ESO `dbo.raw` | Hard-fails with a SQL-Server geography error — the table holds rows whose coordinates do not validate. A plain ra/dec box works and is faster. |
| `astroquery.eso` for archive access | Wraps the web form; awkward for the `dbo.raw` / `ivoa.ObsCore` comparison that is the whole of M0. `pyvo` gives direct ADQL against both. |
| Reducing all 20 nights from raw with esorex/cr2res | M0 measured that 17 are already reduced by ESO. Building cr2res to recover 3 nights is a late optimisation, not a prerequisite. |
| Using `EMPEROR` (the paper's sampler) for M3 | Would make the reproduction circular. `radvel` is used instead so that agreement means something. |
| Using `sy_hmag` from the NASA Exoplanet Archive as the companion brightness cut | It is the **system** magnitude, dominated by the primary. Useless for a companion flux cut. |
| Trusting the NASA Exoplanet Archive alone for the M5 target list | It caps companion mass at 30 M_Jup and therefore **does not contain CD-35 2722 B**. M5 was rebuilt archive-first, with CD-35 2722 B's rediscovery as the control. |
| Resolving companions by SIMBAD **name** | Identifiers are unforgiving about spacing: `CD-35  2722B` resolves, `CD-35 2722 B` and `BET PIC B` do not. Normalise and match against *all* identifiers instead. |
| Resolving companions by **position alone** | A cone search finds the system, not the component. It resolved `BET PIC B` to beta Pic **c** and `PZ TEL B` to the G9IV primary. Two stages are needed: cone for the system, identifier match for the component. |
| Ranking M5 targets by **frame count** | beta Pic b has 753 frames — on 6 nights. AB Pic B's 64 frames span 3 days. An RV orbit needs epochs spread over time; rank by nights and baseline. |
| Filtering companions by SIMBAD `otype` alone | `tau Boo B` (M3V) and `HD 149274B` (M5) are typed `*` and pass as "borderline". Spectral type is the more specific statement and must override. |

## 4. Silent failures that cost data

### `pathlib.Path.write_text()` truncated `README.md` to zero bytes

On Windows, `write_text()` defaults to the cp1252 locale encoding. Writing a string
containing `→` raised `UnicodeEncodeError` — **but only after opening the file in write
mode**, which had already truncated it. The exception looked like "nothing happened"; the
file was in fact destroyed. A follow-up read-modify-write then read the now-empty file,
found nothing to replace, and wrote the emptiness back.

**Rule: always pass `encoding="utf-8"` explicitly to both `read_text` and `write_text` on
this platform.** The read side is worse than the write side — cp1252 is a single-byte codec
that decodes almost any byte without raising, so reading a UTF-8 file with it produces
silent mojibake rather than an error.

Damage was limited to `README.md`, rewritten from source. Nothing else round-tripped
through Python text I/O.

### A hand-written night count that disagreed with the pipeline

An ad-hoc scoping script counted **18** public reduced nights; the pipeline reports **17**
in H band. The pipeline is right — the extra night (2024-01-03) was taken in the **K**
setting. The ad-hoc script had no band filter. Cross-check band before quoting an epoch
count.

## 5. Things that look like problems and are not

- **`access_estsize` is 0** for every CRIRES+ product in ObsCore. The column is unpopulated,
  not the products empty. Download size is unknown until M1 fetches one.
- **`sorted(...)[0]` on a settings set** looks arbitrary but is deliberate: reduced products
  carry no setting, so they inherit the night's raw settings, and a stable pick is needed.
  Now written as `min(...)`.
- **`nan pc` distances** were SIMBAD returning NaN rather than NULL for a missing parallax,
  which a bare truthiness check lets through as though it were a measurement. Now filtered
  with `math.isfinite`.
- **`archive.eso.org` timing out** is not a code fault. It served M0's queries, then went
  unreachable for all of M1 (connect timeout, HTTP 000) while `www.eso.org` returned 302 and
  other TAP services 200. Retry before debugging.
- **Two extra public nights (2023-01-04, 2023-02-01)** exist that the paper does not use.
  They are J/YJ band, not H, so they are not a discrepancy — see M0 §3. They may still be
  useful to M4 for baseline leverage.

## 6. Values still unverified

One remains, and it is load-bearing for M5:

**CD-35 2722 B's H magnitude.** Used as the brightness anchor for the whole analogue flux
cut, and estimated at ~14 from an L4 spectral type at 22.36 pc. The preprint does not state
it; SIMBAD does not resolve the companion separately (nor AB Pic b, PZ Tel B, GQ Lup B, AF
Lep b, or 51 Eri b — of 17 companions tried, 6 returned photometry). It must come from
Wahhaj et al. 2011 (the discovery paper) before M5's cut means anything. VizieR TAP is
reachable at `https://tapvizier.cds.unistra.fr/TAPVizieR/tap`; the catalogue identifier was
not resolved on the one attempt made.

Measured companion magnitudes already in hand, for calibration: DH Tau b H = 14.96,
kappa And b H = 15.01, HN Peg b H = 15.40, TYC 8998-760-1 b H = 15.87, GU Psc b H = 17.70,
51 Eri b H = 18.99.

## 7. Risk register

**The single unretired risk is whether ESO's `calib_level=2` products preserve what `viper`
needs.** If they are order-merged or resampled such that the per-order wavelength solution
is destroyed, forward-modelling RV extraction at tens of m/s is not possible from them, and
the project reverts to building cr2res for all 20 nights — a much larger undertaking.
**RETIRED in M1.** The products are per-order extractions with native wavelength solutions
(7 orders x 3 detectors x 2048 pixels, labelled by `ORDER`/`DETEC`/`XPOS`, curved dispersion
within each segment). `viper` can use them. See M1-RESULTS §5.

Note the first automated verdict said the opposite — `describe()` counted wavelength columns,
saw one, and reported ORDER-MERGED. **Acting on it would have meant rebuilding cr2res for 20
nights that never needed it.** Structural columns beat statistical heuristics; the classifier
now keys on ORDER/DETEC and `tests/test_fetch.py` pins both shapes.

Residual cost, known in advance: the archived product is the *combined* one (ESO serves one
per night; the paper used individual nodding frames), so it carries a ~10% precision penalty
— 34.49 vs 31.44 m/s. M3 must not read that offset as disagreement.
