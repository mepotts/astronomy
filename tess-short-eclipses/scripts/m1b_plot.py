"""Render M1b catalog comparison without modifying pixel results."""

import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

ROOT = Path(__file__).resolve().parents[1]


def main():
    figure, axes = plt.subplots(1, 3, figsize=(15, 5.3), constrained_layout=True)
    for axis, tic in zip(axes, (450781262, 53206761, 2041210548), strict=True):
        result = json.loads((ROOT / "out" / f"m1b-{tic}.json").read_bytes())
        images = result["images"]
        values = np.array(images["difference"], dtype=float)
        values[~np.array(images["valid_pixels"], dtype=bool)] = np.nan
        scale = np.nanmax(np.abs(values))
        artist = axis.imshow(values, origin="lower", cmap="RdBu_r", vmin=-scale, vmax=scale)
        target = result["target_xy_zero_based"]
        fit = result["centroid_surrogate"]
        axis.scatter(*target, marker="+", s=130, color="black", label="Header target")
        axis.scatter(fit["x"], fit["y"], marker="x", s=90, color="limegreen", label="Difference centroid")
        axis.add_patch(Circle((fit["x"], fit["y"]), 1, fill=False, linestyle="--", color="limegreen"))
        neighbors = result["catalog"]
        if "rows_in_stamp" not in neighbors:
            axis.text(.03, .04, "Gaia query unavailable\nNeighbor field NOT cleared", transform=axis.transAxes,
                      fontsize=9, color="darkred", bbox={"facecolor": "white", "alpha": .9, "edgecolor": "none"})
        for row in neighbors.get("rows_in_stamp", []):
            if row["centroid_separation_pixels"] <= 2:
                is_target = row["source_id"] == neighbors.get("provisional_target_id")
                axis.scatter(row["x"], row["y"], marker="o", s=50, facecolors="none",
                             edgecolors="green" if is_target else "darkorange")
        for y, x in np.argwhere(np.array(images["aperture"], dtype=bool)):
            axis.add_patch(Rectangle((x-.5, y-.5), 1, 1, fill=False, edgecolor="orange", linewidth=.8))
        axis.set_title(f"TIC {tic} / sector {result['headers']['SECTOR']}\n"
                       f"Centroid offset {result['centroid_target_distance_pixels']:.3f} pixel", fontsize=10)
        axis.set_xlabel("Column x (zero-based)")
        axis.set_ylabel("Row y (zero-based)")
        figure.colorbar(artist, ax=axis, shrink=.68, label="Local eclipse difference [e-/s]")
    axes[0].legend(fontsize=7, loc="lower left")
    figure.suptitle("Published controls only: fixed M0b ephemerides, Gaussian centroid surrogate\n"
                   "Open circles: Gaia within 2 pixels (green provisional target; orange other sources). No discovery claim.", fontsize=11)
    path = ROOT / "out/m1b-controls-catalog-status.png"
    if path.exists():
        raise FileExistsError(path)
    figure.savefig(path, dpi=150)
    plt.close(figure)
    print(path)


if __name__ == "__main__":
    main()
