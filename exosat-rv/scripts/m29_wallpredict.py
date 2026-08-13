"""M29: test S = contrast / theta^2 against the systems held out of its construction.

M29 sec 7 found that neither contrast nor separation orders this project's extraction
outcomes, but their combination does: S = contrast / theta^2, the ratio of scattered host
flux to companion flux at the slit. It was built on six systems. Six points and two
classes separate under many statistics by chance, so the claim is worth nothing until it
predicts systems it was not built on.

This does that. It parses Lazzoni et al. 2022 Table 1 -- which carries Sep in mas, host
magnitude and companion magnitude for 37 companions, and which this project transcribed
only three columns of -- computes S for every system, and compares the prediction against
the extraction verdict this project reached independently.

The threshold is fixed in advance from the construction set: CLEAN below 4327, FAILS above
15202. Anything landing in between is recorded as INDETERMINATE rather than assigned to
whichever side would look better.

Known caveat carried through: Lazzoni's companion-magnitude column is apparent magnitude
(validated on YSES 1 b against Bohn+2020 to 0.14 mag) but is not uniformly reliable -- it
is wrong by 2.4 mag for beta Pic b against Currie+2013. Rows resting on it alone are
marked.

Usage: python scripts/m29_wallpredict.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LZ = ROOT / "papers" / "text" / "lazzoni2022_detectability.txt"

# Thresholds fixed from the six-system construction set (M29 sec 7), not tuned here.
CLEAN_MAX, FAILS_MIN = 4327.0, 15202.0

# Lazzoni's companion-magnitude column is not uniformly reliable. Where a primary source
# exists it overrides. beta Pic b: Currie+2013 Gemini/NICI Ks = 12.47 against host K 3.48,
# so 3954x -- not the 36983x Lazzoni's 14.9 implies.
CONTRAST_OVERRIDE = {"beta Pic b": (3954.0, "Currie+2013 Ks=12.47")}

# Systems used to BUILD S. Only the rest are a real test of it.
CONSTRUCTION = {"CD-35 2722 B", "eta Tel B", "beta Pic b", "PDS 70 b",
                "YSES 1 b", "HIP 81208 B"}

# This project's own extraction verdicts, from the milestone documents. None of these
# were derived from S; all predate it.
VERDICTS = {
    "CD-35 2722 B": ("CLEAN", "70-90 m/s, blind detection (M14)"),
    "eta Tel B":    ("CLEAN", "116-130 m/s, injection-gated null (M15)"),
    "beta Pic b":   ("FAILS", "km/s, r(BERV)=+0.88, contamination-limited (M20)"),
    "PDS 70 b":     ("FAILS", "star dominates at 0.17 arcsec (M20)"),
    # --- held out of the construction set ---
    "AB Pic b":     ("CLEAN", "120-190 m/s, gates pass (M17)"),
    "CT Cha b":     ("CLEAN", "180-310 m/s, screened series (M17/M23)"),
    "DH Tau B":     (None,    "no data reduced -- prediction only"),
    "GSC 6214-210 B": (None,  "no data reduced -- prediction only"),
    "51 Eri b":     ("FAILS", "3 of 11 orders respond (M23; HiRISE-provisional)"),
    "1RXS J160929.1-210524 b": (None, "no data reduced -- prediction only"),
}

# name (may contain digits and spaces), then 8 numeric fields, then the reference,
# which always begins with a capital letter. Non-greedy name + anchored ref lets rows
# like "51 Eri b" and "1RXS J160929.1-210524 b" parse.
NUM = r"([<>]?\s*[\d,]+\.?\d*)"
ROW = re.compile(r"^(?P<name>.+?)\s+" + r"\s+".join([NUM] * 8) +
                 r"\s+(?P<ref>[A-Z][A-Za-z].*)$")


def _f(x):
    try:
        return float(x.replace(",", "").replace(">", "").replace("<", "").strip())
    except ValueError:
        return None


def parse():
    txt = LZ.read_text(encoding="utf-8", errors="ignore")
    txt = "".join(ch for ch in txt if ch.isprintable() or ch == "\n")
    out = {}
    for line in txt.splitlines():
        m = ROW.match(line.strip())
        if not m:
            continue
        name = m.group("name").strip()
        g = [_f(m.group(i)) for i in range(2, 10)]
        if any(v is None for v in g):
            continue
        age, plx, host, comp, sep_mas, a_au, ms, mp = g
        # sanity: a separation in mas, a companion fainter than its host, a real parallax
        if not (0 < sep_mas < 60000) or comp <= host or not (0 < plx < 500):
            continue
        out[name] = dict(sep=sep_mas / 1000.0, host=host, comp=comp, age=age,
                         contrast=10 ** (0.4 * (comp - host)), ref=m.group("ref")[:34])
    return out


def main():
    rows = parse()
    print(f"# Lazzoni+2022 Table 1 parsed: {len(rows)} companions with Sep, host mag, "
          f"companion mag")
    print(f"# S = contrast / theta^2 ; thresholds fixed from the construction set: "
          f"CLEAN < {CLEAN_MAX:.0f}, FAILS > {FAILS_MIN:.0f}\n")
    print(f"{'system':<26s} {'sep(\")':>7s} {'contrast':>9s} {'S':>9s} "
          f"{'predicted':<14s} {'observed':<8s} {'role':<9s} {'verdict'}")

    hits = miss = indet = 0
    for name, v in sorted(rows.items(), key=lambda kv: kv[1]["contrast"] / kv[1]["sep"]**2):
        contrast, csrc = CONTRAST_OVERRIDE.get(name, (v["contrast"], "Lazzoni T1"))
        S = contrast / v["sep"] ** 2
        pred = ("CLEAN" if S < CLEAN_MAX else
                "FAILS" if S > FAILS_MIN else "INDETERMINATE")
        obs, note = VERDICTS.get(name, (None, ""))
        if obs is None:
            mark = "(no data)" if name in VERDICTS else ""
        elif pred == "INDETERMINATE":
            mark = "indeterminate"; indet += 1
        elif pred == obs:
            mark = "AGREES"; hits += 1
        else:
            mark = "*** DISAGREES ***"; miss += 1
        if obs is None and name not in VERDICTS:
            continue
        role = "built-on" if name in CONSTRUCTION else "HELD OUT"
        print(f"{name:<26s} {v['sep']:>7.3f} {contrast:>8.0f}x {S:>9.0f} "
              f"{pred:<14s} {str(obs or '-'):<8s} {role:<9s} {mark}")

    held = [n for n, v in rows.items()
            if n in VERDICTS and VERDICTS[n][0] and n not in CONSTRUCTION]
    print("")
    print("# systems with a verdict: %d agree, %d disagree, %d indeterminate"
          % (hits, miss, indet))
    print("# genuinely held out (not used to build S): %d -> %s" % (len(held), held))
    print("#")
    print("# HOW MUCH DOES THIS VALIDATE S? Honestly: very little.")
    print("#  1. Only two held-out systems carry a verdict, both CLEAN, and both sit")
    print("#     50-100x BELOW the CLEAN threshold of %.0f. Predicting clean for a"
          % CLEAN_MAX)
    print("#     target two orders below the boundary does not discriminate.")
    print("#  2. There is NO held-out FAILS case. The criterion has never been asked")
    print("#     to predict a failure it did not already know about.")
    print("#  3. beta Pic b at its SOURCED contrast lands essentially ON the threshold,")
    print("#     because the threshold was set by beta Pic b. With PDS 70 b at 15297")
    print("#     the failure side rests on two points 1 percent apart, one of which")
    print("#     may fail by a different mechanism (companion inside the AO core).")
    print("#")
    print("# S is CONSISTENT with every outcome measured here and is NOT YET TESTED")
    print("# BY THEM. The informative experiment needs a target with S between")
    print("#   %.0f and %.0f -- exactly where nothing has been observed."
          % (CLEAN_MAX, FAILS_MIN))
    print("\n# predictions for systems with no reduced data yet (falsifiable):")
    for name in ("DH Tau B", "GSC 6214-210 B", "1RXS J160929.1-210524 b"):
        if name in rows:
            v = rows[name]; S = v["contrast"] / v["sep"] ** 2
            pred = ("CLEAN" if S < CLEAN_MAX else
                    "FAILS" if S > FAILS_MIN else "INDETERMINATE")
            print(f"#   {name:<26s} S = {S:>8.0f}  ->  {pred}")
    print("\n# CAVEAT: Lazzoni's companion magnitudes are validated on YSES 1 b to 0.14")
    print("# mag but wrong by 2.4 mag on beta Pic b. Any row here resting on that column")
    print("# alone inherits that uncertainty.")


if __name__ == "__main__":
    main()
