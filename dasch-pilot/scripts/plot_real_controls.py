"""Render public real-control evidence; no thresholds or analysis outputs altered."""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import real_controls as rc
from colour_validation import joined
from m0_extension import table


def main():
    result = json.loads((rc.OUT / "results.json").read_bytes())
    if result["contract"] != rc.contract():
        raise ValueError("real-control contract changed")
    archive = rc.Archive(replay=True)
    fig, axes = plt.subplots(3, 2, figsize=(12, 9), constrained_layout=True)
    for i, control in enumerate(result["controls"]):
        source = control["source"]
        rows = table(archive.fetch(f"{i}-lightcurve", "lightcurve", {"refcat": "apass",
                     "ref_number": int(source["ref_number"]), "gsc_bin_index": int(source["gsc_bin_index"])}))
        exps = table(archive.fetch(f"{i}-exposures", "queryexps", {
            k: control[k] for k in ("ra_deg", "dec_deg")}))
        data, _ = joined(rows, exps, quarantine=True)
        left, right = axes[i]
        left.scatter([r["year"] for r in data], [r["mag"] for r in data], s=5, alpha=.25, color="#235789")
        left.invert_yaxis()
        left.set_ylabel("APASS-calibrated B magnitude")
        left.set_title(control["name"]+" | known published variable", fontsize=10)
        start, end = min(control["starts"]), max(control["starts"])+5
        for ax in (left, right):
            ax.axvspan(start, end, color="#e5a83b", alpha=.12)
            ax.set_xlim(1880, 1990)
            ax.grid(alpha=.2)
        series = sorted({s for w in control["windows"] for s in w["series_medians"]})
        palette = plt.get_cmap("tab20")
        for j, s in enumerate(series):
            ws = [w for w in control["windows"] if s in w["series_medians"]]
            for w in ws:
                right.scatter(w["start"]+2.5, w["series_medians"][s], s=27,
                              facecolors=palette(j % 20) if w["eligible"] else "none",
                              edgecolors=palette(j % 20), linewidths=.9)
        right.axhline(.5, color="#ad343e", linestyle="--", linewidth=1)
        right.axhline(-.5, color="#ad343e", linestyle="--", linewidth=1)
        right.axhline(0, color="gray", linewidth=.7)
        right.set_ylim(-1.5, 1.5)
        right.set_ylabel("Matched residual (mag; + is fainter)")
        right.set_title("Series medians | filled: eligible window; open: insufficient support", fontsize=9)
    for ax in axes[-1]:
        ax.set_xlabel("Calendar year")
    fig.suptitle("Real-event transfer check: 0/3 recoveries with the unchanged five-year detector\n"
                 "Known controls only - shaded epochs from Tang et al. (2010); no new discovery", fontsize=13)
    destination = rc.OUT / "real-event-transfer.png"
    fig.savefig(destination, dpi=150, metadata={"Software": "astronomy plot_real_controls.py"})
    plt.close(fig)
    print(destination)


if __name__ == "__main__":
    main()
