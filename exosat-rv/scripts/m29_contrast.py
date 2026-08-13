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
    "CD-35 2722 B": "CD-35 2722",
    "beta Pic b": "bet Pic",
    "PDS 70 b": "PDS 70",
    "PDS 70 c": "PDS 70",
    "HIP 65426 b": "HIP 65426",
    "eta Tel B": "eta Tel",
    "HD 1160 B": "HD 1160",
    "AF Lep b": "AF Lep",
    "51 Eri b": "51 Eri",
    "HIP 81208 B": "HIP 81208",
    "YSES 1 b": "TYC 8998-760-1",
    "HD 19467 B": "HD 19467",
    "HD 206893 B": "HD 206893",
    "AB Pic b": "AB Pic",
    "CT Cha B": "CT Cha",
    "2M0103AB b": "2MASS J01033563-5515561",
}

# separations in arcsec as used by the wall (M20 sec 6, M23, M28 sec 5)
SEP_ARCSEC = {
    "CD-35 2722 B": 2.8, "beta Pic b": 0.55, "PDS 70 b": 0.17, "PDS 70 c": 0.24,
    "HIP 65426 b": 0.8, "eta Tel B": 4.2, "AF Lep b": 0.45, "51 Eri b": 0.45,
    "HIP 81208 B": 0.3, "YSES 1 b": 1.7,
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
              f"{mh:>7.2f} {band:>5s} {d:>6.2f} {ratio:>10.0f}x")

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
