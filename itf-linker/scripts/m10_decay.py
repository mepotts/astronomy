"""M10: re-measure the ledger's decay clock, now that there is more than one interval.

M9 measured "3.3% of fitted candidates in two days" from a single difference (30 of
M8's 900 between two ITF pulls). A single difference has no uncertainty and cannot
distinguish a steady hazard from one MPC batch sweep that happened to fall inside the
window. ``m10_refresh.py`` tested the same tracklet keys against **four** snapshots, so
this script can ask three questions the M9 number could not:

1. **What is the rate, with an uncertainty?** Both a pooled estimate over the whole
   window (Poisson/binomial interval) and the three per-interval hazards, which is
   where any burstiness shows up.
2. **Is the hazard uniform across the ledger?** M8's rows are the shallow head of a
   February/April sweep; M9's are the deep queue and a June designation batch. If the
   MPC's own sweeps eat the head first, the two populations must decay at different
   rates -- and that difference, not the pooled number, is what tells Matthew which
   rows are actually perishable.
3. **What does it imply for review latency?** An exponential survival fit turns a rate
   into a half-life, which is the number a human can plan against.

Reads ``data/raw/rubin/m10-refresh.json``; writes ``data/raw/rubin/m10-decay.json``.
Pure post-run analysis: no network, no fits, nothing loosened.
"""

from __future__ import annotations

import itertools
import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

REFRESH = ROOT / "data" / "raw" / "rubin" / "m10-refresh.json"
OUT = ROOT / "data" / "raw" / "rubin" / "m10-decay.json"


def parse_http_date(s: str) -> datetime:
    return datetime.strptime(s, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=UTC)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval -- behaves at k = 0, which the normal interval does not."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (c - r) / d), min(1.0, (c + r) / d))


def fisher_exact_greater(a: int, b: int, c: int, d: int) -> float:
    """One-sided p for a 2x2 table [[a,b],[c,d]] (a = consumed in group 1)."""
    def logcomb(n: int, k: int) -> float:
        return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)

    n = a + b + c + d
    r1, c1 = a + b, a + c
    lo, hi = max(0, c1 - (n - r1)), min(r1, c1)
    total = 0.0
    for x in range(lo, hi + 1):
        total += math.exp(
            logcomb(r1, x) + logcomb(n - r1, c1 - x) - logcomb(n, c1)
        )
    p = 0.0
    for x in range(a, hi + 1):
        p += math.exp(logcomb(r1, x) + logcomb(n - r1, c1 - x) - logcomb(n, c1))
    return min(1.0, p / total if total else 1.0)


def survival_rate(k: int, n: int, days: float) -> dict[str, Any]:
    """Exponential hazard from k consumptions out of n rows over `days`."""
    lo, hi = wilson(k, n)
    def lam(frac: float) -> float:
        return -math.log(max(1e-12, 1.0 - frac)) / days if days > 0 else 0.0
    l, l_lo, l_hi = lam(k / n if n else 0.0), lam(lo), lam(hi)
    return {
        "consumed": k,
        "n": n,
        "days": round(days, 4),
        "fraction": round(k / n, 5) if n else None,
        "fraction_ci95": [round(lo, 5), round(hi, 5)],
        "percent_per_2_days": round(100.0 * (1.0 - math.exp(-l * 2.0)), 3),
        "percent_per_2_days_ci95": [
            round(100.0 * (1.0 - math.exp(-l_lo * 2.0)), 3),
            round(100.0 * (1.0 - math.exp(-l_hi * 2.0)), 3),
        ],
        "hazard_per_day": round(l, 6),
        "half_life_days": round(math.log(2) / l, 1) if l > 0 else None,
        "half_life_days_ci95": [
            round(math.log(2) / l_hi, 1) if l_hi > 0 else None,
            round(math.log(2) / l_lo, 1) if l_lo > 0 else None,
        ],
    }


def main() -> None:
    doc = json.loads(REFRESH.read_text(encoding="utf-8"))
    curve = doc["decay_curve"]
    rows = doc["rows"]
    t0 = parse_http_date(curve[0]["last_modified"])
    for c in curve:
        c["days_since_base"] = round(
            (parse_http_date(c["last_modified"]) - t0).total_seconds() / 86400.0, 4
        )

    # ---- per-interval hazards: where burstiness shows -------------------------------
    intervals = []
    for a, b in itertools.pairwise(curve):
        dt = b["days_since_base"] - a["days_since_base"]
        for label, live_k, tot_k in (("fitted", "fitted_live", "fitted_total"),
                                     ("pass", "pass_live", "pass_total")):
            k = a[live_k] - b[live_k]
            intervals.append({
                "population": label,
                "from": a["snapshot_id"], "to": b["snapshot_id"],
                "days": round(dt, 4),
                "at_risk": a[live_k],
                "consumed": k,
                "hazard_per_day": round(k / a[live_k] / dt, 5) if a[live_k] and dt else None,
            })

    total_days = curve[-1]["days_since_base"]

    # ---- pooled rates, whole window --------------------------------------------------
    fitted = [r for r in rows if r["ledger"] in ("M8", "M9") and r["n_obs_base"] > 0]
    def consumed(rs: list[dict[str, Any]]) -> int:
        return sum(1 for r in rs if r["itf_status"] != "STILL_LIVE")

    pops: dict[str, list[dict[str, Any]]] = {
        "all_fitted": fitted,
        "all_pass": [r for r in fitted if r["verdict"] == "PASS"],
        "M8_fitted": [r for r in fitted if r["ledger"] == "M8"],
        "M8_pass": [r for r in fitted if r["ledger"] == "M8" and r["verdict"] == "PASS"],
        "M9_fitted": [r for r in fitted if r["ledger"] == "M9"],
        "M9_pass": [r for r in fitted if r["ledger"] == "M9" and r["verdict"] == "PASS"],
        "M9ext_pass": [r for r in fitted if r.get("provenance") == "M9-extension"
                       and r["verdict"] == "PASS"],
        "M9part_pass": [r for r in fitted if r.get("provenance") == "M9-partitions"
                        and r["verdict"] == "PASS"],
        "all_fail": [r for r in fitted if r["verdict"] == "FAIL"],
    }
    rates = {k: survival_rate(consumed(v), len(v), total_days) for k, v in pops.items()}

    # ---- is the head eaten faster than the tail? ------------------------------------
    m8p, m9p = pops["M8_pass"], pops["M9_pass"]
    a, b = consumed(m8p), len(m8p) - consumed(m8p)
    c, d = consumed(m9p), len(m9p) - consumed(m9p)
    head_vs_tail = {
        "table": {"M8_pass_consumed": a, "M8_pass_live": b,
                  "M9_pass_consumed": c, "M9_pass_live": d},
        "fisher_p_one_sided_M8_higher": round(fisher_exact_greater(a, b, c, d), 6),
    }

    # ---- rank dependence inside M8's own queue --------------------------------------
    # M8's ledger rows are in queue-rank order; split at the median to see whether the
    # MPC's sweep eats the queue head preferentially.
    m8f = pops["M8_fitted"]
    half = len(m8f) // 2
    rank_split = {
        "top_half": survival_rate(consumed(m8f[:half]), half, total_days),
        "bottom_half": survival_rate(consumed(m8f[half:]), len(m8f) - half, total_days),
    }

    out = {
        "generated_utc": doc["generated_utc"],
        "base_snapshot": doc["base_snapshot"],
        "window_days": round(total_days, 4),
        "curve": curve,
        "per_interval_hazards": intervals,
        "pooled_rates": rates,
        "head_vs_tail": head_vs_tail,
        "m8_queue_rank_split": rank_split,
        "m9_single_interval_claim": {
            "text": "3.3% of fitted candidates (30 of 900) in two days",
            "reproduced_here": rates["M8_fitted"],
        },
    }
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "curve"}, indent=2))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
