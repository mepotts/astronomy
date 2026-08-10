# HANDOFF — exosat-rv

Picking this up cold? Read in this order:

1. [`SPEC.md`](SPEC.md) — what is being tested and why it is worth testing.
2. [`M0-RESULTS.md`](M0-RESULTS.md) — what the archive actually contains.
3. [`BUILD-PLAN.md`](BUILD-PLAN.md) — stack, architecture, milestones.
4. [`DATA-SOURCES.md`](DATA-SOURCES.md) — endpoints, and the traps in each.

The rest of this file is the expensive part: claims that turned out false, approaches
measured and rejected, and silent failures that cost data. The code is not the expensive
part.

---

## 1. Claims published here and later found false

**None yet** — no result has been published from this project. One *inherited* claim has
been disproved, below.

## 2. Inherited claims that do not survive checking

### `hill_radius_au = 1.07` (Hoy et al., per an AI summary of the body) — INCONSISTENT

A 1.07 au Hill radius for a 37 M_Jup companion inside a 0.5 M_sun primary implies an
orbital separation of **3.73 au**. CD-35 2722 B is directly imaged at 2.8", which at the
SIMBAD parallax of 44.72 mas is **62.6 au**, where the Hill radius is **~17.9 au**. The two
cannot both be true.

Handling: the value is **kept** in `config.py`, flagged, and pinned by
`test_published_hill_radius_is_internally_inconsistent`, so that whoever eventually reads
the real PDF is forced to resolve it rather than quietly overwrite it. All physics
assertions use a self-consistent Hill radius instead. Both satellite orbits are stable
either way (a = 0.199 au is 1.1% of the true Hill radius).

**This was never the paper's error to answer for.** It came from an AI summary of a PDF
that would not extract, which is the actual root cause — see §3.

## 3. Approaches measured and rejected

| Approach | Why rejected |
|---|---|
| Populating `config.py` from AI summaries of the paper body | Produced at least one impossible value (§2). Every such field is now tagged `[SUMM]` and **barred from backing a test**. Reading the PDF under WSL is an M1 task and an M3 prerequisite. |
| `CONTAINS(POINT(...), CIRCLE(...))` on ESO `dbo.raw` | Hard-fails with a SQL-Server geography error — the table holds rows whose coordinates do not validate. A plain ra/dec box works and is faster. |
| `astroquery.eso` for archive access | Wraps the web form; awkward for the `dbo.raw` / `ivoa.ObsCore` comparison that is the whole of M0. `pyvo` gives direct ADQL against both. |
| Reducing all 20 nights from raw with esorex/cr2res | M0 measured that 17 are already reduced by ESO. Building cr2res to recover 3 nights is a late optimisation, not a prerequisite. |
| Using `EMPEROR` (the paper's sampler) for M3 | Would make the reproduction circular. `radvel` is used instead so that agreement means something. |
| Using `sy_hmag` from the NASA Exoplanet Archive as the companion brightness cut | It is the **system** magnitude, dominated by the primary. Useless for a companion flux cut. |
| Trusting the NASA Exoplanet Archive alone for the M5 target list | It caps companion mass at 30 M_Jup and therefore **does not contain CD-35 2722 B**. A list built from it would exclude the object being reproduced. |

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
- **Two extra public nights (2023-01-04, 2023-02-01)** exist that the paper does not use.
  They are J/YJ band, not H, so they are not a discrepancy — see M0 §3. They may still be
  useful to M4 for baseline leverage.

## 6. Open risk, stated plainly

**The single unretired risk is whether ESO's `calib_level=2` products preserve what `viper`
needs.** If they are order-merged or resampled such that the per-order wavelength solution
is destroyed, forward-modelling RV extraction at tens of m/s is not possible from them, and
the project reverts to building cr2res for all 20 nights — a much larger undertaking.
Nobody has opened one of these files yet. **M1 exists to retire this risk and should be
done before anything else.**
