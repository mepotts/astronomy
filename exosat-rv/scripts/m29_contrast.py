"""M29: derive the contrast ratios the "contrast wall" is quoted along.

M20 sec 6 states the wall in contrast -- clean at ~2000x, flooded at ~5000x, gone at
~30000x -- and those figures propagate to docs/target-queue.md, the README and every
summary since. Nothing in this repository computes them. This does.

Contrast is a flux ratio at the observed band:

    contrast = 10 ** (0.4 * (m_companion - m_host))

Companion K magnitudes come from data/m7-survey.json (M7's screen). Host magnitudes are
queried live from SIMBAD, which is the only external call here. Where SIMBAD has no K for
the host, H is used and the substitution is reported rather than hidden.

Caveat carried into the output: several of these campaigns observed in H1567, not K, and
a companion's H-K colour differs from its host's -- so a K-band ratio is an approximation
to the contrast that actually applied at the slit. The band used is printed per row.

Usage: python scripts/m29_contrast.py
"""
import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
SIMBAD = "https://simbad.cds.unistra.fr/simbad/sim-tap/sync"

# companion -> host, for the systems the wall is stated on
HOSTS = {
    # keys MUST match data/m7-survey.json's own names exactly -- a mismatch drops the row
    # before SIMBAD is ever queried, which is why an earlier run resolved only six systems.
    "CD-35 2722 B":      "CD-35 2722",
    "beta Pic b":        "bet Pic",
    "PDS 70 b":          "PDS 70",
    "PDS 70 c":          "PDS 70",
    "HIP65426 b":        "HIP 65426",
    "eta Tel B":         "eta Tel",
    "HD1160 c":          "HD 1160",
    "AF Lep b":          "AF Lep",
    "51 Eri b":          "51 Eri",
    "HIP 81208 B":       "HIP 81208",
    "TYC 8998-760-1 b":  "TYC 8998-760-1",
    "TYC 8998-760-1 c":  "TYC 8998-760-1",
    "HD19467 B":         "HD 19467",
    "HD 206893 B":       "HD 206893",
    "AB Pic b":          "AB Pic",
    "CT Cha b":          "CT Cha",
    "PZ Tel B":          "PZ Tel",
}

# separations in arcsec as used by the wall (M20 sec 6, M23, M28 sec 5)
# Separations. Sourced from Lazzoni+2022 Table 1 (Sep, mas) wherever that table has the
# system -- the column this project never transcribed -- and from the discovery paper
# otherwise. Values previously carried without provenance are marked with their old value.
SEP_ARCSEC = {
    "CD-35 2722 B": 2.8,      # M0-RESULTS (2.8" at 22.36 pc = 62.6 au); H26 quote ~2.8"
    "beta Pic b":   0.511,    # Lazzoni T1: 510.8 mas   (was 0.55, unsourced)
    "PDS 70 b":     0.173,    # Lazzoni T1: 173.5 mas
    "PDS 70 c":     0.213,    # Lazzoni T1: 213.2 mas   (was 0.24, unsourced)
    "51 Eri b":     0.434,    # Lazzoni T1: 434.0 mas   (was 0.45, unsourced)
    "AB Pic b":     5.400,    # Lazzoni T1: 5400 mas    (was blank)
    "eta Tel B":    4.210,    # Lazzoni T1: 4210 mas
    "CT Cha b":     2.680,    # Lazzoni T1: 2680 mas    (was absent)
    "HIP 81208 B":  0.325,    # Viswanath+2023: 320.9 / 328.7 mas over two epochs
    "TYC 8998-760-1 b": 1.7,      # queue; not in Lazzoni T1 under this name -- UNSOURCED
    "HIP65426 b":   0.8,      # UNSOURCED
    "AF Lep b":     0.45,     # UNSOURCED
}


def simbad_mags(name):
    q = ("SELECT f.filter, f.flux FROM basic b JOIN ident i ON i.oidref = b.oid "
         "JOIN allfluxes f ON f.oidref = b.oid WHERE i.id = '%s'" % name.replace("'", "''"))
    try:
        r = requests.get(SIMBAD, params={"REQUEST": "doQuery", "LANG": "ADQL",
                                         "FORMAT": "json", "QUERY": q}, timeout=60)
        if r.status_code != 200:
            return {}
        return {str(a): float(b) for a, b in r.json()["data"] if b is not None}
    except Exception:
        return {}


def simbad_flux(name):
    """allfluxes is not uniformly available; fall back to the basic K/H columns."""
    for cols in (("K", "H"),):
        q = ("SELECT K, H FROM allfluxes JOIN ident USING(oidref) "
             "WHERE id = '%s'" % name.replace("'", "''"))
        try:
            r = requests.get(SIMBAD, params={"REQUEST": "doQuery", "LANG": "ADQL",
                                             "FORMAT": "json", "QUERY": q}, timeout=60)
            if r.status_code == 200 and r.json()["data"]:
                row = r.json()["data"][0]
                return {c: (float(v) if v is not None else None)
                        for c, v in zip(cols, row)}
        except Exception:
            pass
    return {}


# Lazzoni's companion column is apparent magnitude (validated on YSES 1 b against
# Bohn+2020 to 0.14 mag) but not uniformly reliable. Primary sources override it.
OVERRIDE = {
    "beta Pic b": (12.47, "Currie+2013 Gemini/NICI Ks (via Bonnefoy+2014)"),
}


def main():
    survey = json.loads((ROOT / "data" / "m7-survey.json").read_text(encoding="utf-8"))
    # exclude entries the survey itself flags as limits rather than measurements
    # (51 Eri b: "no measured K -- upper limit only, unrankable")
    comp, excluded = {}, {}
    for t in survey["targets"]:
        v = str(t.get("verdict", "")).lower()
        if "no measured k" in v or "upper limit only" in v:
            excluded[t["name"]] = t.get("verdict")
            continue
        comp[t["name"]] = t.get("k_mag")

    print("# M29: contrast ratios derived from magnitudes, not asserted")
    print("# contrast = 10^(0.4 * (m_companion - m_host)); companion K from "
          "data/m7-survey.json (M7)")
    print("# host magnitudes queried live from SIMBAD\n")
    print(f"{'companion':<16s} {'sep(\")':>7s} {'K_comp':>7s} {'host':<24s} "
          f"{'m_host':>7s} {'band':>5s} {'dmag':>6s} {'contrast':>11s}")
    rows = []
    for c, host in HOSTS.items():
        kc = comp.get(c)
        if kc is None:
            continue
        src = "Lazzoni T1"
        if c in OVERRIDE:
            kc, src = OVERRIDE[c]
        f = simbad_flux(host)
        mh, band = (f.get("K"), "K") if f.get("K") is not None else (f.get("H"), "H")
        sep = SEP_ARCSEC.get(c)
        if mh is None:
            print(f"{c:<16s} {sep if sep else '-':>7} {kc:>7.2f} {host:<24s} "
                  f"{'--':>7s} {'--':>5s} {'--':>6s} {'SIMBAD: no K/H':>11s}")
            continue
        d = kc - mh
        ratio = 10 ** (0.4 * d)
        rows.append((c, sep, ratio, band))
        print(f"{c:<16s} {str(sep) if sep else '-':>7s} {kc:>7.2f} {host:<24s} "
              f"{mh:>7.2f} {band:>5s} {d:>6.2f} {ratio:>10.0f}x"
              f"{'  <- ' + src if c in OVERRIDE else ''}")

    print("\n# the wall's quoted figures, against these derived values")
    for label, quoted, who in (("clean", 2000, ["HIP 65426 b", "CD-35 2722 B"]),
                               ("flooded", 5000, ["beta Pic b"]),
                               ("gone", 30000, ["AF Lep b", "51 Eri b"])):
        got = [(c, r) for c, s, r, b in rows if c in who]
        s = ", ".join(f"{c} = {r:.0f}x" for c, r in got) or "none derived"
        print(f"#   {label:<8s} quoted ~{quoted:>6d}x  |  derived: {s}")
    print("\n# NOTE: several of these campaigns observed in H1567, not K. A K-band")
    print("# ratio approximates the contrast that applied at the slit; the companion's")
    print("# H-K colour differs from its host's. Band actually used is printed above.")


if __name__ == "__main__":
    main()
