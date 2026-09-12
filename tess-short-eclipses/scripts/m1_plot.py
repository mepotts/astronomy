"""Render retained public-control M1 maps; does not recompute science."""

import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

ROOT = Path(__file__).resolve().parents[1]


def main():
    for tic in (450781262, 53206761, 2041210548):
        source = ROOT / "out" / f"m1-{tic}.json"
        if not source.exists():
            continue
        result = json.loads(source.read_bytes())
        images = result["images"]
        difference = np.array(images["difference"], dtype=float)
        error = np.array(images["block_standard_error"], dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            snr = difference / error
        panels = [(difference, "Locally paired eclipse difference", "e-/s"),
                  (snr, "Difference / day-block standard error", "descriptive ratio"),
                  (np.array(images["background_difference"], dtype=float), "Pipeline-background difference", "e-/s"),
                  (np.array(images["residual"], dtype=float), "Residual after Gaussian + plane", "e-/s")]
        fig, axes = plt.subplots(2, 2, figsize=(10, 9), constrained_layout=True)
        target = result["target_xy_zero_based"]
        fit = result["centroid_surrogate"]
        valid = np.array(images["valid_pixels"], dtype=bool)
        for axis, (values, title, units) in zip(axes.flat, panels, strict=True):
            shown = np.where(valid, values, np.nan)
            amplitude = np.nanmax(np.abs(shown))
            artist = axis.imshow(shown, origin="lower", cmap="RdBu_r", vmin=-amplitude, vmax=amplitude)
            axis.set_title(title, fontsize=10)
            axis.set_xlabel("Column x (zero-based)")
            axis.set_ylabel("Row y (zero-based)")
            axis.scatter(*target, marker="+", s=180, c="black", linewidths=1.5, label="Header target")
            axis.add_patch(Circle(target, .75, fill=False, color="black", linewidth=.8, linestyle="--"))
            if fit["success"]:
                axis.scatter(fit["x"], fit["y"], marker="x", s=100, c="limegreen", linewidths=1.5, label="Gaussian centroid")
            for y, x in np.argwhere(np.array(images["aperture"], dtype=bool)):
                axis.add_patch(Rectangle((x-.5, y-.5), 1, 1, fill=False, edgecolor="orange", linewidth=1))
            fig.colorbar(artist, ax=axis, shrink=.8, label=units)
        axes[0, 0].legend(loc="upper left", fontsize=8)
        fig.suptitle(f"Published control TIC {tic} | sector {result['headers']['SECTOR']}\n"
                     "Fixed M0b ephemeris; centroid surrogate, not calibrated source identification", fontsize=12)
        destination = ROOT / "out" / f"m1-{tic}.png"
        if destination.exists():
            raise FileExistsError(destination)
        fig.savefig(destination, dpi=140)
        plt.close(fig)
        print(destination)


if __name__ == "__main__":
    main()
