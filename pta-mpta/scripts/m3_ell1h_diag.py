#!/usr/bin/env python3
"""M3 diagnostic: how PINT reads the ELL1H orthometric Shapiro parameters
(H3 + STIG) of the A1-failing MPTA pars."""
import sys

import pint.logging

pint.logging.setup(level="ERROR")
from pint.models import get_model  # noqa: E402

psr = sys.argv[1]
m = get_model(f"data/partim/{psr}.par", allow_tcb=True, allow_T2=True)
print("components:", [c for c in m.components
                      if "Binary" in c or "ELL1" in c or "DD" in c])
print("shapiro-ish params:",
      [p for p in m.params
       if any(k in p for k in ("H3", "H4", "STIG", "SIGMA", "NHARM",
                               "SINI", "M2"))])
for p in ("H3", "H4", "STIGMA", "STIG", "NHARMS", "SINI", "M2", "VARSIGMA"):
    if p in m.params:
        v = getattr(m, p)
        print(f"  {p} = {v.value}  frozen={v.frozen}")
