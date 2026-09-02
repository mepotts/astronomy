#!/usr/bin/env python3
"""Parse the MPTA published noise + deterministic tables for all 83 pulsars.

Source: arXiv:2412.01148 LaTeX source (data/paper/mnras_template.tex,
retrieved from https://arxiv.org/e-print/2412.01148 2026-08-21; the same
file M1/M2 transcribed their ten pulsars from by hand).

Emits results/m3/published_table.json:
  {psr: {"pub": {key: [MAP, lo_off, hi_off] or ["fixed", 4.0]},
         "model": {equad, ecorr, dm, red, chrom, sw, bump, annual},
         "curn_sourced": bool}}

`model` is INFERRED from which columns carry values, exactly the way M2
transcribed its ten by hand:
  - E_Q / E_C column present  -> equad / ecorr in the favoured model
  - log10A_Red present        -> free achromatic red
  - log10A_DM present         -> DM GP
  - log10A_Chrom present      -> chromatic GP; beta column "4" -> fixed4,
                                 a CI -> free beta
  - n_earth "4" (no CI) and no SW GP -> sw="fixed"
    n_earth with CI and no SW GP     -> sw="det"
    SW GP columns present            -> sw="full"
  - deterministic table: Gaussian-event row -> bump=+1/-1; annual row -> annual

Cross-check: the ten pulsars M2 transcribed by hand must reproduce exactly.
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TEX = REPO / "data" / "paper" / "mnras_template.tex"
OUT = REPO / "results" / "m3" / "published_table.json"

VAL = re.compile(r"\$\{(-?[\d.]+)\}_\{([+-][\d.]+)\}\^\{([+-][\d.]+)\}\$")

NOISE_COLS = ["efac", "log10_tnequad", "log10_ecorr",
              "red_log10_A", "red_gamma", "dm_log10_A", "dm_gamma",
              "chrom_log10_A", "chrom_gamma", "chrom_beta",
              "sw_log10_A", "sw_gamma", "gw13_log10_A", "n_earth"]
DET_COLS = ["bump_log10_A", "bump_beta", "bump_t0", "bump_sigma", "bump_sign",
            "ann_log10_A", "ann_beta", "ann_phase"]


def cell(s):
    """Parse one LaTeX table cell -> None | float (fixed) | (map, lo, hi)."""
    s = s.strip()
    if s in ("", "-", "--"):
        return None
    m = VAL.search(s)
    if m:
        return (float(m.group(1)), float(m.group(2)), float(m.group(3)))
    if s in ("$+$", "$-$"):
        return 1.0 if s == "$+$" else -1.0
    try:
        return float(s)                      # a bare "4" = fixed value
    except ValueError:
        return None


def rows(text, ncol):
    """Yield (psrname, [cells], bold) for LaTeX longtable body rows."""
    for line in text.splitlines():
        line = line.strip()
        if not line.endswith(r"\\") or "&" not in line:
            continue
        parts = [p.strip() for p in line[:-2].split("&")]
        if len(parts) != ncol:
            continue
        name = parts[0]
        bold = "textbf" in name
        m = re.search(r"(J\d{4}[+-]\d{4})", name)
        if not m:
            continue
        yield m.group(1), parts[1:], bold


def main():
    text = TEX.read_text(encoding="utf-8", errors="replace")
    out = {}

    for psr, cells, _bold in rows(text, 15):
        vals = [cell(c) for c in cells]
        rec = {k: v for k, v in zip(NOISE_COLS, vals)}
        out[psr] = dict(pub=rec, curn_sourced=False)

    ndet = 0
    for psr, cells, bold in rows(text, 9):
        vals = [cell(c) for c in cells]
        rec = {k: v for k, v in zip(DET_COLS, vals)}
        if psr not in out:
            print(f"WARNING: det-table pulsar {psr} not in noise table")
            continue
        out[psr]["pub"].update({k: v for k, v in rec.items() if v is not None})
        out[psr]["curn_sourced"] = bool(bold)
        ndet += 1

    # --- infer the favoured model per pulsar ---
    for psr, rec in out.items():
        p = rec["pub"]
        beta = p.get("chrom_beta")
        chrom = None
        if p.get("chrom_log10_A") is not None:
            chrom = "fixed4" if isinstance(beta, float) else "free"
        ne = p.get("n_earth")
        if p.get("sw_log10_A") is not None:
            sw = "full"
        elif isinstance(ne, tuple):
            sw = "det"
        else:
            sw = "fixed"                      # n_earth printed as bare 4
        rec["model"] = dict(
            equad=p.get("log10_tnequad") is not None,
            ecorr=p.get("log10_ecorr") is not None,
            dm=p.get("dm_log10_A") is not None,
            red=p.get("red_log10_A") is not None,
            chrom=chrom, sw=sw,
            bump=(int(p["bump_sign"]) if p.get("bump_sign") is not None
                  else None),
            annual=p.get("ann_log10_A") is not None,
        )
        # sampled-parameter count (= comparison-set size)
        n = 1                                  # EFAC
        n += int(rec["model"]["equad"]) + int(rec["model"]["ecorr"])
        n += 2 * (int(rec["model"]["red"]) + int(rec["model"]["dm"]))
        if chrom:
            n += 2 + (1 if chrom == "free" else 0)
        if sw == "full":
            n += 3                             # A_SW, gamma_SW, n_earth
        elif sw == "det":
            n += 1
        if rec["model"]["bump"] is not None:
            n += 4
        if rec["model"]["annual"]:
            n += 3
        n += 1                                 # A_13/3
        rec["n_sampled"] = n

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True))
    print(f"parsed {len(out)} noise rows, {ndet} deterministic rows -> {OUT}")

    # --- cross-check against M2's hand transcription ---
    sys.path.insert(0, str(Path(__file__).parent))
    import mpta_models as M
    bad = 0
    for psr in M.TOP10:
        for key, want in M.PUBLISHED[psr].items():
            got = out[psr]["pub"].get(key)
            if got is None or tuple(got) != tuple(want):
                print(f"  MISMATCH {psr}.{key}: parsed {got} vs M2 {want}")
                bad += 1
        mm, m2 = out[psr]["model"], M.MODELS[psr]
        for k in ("equad", "ecorr", "dm", "red", "chrom", "sw", "bump",
                  "annual"):
            if bool(mm[k]) != bool(m2[k]) or mm[k] != m2[k]:
                print(f"  MODEL MISMATCH {psr}.{k}: {mm[k]} vs {m2[k]}")
                bad += 1
    print(f"cross-check vs M2 hand transcription: "
          f"{'PASS (0 mismatches)' if bad == 0 else f'{bad} MISMATCHES'}")

    # inventory
    from collections import Counter
    c = Counter()
    for psr, rec in out.items():
        m = rec["model"]
        c["dm"] += m["dm"]; c["red"] += m["red"]
        c["chrom_fixed4"] += (m["chrom"] == "fixed4")
        c["chrom_free"] += (m["chrom"] == "free")
        c[f"sw_{m['sw']}"] += 1
        c["bump"] += m["bump"] is not None
        c["annual"] += m["annual"]
        c["equad"] += m["equad"]; c["ecorr"] += m["ecorr"]
    print("model inventory:", dict(sorted(c.items())))
    print("total sampled parameters across the array:",
          sum(r["n_sampled"] for r in out.values()))


if __name__ == "__main__":
    main()
