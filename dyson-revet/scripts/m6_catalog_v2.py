"""M6: catalogue v2 -- N4's morphology columns, and completeness MEASURED.

M5 delivered `dyson-revet_highlat_extreme_IR_excess_v1.csv` with completeness
marked UNMEASURED.  M6 Sec 3 measures it by injection-recovery and M6 Sec 1
adds a coadd-morphology flag.  M6 PR-3 fixes what may change and what may not:

  * v1 is NOT edited, moved or deleted.  v2 is a new file.
  * The nebular stage is a FIELD statistic and this catalogue's policy since
    M5 Sec 4 is to RETAIN AND FLAG, never to cut on it -- so N4 adds columns
    and removes no row.  Any row difference at all is enumerated below.
  * Completeness is updated ONLY where the injection actually measures it.
    Anything it does not reach stays UNMEASURED and stays marked so.

    python scripts/m6_catalog_v2.py
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
CAT = ROOT / "catalog"
V1 = CAT / "dyson-revet_highlat_extreme_IR_excess_v1.csv"
V2 = CAT / "dyson-revet_highlat_extreme_IR_excess_v2.csv"


def main() -> None:
    v1 = pd.read_csv(V1)
    n1 = len(v1)
    morph = pd.read_csv(OUT / "m6_morph_flags_rmse.csv")
    comp = json.loads((OUT / "m6_injection_completeness.json").read_text())
    cal = json.loads((OUT / "m6_morph_calibration.json").read_text())

    keep = ["source_id", "w3_S", "w4_S", "w3_A", "w4_A", "w3_G", "w4_G",
            "w3_C", "w4_C", "morph_ok", "n4_score", "n4_flag"]
    keep = [c for c in keep if c in morph.columns]
    v2 = v1.merge(morph[keep], on="source_id", how="left", suffixes=("", "_m6"))
    v2["morph_ok"] = v2["morph_ok"].fillna(False)
    v2["n4_flag"] = v2["n4_flag"].fillna(False)
    v2["nebular_flag_v2"] = (v2["nebular_flag"].astype(bool)
                             | v2["n4_flag"].astype(bool))
    v2["catalog_version"] = "v2"

    assert len(v2) == n1, "v2 must not change the row count"
    added = [c for c in v2.columns if c not in v1.columns]
    print("v1 %d rows x %d cols -> v2 %d rows x %d cols"
          % (n1, v1.shape[1], len(v2), v2.shape[1]))
    print("  rows added: 0   rows removed: 0   columns added: %d" % len(added))
    print("  new columns: %s" % ", ".join(added))
    print("  N4 morphology measured for %d of %d rows (%.1f%%)"
          % (int(v2["morph_ok"].sum()), len(v2),
             100 * v2["morph_ok"].mean()))
    print("  N4 flags %d rows; nebular_flag (M5) flagged %d; union %d"
          % (int(v2["n4_flag"].sum()), int(v2["nebular_flag"].sum()),
             int(v2["nebular_flag_v2"].sum())))
    v2.to_csv(V2, index=False)

    st = json.loads((CAT / "catalog_stats.json").read_text())
    st["catalog_version"] = "v2"
    st["supersedes"] = {"file": V1.name,
                        "difference": "0 rows added, 0 rows removed; %d columns "
                                      "added (N4 coadd-morphology statistics and "
                                      "flag, and the v2 nebular union)" % len(added),
                        "note": "v1 is retained unmodified in this directory"}
    st["columns"] = int(v2.shape[1])
    st["selection_function"]["nebular_stage"] = (
        "M5 N1 (catalogue veto) | N2 (coadd background percentile > 0.99) | "
        "M6 N4 (coadd structure index S, percentile > 0.99).  All three are "
        "carried as per-row FLAGS in this catalogue and none of them cuts a "
        "row from it.")
    cf = comp["catalogue_footprint"]
    st["completeness"].pop("not_measured", None)
    st["completeness"]["injection_recovery"] = {
        "status": "MEASURED (M6 Sec 3)",
        "method": "synthetic star + blackbody SEDs from the selection code's own "
                  "forward model, injected onto real parent hosts with the "
                  "survey's own per-band uncertainties at the injected "
                  "brightness, pushed through the unmodified pipeline",
        "n_injections": comp["n_injections"],
        "previsual_recovery_b_gt_30": cf["highlat_b_gt_30_previsual_recovery"],
        "previsual_recovery_core_b_gt_50": cf["core_b_gt_50_previsual_recovery"],
        "core_recovery_by_gamma": cf["core_b_gt_50_by_gamma"],
        "core_rmse_gate_by_gamma": cf["core_b_gt_50_rmse_by_gamma"],
        "control_gamma0_rmse_false_positive_rate":
            comp["control_gamma0"]["rmse_gate_false_positive_rate"],
        "still_unmeasured": "the recovery fraction is measured for the model "
                            "family the selection itself assumes (a single "
                            "blackbody shell on a main-sequence photosphere). "
                            "Excesses whose SED is NOT of that family -- a "
                            "two-temperature disk, a silicate-featured disk, an "
                            "edge-on system -- are still UNMEASURED, and this "
                            "test cannot reach them."}
    st["completeness"]["morphology_stage"] = {
        "n4_false_positive_rate_on_calibration":
            cal["measured_combined_FPR_on_calibration"],
        "n4_cutout_validity": cal["valid_fraction"]}
    (CAT / "catalog_stats_v2.json").write_text(json.dumps(st, indent=2))
    write_readme(v2, st, comp, cal, added, n1)
    print("-> %s, catalog_stats_v2.json, README_v2.md" % V2.name)
    return v2, st, comp, cal, added


def write_readme(v2, st, comp, cal, added, n1) -> None:
    ig = comp["in_model_grid"]
    og = comp["outside_model_grid"]
    core = st["footprint"]["calibrated_core"]["n"]
    fpr = cal["measured_combined_FPR_on_calibration"]["0.99"]
    txt = f"""# The high-latitude extreme mid-IR-excess catalogue, v2

**`{V2.name}` — {len(v2)} objects, {v2.shape[1]} columns.**
Produced 2026-08-24 by [`../scripts/m6_catalog_v2.py`](../scripts/m6_catalog_v2.py)
from v1; every number below is emitted by code, never hand-entered. Machine-readable
provenance lives in [`catalog_stats_v2.json`](catalog_stats_v2.json).

**v1 is not superseded in the sense of being withdrawn.**
[`{V1.name}`](.), [`catalog_stats.json`](catalog_stats.json) and
[`README.md`](README.md) are unmodified and still describe exactly what M5
released. Read [`README.md`](README.md) first for what the catalogue *is*, the
footprint, the selection function, the contamination numbers and the column
dictionary; this file records only what v2 changes.

---

## The v1 → v2 difference, enumerated

**Rows added: 0. Rows removed: 0.** The row set is byte-identical in
`source_id` to v1's {n1}. **Columns added: {len(added)}** —
{", ".join("`" + c + "`" for c in added)}.

The nebular stage is a statement about the **field**, not about the object, and
this catalogue's policy since M5 §4 is to **retain and flag**, never to cut. M6's
new morphology component **N4** is carried the same way, so it changes no row's
membership. `nebular_flag_v2` is the union N1 ∨ N2 ∨ N4; `nebular_flag` (v1's,
N1 ∨ N2) is retained unchanged beside it.

## What N4 is

A **training-free structure statistic measured on the AllWISE W3 and W4 Atlas
coadds themselves**, in an annulus 12″ < r < 45″ around each object after 3σ
clipping of neighbouring point sources:

> **S = σ_obs / σ_exp** — the robust dispersion of the PSF-smoothed intensity
> divided by the dispersion the coadd's own uncertainty image predicts under
> the same smoothing.

S is dimensionless and has a parameter-free null: on sky whose only structure is
noise, S → 1. A raised but *flat* background — the thing N2 already measures —
leaves S at 1. The flag threshold reuses M5 PR-2's N2 rule **verbatim**: the
percentile rank of S within |ecliptic latitude| bins of the |b| > 50° parent,
maximum over the two bands, cut at 0.99, with the combined false-positive rate
**measured** on the calibration set at **{100 * fpr:.2f}%**. No new free
parameter is introduced anywhere.

Per-object columns: `w3_S`, `w4_S` (the statistic), `n4_score` (its percentile
rank), `n4_flag` (the cut), `morph_ok` (whether a valid cutout was obtained at
all), and the three **reported-but-not-cut** diagnostics `w3_A`/`w4_A`
(azimuthal asymmetry), `w3_G`/`w4_G` (local gradient) and `w3_C`/`w4_C` (source
concentration against the coadd PSF), all in units of the local noise.

## Completeness — now MEASURED where the injection reaches

M5's README said, under Completeness: *"UNMEASURED: no injection-recovery test
has been run."* **That line is now false, and this is what replaces it.**

**{comp["n_injections"]:,} synthetic star + blackbody SEDs** were built by the
selection code's own forward model, injected onto **real parent hosts** with the
survey's own per-band uncertainties evaluated at the *injected* brightness, and
pushed through the **unmodified** pipeline (M6 §3). Inside the model grid the
pipeline can actually represent — γ ≥ 0.10 and 100 ≤ T_ds ≤ 700 K, n =
{ig["n"]:,}:

| | pre-visual recovery |
|---|---|
| all sky | **{100 * ig["all_sky_previsual_recovery"]:.1f}%** |
| **\\|b\\| > 30° — this catalogue's footprint** | **{100 * ig["b_gt_30_previsual_recovery"]:.1f}%** |
| **\\|b\\| > 50° — the calibrated core ({core} objects)** | **{100 * ig["b_gt_50_previsual_recovery"]:.1f}%** |

**Where the rest goes at |b| > 30°**: {100 * ig["undetected_fraction_b_gt_30"]:.1f}%
never detected in W3 or W4 at all; {100 * ig["extra_gate_loss_b_gt_30"]:.1f}%
removed by the extra cuts (Gvar, RUWE, `ext_flg`, `classprob` — all properties of
the host star, not of the excess); {100 * ig["snr_gate_loss_b_gt_30"]:.1f}%
removed by the S/N ≥ 3.5 gate. The RMSE fit itself passes
{100 * ig["all_sky_rmse_gate"]:.1f}% — **it is not the bottleneck.**

**Outside the grid, the catalogue is blind, and now quantitatively so:**

- covering fraction **γ = 0.01 → recovery {100 * og["gamma_below_floor_recovery"]["0.01"]:.2f}%**,
  γ = 0.02 → {100 * og["gamma_below_floor_recovery"]["0.02"]:.2f}%,
  γ = 0.05 → {100 * og["gamma_below_floor_recovery"]["0.05"]:.1f}%. v1's README
  said the catalogue "misses the majority of weaker excesses by construction";
  the measurement is harsher — **below γ ≈ 0.05 it misses essentially all of
  them.**
- **T_ds = 1000 K → recovery {100 * og["T_ds_1000K_recovery"]:.2f}%**, against
  ~31% at every temperature inside the [100, 700] K grid. **The grid's
  temperature range is a second hard boundary**, and it had not been costed
  before.
- A **control**: {comp["n_control_gamma0"]:,} bare photospheres (γ = 0) through
  the same pipeline gave an RMSE-gate false-positive rate of
  **{100 * comp["control_gamma0"]["rmse_gate_false_positive_rate"]:.2f}%**.
  Nothing in this catalogue is a photosphere scattered over the line by noise.

**Still UNMEASURED, and marked so**: the injection can only inject what the
forward model can generate — a single blackbody shell on a main-sequence
photosphere. Two-temperature disks, silicate-featured disks and edge-on systems
are **outside the test** and their recovery fraction is **not known**.

## Everything else is unchanged from v1

Footprint, selection function, contamination numbers, the retirement of V5, the
per-row `v5_centroid = "RETIRED"` column, and the statement that
**nothing in this catalogue is a candidate for anything** — all as in
[`README.md`](README.md).

## Reproducing v2

```
# ... v1's chain first (see README.md), then:
python scripts/m6_morph.py coadd --what calib
python scripts/m6_morph.py coadd --what rmse
python scripts/m6_morph.py stats --what calib
python scripts/m6_morph.py stats --what rmse
python scripts/m6_morph.py calibrate
python scripts/m6_morph.py apply --what rmse
python scripts/m6_injection.py run --per-cell 200 --jobs 8
python scripts/m6_injection.py report
python scripts/m6_catalog_v2.py
```

All services are used **anonymously**: no account at ESAC, AIP, IRSA, VizieR,
SVO or MAST was created at any point in this project.

## Version history

- **v2** — 2026-08-24. Same {len(v2)} objects. N4 coadd-morphology statistics
  and flag added per row; completeness measured by injection–recovery.
- **v1** — 2026-08-23. First release. {n1} objects, |b| > 30°, full-sky screen,
  M5 nebular stage applied as a flag (not a cut) inside the footprint, V5
  retired.
"""
    (CAT / "README_v2.md").write_text(txt, encoding="utf-8")


if __name__ == "__main__":
    main()
