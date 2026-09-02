#!/usr/bin/env python3
"""M3 section 6.4: the DECLARED POST-HOC supplementary check on the solar-wind
GP spectral-index prior.

Seven tabulated gamma_SW values are negative and therefore unreachable under
the pre-registered gamma ~ U(0,7). This compares, per pulsar, the registered
run (tag n1, gamma_SW ~ U(0,7)) with a supplementary run (tag swp, gamma_SW ~
U(-4,4)) against the published values. It is reported separately and does not
enter any registered statistic.
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RES = REPO / "results" / "m3"
TAB = json.loads((RES / "published_table.json").read_text())
KEYS = ("sw_gp_gamma", "sw_gp_log10_A", "n_earth", "gw13_log10_A")


def load(psr, tag):
    f = RES / f"{psr}_noise_{tag}.summary.json"
    if not f.exists():
        return None
    s = json.loads(f.read_text())
    return dict(gate=bool(s.get("gate_met")),
                raw=(s.get("chain") or {}).get("raw_postburn"),
                acc=(s.get("chain") or {}).get("acc_rate"),
                agree=s.get("n_agree"), comp=s.get("n_compared"),
                params={r["param"].replace(f"{psr}_", ""): r
                        for r in (s.get("chain") or {}).get("params", [])},
                a2={r["param"].replace(f"{psr}_", ""): r
                    for r in s.get("a2", [])})


def main():
    psrs = sys.argv[1:] or ["J1327-0755", "J1730-2304"]
    out = {}
    for psr in psrs:
        a, b = load(psr, "n1"), load(psr, "swp")
        if not a or not b:
            print(f"{psr}: missing run(s)")
            continue
        print(f"\n{psr}: registered n1 gate={a['gate']} raw={a['raw']} "
              f"agree {a['agree']}/{a['comp']}  |  supplementary swp "
              f"gate={b['gate']} raw={b['raw']}")
        rec = {}
        for k in KEYS:
            if k not in a["params"]:
                continue
            pk = {"sw_gp_gamma": "sw_gamma", "sw_gp_log10_A": "sw_log10_A",
                  "n_earth": "n_earth",
                  "gw13_log10_A": "gw13_log10_A"}[k]
            pub = TAB[psr]["pub"].get(pk)
            pubs = (f"{pub[0]:+.2f} [{pub[0]+pub[1]:+.2f},{pub[0]+pub[2]:+.2f}]"
                    if isinstance(pub, list) else "-")
            ra, rb = a["params"][k], b["params"].get(k)
            ag_a = a["a2"].get(k, {}).get("agree")
            ag_b = b["a2"].get(k, {}).get("agree")
            print(f"  {k:16s} pub {pubs:26s} "
                  f"n1 {ra['median']:+7.2f} [{ra['ci68'][0]:+.2f},"
                  f"{ra['ci68'][1]:+.2f}] {str(ag_a):5s} | "
                  f"swp {rb['median']:+7.2f} [{rb['ci68'][0]:+.2f},"
                  f"{rb['ci68'][1]:+.2f}] {str(ag_b):5s}"
                  if rb else f"  {k}: no swp value")
            rec[k] = dict(published=pub, n1=ra, swp=rb, agree_n1=ag_a,
                          agree_swp=ag_b)
        out[psr] = dict(n1_agree=[a["agree"], a["comp"]],
                        swp_agree=[b["agree"], b["comp"]],
                        n1_gate=a["gate"], swp_gate=b["gate"], params=rec)
    (RES / "swprior_check.json").write_text(json.dumps(out, indent=1))
    print(f"\n-> {RES/'swprior_check.json'}")


if __name__ == "__main__":
    main()
