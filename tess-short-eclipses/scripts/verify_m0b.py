"""Read-only replay of M0b, optionally plot published controls (never unknowns)."""
import argparse
import json
from itertools import pairwise
from pathlib import Path

import m0
import numpy as np
from astropy.io import fits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--figure", type=Path)
    args = parser.parse_args()
    panels = []
    for tic in m0.CONTROLS:
        recorded = json.loads((m0.ROOT / "out" / f"m0b-{tic}.json").read_bytes())
        for key, path in (("protocol_sha256", m0.PROTOCOL), ("base_protocol_sha256", m0.BASE_PROTOCOL),
                          ("script_sha256", Path(m0.__file__)), ("runner_sha256", m0.RUNNER)):
            if m0.sha(path) != recorded[key]:
                raise ValueError(f"provenance mismatch: {key}")
        receipt = recorded["input"]
        if ("reused_from" in receipt
                and m0.sha(m0.ROOT / receipt["reused_from"]) != receipt["original_receipt_sha256"]):
            raise ValueError("original acquisition receipt mismatch")
        path = m0.ROOT / receipt["input_path"] if "input_path" in receipt else m0.DATA/str(tic)/receipt["filename"]
        if m0.sha(path) != receipt["sha256"]:
            raise ValueError("FITS hash mismatch")
        with fits.open(path) as hdus:
            m0.validate_header(hdus[0].header, hdus[1].header, tic, m0.CONTROLS[tic][0])
            d = hdus[1].data
            t, y, dy = m0.prepare(d["TIME"], d["PDCSAP_FLUX"], d["PDCSAP_FLUX_ERR"], d["QUALITY"])
            crowd = hdus[1].header.get("CROWDSAP")
        solution = m0.search(t, y, dy)
        full = m0.depth_stats(t, y, dy, solution)
        first = t < (t.min()+t.max())/2
        halves = [m0.depth_stats(t[s], y[s], dy[s], solution) for s in (first, ~first)]
        grade = m0.grade(solution, full, halves, m0.CONTROLS[tic][1])
        if any(value != recorded[key] for key, value in
               (("solution", solution), ("full", full), ("halves", halves), ("grade", grade))):
            raise ValueError(f"scientific replay differs for known control {tic}")
        print(json.dumps({"tic": tic, "replay": "PASS", "grade": grade,
                          "crowdsap_header": crowd, "depth_is_physical_measurement": False}))
        panels.append((tic, t, y, dy, solution))
    if args.figure:
        if args.figure.exists():
            raise FileExistsError("figure exists; do not overwrite")
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), constrained_layout=True)
        for ax, (tic, t, y, dy, solution) in zip(axes, panels, strict=True):
            period = solution["period"]
            phase = ((t-solution["transit_time"]+period/2) % period-period/2)*1440
            halfwidth = max(25., solution["duration"]*1440*2.5)
            edges = np.linspace(-halfwidth, halfwidth, 51)
            xs, ys, es = [], [], []
            for lo, hi in pairwise(edges):
                mask = (phase >= lo) & (phase < hi)
                if mask.any():
                    w = dy[mask]**-2
                    xs.append((lo+hi)/2)
                    ys.append(np.average(y[mask], weights=w))
                    es.append(np.sqrt(1/w.sum()))
            ax.errorbar(xs, ys, yerr=es, fmt=".", color="#236b8e", capsize=2)
            ax.set(title=f"Known TIC {tic}\nP = {period:.7f} d", xlabel="Minutes from fitted eclipse")
            ax.grid(alpha=.2)
        axes[0].set_ylabel("Median-normalized PDCSAP flux")
        fig.suptitle("Published control recovery — not new discoveries; depths are not physical calibration")
        args.figure.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.figure, dpi=150)
        plt.close(fig)
    print("M0b exact raw-data replay: 3/3 PASS")


if __name__ == "__main__":
    main()
