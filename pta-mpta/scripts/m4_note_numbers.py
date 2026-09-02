#!/usr/bin/env python3
"""M4 N2: re-derive EVERY number in the table-audit note from the committed
artifacts, independently of M3's prose and independently of M3's parser.

Pre-registration: pta-mpta/M4-finish-the-array.md section 1.5 (N2).

The note's four claims are properties of a published table.  A note that
asserts them has to be able to show where each digit came from, so this script
does three things:

  1. RE-PARSES the two longtables straight out of the arXiv LaTeX source
     (data/paper/mnras_template.tex) with code written fresh for this purpose,
     sharing nothing with scripts/m3_parse_tables.py;
  2. CROSS-CHECKS that independent parse against the M3 artifact
     (results/m3/published_table.json) value by value -- a second, independent
     acceptance on top of M3's own hand-transcription check;
  3. RECOMPUTES every claim and prints an AUDIT TABLE: claim, value,
     the artifact + field it came from, and PASS / CORRECTED against the
     number M3 wrote in prose.

Outputs results/m4/note_numbers.json and prints the audit table as markdown.

    python scripts/m4_note_numbers.py
"""
import json
import re
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TEX = REPO / "data" / "paper" / "mnras_template.tex"
M3TAB = REPO / "results" / "m3" / "published_table.json"
OUT = REPO / "results" / "m4" / "note_numbers.json"

FLOOR = -16.5   # the paper's OWN "clearly disfavoured" point (its section on
                # the Savage-Dickey ratio: p(log10 A_CURN,FL < -16.5))

NOISE_COLS = ["efac", "log10_tnequad", "log10_ecorr",
              "red_log10_A", "red_gamma", "dm_log10_A", "dm_gamma",
              "chrom_log10_A", "chrom_gamma", "chrom_beta",
              "sw_log10_A", "sw_gamma", "gw13_log10_A", "n_earth"]
DET_COLS = ["bump_log10_A", "bump_beta", "bump_t0", "bump_sigma",
            "bump_sign", "ann_log10_A", "ann_beta", "ann_phase"]

# M3's prose numbers, transcribed here so the audit is a real comparison and
# not a re-print.  Source: M3-noise-criticism.md sections 4, 5.
M3_CLAIMS = {
    "n_values": 588,
    "n_noise_rows": 83,
    "n_det_rows": 23,
    "n_map_outside": 26,
    "n_pulsars_map_outside": 22,
    "n_zero_edge": 4,
    "outside_gw13": 13,
    "outside_equad": 5,
    "outside_annA": 2,
    "outside_ecorr": 2,
    "outside_dmA": 2,
    "n_swfull": 26,
    "n_sw_gamma_negative": 7,
    "n_sw_gamma_ci_crossing": 12,
    "n_sw_affected": 19,
    "n_sw_below_ee_default": 2,
    "n_a13_prior_limited": 66,
    "n_a13_two_sided": 17,
    "n_a13_better_than_0p7": 6,
    "a13_median_width_prior_limited": 3.01,
    "a13_max_width": 4.01,
}

VAL = re.compile(
    r"\$\{(-?[\d.]+)\}_\{([-+]?[\d.]+)\}\^\{([-+]?[\d.]+)\}\$")


def _psrname(cell):
    r"""Pulsar name cell -> JHHMM+DDMM. Handles $-$/$+$ and the \textbf{}
    the deterministic table uses to mark its two CURN-sourced rows."""
    c = cell.strip()
    c = re.sub(r"\\textbf\{(.*?)\}", r"\1", c)
    c = re.sub(r"\\mathbf\{(.*?)\}", r"\1", c)
    c = c.replace("$-$", "-").replace("$+$", "+").replace("$", "")
    c = c.replace("\\,", "").replace("~", "").strip()
    return c


def parse_cell(cell):
    """-> ('none',), ('fixed', v), or ('val', map, lo_off, hi_off)."""
    c = cell.strip()
    if c in ("-", "--", "---", ""):
        return ("none",)
    m = VAL.match(c)
    if m:
        return ("val", float(m.group(1)), float(m.group(2)),
                float(m.group(3)))
    if re.fullmatch(r"-?[\d.]+", c):
        return ("fixed", float(c))
    return ("other", c)


def rows_of(tex, label):
    """Data rows of the longtable carrying \\label{label}."""
    i = tex.index("\\label{" + label + "}")
    j = tex.index("\\endhead", i)
    k = tex.index("\\end{longtable}", j)
    body = tex[j:k]
    out = []
    for line in body.split("\n"):
        line = line.strip()
        # the deterministic table bolds the two rows whose values are taken
        # from the CURN analysis, so a bare startswith("J") silently drops
        # them (caught by the M3 cross-check: 580 vs 588 values)
        if not (line.startswith("J") or line.startswith("\\textbf{J")):
            continue
        line = line.rstrip("\\").rstrip()
        while line.endswith("\\"):
            line = line[:-1].rstrip()
        cells = [c.strip() for c in line.split("&")]
        out.append(cells)
    return out


def main():
    tex = TEX.read_text(encoding="utf-8", errors="replace")
    audit = []          # (claim, value, source, m3_value, verdict)
    res = {}

    def rec(key, label, value, source):
        res[key] = value
        m3 = M3_CLAIMS.get(key)
        if m3 is None:
            verdict = "new"
        elif isinstance(value, float) and isinstance(m3, (int, float)):
            verdict = "PASS" if abs(value - m3) < 0.005 else "CORRECTED"
        else:
            verdict = "PASS" if value == m3 else "CORRECTED"
        audit.append((label, value, source, m3, verdict))

    # ---------- 1. independent parse -------------------------------------
    noise = {}
    for cells in rows_of(tex, "Table: MPTA noise models"):
        psr = _psrname(cells[0])
        assert len(cells) == 15, (psr, len(cells))
        noise[psr] = {k: parse_cell(c)
                      for k, c in zip(NOISE_COLS, cells[1:])}
    det = {}
    for cells in rows_of(tex, "Table: MPTA determinstic models"):
        psr = _psrname(cells[0])
        assert len(cells) == 9, (psr, len(cells))
        det[psr] = {k: parse_cell(c) for k, c in zip(DET_COLS, cells[1:])}

    rec("n_noise_rows", "noise-table rows (independent parse of the "
        "arXiv LaTeX)", len(noise), "data/paper/mnras_template.tex")
    rec("n_det_rows", "deterministic-table rows", len(det),
        "data/paper/mnras_template.tex")

    # every ${x}_{-a}^{+b} cell across both tables = one sampled value
    vals = [(p, k, v) for p, r in noise.items() for k, v in r.items()
            if v[0] == "val"]
    vals += [(p, k, v) for p, r in det.items() for k, v in r.items()
             if v[0] == "val"]
    rec("n_values", "tabulated parameter values with a printed interval",
        len(vals), "independent parse, both longtables")

    # ---------- 2. cross-check vs the M3 artifact ------------------------
    m3tab = json.loads(M3TAB.read_text())
    mism, checked = [], 0
    for psr, row in noise.items():
        pub = m3tab.get(psr, {}).get("pub", {})
        for k, v in row.items():
            if v[0] != "val":
                continue
            checked += 1
            got = pub.get(k)
            if not (isinstance(got, list) and len(got) == 3
                    and abs(got[0] - v[1]) < 1e-9
                    and abs(got[1] - v[2]) < 1e-9
                    and abs(got[2] - v[3]) < 1e-9):
                mism.append((psr, k, v[1:], got))
    res["crosscheck_noise_values"] = checked
    res["crosscheck_mismatches"] = mism
    audit.append(("independent parse vs results/m3/published_table.json",
                  f"{checked} noise values, {len(mism)} mismatches",
                  "cross-check", "0 mismatches (M3 P1)",
                  "PASS" if not mism else "CORRECTED"))

    # ---------- 3. claim (c): MAP outside its own printed interval -------
    outside, zero_edge = [], []
    per_key = Counter()
    for psr, k, v in vals:
        _, m, lo, hi = v
        if lo > 0 or hi < 0:
            outside.append(dict(psr=psr, key=k, map=m, lo=lo, hi=hi,
                                side="low" if lo > 0 else "high"))
            per_key[k] += 1
        elif lo == 0 or hi == 0:
            zero_edge.append(dict(psr=psr, key=k, map=m, lo=lo, hi=hi))
    rec("n_map_outside", "values whose MAP lies outside their own printed "
        "68% interval", len(outside), "independent parse (strict inequality)")
    rec("n_pulsars_map_outside", "pulsars affected",
        len({o['psr'] for o in outside}), "independent parse")
    rec("n_zero_edge", "further values printing an offset of exactly 0.00 on "
        "one side (rounding; excluded)", len(zero_edge),
        "independent parse")
    rec("outside_gw13", "  of which log10 A_13/3", per_key["gw13_log10_A"],
        "independent parse")
    rec("outside_equad", "  of which E_Q", per_key["log10_tnequad"],
        "independent parse")
    rec("outside_ecorr", "  of which E_C", per_key["log10_ecorr"],
        "independent parse")
    rec("outside_dmA", "  of which log10 A_DM", per_key["dm_log10_A"],
        "independent parse")
    rec("outside_annA", "  of which log10 A_s (annual)",
        per_key["ann_log10_A"], "independent parse")
    res["outside"] = outside
    res["outside_by_key"] = dict(per_key)
    tot_by_key = Counter(k for _, k, _ in vals)
    res["totals_by_key"] = dict(tot_by_key)
    # the pathology's shape: is it confined to amplitudes?
    amp_keys = {k for k in tot_by_key if "log10_A" in k or k.startswith(
        "log10_") or k == "efac"}
    nonamp = sorted({k for k in per_key
                     if "log10" not in k and k != "efac"})
    res["nonamplitude_columns_hit"] = nonamp
    audit.append(("non-amplitude columns affected", ", ".join(nonamp) or "none",
                  "independent parse",
                  "phase (annual) only", "PASS" if nonamp == ["ann_phase"]
                  else "CORRECTED"))
    res["pct_map_outside"] = round(100 * len(outside) / len(vals), 2)

    # ---------- 4. claim (b): gamma_SW ------------------------------------
    swf = [p for p, r in noise.items() if r["sw_gamma"][0] == "val"]
    rec("n_swfull", "pulsars with a sampled gamma_SW (the SW_Full class)",
        len(swf), "independent parse")
    neg = [(p, noise[p]["sw_gamma"][1]) for p in swf
           if noise[p]["sw_gamma"][1] < 0]
    rec("n_sw_gamma_negative", "of those, published gamma_SW NEGATIVE "
        "(unreachable under gamma in [0,7])", len(neg), "independent parse")
    cross = [(p, noise[p]["sw_gamma"][1] + noise[p]["sw_gamma"][2])
             for p in swf
             if noise[p]["sw_gamma"][1] >= 0
             and noise[p]["sw_gamma"][1] + noise[p]["sw_gamma"][2] < 0]
    rec("n_sw_gamma_ci_crossing", "further pulsars whose gamma_SW 68% "
        "interval crosses zero", len(cross), "independent parse")
    rec("n_sw_affected", "gamma_SW value or interval outside [0,7]",
        len(neg) + len(cross), "independent parse")
    below = [(p, g) for p, g in neg if g < -2.0]
    rec("n_sw_below_ee_default", "published gamma_SW below the "
        "enterprise_extensions default floor of -2", len(below),
        "independent parse + e_e source")
    res["sw_negative"] = sorted(neg)
    res["sw_ci_crossing"] = sorted(cross)
    res["sw_below_ee_default"] = sorted(below)
    lowest_edge = min(noise[p]["sw_gamma"][1] + noise[p]["sw_gamma"][2]
                      for p in swf)
    res["sw_gamma_lowest_ci_edge"] = lowest_edge
    # -3.14 is what the M4 PRE-REGISTRATION (section 1.3, V3) asserted, taken
    # from M3 prose rather than re-derived; corrected in M4 section 1.7.
    audit.append(("lowest printed gamma_SW 68% lower edge", lowest_edge,
                  "independent parse", "-3.14 (M4 pre-reg 1.3)",
                  "PASS" if abs(lowest_edge + 3.14) < 0.005 else "CORRECTED"))
    res["sw_gamma_lowest_ci_edge_psr"] = min(
        swf, key=lambda p: noise[p]["sw_gamma"][1] + noise[p]["sw_gamma"][2])

    # ---------- 5. claim (d): A_13/3 prior-bounded ------------------------
    a13 = {p: r["gw13_log10_A"] for p, r in noise.items()
           if r["gw13_log10_A"][0] == "val"}
    lim, two = [], []
    for p, (_, m, lo, hi) in a13.items():
        (lim if m + lo < FLOOR else two).append(
            dict(psr=p, map=m, lo=m + lo, hi=m + hi, width=hi - lo))
    rec("n_a13_prior_limited", "A_13/3 rows whose 68% interval reaches below "
        f"{FLOOR} (prior-bounded)", len(lim), "independent parse")
    rec("n_a13_two_sided", "A_13/3 rows bounded on both sides", len(two),
        "independent parse")
    good = sorted([r for r in two if r["width"] < 0.7],
                  key=lambda r: r["width"])
    rec("n_a13_better_than_0p7", "A_13/3 rows constrained better than "
        "0.7 dex", len(good), "independent parse")
    ws = sorted(r["width"] for r in lim)
    med_w = ws[len(ws) // 2]
    rec("a13_median_width_prior_limited",
        "median 68% width of the prior-bounded A_13/3 rows (dex)",
        round(med_w, 2), "independent parse")
    rec("a13_max_width", "widest A_13/3 68% interval (dex)",
        round(max(r["width"] for r in lim + two), 2),
        "independent parse")
    res["a13_best"] = good
    res["a13_two_sided"] = sorted(two, key=lambda r: r["width"])
    res["a13_prior_limited"] = sorted(r["psr"] for r in lim)

    # ---------- 6. claim (a): are any prior RANGES stated? ----------------
    # search the whole source for a prior range expressed numerically
    prior_lines = [ln.strip() for ln in tex.split("\n")
                   if re.search(r"\bprior", ln, re.I)]
    ranged = [ln for ln in prior_lines
              if re.search(r"(uniform|log.?uniform|\\mathcal\{U\}|U\s*\(|"
                           r"\[\s*-?\d+\s*,\s*-?\d+\s*\])", ln, re.I)]
    res["n_prior_mentions"] = len(prior_lines)
    res["prior_range_lines"] = ranged
    audit.append(("lines in the LaTeX source mentioning 'prior'",
                  len(prior_lines), "regex over mnras_template.tex",
                  "prose only", "n/a"))
    audit.append(("of those, stating a numeric prior RANGE", len(ranged),
                  "regex over mnras_template.tex", 0,
                  "PASS" if len(ranged) == 0 else "CORRECTED"))

    # ---------- 7. the enterprise_extensions default, from source --------
    ee = None
    for cand in REPO.glob(".venv/lib/python*/site-packages/"
                          "enterprise_extensions/chromatic/solar_wind.py"):
        ee = cand
    if ee is not None:
        txt = ee.read_text(errors="replace")
        m = re.search(r"gamma_(?:sw|gp)?\s*=\s*parameter\.Uniform"
                      r"\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\)", txt)
        if m is None:
            m = re.search(r"Uniform\(\s*(-2(?:\.0)?)\s*,\s*(1(?:\.0)?)\s*\)",
                          txt)
        if m:
            res["ee_sw_gamma_default"] = [float(m.group(1)),
                                          float(m.group(2))]
            ln = txt[:m.start()].count("\n") + 1
            res["ee_sw_gamma_source"] = (
                "enterprise_extensions/chromatic/solar_wind.py:%d" % ln)
            audit.append(("enterprise_extensions solar_wind_block gamma "
                          "default", f"U({m.group(1)},{m.group(2)})",
                          res["ee_sw_gamma_source"], "U(-2,1)",
                          "PASS" if [float(m.group(1)), float(m.group(2))]
                          == [-2.0, 1.0] else "CORRECTED"))

    # ---------- 8. J1825-0319's negative Shapiro amplitude ---------------
    par = REPO / "data" / "partim" / "J1825-0319.par"
    if par.exists():
        h3 = sig = binm = None
        for ln in par.read_text(errors="replace").split("\n"):
            f = ln.split()
            if not f:
                continue
            if f[0] == "H3":
                h3 = float(f[1])
            elif f[0] in ("STIG", "VARSIGMA"):
                sig = float(f[1])
            elif f[0] == "BINARY":
                binm = f[1]
        res["j1825_H3"] = h3
        res["j1825_stig"] = sig
        res["j1825_binary"] = binm
        audit.append(("J1825-0319 released ephemeris H3 (s)", h3,
                      "data/partim/J1825-0319.par", -2.98e-7,
                      "PASS" if h3 is not None and abs(h3 + 2.98e-7)
                      < 1e-9 else "CORRECTED"))
        if h3 is not None and sig:
            res["j1825_M2_implied"] = h3 / (sig ** 3) / 4.925490947e-6
            audit.append(("J1825-0319 implied companion mass (Msun)",
                          round(res["j1825_M2_implied"], 3),
                          "H3/stig^3 / T_sun", -0.448,
                          "PASS" if abs(res["j1825_M2_implied"] + 0.448)
                          < 0.01 else "CORRECTED"))

    # ---------- print the audit table ------------------------------------
    print("| # | claim | re-derived value | source | M3 prose | verdict |")
    print("|---|---|---|---|---|---|")
    for i, (label, value, source, m3, verdict) in enumerate(audit, 1):
        print(f"| {i} | {label} | {value} | `{source}` | {m3} | {verdict} |")
    bad = [a for a in audit if a[4] == "CORRECTED"]
    print(f"\n{len(audit)} audited, {len(bad)} CORRECTED")
    for a in bad:
        print(f"  CORRECTED: {a[0]}: M3 said {a[3]}, re-derivation gives "
              f"{a[1]}")

    res["audit"] = [dict(claim=a[0], value=a[1], source=a[2], m3=a[3],
                         verdict=a[4]) for a in audit]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1, default=str))
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
