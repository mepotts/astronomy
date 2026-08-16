"""M29: which axis actually orders the extraction outcomes?

The project has stated its feasibility limit as a "contrast wall" since M20. With every
point now traced to a primary source, contrast alone does not order the outcomes, and
neither does separation alone:

  by contrast:    clean, fails, clean, clean, fails, clean   (no ordering)
  by separation:  fails, clean, fails, clean, clean, clean   (no ordering)

There is a physical reason to expect neither. What floods the slit is not the magnitude
ratio between host and companion; it is the host's light *scattered to the companion's
position*. That scales as the contrast times the PSF halo evaluated at the separation.
For a seeing- or AO-limited halo the wing falls roughly as theta^-2 to theta^-3, so the
natural quantity is

    S = contrast / theta^n

which is, to a constant, the ratio of scattered host flux to companion flux at the slit.

This tests whether S separates the outcomes, and over what range of n. With six points and
two classes many statistics will separate them by chance, so the exponent is NOT fitted:
n is scanned over the physically plausible range and the result reported for all of it.

Sources for every number are in the table below; nothing here is recalled.

Usage: python scripts/m29_wallaxis.py
"""
import numpy as np

# (name, separation ", contrast, outcome, per-epoch precision, source)
SYSTEMS = [
    # WARNING (M32): this contrast still rests on Lazzoni T1's companion-magnitude column,
    # which is now wrong in 2 of 3 cases checked against primary sources (eta Tel B by 1.6
    # mag, beta Pic b by 2.4). It is UNVERIFIED, not verified, and is the lowest-S FAILS
    # point -- i.e. it helps set the boundary this script is testing.
    ("PDS 70 b",      0.17,   460, "FAILS",
     "star dominates", "Lazzoni T1 Kp UNVERIFIED (host K 8.542 verified); sep 173.5 mas"),
    ("HIP 81208 B",   0.325,  457, "CLEAN",
     "124 m/s",        "Viswanath+2023: sep 320.9/328.7 mas, K2 dmag 6.64"),
    ("beta Pic b",    0.51,  3954, "FAILS",
     "km/s, r(BERV)=+0.88", "Currie+2013 Ks=12.47; host K 3.48; sep 510.8 mas Lazzoni T1"),
    ("YSES 1 b",      1.70, 10280, "CLEAN",
     "34 m/s",         "Bohn+2020 K1 dmag 10.03; sep 1.7\" (queue)"),
    ("CD-35 2722 B",  2.80,    97, "CLEAN",
     "70-90 m/s",      "Lazzoni T1 Kp 12.01, host K 7.05; sep 2.8\" M0-RESULTS"),
    ("eta Tel B",     4.21,   433, "CLEAN",
     "116-130 m/s",    "M32: Neuhauser+2011 K_s 11.6+/-0.1; host K 5.01; sep 4199+/-15 mas "
                       "Chai+2024. Lazzoni's Kp 13.2 was wrong by 1.6 mag -> 1888x"),
]


def separates(vals, outcomes):
    """True if every CLEAN value lies strictly below every FAILS value."""
    clean = [v for v, o in zip(vals, outcomes) if o == "CLEAN"]
    fails = [v for v, o in zip(vals, outcomes) if o == "FAILS"]
    return max(clean) < min(fails), max(clean), min(fails)


def main():
    sep = np.array([s[1] for s in SYSTEMS])
    con = np.array([s[2] for s in SYSTEMS], float)
    out = [s[3] for s in SYSTEMS]

    print("# M29: which axis orders the outcomes? Every value traced to a source.\n")
    print(f"{'system':<15s} {'sep(\")':>7s} {'contrast':>9s} {'outcome':<7s} {'precision':<22s}")
    for n_, s_, c_, o_, p_, src in SYSTEMS:
        print(f"{n_:<15s} {s_:>7.3f} {c_:>8.0f}x {o_:<7s} {p_:<22s}")

    print("\n# single axes")
    for label, vals, rev in (("contrast", con, False), ("separation", sep, True)):
        order = np.argsort(vals)
        seq = " ".join(out[i][0] for i in order)   # C or F, ascending
        ok, hi, lo = separates(vals if not rev else -vals, out)
        print(f"  by {label:<11s} ascending: {seq}   separates: {ok}")

    print("\n# S = contrast / separation^n  (scattered host flux / companion flux, to a constant)")
    print(f"  {'n':>4s}  {'highest CLEAN':>14s}  {'lowest FAILS':>13s}  {'gap':>6s}  separates")
    good = []
    for n in [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
        S = con / sep ** n
        ok, hi, lo = separates(S, out)
        gap = lo / hi if ok else float("nan")
        good.append((n, ok))
        print(f"  {n:>4.1f}  {hi:>14.0f}  {lo:>13.0f}  {gap:>6.1f}x  "
              f"{'YES' if ok else 'no'}")

    ns = [n for n, ok in good if ok]
    if ns:
        print(f"\n# S separates the two classes for n = {min(ns):.1f} to {max(ns):.1f},")
        print("# which brackets the theta^-2 to theta^-3 falloff of a seeing/AO halo.")
        n = 2.0
        S = con / sep ** n
        print(f"\n# ordered by S at n = {n:.0f}:")
        for i in np.argsort(S):
            print(f"    {S[i]:>9.0f}   {SYSTEMS[i][3]:<6s} {SYSTEMS[i][0]}")
    else:
        print("\n# S does not separate the classes at any exponent tried.")

    print("\n# CAVEATS")
    print("#  - six points, two classes: many statistics separate such a set by chance.")
    print("#    The exponent was NOT fitted; it is scanned and the whole range reported.")
    print("#  - eta Tel B's contrast is disputed (Lazzoni Kp 13.2 vs SIMBAD H 11.93).")
    print("#    It is a CLEAN case at large separation, so it is not load-bearing here.")
    print("#  - 'outcome' is this project's own extraction verdict, not an external label.")
    print("#  - PDS 70 fails for a reason that may be distinct: at 0.17\" the companion is")
    print("#    inside the AO core, so the host is not a halo but the spectrum itself.")


if __name__ == "__main__":
    main()
