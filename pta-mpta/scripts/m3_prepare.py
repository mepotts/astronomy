#!/usr/bin/env python3
"""M3 preparation: A1 (stack acceptance) + TDB par for one MPTA pulsar.

Same machinery as scripts/w1b_residuals.py but headless (no figure) and
JSON-emitting, so the all-83 campaign can run it 32-way in parallel.

Writes:
  data/partim_tdb/<psr>.tdb.par        (enterprise input)
  data/partim_tdb/<psr>.notrack.par    (only when the par carries TRACK)
  results/m3/a1/<psr>.json             (A1 record)

Usage (inside the WSL venv):
    python scripts/m3_prepare.py J1909-3744
"""
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PARTIM = REPO / "data" / "partim"
TDBDIR = REPO / "data" / "partim_tdb"
OUT = REPO / "results" / "m3" / "a1"


def par_value(parfile: Path, key: str):
    for line in parfile.read_text().splitlines():
        toks = line.split()
        if toks and toks[0] == key:
            return toks[1:]
    return None


def main():
    psr = sys.argv[1]
    # A1 fallback (pre-registered, M3 doc 1.2): pars whose PINT residuals miss
    # the in-release TRES by >15% as loaded get ONE WLS refit of their own
    # released free parameters; A1 is then re-tested on the refit model and
    # the refit par is what the campaign samples. `--zero-h3` additionally
    # zeroes an unphysical negative orthometric Shapiro amplitude (only
    # J1825-0319, whose released H3 < 0 makes PINT's DDH refuse to build).
    refit = "--refit" in sys.argv
    zero_h3 = "--zero-h3" in sys.argv
    OUT.mkdir(parents=True, exist_ok=True)
    TDBDIR.mkdir(parents=True, exist_ok=True)
    par = PARTIM / f"{psr}.par"
    tim = PARTIM / f"{psr}.tim"
    rec = dict(psr=psr, ok=False)
    try:
        text = par.read_text()
        # release quirk (12/83): TRACK -2 wants tim pulse numbers that the
        # released tims do not carry -> PINT refuses residuals. Strip it
        # (measured inert for the shipped data, M2 doc 2.1 item 4).
        if any(ln.split()[:1] == ["TRACK"] for ln in text.splitlines()):
            par = TDBDIR / f"{psr}.notrack.par"
            par.write_text("\n".join(
                ln for ln in text.splitlines()
                if ln.split()[:1] != ["TRACK"]) + "\n")
            rec["track_stripped"] = True

        rec["tres_pub"] = float(par_value(par, "TRES")[0])
        rec["chi2r_pub"] = float(par_value(par, "CHI2R")[0])
        rec["ntoa_pub"] = int(par_value(par, "NTOA")[0])
        rec["binary"] = (par_value(par, "BINARY") or ["NONE"])[0]

        import pint.logging
        pint.logging.setup(level="ERROR")
        from pint.models import get_model_and_toas
        from pint.residuals import Residuals

        if zero_h3:
            # J1825-0319 only: the released par carries H3 = -2.98e-7 s, an
            # UNPHYSICAL negative orthometric Shapiro amplitude (it implies
            # M2 = H3/STIG^3 < 0, which PINT's DDH refuses to build; a refit
            # from it lands negative again, so the data genuinely pull that
            # way). We drop the Shapiro term (H3 = STIG = 0, held fixed) and
            # let the WLS refit re-absorb it; the delay is <= |H3| = 0.3 us
            # against a 4.6 us TRES and is inside the timing-model design
            # matrix either way.
            src = par.read_text().splitlines()
            keep = []
            for ln in src:
                k = ln.split()[:1]
                if k in (["H3"], ["STIG"], ["H4"]):
                    continue
                if k == ["BINARY"]:
                    ln = "BINARY         DD"
                keep.append(ln)
            par = TDBDIR / f"{psr}.h3zero.par"
            par.write_text("\n".join(keep) + "\n")
            rec["h3_zeroed"] = True

        t0 = time.perf_counter()
        model, toas = get_model_and_toas(str(par), str(tim), allow_tcb=True,
                                         allow_T2=True, planets=True)
        rec["load_s"] = round(time.perf_counter() - t0, 1)
        if refit:
            from pint.fitter import Fitter
            res0 = Residuals(toas, model)
            rec["wrms_us_asloaded"] = float(
                res0.rms_weighted().to_value("us"))
            before = {p: getattr(model, p).value
                      for p in model.free_params}
            errs = {p: getattr(model, p).uncertainty_value
                    for p in model.free_params}
            f = Fitter.auto(toas, model)
            f.fit_toas(maxiter=5)
            model = f.model
            rec["refit"] = True
            shifts = {}
            for p, v0 in before.items():
                v1 = getattr(model, p).value
                try:
                    d = float(v1) - float(v0)
                except (TypeError, ValueError):
                    continue
                e = errs.get(p) or 0.0
                shifts[p] = [float(d),
                             (float(d / e) if e else None)]
            rec["refit_shifts"] = dict(sorted(
                shifts.items(),
                key=lambda kv: -(abs(kv[1][1]) if kv[1][1] else 0))[:8])
        res = Residuals(toas, model)
        rec["ntoa"] = int(res.toas.ntoas)
        rec["wrms_us"] = float(res.rms_weighted().to_value("us"))
        rec["chi2r"] = float(res.reduced_chi2)
        rec["frac"] = (rec["wrms_us"] - rec["tres_pub"]) / rec["tres_pub"]
        rec["a1"] = "PASS" if abs(rec["frac"]) <= 0.15 else "FAIL"
        mjd = toas.get_mjds().value
        rec["tmin_mjd"] = float(mjd.min())
        rec["tmax_mjd"] = float(mjd.max())
        rec["tspan_days"] = float(mjd.max() - mjd.min())
        (TDBDIR / f"{psr}.tdb.par").write_text(model.as_parfile())
        rec["ok"] = True
    except Exception as e:
        import traceback
        rec["error"] = traceback.format_exc()[-2000:]
        rec["a1"] = "ERROR"
        print(f"{psr}: ERROR {e}", file=sys.stderr)
    (OUT / f"{psr}.json").write_text(json.dumps(rec, indent=2))
    print(f"{psr}: {rec.get('a1')} frac={rec.get('frac')} "
          f"ntoa={rec.get('ntoa')}")


if __name__ == "__main__":
    main()
