"""Separate exploratory postprocessor. Never changes original labels or analysis."""
import argparse
import csv
import hashlib
import io
import json
import math
from collections import Counter
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAIRS = {"D1": (0.154, 0.0), "D4": (0.30, 0.075)}
AUC = {"D2": .659, "D3": .344}


def number(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (ValueError, TypeError):
        return None


@lru_cache(maxsize=256)
def design_power(test, nc, ns):
    from m5_activity_discriminator import fisher_power
    ps, pc = PAIRS[test]
    return float(fisher_power(nc, pc, ns, ps, alpha=.05))


def translate(row, power_fn=design_power):
    original = dict(row)
    test, analysis = row["test"], row["analysis"]
    if test not in (*PAIRS, *AUC) or analysis not in ("primary", "pooled", "regression"):
        raise ValueError("unknown test or scope")
    if analysis == "regression":
        return {"original": original, "variant_label": row["label"], "regression_passthrough": True}
    p, effect = number(row.get("p_holm")), number(row.get("effect"))
    control = number(row.get("control_p"))
    nc, ns = int(row["n_conf"]), int(row["n_spur"])
    if nc < 0 or ns < 0 or (p is not None and not 0 <= p <= 1):
        raise ValueError("invalid sizes/probability")
    if control is not None and not 0 <= control <= 1:
        raise ValueError("invalid negative-control p")
    output = {"original": original, "variant_label": "NOT TESTABLE",
              "design_power": None, "design_decisive": False,
              "negative_control_veto": control is not None and control < .05,
              "positive_finding_reportable": False}
    if min(nc, ns) < 5 or p is None or effect is None:
        return output
    if test in PAIRS:
        power = power_fn(test, nc, ns)
        if number(power) is None or not 0 <= power <= 1 + 1e-10:
            raise ValueError("invalid exact power")
        decisive = power >= .8
        output.update(design_power=power, power_method="existing exact Fisher sum; nominal alpha=.05")
        direction = effect > 0
    else:
        md = number(row.get("min_detectable"))
        decisive = md is not None and md <= max(AUC[test], 1 - AUC[test])
        output["power_method"] = "unchanged original minimum-detectable AUC"
        direction = effect > .5 if test == "D2" else effect < .5
    output["design_decisive"] = bool(decisive)
    if p >= .05:
        label = "POOLED: UNINTERPRETABLE" if analysis == "pooled" else ("NULL" if decisive else "UNDERPOWERED")
    elif not direction:
        label = "POOLED REVERSAL: NOT INTERPRETABLE AS A FINDING" if analysis == "pooled" else "DIRECTION REVERSAL"
    elif not decisive:
        label = "SIGNIFICANT, EXPECTED DIRECTION; NOT DESIGN-DECISIVE"
        if analysis == "pooled":
            label += " (POOLED)"
    else:
        label = "POSITIVE (conservative, pooled)" if analysis == "pooled" else "POSITIVE"
        output["positive_finding_reportable"] = control is not None and control >= .05
    if p < .05 and direction:
        if output["negative_control_veto"]:
            label += " -- VETOED by the negative control"
        elif control is None:
            label += " -- NOT REPORTABLE: negative control unavailable"
    output["variant_label"] = label
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve() or args.output.exists():
        raise ValueError("refuse to overwrite input or existing result")
    raw = args.input.read_bytes()
    rows = list(csv.DictReader(io.StringIO("\n".join(
        line for line in raw.decode("utf-8-sig").splitlines() if not line.startswith("#")))))
    if not rows:
        raise ValueError("no labels")
    labels = []
    for row in rows:
        labels.append(translate(row))
        print(f"{row.get('scenario', '')} {row['test']} {row['analysis']}: {labels[-1]['variant_label']}", flush=True)
    if args.input.read_bytes() != raw:
        raise ValueError("source changed during run")
    variant = (ROOT / "VARIANT-2026-09-06.md").read_bytes().replace(b"\r\n", b"\n")
    result = {"variant": "exploratory-2026-09-06", "input_sha256": hashlib.sha256(raw).hexdigest(),
              "variant_sha256": hashlib.sha256(variant).hexdigest(), "original_unchanged": True,
              "labels": labels, "counts": dict(Counter(r["variant_label"] for r in labels)),
              "changed_label_count": sum(r["variant_label"] != r["original"]["label"] for r in labels)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({k: v for k, v in result.items() if k != "labels"}, indent=2))


if __name__ == "__main__":
    main()
