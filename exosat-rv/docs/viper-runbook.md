# Runbook — extracting RVs from ESO archive spectra with `viper`

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

1. **Individual nodding frames.** The authors treat each nodding position as a separate
   observation (31.44 m/s) rather than using the combined spectrum (34.49 m/s). **ESO
   archives only the combined product**, so this requires running `cr2res` on the public raw
   frames. It is the only remaining difference the authors themselves name.
2. **Band.** Köhler's cell-free demonstration is in **K**. This data is **H**, and cell-free
   H-band precision is not characterised in any paper read so far. This may be the real
   ceiling and is worth establishing before more tuning.
3. **Brightness.** Their 10–16 m/s used bright RV standards; CD-35 2722 B is S/N ≈ 18.

Untried settings: `-telluric mask`/`sig`/`add2`, IP models beyond `g`, `-chunks` > 1.

## 8. Validate before believing any result

Run the positive control. `GJ 229 B` (= `HD 42581 B`) has 16 public products, **all H1567**,
the same setting as CD-35 2722 B, and a *known* 12.1-day binary (Xuan et al. 2024) implying
K = 18.07 km/s. Fetch by coordinate (92.64254, −21.87071), filter `target_name` to the B
component, convert, and run with a **GJ 229 B self-template**.

Expected: χ² about a constant ≈ 80 falling to ≈ 17 when fitted at 12.1 d. Recovered
K ≈ 6 km/s, not 18 — the pair is unresolved and double-lined, so a single-template fit tracks
a suppressed flux-weighted centroid. See M3-RESULTS §4.

**A null from this pipeline means nothing without this control passing.**
