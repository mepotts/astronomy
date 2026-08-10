# M2 — RV extraction, and the reproduction verdict

**Question:** can `viper` be run on ESO's public archive products, and does it reach the
~31 m/s the detection needs?

**Answers: yes, and no.** The archive products can be made to feed viper — that took a
format converter and four configuration discoveries, all documented below — and viper then
extracts RVs for all 18 public epochs. But the precision reached is **~760 m/s formal, with
real scatter of 800–2800 m/s**, some 25–90× short of the paper's 31.44 m/s.

**The 246 m/s signal is therefore not recovered, and this milestone does not reproduce the
detection.** That is the result, not a bug to be tuned away in the write-up. §5 states
plainly what would be needed and what remains untried.

---

## 1. The spectra, and two things they revealed

All 18 public reduced products downloaded (2.0 MB each, `exosat-rv probe --n 18`). Every one
is setting **H1567**, 1468.9–1779.9 nm, 21 segments × 2048 px — a homogeneous set.

Median per-segment S/N across epochs is **18.3** (range 12.9–22.4), except one:

| Epoch | Median S/N | Best segment |
|---|---:|---:|
| **2024-10-21** | **2.2** | **4.9** |
| all others | 12.9–22.4 | 18.0–28.2 |

The preprint says it obtained 21 epochs and **discarded one for "a very low signal-to-noise
ratio (S/N) in the spectral continuum of ~5"**. 2024-10-21 is that epoch — identified here
independently, from the archive, without reference to which night the authors dropped.

**And an ESO metadata error.** Cross-checking all 18 products against `dbo.raw` found one
mismatch: 2024-01-03 is labelled `filter_path = K,HK` in the raw table, but the product built
from exactly those two frames (`PROV1`/`PROV2` name them) carries `INS WLEN ID = H1567` and
spans 1468.9–1779.9 nm. **It is an H-band observation mislabelled as K.**

That corrects M0's arithmetic in both terms. The true count is **18 reduced + 3 raw-only = 21
public H-band nights**, matching the **21 epochs the paper obtained** — of which one (the
S/N 2.2 night) was discarded, leaving 20. M0 reported 20 ↔ 20; the real correspondence is
21 ↔ 21, and it identifies the discarded night as well.

## 2. The converter

viper reads the *pipeline's* output, not the archive's. `inst_CRIRES.Spectrum` wants three
BinTable extensions — one per detector — with columns `0<order>_01_SPEC`, `_ERR`, `_WL`.
The ADP product holds the same numbers in one flat table keyed by `ORDER`/`DETEC`/`XPOS`.

`exosat_rv.archive.cr2res` performs that reshape. **Nothing is resampled or rescaled**;
`verify_roundtrip` confirms a maximum absolute difference of **0** across all 18 files and
all 21 segments each.

This is the piece that makes the reproduction repeatable by anyone: it removes the need for
the authors' intermediate files.

**The mistake worth recording:** the first version wrote *one row holding a 2048-element
array* per column. cr2res writes *2048 rows of scalars*. viper indexes columns without a row
index, so the array-cell layout handed it a `(1, 2048)` 2-D array — surfacing much later as
`ValueError: truth value of an array is ambiguous` for observations and `ValueError: 'x' must
be 1-dimensional` for templates. Neither message names the cause. `tests/test_cr2res.py`
pins the layout.

## 3. Four configuration discoveries

None of these are documented for archive data; each cost a failed run.

1. **viper cannot import headlessly.** `utils/gplot.py` calls `gnuplot` in two class bodies,
   so the import fails outright where gnuplot is absent — even though it is needed only for
   interactive `-look*` plots. Two `try/except` wrappers fix it (`scratchpad/patch_viper.py`).
2. **It needs Unix.** `utils/pause.py` imports `termios`. Run under WSL, not Windows.
3. **The default FTS template is K-band.** `inst_CRIRES.FTS` defaults to
   `...WN3000-5000_Kband.dat` — wavenumbers 3000–5000 cm⁻¹, i.e. 2000–3333 nm. H-band data
   has no overlap with it, so *every pixel is trimmed* and the fit dies in
   `np.where(flag_obs==0)[0][[0,-1]]` with an empty-index `IndexError`. The H-band file
   **is** shipped — `...WN5000-10000_Hband.dat` — and must be passed with `-fts`.
4. **Templates are in Ångström; observations are in nm.** `Spectrum` multiplies WL by 10;
   the `*_tpl.fits` branch of `Tpl` does not. Handing viper a template copied from an
   observation puts the two 10× apart, they never overlap, and you get the *same* empty-index
   failure as (3) — from an entirely different cause. The template must also be named
   `*_tpl.fits`; viper dispatches on the filename.

With all four applied, viper runs clean over 18 epochs and 10 usable orders in ~3 s/epoch.

## 4. The RVs, and why they are not good enough

18 of 18 epochs returned finite RVs. Formal errors: median **763 m/s**. Scatter: **823 m/s**.

Per-order behaviour shows the problem is systematics, not photon noise:

| Order | rms (m/s) | median formal error | ratio |
|---:|---:|---:|---:|
| 8 | 4247 | 101 | **42** |
| 16 | 1082 | 264 | 4.1 |
| 12 | 734 | 444 | 1.7 |
| 11 | 3954 | 1221 | 3.2 |

**Formal errors are inconsistent with actual scatter by factors of 2–40.** An inverse-variance
combination of the five formally-best orders gives a median error of 83 m/s against an rms of
2816 m/s — the errors are meaningless in this configuration. Nothing here is photon-limited.

The GLS of these RVs peaks at **368 d**, close to a year — the observing-season structure —
with power 0.545. Power at the published 169.45 d is 0.243, not a detection. At 763 m/s
errors over 18 epochs a 246 m/s signal has SNR ≈ 1.4, so this is the expected outcome, not a
surprising one.

## 5. What is missing, stated plainly

The gap to 31.44 m/s is not a tuning detail. Three things differ from the paper:

1. **The template.** Ours is a single epoch (S/N ~21). The paper used an empirical template;
   viper builds one with `-createtpl`, which would raise template S/N by ~√18. **That run
   failed here on a network fetch (`ConnectionResetError`) and was not retried.** This is the
   most likely single largest win and the obvious next step.
2. **Telluric handling.** The paper pinned its wavelength solution to stable telluric lines
   at ~10 m/s. This run used `-telluric ''` — no telluric modelling at all. viper offers
   `mask`, `sig`, `add`, `add2`, plus `-tellshift`; none were tried.
3. **The nodding frames.** The paper's 31.44 m/s came from treating individual nodding
   positions as separate observations; the combined product it compares against gave 34.49
   m/s. ESO archives only the combined product, so ~10% is unavailable by construction —
   but that is a rounding error next to the factor of 25 above, and does **not** explain it.

Also untried: order selection/clipping (`-kapsig`), IP model choice, `-chunks`, and the
`-oset` default excluding 11 of 21 segments.

## 6. Verdict

**M3's reproduction verdict is: not achieved at this precision.** The published detection is
neither confirmed nor contradicted by this work — the data as extracted here cannot see a
246 m/s signal, so this is a null of *method*, not of *nature*.

What the milestone does establish, and what is reusable:

- ESO's public products **can** feed viper, via a verified-lossless converter.
- The four configuration traps above are now documented, with the exact symptoms.
- The epoch inventory is corrected (21 ↔ 21) and the discarded epoch identified.
- The precision floor of *this* configuration is measured: ~800 m/s, systematics-dominated.

The path to a real reproduction runs through §5 item 1, and nothing further should be claimed
until it is tried.
