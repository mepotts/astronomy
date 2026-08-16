"""M32: re-test the contrast axis using MEASURED contrasts, in one band, from one instrument.

The wall note's contrast axis (M29 sec 7, `m29_wallaxis.py`) has a provenance problem that
M32 sec 3 made explicit: its magnitudes come from Lazzoni et al. 2022 Table 1's compiled
companion-magnitude column, which has been checked against primary sources three times and is
wrong twice -- by 1.6 mag for eta Tel B and 2.4 mag for beta Pic b. That is a factor 4-9 in
contrast against a boundary interval only a factor 3.5 wide.

Lazzoni et al. 2020 (A&A 641, A131) -- the satellite-search paper that is also this project's
source for eta Tel B's mass, and which went unread here until M32 -- carries something better
in its Table 2: **contrasts MEASURED from SPHERE observations**, with the matching separation
at the same epoch, for 27 companions. Same instrument, same band, same reduction, one paper.
That is the primary-source photometry the wall note's pre-submission item 0 asks for.

This script re-runs the class test on that column alone. It is deliberately NOT a merge with
the K-band roster: mixing bands is how the contrast axis went wrong in the first place, and a
companion is redder than its host, so an H-band contrast is systematically larger than a
K-band one for the same pair. Every number below comes from one table.

Coverage is the limitation and is reported rather than worked around. Of the six systems in
the wall's own roster, three appear in Lazzoni 2020 (eta Tel B, beta Pic b, PDS 70 b); CD-35
2722 B, HIP 81208 B and YSES 1 b do not, so this cannot replace the K-band test, only check
whether its ordering survives an independent, better-sourced measurement of the same quantity.

Usage: python scripts/m32_wall_measured.py
"""

# Lazzoni et al. 2020, A&A 641, A131, Table 2. Contrast measured from SPHERE observations
# (their caption: "Projected distance and contrast values were obtained from the observations
# presented in the previous Table"); separation at the same epoch. Verdicts are this
# project's own extraction outcomes and predate any of this.
#
# (name, separation ", contrast ratio (companion/host), this project's verdict)
MEASURED = [
    ("eta Tel B",  4.21, 1.5e-3, "CLEAN",
     "116-130 m/s, injection-gated null (M15)"),
    ("beta Pic b", 0.33, 1.0e-4, "FAILS",
     "km/s, r(BERV)=+0.88, and blended at R=0.54 (M29)"),
    ("PDS 70 b",   0.19, 5.5e-4, "FAILS",
     "star dominates at <0.2 arcsec (M20)"),
]

# Systems in Lazzoni 2020 Table 2 with no extraction verdict here -- reported as predictions,
# not as evidence, exactly as m29_wallpredict.py does for the 2022 table.
UNJUDGED = [
    ("DH Tau B", 2.35, 4.1e-3), ("CT Cha B", 2.68, 1.7e-3),
    ("AB Pic B", 5.40, 6.4e-4), ("HD1160 C", 5.15, 4.4e-3),
    ("HIP78530 B", 4.18, 7.1e-4), ("GQ Lup B", 0.70, 3.1e-3),
    ("HD4747 B", 0.59, 6.5e-4), ("HIP65426 b", 0.83, 3.4e-5),
    ("51 Eri b", 0.45, 5.8e-6), ("HR8799 b", 1.72, 2.8e-5),
]

N = 2.0   # the exponent fixed in M29 from halo physics, not fitted here either


def S(sep, contrast_ratio):
    """Scattered host flux over companion flux at the slit, to a constant."""
    return (1.0 / contrast_ratio) / sep ** N


def main():
    print("# M32: the contrast axis re-tested on MEASURED SPHERE contrasts")
    print("# source: Lazzoni et al. 2020, A&A 641, A131, Table 2 -- one instrument, one")
    print(f"# band, one paper. S = contrast / theta^{N:.0f}, exponent carried over from M29.\n")

    print(f"{'system':<13s} {'sep(\")':>7s} {'contrast':>11s} {'S':>10s}  verdict   note")
    rows = []
    for name, sep, c, verdict, note in MEASURED:
        s = S(sep, c)
        rows.append((name, s, verdict))
        print(f"{name:<13s} {sep:>7.2f} {1.0/c:>10.0f}x {s:>10.0f}  {verdict:<8s}  {note}")

    clean = [s for _, s, v in rows if v == "CLEAN"]
    fails = [s for _, s, v in rows if v != "CLEAN"]
    print("")
    if clean and fails:
        hi_clean, lo_fail = max(clean), min(fails)
        sep_ok = hi_clean < lo_fail
        print(f"# highest CLEAN S = {hi_clean:,.0f} ; lowest FAILS S = {lo_fail:,.0f}")
        print(f"# separates: {sep_ok}   gap = {lo_fail / hi_clean:,.0f}x")
        print("")
        if sep_ok:
            print("# The ordering SURVIVES an independent, better-sourced measurement of the")
            print("# same quantity, and the margin is far wider than on the compiled column")
            print("# (a factor 3.5 there). Both failure cases sit three orders of magnitude")
            print("# above the clean one.")
    print("")
    print("# WHAT THIS DOES AND DOES NOT ESTABLISH")
    print("#  - It is THREE points. Three points in two classes separate by chance easily,")
    print("#    and no threshold should be read off them.")
    print("#  - It is an independent CHECK on the K-band test, not a replacement: three of")
    print("#    the wall's six systems are absent from this table (CD-35 2722 B, HIP 81208 B,")
    print("#    YSES 1 b), so the full roster cannot be rebuilt in this band.")
    print("#  - PDS 70 b matters most here. On the compiled column it sat at S = 15,917 --")
    print("#    the lowest failure and thus the point defining the boundary -- from an")
    print("#    UNVERIFIED magnitude. Measured, it is far deeper into the failing regime,")
    print("#    so the boundary was if anything drawn too tight, not too loose.")
    print("#  - PDS 70 b may still fail by a different mechanism: at <0.2 arcsec the")
    print("#    companion is inside the AO core, where the host is not a halo but the")
    print("#    spectrum itself. That caveat is unchanged by better photometry.")

    print("\n# predictions for measured systems with no extraction verdict here")
    print("# (falsifiable, and stated before any of these are reduced):")
    for name, sep, c in sorted(UNJUDGED, key=lambda r: S(r[1], r[2])):
        s = S(sep, c)
        call = "clean" if s < max(clean) * 3 else ("fails" if s > min(fails) / 3 else "--")
        print(f"#   {name:<12s} sep {sep:>4.2f}\"  S = {s:>9,.0f}  -> {call}")
    print("#   ('--' means it lands between the two classes, where this project has never")
    print("#    observed anything and makes no call.)")


if __name__ == "__main__":
    main()
