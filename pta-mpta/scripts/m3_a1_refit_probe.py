#!/usr/bin/env python3
"""M3 probe: is the A1 failure of 8 released pars a *parameter-value*
mismatch (a WLS refit recovers TRES -> absorbed by enterprise's analytic
timing-model marginalisation) or a *functional-form* mismatch (it does not)?

For one pulsar, report weighted RMS:
  (a) as loaded (TCB par auto-converted to TDB by PINT, no refit)
  (b) after a WLS refit of the free parameters
  (c) as loaded but with the orthometric Shapiro amplitude H3 zeroed
      (isolates the Shapiro term)
  (d) after a refit with H3/STIGMA frozen at the released values
"""
import json
import sys
from pathlib import Path

import numpy as np
import copy as _copy
import pint.logging

pint.logging.setup(level="ERROR")
from pint.models import get_model_and_toas  # noqa: E402
from pint.residuals import Residuals  # noqa: E402
from pint.fitter import Fitter  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "results" / "m3" / "a1_refit"


def wrms(toas, model):
    return float(Residuals(toas, model).rms_weighted().to_value("us"))


def main():
    psr = sys.argv[1]
    OUT.mkdir(parents=True, exist_ok=True)
    parp = REPO / "data" / "partim" / f"{psr}.par"
    text = parp.read_text()
    if any(ln.split()[:1] == ["TRACK"] for ln in text.splitlines()):
        parp = REPO / "data" / "partim_tdb" / f"{psr}.notrack.par"
    tim = REPO / "data" / "partim" / f"{psr}.tim"
    tres = float([l.split()[1] for l in parp.read_text().splitlines()
                  if l.split()[:1] == ["TRES"]][0])

    model, toas = get_model_and_toas(str(parp), str(tim), allow_tcb=True,
                                     allow_T2=True, planets=True)
    rec = dict(psr=psr, tres_pub=tres, wrms_load=wrms(toas, model))
    rec["h3"] = (float(model.H3.value) if "H3" in model.params
                 and model.H3.value is not None else None)
    rec["stigma"] = (float(model.STIGMA.value) if "STIGMA" in model.params
                     and model.STIGMA.value is not None else None)
    rec["binary"] = getattr(model, "BINARY", None) and str(model.BINARY.value)

    try:
        f = Fitter.auto(toas, _copy.deepcopy(model))
        f.fit_toas(maxiter=5)
        rec["wrms_refit"] = wrms(toas, f.model)
    except Exception as e:
        rec["wrms_refit"] = None
        rec["refit_error"] = repr(e)[:300]

    if rec["h3"]:
        m2 = _copy.deepcopy(model)
        m2.H3.value = 0.0
        m2.H3.frozen = True
        if "STIGMA" in m2.params and m2.STIGMA.value is not None:
            m2.STIGMA.frozen = True
        rec["wrms_noshapiro"] = wrms(toas, m2)
        try:
            m3 = _copy.deepcopy(model)
            m3.H3.frozen = True
            if "STIGMA" in m3.params and m3.STIGMA.value is not None:
                m3.STIGMA.frozen = True
            f3 = Fitter.auto(toas, m3)
            f3.fit_toas(maxiter=5)
            rec["wrms_refit_frozen_shapiro"] = wrms(toas, f3.model)
            rec["h3_refit"] = (float(f.model.H3.value)
                               if rec.get("wrms_refit") else None)
            rec["stigma_refit"] = (float(f.model.STIGMA.value)
                                   if rec.get("wrms_refit")
                                   and f.model.STIGMA.value is not None
                                   else None)
        except Exception as e:
            rec["frozen_error"] = repr(e)[:300]

    (OUT / f"{psr}.json").write_text(json.dumps(rec, indent=1))
    print(json.dumps(rec, indent=1))


if __name__ == "__main__":
    main()
