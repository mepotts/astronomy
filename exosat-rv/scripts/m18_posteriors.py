"""M18: posterior samples on the published Nature RV table, for the H26 figure-match set.

`nested_orbits.py` (M14) answers the evidence question and keeps only logZ and posterior
means. The figure-by-figure comparison against H26 needs the posteriors themselves:

  H26 Fig. 5  period posterior for the *second* signal, wide prior, then windowed at each
              peak -> the `two_wideP2` and `win*` runs here.
  H26 Fig. 6  the high-evidence 2-satellite models drawn as RV curves -> `win*` samples.
  H26 Fig. 8  corner plot for the large satellite -> `sat1_ecc`.
  H26 Fig. 9  corner plot for the small satellite -> `sat2_win88`.

Model, likelihood and priors are imported from `nested_orbits.py` unchanged, so the
evidence numbers printed here are directly comparable with M14's table. The only additions
are (a) equal-weight resampled posteriors written to .npz and (b) wide / walked priors on
P2, which M14 had no reason to run.

Derived masses use a host mass calibrated so that H26's own (P, K, e) reproduce H26's own
m sin i -- see `calibrate_host_mass`. That keeps our mass axis on their scale rather than
importing a mass from the discovery paper and silently comparing two different scales.

Usage: python scripts/m18_posteriors.py [--nlive 800] [--out data/m18-posteriors.npz]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import nested_orbits as no_  # noqa: E402
from exosat_rv.analysis.orbits import load_published  # noqa: E402

G = 6.674e-11
M_JUP = 1.89813e27
AU = 1.495978707e11
DAY = 86400.0

# H26, Nature Table 1 (published version; supersedes arXiv v1 -- M12 SS1).
H26 = {
    "P1_1sat": 171.112, "e1_1sat": 0.269, "K1_1sat": 318.5, "msini1_1sat": 0.918,
    "P1_2sat": 171.454, "K1_2sat": 306.0, "e1_2sat": 0.001, "msini1_2sat": 0.918,
    "P2": 87.349, "e2": 0.008, "msini2": 0.219,
    "logz1": -144.323, "logz1_err": 0.695, "logz2": -141.701, "logz2_err": 0.691,
    "dlogz": 2.622,
    # arXiv v1 values, for the "which version are you looking at" note
    "v1_P1": 169.45, "v1_msini1": 0.743, "v1_P2": 87.46, "v1_msini2": 0.277,
    "v1_dlogz": 6.641,
}
# The four peaks H26's Fig. 5 panel 1 shows for the second signal.
H26_FIG5_PEAKS = [14.0, 70.0, 88.0, 115.0]


def msini_jup(P_d, K, e, m_host_kg):
    """m sin i in M_Jup for a companion of mass << host, from the mass function."""
    P = np.asarray(P_d, float) * DAY
    return (np.asarray(K, float) * np.sqrt(1 - np.asarray(e, float) ** 2)
            * m_host_kg ** (2 / 3) * (P / (2 * np.pi * G)) ** (1 / 3)) / M_JUP


def semimajor_au(P_d, m_host_kg):
    P = np.asarray(P_d, float) * DAY
    return (G * m_host_kg * P**2 / (4 * np.pi**2)) ** (1 / 3) / AU


def calibrate_host_mass():
    """Host mass reproducing H26's own m sin i from H26's own (P, K, e).

    H26 quote m sin i = 0.918 M_Jup for the 2-satellite fit's P = 171.454 d,
    K = 306.0 m/s, e = 0.001. Wahhaj et al. (2011) give 31 +- 8 M_Jup for the host brown
    dwarf; solving instead for the mass implied by the paper's own numbers keeps our
    derived masses on the paper's scale. m sin i ~ M^(2/3), so the update below is exact
    in one step and iterated only to kill round-off.
    """
    m = 31.0 * M_JUP
    for _ in range(40):
        got = msini_jup(H26["P1_2sat"], H26["K1_2sat"], H26["e1_2sat"], m)
        m *= (H26["msini1_2sat"] / got) ** 1.5
    return m


@contextmanager
def period_window(index, lo, hi):
    """Temporarily replace one of nested_orbits' windowed period priors."""
    saved = list(no_.P_WINDOWS)
    win = list(saved)
    win[index] = (lo, hi)
    no_.P_WINDOWS = win
    try:
        yield
    finally:
        no_.P_WINDOWS = saved


def run(spec, nlive, seed, nsamp=4000):
    """Nested sampling, returning equal-weight posterior samples alongside logZ."""
    import dynesty

    ndim, ptf, lnl, labels = no_.make_model(*spec)
    t0 = time.time()
    sam = dynesty.NestedSampler(lnl, ptf, ndim, nlive=nlive,
                                rstate=np.random.default_rng(seed), sample="rwalk")
    sam.run_nested(dlogz=0.01, print_progress=False)
    res = sam.results
    logwt = res.logwt - res.logz[-1]
    w = np.exp(logwt - logwt.max())
    w /= w.sum()
    idx = np.random.default_rng(seed + 7).choice(len(w), size=nsamp, p=w)
    return dict(samples=res.samples[idx], labels=labels, logz=float(res.logz[-1]),
                logzerr=float(res.logzerr[-1]), secs=round(time.time() - t0, 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nlive", type=int, default=800)
    ap.add_argument("--out", default=str(ROOT / "data" / "m18-posteriors.npz"))
    ap.add_argument("--summary", default=str(ROOT / "data" / "m18-posteriors.json"))
    args = ap.parse_args()

    data = load_published(version="nature")
    no_.TT = data.bjd - data.bjd.min()
    no_.RV, no_.ERV = data.rv, data.erv
    print(f"Nature table: n={len(data.rv)}, baseline {no_.TT.max():.1f} d", flush=True)

    m_host = calibrate_host_mass()
    print(f"host mass calibrated to H26's own m sin i: {m_host / M_JUP:.1f} M_Jup "
          f"(Wahhaj+11 quote 31 +- 8)", flush=True)

    store = {}
    summary = {"host_mass_mjup": m_host / M_JUP, "t_ref": float(data.bjd.min()),
               "nlive": args.nlive, "h26": H26, "fig5_peaks": H26_FIG5_PEAKS, "runs": {}}

    def record(name, r, note):
        store[f"{name}__samples"] = r["samples"]
        store[f"{name}__labels"] = np.array(r["labels"], dtype=object)
        summary["runs"][name] = {"logz": r["logz"], "logzerr": r["logzerr"],
                                 "labels": r["labels"], "secs": r["secs"], "note": note}
        print(f"[{name}] logZ = {r['logz']:.3f} +- {r['logzerr']:.3f}  "
              f"({r['secs']}s, ndim={r['samples'].shape[1]})", flush=True)

    # H26 Fig. 8 -- the large satellite, from the 1-satellite eccentric fit.
    record("sat1_ecc", run((None, 1, True), args.nlive, 1000),
           "1-satellite eccentric, P ~ U(150,200); H26 Fig. 8 counterpart")

    # H26 Fig. 9 -- the small satellite, 2-satellite fit with P2 in H26's own window.
    record("sat2_win88", run((None, 2, True), args.nlive, 2000),
           "2-satellite eccentric, P1 ~ U(150,200), P2 ~ U(75,100); H26 Fig. 9")

    # H26 Fig. 5 panel 1 -- second-signal period posterior under a wide prior.
    with period_window(1, 5.0, 150.0):
        record("two_wideP2", run((None, 2, False), args.nlive, 3000),
               "2-satellite circular, P2 ~ U(5,150); H26 Fig. 5 panel 1")

    # H26 Fig. 5 panels 2-5 and Fig. 6 -- windowed fits at each of their four peaks.
    for pk in H26_FIG5_PEAKS:
        lo, hi = pk * 0.85, pk * 1.15
        with period_window(1, lo, hi):
            record(f"win{pk:g}", run((None, 2, False), args.nlive, 4000 + int(pk)),
                   f"2-satellite circular, P2 ~ U({lo:.1f},{hi:.1f}) "
                   f"around H26 peak {pk:g} d")

    # The one-satellite baseline the windowed models are scored against, same priors.
    base = summary["runs"]["sat1_ecc"]["logz"]
    for pk in H26_FIG5_PEAKS:
        r = summary["runs"][f"win{pk:g}"]
        r["dlogz_vs_1sat"] = round(r["logz"] - base, 3)
        print(f"  window {pk:g} d: dlogZ(2-sat - 1-sat) = {r['dlogz_vs_1sat']:+.3f}",
              flush=True)

    np.savez_compressed(args.out, **store)
    Path(args.summary).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"wrote {args.out} and {args.summary}", flush=True)


if __name__ == "__main__":
    main()
