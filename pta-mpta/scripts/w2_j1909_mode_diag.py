#!/usr/bin/env python3
"""Post-run diagnostic for the J1909-3744 chromatic-block disagreement:
evaluate our likelihood at the PUBLISHED MAP vs the best point our short
chain found. If lnL(published) > lnL(chain best), the chain simply had not
found the global mode within the A3 budget (under-sampling); if the chain's
SW-dominated point beats the published one under our likelihood, that is a
genuine model-difference finding. Diagnosis only -- the pre-registered
verdict is unchanged."""
import json
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from w2_noise_run import build_pta, REPO

# our param order (alphabetical, = pta.param_names):
# dm_gp_gamma, dm_gp_log10_A, efac, gw13_log10_A, log10_ecorr,
# log10_tnequad, sw_gp_gamma, sw_gp_log10_A, n_earth
X_PUB = np.array([2.04, -13.60, 1.04, -14.28, -7.17, -7.17, 1.39, -6.43, 4.96])

pta = build_pta("J1909-3744")
assert [p.split("_", 1)[1] if p.startswith("J1909") else p
        for p in pta.param_names] == \
    ["dm_gp_gamma", "dm_gp_log10_A", "efac", "gw13_log10_A", "log10_ecorr",
     "log10_tnequad", "sw_gp_gamma", "sw_gp_log10_A", "n_earth"], \
    pta.param_names

chain = np.loadtxt(REPO / "chains" / "J1909-3744" / "chain_1.txt")
ndim = 9
lnlike_col = chain[:, ndim + 1]
i_best = int(np.argmax(lnlike_col))
x_best = chain[i_best, :ndim]

ll_pub = pta.get_lnlikelihood(X_PUB)
ll_best_recomp = pta.get_lnlikelihood(x_best)

print(f"lnL(published MAP)      = {ll_pub:.2f}")
print(f"lnL(chain best, stored) = {lnlike_col[i_best]:.2f}")
print(f"lnL(chain best, recomp) = {ll_best_recomp:.2f}")
print(f"Delta lnL (pub - chain) = {ll_pub - ll_best_recomp:+.2f}")
print("chain best point:", dict(zip(pta.param_names, np.round(x_best, 3))))
out = dict(lnL_published=float(ll_pub), lnL_chain_best=float(ll_best_recomp),
           delta=float(ll_pub - ll_best_recomp),
           chain_best={k: float(v) for k, v in zip(pta.param_names, x_best)})
(REPO / "results" / "w2_J1909_mode_diag.json").write_text(
    json.dumps(out, indent=2))
