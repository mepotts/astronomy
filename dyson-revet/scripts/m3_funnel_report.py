"""M3: the funnel, stage by stage, against Hephaistos II Table 4, with Poisson
intervals and the sky fraction stated on every projection.

Reads the funnel JSONs written by `w4_screen.py select` and emits a markdown
table plus a JSON summary. Nothing is hand-copied: every number in the M3
write-up comes from here.

Why Poisson intervals: each funnel stage is a COUNT of objects on a randomly
placed sky sample. The comparison "my 5 vs the paper's 6.7 expected" is
meaningless without an interval, and the Gaussian sqrt(N) approximation is
wrong at the counts that matter (the last stages have N < 30). We use exact
(Garwood) intervals from the chi-square quantiles, which are the standard
conservative Poisson confidence limits:

    lower = 0.5 * chi2.ppf(alpha/2, 2N)          (0 for N = 0)
    upper = 0.5 * chi2.ppf(1 - alpha/2, 2N + 2)

Run:  python scripts/m3_funnel_report.py --tags g0.1_full g0.01_full
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import chi2

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
SKY_DEG2 = 41252.96

# Hephaistos II (Suazo et al. 2024) Table 4 all-sky counts, stage by stage.
# The parent sample and the W3+W4-detected count are quoted in their Sec 2.1;
# the rest are the Table 4 rows. These are the published rates the screen is
# measured against.
PAPER = [
    ("parent sample (Gaia <300 pc x 2MASS x AllWISE)", None, 5.0e6),
    ("W3 and W4 both detected (C2a)", "T2_w34det", 3.2e5),
    ("cc_flags clean (C2b)", "T3_ccflags", None),
    ("... with full 10-band photometry", "T2_full10band", None),
    ("... inside the template M_G window", "T3_in_template_window", None),
    ("RMSE <= 0.2 star+DS grid fit (C3)", "T3_rmse", 11243),
    ("+ Gvar, RUWE, ext_flg, classprob (C5b-e)", "T4_extra", 5137),
    ("+ W3 & W4 S/N >= 3.5 (C6) -- pre-visual survivors", "T5_snr", 368),
    ("final candidates (C4 CNN + C7 visual)", None, 7),
]


def poisson_ci(n: int, alpha: float = 0.3173) -> tuple[float, float]:
    """Exact (Garwood) Poisson interval; default alpha gives the 68.27% CI."""
    lo = 0.0 if n == 0 else 0.5 * chi2.ppf(alpha / 2.0, 2 * n)
    hi = 0.5 * chi2.ppf(1.0 - alpha / 2.0, 2 * n + 2)
    return float(lo), float(hi)


def fmt_ratio(n: int, exp: float) -> str:
    """Observed/expected with the Poisson interval carried through."""
    if exp is None or exp <= 0:
        return "—"
    lo, hi = poisson_ci(n)
    return f"**{n / exp:.2f}×** [{lo / exp:.2f}–{hi / exp:.2f}]"


def report(tag: str) -> dict:
    path = OUT / f"w4_funnel_{tag}.json"
    if not path.exists():
        raise SystemExit(f"missing {path} -- run w4_screen.py select --tag {tag}")
    f = json.loads(path.read_text())
    f["_tag"] = tag
    return f


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags", nargs="+", required=True,
                    help="funnel tags to compare; the FIRST is the primary")
    ap.add_argument("--out", default="m3_funnel_report.md")
    a = ap.parse_args()

    fs = [report(t) for t in a.tags]
    prim = fs[0]
    area = prim["_area_deg2"]
    fsky = prim["_sky_fraction"]
    for f in fs[1:]:
        if abs(f["_sky_fraction"] - fsky) > 1e-9:
            print(f"WARNING: {f['_tag']} covers a different sky fraction "
                  f"({f['_sky_fraction']:.4f} vs {fsky:.4f})")

    # tile count from the live manifest (select does not record it)
    n_tiles = "?"
    mf = ROOT / "data" / "w4" / "manifest.json"
    if mf.exists():
        m = json.loads(mf.read_text())
        n_tiles = sum(1 for v in m["tiles"].values()
                      if v.get("status") == "done")

    L = []
    L.append(f"**Coverage: {area:,.0f} deg² = {100 * fsky:.2f}% of the sky** "
             f"({n_tiles} tiles). 'Paper expected' = "
             f"Suazo et al. 2024 Table 4 all-sky counts × {fsky:.4f}. "
             f"Intervals are exact Poisson 68% on the observed count.\n")
    hdr = "| stage | " + " | ".join(
        f"γ ≥ {f['_gamma_floor']:g}" for f in fs) + \
        " | paper expected | ratio (primary) |"
    L.append(hdr)
    L.append("|---" * (len(fs) + 3) + "|")

    summary = {"_area_deg2": area, "_sky_fraction": fsky, "stages": []}
    for label, key, allsky in PAPER:
        exp = None if allsky is None else allsky * fsky
        cells = []
        for f in fs:
            v = f.get(key) if key else None
            cells.append("—" if v is None else f"{v:,}")
        expc = "—" if exp is None else f"{exp:,.1f}"
        ratio = "—"
        n0 = prim.get(key) if key else None
        if n0 is not None and exp:
            ratio = fmt_ratio(int(n0), exp)
        L.append(f"| {label} | " + " | ".join(cells) +
                 f" | {expc} | {ratio} |")
        rec = {"stage": label, "key": key, "paper_allsky": allsky,
               "paper_expected": exp}
        for f in fs:
            rec[f"n_g{f['_gamma_floor']:g}"] = f.get(key) if key else None
        if n0 is not None:
            lo, hi = poisson_ci(int(n0))
            rec["poisson68"] = [lo, hi]
        summary["stages"].append(rec)

    # sky-wide projections, with the fraction stated
    L.append("\n**Sky-wide projections** (observed count ÷ sky fraction "
             f"{fsky:.4f}; the projection is only as good as the "
             "unbiasedness of the tile order — see PR-1):\n")
    L.append("| stage | " + " | ".join(f"γ ≥ {f['_gamma_floor']:g} projected"
                                       for f in fs) + " | paper all-sky |")
    L.append("|---" * (len(fs) + 2) + "|")
    for label, key, allsky in PAPER:
        if key is None:
            continue
        cells = []
        for f in fs:
            v = f.get(key)
            if v is None:
                cells.append("—")
                continue
            lo, hi = poisson_ci(int(v))
            cells.append(f"{v / fsky:,.0f} [{lo / fsky:,.0f}–{hi / fsky:,.0f}]")
        L.append(f"| {label} | " + " | ".join(cells) +
                 f" | {'—' if allsky is None else f'{allsky:,.0f}'} |")

    txt = "\n".join(L)
    (OUT / a.out).write_text(txt, encoding="utf-8")
    (OUT / a.out.replace(".md", ".json")).write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print(txt)
    print(f"\nwrote {OUT / a.out}")


if __name__ == "__main__":
    main()
