# Runbook — extracting RVs from ESO archive spectra with `viper`

> ## ⚠ THIS RUNBOOK REPRODUCES THREE KNOWN BUGS. Read [`M12-RESULTS.md`](../M12-RESULTS.md) first.
>
> 1. **§5's command is missing `-nocell`.** `[CRIRES]` in `config_viper.ini` is the
>    *gas-cell* configuration; our data has `INS1 OPTI1 ID = FREE`. Without the flag viper
>    multiplies the model by the SGC2 N₂O cell spectrum. Köhler §5.4: cell-free modelling
>    proceeds *"just without the modelling of the cell lines."*
> 2. **§4's template is wrong.** Copying an observation gives a template with the tellurics
>    still in it, and they Doppler-shift with the fitted RV while the real ones stay put.
>    Build it with `-createtpl 1 -nocell -tpl_wave tell` instead.
> 3. **§7's precision target of 31.44 m/s is superseded.** The peer-reviewed figure is
>    **57.68 m/s**.
>
> Fixing 1 and 2 takes the archive route from 763 to 480 m/s on the paper's own error
> statistic and removes a significant RV–BERV correlation.
>
> **And the archive route is not the whole process.** For a new target you need the
> reduction too — see §9 below and [`scripts/cr2res/`](../scripts/cr2res/).

Everything needed to rebuild M2's pipeline from scratch. Written because the sequence took
most of a working session to discover and none of it is documented upstream for archive data.

Expected outcome if you follow this exactly: **RVs for all 18 public CD-35 2722 B epochs, at
~760 m/s formal error and ~800 m/s scatter.** That is 25× short of the 31.44 m/s the paper
achieved, and closing that gap is the project's open problem — see [§7](#7-the-open-problem).
Do not expect this runbook to reproduce the detection. It reproduces the *state of the art in
this repository*, which is a working but coarse extraction.

---

## 1. Why WSL

`viper` imports `termios` (`utils/pause.py`), so it does not run on Windows. It also calls
`gnuplot` at **import time** in two class bodies of `utils/gplot.py`, so it fails to import
anywhere gnuplot is absent — even though gnuplot is only needed for interactive `-look*`
plots that RV extraction never uses.

```bash
wsl bash -lc 'python3 -m venv ~/viperenv && ~/viperenv/bin/pip install numpy scipy astropy'
wsl bash -lc 'cd ~ && git clone --depth 1 https://github.com/mzechmeister/viper.git viper-src'
```

Do **not** `pip install viper`. The published wheel omits the `inst/` package, so
`importlib.import_module("inst.inst_CRIRES")` fails. Clone the repository.

## 2. Patch the gnuplot calls

```bash
wsl bash -lc '~/viperenv/bin/python /mnt/c/.../exosat-rv/scripts/patch_viper.py ~/viper-src'
```

[`scripts/patch_viper.py`](../scripts/patch_viper.py) wraps both calls in `try/except` and
leaves behaviour unchanged on machines that do have gnuplot. If you would rather not patch
someone else's source, [`scripts/gnuplot_shim.sh`](../scripts/gnuplot_shim.sh) is a no-op
`gnuplot` you can drop on `PATH` instead — it answers `-V` and sinks stdin so viper's
subprocess pipe stays open.

> Write the shim from a file, not from a shell heredoc. Nested quoting mangles `$1` and it
> silently becomes an empty `case` that matches nothing.

## 3. Fetch and convert the spectra

```bash
exosat-rv probe --n 18          # downloads ESO ADP products to data/spectra/
```

Then reshape them into the layout `inst_CRIRES` expects:

```python
from pathlib import Path
from exosat_rv.archive.cr2res import convert, verify_roundtrip
for src in sorted(Path("data/spectra").glob("*.fits")):
    dest = convert(src, Path("data/cr2res") / src.name)
    assert verify_roundtrip(src, dest)["max_abs_diff"] == 0.0
```

**The layout detail that matters:** cr2res writes **2048 rows of scalar columns**, not one
row holding a 2048-element array. `inst_CRIRES` indexes columns with no row index, so an
array-cell layout hands it a `(1, 2048)` 2-D array. The failure surfaces far from the cause —
`truth value of an array is ambiguous` for observations, `` `x` must be 1-dimensional `` for
templates.

## 4. Build a template

**Templates are in Ångström; observations are in nm.** `Spectrum` multiplies WL by 10, the
`*_tpl.fits` branch of `Tpl` does not. A template copied from an observation lands a factor
10 away, never overlaps, and every pixel is trimmed.

The filename must also end in `_tpl.fits` — viper dispatches on it.

```python
from astropy.io import fits
with fits.open("data/cr2res/<best-S/N-epoch>.fits") as h:
    for det in (1, 2, 3):
        for c in h[det].columns:
            if c.name.endswith("_WL"):
                h[det].data[c.name] = h[det].data[c.name] * 10.0   # nm -> Angstrom
    h.writeto("cd35_2722B_tpl.fits", overwrite=True)
```

A co-added template via `-createtpl` also works and **makes no measurable difference** (M2 §5).
Build it from that seed if you want one; viper writes it already in Ångström.

> **Template spectral type must match the target.** M3 found this is not a refinement: an
> L-dwarf template on a T dwarf turned a real 18 km/s signal into reduced χ² = 0.53, i.e.
> nothing. A matched template gave 5.36 on the same data.

## 5. Run

```bash
wsl bash -lc 'export PATH="$HOME/bin:$PATH"; cd ~/viper-src && \
  ~/viperenv/bin/python viper.py "cr2res_data/*.fits" cd35_2722B_tpl.fits \
    -inst CRIRES \
    -fts lib/CRIRES/FTS/CRp_SGC2_FTStmpl-HR0p007-WN5000-10000_Hband.dat \
    -targ "CD-35 2722" -tag run1'
```

**`-fts` is mandatory for H-band data.** `inst_CRIRES.FTS` defaults to the **K-band** template
(`WN3000-5000` = 2000–3333 nm). H-band data has zero overlap with it, so every pixel is
trimmed and the fit dies with an empty-index `IndexError` — the *same* symptom as the
Ångström/nm mismatch in §4, from a completely different cause.

viper resolves the target through SIMBAD and caches to `<tag>.targ.csv`. A new `-tag`
triggers a fresh network fetch, which fails intermittently (`ConnectionResetError`). Copy the
cached file across tags: `cp tmp.targ.csv run1.targ.csv`.

## 6. Read `config_viper.ini` before changing any setting

The `[CRIRES]` section already sets:

```
telluric = add      oset = 7:17      kapsig = 15 6
deg_bkg = 1         deg_norm = 2     deg_wave = 2
chunks = 1          ip = g           vcut = 100
```

So `-telluric add` is a **no-op** — verified byte-identical output. M2 spent effort on the
belief that telluric modelling was off. It never was.

**Do not add `-tellshift`.** For cell-free data the telluric lines *are* the wavelength
reference and must stay fixed (Köhler et al. 2025 §5.4). `-tellshift` frees them and roughly
triples the scatter.

## 7. The open problem

CRIRES+ is not stabilised; without a proper wavelength correction it drifts **up to 1 km/s**
(Köhler et al. 2025). The ~800 m/s this runbook produces is that drift, only partly removed.
The same paper reaches **10–16 m/s cell-free** on bright M dwarfs and 3 m/s with a gas cell.

Three differences from the authors remain, in the order I would attack them:

1. ~~**Individual nodding frames.**~~ **Demoted by M9 — it is a 10% lever.** The authors
   treat each nodding position as a separate observation (31.44 m/s) rather than the
   combined spectrum (34.49 m/s), and quantify the gain at ~10% in their own Fig. 4. It is
   the only remaining difference they name, but it cannot close a factor of 25. Do this
   last, not first. Order screening was measured too, at 6% — see
   [`M9-RESULTS.md`](../M9-RESULTS.md).

   **What to attack instead: the per-order forward model, template first.** M2's co-added
   template made the scatter *worse* (823 → 1638 m/s), which is what co-adding without
   correct RV alignment looks like.
2. **Band.** Köhler's cell-free demonstration is in **K**. This data is **H**, and cell-free
   H-band precision is not characterised in any paper read so far. This may be the real
   ceiling and is worth establishing before more tuning.
3. **Brightness.** Their 10–16 m/s used bright RV standards; CD-35 2722 B is S/N ≈ 18.

Untried settings: `-telluric mask`/`sig`/`add2`, IP models beyond `g`, `-chunks` > 1.

## 7b. Three traps M11 hit, all operational

**1. `-tpl_wave` defaults to `initial`, which applies NO barycentric correction.**
`viper.py` line 616 sets `bervt = 0` for `initial`. Köhler et al. 2025 §2.2 requires the
correction — *"Co-adding several spectra that were taken at different barycentric
velocities, and are corrected for that, helps reduce residuals from the telluric
correction."* For cell-free CRIRES+ use `-tpl_wave tell` (telluric-derived solution).
**Untested in isolation** — M11 changed it together with template iteration and cannot
score it separately. One run with zero iterations would.

**2. viper's printed `rms(RV)` is NOT the `RV` column it writes.** `vpr.info()` recomputes
a *weighted* mean (`avg='wmean'`, `vpr.py` line 148); the `.rvo.dat` `RV` column is the
plain mean. They differed by **1.8×** in M11 — 308.7 m/s on the banner against 620 m/s in
the column. **Quote the column**, or runs stop being comparable across milestones.

**3. DO NOT iterate a self-built template on a target whose signal you are measuring.**
Two iterations per the published recipe improved CD-35 2722 B (776 → 620 m/s) and **halved
the control's recovered amplitude** — 5948 → 2452 m/s on GJ 229 B's undisputed binary,
after a *single* iteration, with no recovery on the second. Self-templating absorbs the
signal: the template is co-added from the target's own spectra aligned by RVs measured
against a template already containing the signal. See [`M11-RESULTS.md`](../M11-RESULTS.md).

`-createtpl` *does* apply the RV shift (`viper.py` line 624) and Köhler's eq. 14 weighting
(line 630). The recipe is implemented faithfully; the recipe itself is the hazard here.

## 8. Validate before believing any result

Run the positive control. `GJ 229 B` (= `HD 42581 B`) has 16 public products, **all H1567**,
the same setting as CD-35 2722 B, and a *known* 12.1-day binary (Xuan et al. 2024) implying
K = 18.07 km/s. Fetch by coordinate (92.64254, −21.87071), filter `target_name` to the B
component, convert, and run with a **GJ 229 B self-template**.

Expected: χ² about a constant ≈ 80 falling to ≈ 17 when fitted at 12.1 d. Recovered
K ≈ 6 km/s, not 18 — the pair is unresolved and double-lined, so a single-template fit tracks
a suppressed flux-weighted centroid. See M3-RESULTS §4.

**A null from this pipeline means nothing without this control passing.**


## 9. From raw data — the half this runbook never covered

Everything above starts from ESO's archived `calib_level=2` product. That only exists where
ESO happened to reduce the night, and it is one spectrum per night rather than the two
nodding frames the method wants. For a new target, build the reduction too.

`cr2res` **1.6.10** — the paper's version — installs from ESO's self-contained kit. Three
traps, all hit:

- `install_pipeline` needs a **tty** (wrap it in `script`), refuses to rerun in a used kit
  directory (**and a blank line at that prompt means ABORT**), and restarts from zero every
  time. On a box where the WSL service crashes under load it therefore never finishes.
  [`scripts/cr2res/build_cr2res.sh`](../scripts/cr2res/build_cr2res.sh) builds the eleven
  components directly instead, with a stamp per component so it resumes.
- CPL needs a **thread-safe cfitsio** (`--enable-reentrant`) and its bundled **libcext**
  installed separately first; esorex and cr2re both need `--with-cext`.
- cr2re needs **pkg-config** and **libcurl** headers. With no sudo, build both into the same
  prefix ([`pkgconf.sh`](../scripts/cr2res/pkgconf.sh), [`curl.sh`](../scripts/cr2res/curl.sh)).

> **Then do not source [`cr2env.sh`](../scripts/cr2res/cr2env.sh) in any shell that does
> networking.** The minimal libcurl built above has **no SSL** and sits on
> `LD_LIBRARY_PATH`, which shadows the system libcurl for *every* binary in that shell —
> even `/usr/bin/curl` returns HTTP 000. Keep the download and reduction stages separate.

### The cascade

```bash
scripts/cr2res/urls_for_night.py <ADP file> urls.txt   # resolve raw frames + masters
scripts/cr2res/fetch_night.sh                          # ~1.5 GB per night
scripts/cr2res/reduce_night.sh   # cal_dark -> cal_flat -> cal_wave -> obs_nodding
```

ESO's calselector serves mostly **raw** FLAT/DARK/WAVE_UNE/WAVE_FPET, not the master
products it used, so the calibration cascade has to be run rather than downloaded. All twelve
`cr2res_obs_nodding` defaults match what the ADP headers record ESO used, so the reduction
differs from theirs only where you choose. Validated: our combined extraction reproduces
ESO's archived product to **57 m/s** in wavelength and **42 m/s** in final RV.

### Feeding the per-nodding products to viper

`cr2res_obs_nodding_extractedA/B.fits` are already in viper's native layout — no converter.
But **strip order 09 first** ([`strip09.py`](../scripts/cr2res/strip09.py)): cr2res extracts
8 orders where ESO's IDP keeps 7, and viper derives the DRS order from `columns.names[-1]`
separately for observation and template, so a different highest order puts them permanently
one apart and every pixel is trimmed.

### What you get, and what you do not

The per-nodding products carry **separate wavelength solutions** (`trace_wave_A/B`), and A
and B really are offset — median **4.1 px**, up to 8.6 — from slit tilt over the nodding
throw. ESO's combined product handles this correctly (it resamples before summing), so the
archive is not broken; the gain from working per-frame is the ~5% the paper quotes.

Measured against the published RVs over five nights, the best configuration reaches
**387 m/s rms against their 54 m/s.** Still a factor of 7. See M12 §9b.4 — and note that an
A−B null test made this look like 66 m/s until it was checked against the published values.
**Superseded by §10: M13 brought this to 147–218 m/s.**


## 10. The M13 recipe — the closest configuration to the paper's

[`scripts/injection/m13_batch.sh`](../scripts/injection/m13_batch.sh) is the whole thing:
one telluric-free template over **all 21 segments** (`-createtpl -nocell -tpl_wave tell
-oset 0:21`, one iteration), then RV runs on the reverse-engineered order set.

- **Order set** (`H_C`): `-oset 4,7,8,9,10,12,13,14,17,18,19` — the paper's eleven orders
  mapped through viper's pre-`6e1b19c` CRIRES numbering. M13 §1 has the three-way
  confirmation; do not re-derive it from the paper's labels with current viper.
- **`-kapsig 3`** — worth more than any other flag (rms_pub 492 → 218).
- **Combine orders with the median, not the mean.** The set is bimodal (M13 §2): orders
  7–10 carry night-to-night systematics that injections prove are not transmission
  failures. Median: 147 m/s; clipped mean: 165; mean: 218.
- **Score every change against the published table** with
  [`vs_published.py`](../scripts/injection/vs_published.py), and **injection-validate**
  anything adopted ([`inject_generic.sh`](../scripts/injection/inject_generic.sh) +
  [`inject_score2.py`](../scripts/injection/inject_score2.py) — shift the template, never
  the observation). M13's winner passed at 100% ± 5%.
- Known bad: order 18 fails injection (8% ± 56%); `-chunks 2` helps the mean but not the
  median; `-telluric add2` and `-deg_wave 3` do nothing here.
