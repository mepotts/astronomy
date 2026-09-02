#!/usr/bin/env python3
"""W1b acceptance (A1): load one MPTA pulsar with PINT, compare weighted RMS
against the tempo2 TRES recorded in the released par file, save a residual PNG.

MPTA pars are UNITS TCB; PINT converts to TDB on read (allow_tcb) -- part of
what this test measures. Writes a TDB-converted par for enterprise to use.

Usage (inside the WSL venv):
    python scripts/w1b_residuals.py J1909-3744 [--refit]
"""
import argparse
import re
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parent.parent
PARTIM = REPO / "data" / "partim"
OUTDIR = REPO / "figures"
TDBDIR = REPO / "data" / "partim_tdb"


def par_value(parfile: Path, key: str):
    for line in parfile.read_text().splitlines():
        toks = line.split()
        if toks and toks[0] == key:
            return toks[1:]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("psr")
    ap.add_argument("--refit", action="store_true",
                    help="WLS-refit free params after TCB->TDB conversion")
    args = ap.parse_args()

    par = PARTIM / f"{args.psr}.par"
    tim = PARTIM / f"{args.psr}.tim"
    if not par.exists():
        sys.exit(f"missing {par}")

    # Release quirk (12/83 pars): "TRACK -2" asks tempo2 to use tim-file
    # pulse numbers, but the released tims carry none -> PINT refuses to
    # form residuals. Strip the directive (A1 then measures whether the
    # PINT residuals still match the in-release TRES).
    text = par.read_text()
    if any(ln.split()[:1] == ["TRACK"] for ln in text.splitlines()):
        TDBDIR.mkdir(exist_ok=True)
        par = TDBDIR / f"{args.psr}.notrack.par"
        par.write_text("\n".join(
            ln for ln in text.splitlines()
            if ln.split()[:1] != ["TRACK"]) + "\n")
        print(f"stripped TRACK   : wrote {par.name}")

    tres_pub = float(par_value(par, "TRES")[0])          # us, tempo2's own fit
    chi2r_pub = float(par_value(par, "CHI2R")[0])
    ntoa_pub = int(par_value(par, "NTOA")[0])

    import pint.logging
    pint.logging.setup(level="WARNING")
    from pint.models import get_model_and_toas
    from pint.residuals import Residuals

    t0 = time.perf_counter()
    # allow_T2: tempo2 generic T2 binaries (J0437-4715) are auto-mapped to
    # the closest PINT model (DDK when KIN/KOM present); A1 gates fidelity.
    model, toas = get_model_and_toas(str(par), str(tim), allow_tcb=True,
                                     allow_T2=True, planets=True)
    t_load = time.perf_counter() - t0

    res = Residuals(toas, model)
    label = "PINT (TCB par auto-converted to TDB, no refit)"
    if args.refit:
        from pint.fitter import Fitter
        f = Fitter.auto(toas, model)
        f.fit_toas()
        model = f.model
        res = Residuals(toas, model)
        label = "PINT (TCB->TDB + WLS refit of free params)"

    wrms_us = res.rms_weighted().to_value("us")
    chi2r = res.reduced_chi2
    frac = (wrms_us - tres_pub) / tres_pub

    print(f"pulsar          : {args.psr}")
    print(f"n_toa           : {res.toas.ntoas} (par NTOA {ntoa_pub})")
    print(f"load time       : {t_load:.1f} s")
    print(f"weighted RMS    : {wrms_us:.4f} us   ({label})")
    print(f"par TRES        : {tres_pub:.4f} us  (tempo2, in-release)")
    print(f"fractional diff : {frac:+.2%}   (A1 tolerance 15%)")
    print(f"reduced chi2    : {chi2r:.3f} (par CHI2R {chi2r_pub})")
    verdict = "PASS" if abs(frac) <= 0.15 else "FAIL"
    print(f"A1 verdict      : {verdict}")

    # TDB par for enterprise/W2
    TDBDIR.mkdir(exist_ok=True)
    tdb_par = TDBDIR / f"{args.psr}.tdb.par"
    tdb_par.write_text(model.as_parfile())

    OUTDIR.mkdir(exist_ok=True)
    mjd = toas.get_mjds().value
    r_us = res.time_resids.to_value("us")
    err_us = toas.get_errors().to_value("us")
    fig, ax = plt.subplots(figsize=(9, 4.2), dpi=150)
    ax.errorbar(mjd, r_us, yerr=err_us, fmt=".", ms=2.5, lw=0.5, alpha=0.45,
                color="#20567C", ecolor="#8FB4CE", zorder=2)
    ax.axhline(0, color="0.35", lw=0.8, zorder=1)
    ax.set_xlabel("MJD")
    ax.set_ylabel("residual ($\\mu$s)")
    ax.set_title(f"{args.psr} - MPTA 4.5-yr sub-banded ToAs, {label}\n"
                 f"weighted RMS {wrms_us:.3f} $\\mu$s vs tempo2 TRES "
                 f"{tres_pub:.3f} $\\mu$s ({frac:+.1%}); "
                 f"n={res.toas.ntoas}")
    fig.tight_layout()
    out = OUTDIR / f"w1b_{args.psr}_residuals.png"
    fig.savefig(out)
    print(f"figure          : {out}")


if __name__ == "__main__":
    main()
