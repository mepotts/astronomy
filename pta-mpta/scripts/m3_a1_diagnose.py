#!/usr/bin/env python3
"""M3: diagnose the A1 outliers — which released pars fail to reproduce their
own in-release tempo2 TRES under PINT, and what distinguishes them."""
import glob
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PARTIM = REPO / "data" / "partim"


def par_keys(psr):
    keys = {}
    for line in (PARTIM / f"{psr}.par").read_text().splitlines():
        t = line.split()
        if t:
            keys.setdefault(t[0], []).append(t[1:])
    return keys


def main():
    recs = {}
    for f in glob.glob(str(REPO / "results/m3/a1/*.json")):
        r = json.loads(Path(f).read_text())
        recs[r["psr"]] = r
    fails = sorted([p for p, r in recs.items()
                    if r.get("ok") and r["a1"] != "PASS"],
                   key=lambda p: -abs(recs[p]["frac"]))
    passes = [p for p, r in recs.items() if r.get("ok") and r["a1"] == "PASS"]
    print(f"{len(fails)} FAIL / {len(passes)} PASS")
    interesting = ["TRACK", "BINARY", "DMMODEL", "FD1", "FD2", "DM1", "DM2",
                   "DM3", "JUMP", "PLANET_SHAPIRO", "NE_SW", "PX", "PB",
                   "EPHVER", "T2CMETHOD", "SOLARN0", "DMEPOCH", "GLEP_1",
                   "DMX_0001", "SINI", "M2", "KIN", "KOM", "SHAPMAX"]
    print(f"\n{'psr':13s} {'frac':>9s} {'chi2r':>8s}/{'pub':<8s} flags")
    for p in fails + sorted(passes)[:0]:
        k = par_keys(p)
        r = recs[p]
        flags = [x for x in interesting if x in k]
        print(f"{p:13s} {r['frac']:+8.2%} {r['chi2r']:8.2f}/"
              f"{r['chi2r_pub']:<8.2f} {' '.join(flags)}")
    # what fraction of PASSes carry each flag, vs FAILs
    from collections import Counter
    cf, cp = Counter(), Counter()
    for p in fails:
        for x in par_keys(p):
            cf[x] += 1
    for p in passes:
        for x in par_keys(p):
            cp[x] += 1
    print("\nflag        FAIL/{n_f}  PASS/{n_p}".format(n_f=len(fails),
                                                        n_p=len(passes)))
    for x in sorted(set(cf) | set(cp)):
        if cf[x] / max(len(fails), 1) - cp[x] / max(len(passes), 1) > 0.25 \
                or cp[x] / max(len(passes), 1) - cf[x] / max(len(fails), 1) > 0.25:
            print(f"  {x:12s} {cf[x]:3d}       {cp[x]:3d}")
    # chi2r comparison
    print("\nchi2r(ours)/chi2r(par) for FAILs vs the array:")
    import numpy as np
    rf = [recs[p]["chi2r"] / recs[p]["chi2r_pub"] for p in fails]
    rp = [recs[p]["chi2r"] / recs[p]["chi2r_pub"] for p in passes]
    print(f"  FAIL  median {np.median(rf):.2f}  range "
          f"{min(rf):.2f}-{max(rf):.2f}")
    print(f"  PASS  median {np.median(rp):.2f}  range "
          f"{min(rp):.2f}-{max(rp):.2f}")


if __name__ == "__main__":
    main()
