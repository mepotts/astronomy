#!/usr/bin/env python3
"""M3 campaign inventory: coverage, gates, acceptance audit."""
import glob
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TAB = json.loads((REPO / "results/m3/published_table.json").read_text())


def main():
    variant = sys.argv[1] if len(sys.argv) > 1 else "noise"
    tag = {"noise": "n1", "table": "t1", "fl": "f1"}[variant]
    rows = []
    for psr in sorted(TAB):
        f = REPO / f"results/m3/{psr}_{variant}_{tag}.summary.json"
        if not f.exists():
            rows.append(dict(psr=psr, state="not-started"))
            continue
        s = json.loads(f.read_text())
        ch = s.get("chain") or {}
        rows.append(dict(psr=psr, state=s.get("state"),
                         exit=s.get("exit_reason"),
                         gate=bool(s.get("gate_met")),
                         raw=ch.get("raw_postburn", 0),
                         acc=ch.get("acc_rate"),
                         stable=ch.get("stable"),
                         elapsed=s.get("elapsed_min"),
                         eval_ms=s.get("eval_ms"),
                         verdict=s.get("verdict"),
                         agree=(f"{s['n_agree']}/{s['n_compared']}"
                                if "n_agree" in s else None)))
    done = [r for r in rows if r["state"] in ("done", "error", "aborted")]
    gated = [r for r in rows if r.get("gate")]
    run = [r for r in rows if r["state"] == "running"]
    ns = [r for r in rows if r["state"] == "not-started"]
    err = [r for r in rows if r["state"] == "error"]
    print(f"[{variant}] {len(rows)} pulsars: {len(gated)} gate-met, "
          f"{len(done)-len(gated)} finished-without-gate, {len(run)} running, "
          f"{len(ns)} not started, {len(err)} error")
    lowacc = [r for r in rows if r.get("acc") is not None and r["acc"] < 0.05]
    if lowacc:
        print(f"  ACCEPTANCE FLOOR violations ({len(lowacc)}): "
              + ", ".join(f"{r['psr']}={r['acc']:.3f}" for r in lowacc))
    accs = [r["acc"] for r in rows if r.get("acc") is not None]
    if accs:
        print(f"  acceptance range {min(accs):.3f}-{max(accs):.3f} "
              f"over {len(accs)} runs")
    for r in err:
        print(f"  ERROR {r['psr']}: {r['exit']}")
    nogate = [r for r in done if not r["gate"]]
    for r in nogate:
        print(f"  no-gate {r['psr']}: exit={r['exit']} raw={r['raw']} "
              f"acc={r['acc']} stable={r['stable']} elapsed={r['elapsed']}")
    if variant == "noise":
        full = [r for r in gated if r.get("agree") and
                r["agree"].split("/")[0] == r["agree"].split("/")[1]]
        print(f"  full agreement: {len(full)}/{len(gated)} gated pulsars")
    (REPO / "results/m3/status.json").write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
