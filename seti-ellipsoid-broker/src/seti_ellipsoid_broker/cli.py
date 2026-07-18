"""Command-line entry point for the SETI Ellipsoid Alert Broker.

M1 offline core: `seti-broker run` runs the FULL pipeline in offline/mock mode -- synthetic
alerts -> SQLite staging -> real ellipsoid math -> ranking -> real CSV / .tgt / Markdown
artifacts (no network, no credentials). The live ZTF (Lasair) + Gaia path is gated behind
`--live` and raises a clean error naming the LASAIR_TOKEN requirement (M1 live leg / M2).

    seti-broker run                 # REACT mode, OFFLINE: writes real artifacts from synthetic data
    seti-broker run --live          # live ZTF+Gaia (blocked: needs LASAIR_TOKEN + network)
    seti-broker predict             # PREDICT mode: Window Predictor (M3 stub; mocked row)
    seti-broker version
"""

from __future__ import annotations

from pathlib import Path

import typer

from . import __version__, ranking
from .ellipsoid import REFERENCE_EPOCH, SN1987A_DISTANCE_KPC
from .models import RankedTarget

app = typer.Typer(
    add_completion=False,
    help="Fuse ZTF/ASAS-SN/CHIME alerts against the SN 1987A SETI Ellipsoid (Gaia DR3 distances).",
)

# Column order shared by both modes' printed output.
_COLUMNS = (
    "source_ref",
    "gaia_source_id",
    "ra_deg",
    "dec_deg",
    "distance_pc",
    "crossing_epoch_jyear",
    "crossing_window_yr",
    "density_bin",
    "score",
)


def _print_row(target: RankedTarget) -> None:
    """Print one ranked target as a labeled, fixed-width row."""
    values = {
        "source_ref": target.source_ref,
        "gaia_source_id": target.gaia_source_id,
        "ra_deg": f"{target.ra_deg:.4f}",
        "dec_deg": f"{target.dec_deg:.4f}",
        "distance_pc": f"{target.distance_pc:.1f}",
        "crossing_epoch_jyear": f"{target.crossing_epoch_jyear:.1f}",
        "crossing_window_yr": f"{target.crossing_window_yr:.2f}",
        "density_bin": target.density_bin,
        "score": f"{target.score:.3f}",
    }
    header = " | ".join(f"{c}" for c in _COLUMNS)
    line = " | ".join(f"{values[c]}" for c in _COLUMNS)
    typer.echo(header)
    typer.echo("-" * len(header))
    typer.echo(line)
    if target.notes:
        typer.echo(f"# {target.notes}")


@app.command()
def run(
    live: bool = typer.Option(
        False,
        "--live",
        help="Use live ZTF (Lasair) + Gaia DR3 instead of offline synthetic data. "
        "Requires LASAIR_TOKEN + network; not available in the offline M1 core.",
    ),
    output_dir: Path = typer.Option(
        Path("output"), "--output-dir", "-o", help="Directory for the artifact set."
    ),
    datestamp: str = typer.Option(
        "", "--datestamp", help="Artifact datestamp YYYYMMDD (default: today)."
    ),
) -> None:
    """REACT mode: reactive broker over ZTF (Lasair) + Gaia DR3.

    Default is OFFLINE/mock: runs the full synthetic pipeline and writes real artifacts.
    """
    if live:
        raise typer.Exit(_live_not_available())

    from datetime import date

    from . import pipeline

    stamp = datestamp or date.today().strftime("%Y%m%d")
    typer.echo(
        f"[M1 offline] SN 1987A ellipsoid broker | baseline d={SN1987A_DISTANCE_KPC} kpc "
        f"| ref epoch {REFERENCE_EPOCH}"
    )
    typer.echo("REACT mode (OFFLINE/synthetic) - full pipeline: alerts -> SQLite -> ellipsoid -> rank -> export\n")

    result = pipeline.run_offline(out_dir=output_dir, datestamp=stamp)
    typer.echo(
        f"Staged {result.n_staged} synthetic alert(s); "
        f"{result.n_ranked} survived quality cuts and were ranked.\n"
    )
    if result.targets:
        typer.echo("Top ranked ellipsoid-crossing target:\n")
        _print_row(result.targets[0])
    typer.echo("\nArtifacts written:")
    for kind, path in result.artifacts.items():
        typer.echo(f"  {kind:>3}: {path}")


def _live_not_available() -> int:
    """Emit the clean 'live path blocked' message and return a nonzero exit code."""
    typer.echo(
        "ERROR: the live ZTF+Gaia path is not part of the offline M1 core.\n"
        "It requires a Lasair API token (set LASAIR_TOKEN; register at lasair-ztf.lsst.ac.uk)\n"
        "plus network access to the Lasair REST API and the anonymous Gaia DR3 TAP service.\n"
        "Run without --live for the offline/synthetic pipeline (real CSV/.tgt/.md artifacts).",
        err=True,
    )
    return 2


@app.command()
def predict() -> None:
    """PREDICT mode: Window Predictor rolling forward-crossing calendar. (M0: prints a mocked row.)"""
    typer.echo(
        f"[M0 skeleton] Window Predictor | baseline d={SN1987A_DISTANCE_KPC} kpc "
        f"| ref epoch {REFERENCE_EPOCH}"
    )
    typer.echo("PREDICT mode - next upcoming shell crossing (MOCKED):\n")
    _print_row(ranking.mock_predicted_crossing())


@app.command()
def version() -> None:
    """Print the package version."""
    typer.echo(f"seti-ellipsoid-broker {__version__}")


if __name__ == "__main__":
    app()
