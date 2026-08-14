"""M32: regenerate every number in the eta Tel B research note from the stored JSONs.

The project's own audit (docs/PROPERTY-AUDIT.md) found 34 conflicting and 63 unsourced
values, almost all of them introduced by hand-transcription between a result and a
document. A note that goes outside the repo cannot carry that risk, so nothing in the
draft is typed: every figure is printed here from data/m15-limit.json and recomputed
from first principles, and the draft quotes this script's output.

Two things this makes explicit that prose would hide:

1. K90 is READ OFF THE MEASURED DETECTION GRID -- the smallest injected amplitude whose
   detected fraction reaches 0.90 -- not interpolated and not fitted. Where the grid does
   not reach 0.90 the entry is reported as a lower bound, not silently rounded down.

2. The msini limit scales as (host mass)^(2/3), and the adopted 47 M_Jup is single-source
   (Lazzoni+2022 Table 1, itself citing Langlois et al. 2021b, which this repo does not
   hold). So the headline number inherits an unverified input. The sensitivity table below
   states exactly how much the limit moves if that mass is wrong, so a reader with a better
   mass can rescale without re-running anything.

Usage: python scripts/m32_etatel_numbers.py
"""
import json
from pathlib import Path

G = 6.674e-11
M_JUP = 1.898e27          # kg
DAY = 86400.0

ROOT = Path(__file__).resolve().parents[1]
LIMIT = ROOT / "data" / "m15-limit.json"

# The literature mass of eta Tel B, run down to primary sources (M32). The repo carried
# "47 M_Jup, Lazzoni T1 -> Langlois+2021b, not archived" -- the attribution was wrong and
# the value has company:
#   Lazzoni et al. 2020, A&A 641, A131  47 (+5/-6)   AMES-COND evolutionary models
#   Chai et al. 2024, ApJ               29 (+16/-13) MIRI MRS atmospheric fit
#   Chai et al. 2024, ApJ               42 (+/-14)   orbital posterior, "largely
#                                                    prior-driven" (prior 35 +/- 15)
#   Neuhauser et al. 2011, MNRAS 416    20-50        bolometric luminosity
# The two INDEPENDENT determinations are Lazzoni's 47 and Chai's 29. Both are quoted.
M_HOST_ADOPTED = 47.0     # kept as the adopted value so the published limit is reproducible
DETECT_FRAC = 0.90


def msini(K, P_days, M_host_mjup):
    """Companion msini in M_Jup from a circular-orbit semi-amplitude.

    m sini = K (P/2 pi G)^(1/3) (M + m)^(2/3), solved by iteration on m. Checked below
    against Hoy et al.'s own K1 = 306 m/s, P = 171.45 d, M = 37 M_Jup -> 0.918 M_Jup.
    """
    P = P_days * DAY
    M = M_host_mjup * M_JUP
    m = 0.0
    for _ in range(50):
        m = K * (P / (2 * 3.141592653589793 * G)) ** (1 / 3) * (M + m) ** (2 / 3)
    return m / M_JUP


def k90(fracs, Ks):
    """Smallest gridded K whose detected fraction reaches DETECT_FRAC; None if never."""
    for K in Ks:
        if fracs[str(K)] >= DETECT_FRAC:
            return K
    return None


def main():
    d = json.loads(LIMIT.read_text())
    Ks = d["Ks"]

    print("# formula check against the source paper's own numbers")
    chk = msini(306.0, 171.45, 37.0)
    print(f"#   Hoy et al. K1=306 m/s, P=171.45 d, M=37 MJup -> msini = {chk:.3f} MJup")
    print(f"#   the paper states 0.918 MJup   ->  agrees to {abs(chk-0.918)/0.918*100:.1f}%\n")

    print(f"# eta Tel B sensitivity, host mass {M_HOST_ADOPTED:.0f} MJup, "
          f"{int(DETECT_FRAC*100)}% detection")
    print(f"{'P (d)':>7s} {'K90 (m/s)':>10s} {'msini (MJup)':>13s}   detected fraction "
          f"at that K")
    rows = []
    for P in d["periods"]:
        fr = d["detfrac"][str(P)]
        K = k90(fr, Ks)
        if K is None:
            print(f"{P:>7.0f} {'>'+str(Ks[-1]):>10s} {'-':>13s}   never reaches 0.90 on "
                  f"this grid")
            continue
        m = msini(float(K), P, M_HOST_ADOPTED)
        rows.append((P, K, m))
        print(f"{P:>7.0f} {K:>10d} {m:>13.2f}   {fr[str(K)]:.2f}")

    lo, hi = min(r[2] for r in rows), max(r[2] for r in rows)
    print(f"\n# headline: msini >= {lo:.1f}-{hi:.1f} MJup excluded over "
          f"P = {min(r[0] for r in rows):.0f}-{max(r[0] for r in rows):.0f} d\n")

    print("# HOW MUCH DOES THE UNVERIFIED HOST MASS MATTER? msini scales as M^(2/3).")
    print(f"{'M (MJup)':>9s} {'source / meaning':<34s} {'msini range (MJup)':>20s} "
          f"{'shift':>7s}")
    for M, why in ((29.0, "Chai+2024 MIRI atmospheric fit"),
                   (42.0, "Chai+2024 orbital (prior-driven)"),
                   (M_HOST_ADOPTED, "ADOPTED: Lazzoni+2020 AMES-COND")):
        vals = [msini(float(K), P, M) for P, K, _ in rows]
        f = (M / M_HOST_ADOPTED) ** (2 / 3)
        print(f"{M:>9.0f} {why:<34s} {min(vals):>9.2f}-{max(vals):<10.2f} "
              f"{f:>6.2f}x")
    print("")
    print("# The two independent determinations, 29 and 47 MJup, span a 27% shift in the")
    print("# limit -- and it shifts DOWNWARD from the adopted value, so quoting the 47 is the")
    print("# conservative choice. The exclusion stays sub-Jupiter to Jupiter-mass across")
    print("# the whole range: the qualitative claim survives the disagreement.")

    print("\n# a twin of the CD-35 2722 B satellite (msini 0.918 MJup) at this host mass.")
    print("# The required K falls between grid points, so the detected fraction is quoted")
    print("# as the bracket the measurement supports, not an interpolation across it.")
    for P, K, m in rows:
        need = 0.918 / m * K
        fr = d["detfrac"][str(P)]
        below = [k for k in Ks if k <= need]
        above = [k for k in Ks if k >= need]
        lo = fr[str(max(below))] if below else 0.0
        hi = fr[str(min(above))] if above else 1.0
        br = f"{max(below) if below else 0}-{min(above) if above else 'off-grid'}"
        print(f"#   at P = {P:>3.0f} d it would show K ~ {need:>3.0f} m/s -> detected in "
              f"{lo*100:>3.0f}-{hi*100:<3.0f}% of trials (bracketing K = {br} m/s)")



if __name__ == "__main__":
    main()
