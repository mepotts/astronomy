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
from typing import Optional

import typer

from . import __version__, ranking
from .ellipsoid import REFERENCE_EPOCH, SN1987A_DISTANCE_KPC
from .models import RankedTarget


def _now_jyear() -> float:
    """Current time as a decimal (Julian) year, so rankings track real time (not a frozen
    constant). Falls back to ``ranking.DEFAULT_NOW_JYEAR`` only if astropy is unavailable."""
    try:
        from astropy.time import Time

        return float(Time.now().jyear)
    except Exception:  # pragma: no cover - astropy is a hard dep; belt-and-suspenders
        return ranking.DEFAULT_NOW_JYEAR

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
    "crossing_now",
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
        "crossing_now": bool(target.crossing_now),
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
    transients_csv: Optional[Path] = typer.Option(
        None,
        "--transients-csv",
        help="LIVE, ACCOUNT-FREE path: ingest an externally-exported alert list (CSV: "
        "name,ra,dec[,gaia_source_id,mjd/date]) from ANY broker or your own list, then "
        "crossmatch it against DR3 gaia_source over anonymous Gaia TAP (no token) with the "
        "parallax zero-point correction, and write the full artifact set. The happy path.",
    ),
    no_zeropoint: bool = typer.Option(
        False,
        "--no-zeropoint",
        help="Skip the Gaia DR3 parallax zero-point correction (Lindegren+2021). Epochs "
        "then carry the ~-17 uas DR3 bias (0.7-4.5 yr shift). For diagnostics only.",
    ),
    now: Optional[float] = typer.Option(
        None,
        "--now",
        help="Reference 'now' as a decimal (Julian) year for crossing-proximity scoring. "
        "Default: the current time (Time.now().jyear). Pass a fixed value for reproducibility.",
    ),
    live: bool = typer.Option(
        False,
        "--live",
        help="Auto-ingest live ZTF via the Lasair REST API. ACCOUNT-GATED (needs "
        "LASAIR_TOKEN) and unavailable to most users -> use --transients-csv instead.",
    ),
    output_dir: Path = typer.Option(
        Path("output"), "--output-dir", "-o", help="Directory for the artifact set."
    ),
    datestamp: str = typer.Option(
        "", "--datestamp", help="Artifact datestamp YYYYMMDD (default: today)."
    ),
) -> None:
    """REACT mode: reactive broker over a transient list + Gaia DR3.

    Three input modes, in order of preference:
      * ``--transients-csv PATH`` -> LIVE and ACCOUNT-FREE (anonymous Gaia + zero-point).
      * default (no flags)        -> OFFLINE synthetic pipeline (deterministic demo).
      * ``--live``                -> account-gated Lasair auto-ingest (exits 2; no token).
    """
    from datetime import date

    from . import pipeline

    stamp = datestamp or date.today().strftime("%Y%m%d")
    now_jyear = now if now is not None else _now_jyear()

    # LIVE account-free path takes precedence: it IS the supported live mode.
    if transients_csv is not None:
        typer.echo(
            f"[LIVE] SN 1987A ellipsoid broker | baseline d={SN1987A_DISTANCE_KPC} kpc "
            f"| ref epoch {REFERENCE_EPOCH} | now={now_jyear:.3f}"
        )
        zp = "OFF" if no_zeropoint else "ON"
        typer.echo(
            "REACT mode (LIVE, account-free): CSV -> anonymous Gaia DR3 crossmatch "
            f"[zero-point {zp}] -> ellipsoid -> rank -> export\n"
        )
        result = pipeline.run_live_csv(
            transients_csv,
            out_dir=output_dir,
            datestamp=stamp,
            apply_zeropoint=not no_zeropoint,
            now_jyear=now_jyear,
        )
        _report(result, staged_noun="CSV alert")
        return

    if live:
        raise typer.Exit(_live_not_available())

    typer.echo(
        f"[offline] SN 1987A ellipsoid broker | baseline d={SN1987A_DISTANCE_KPC} kpc "
        f"| ref epoch {REFERENCE_EPOCH} | now={now_jyear:.3f}"
    )
    typer.echo("REACT mode (OFFLINE/synthetic) - full pipeline: alerts -> SQLite -> ellipsoid -> rank -> export\n")

    result = pipeline.run_offline(out_dir=output_dir, datestamp=stamp, now_jyear=now_jyear)
    _report(result, staged_noun="synthetic alert")


def _report(result, *, staged_noun: str) -> None:
    """Print the staged/ranked counts, the top target, and the artifact paths."""
    typer.echo(
        f"Staged {result.n_staged} {staged_noun}(s); "
        f"{result.n_ranked} survived quality cuts and were ranked.\n"
    )
    if result.targets:
        typer.echo("Top ranked ellipsoid-crossing target:\n")
        _print_row(result.targets[0])
    typer.echo("\nArtifacts written:")
    for kind, path in result.artifacts.items():
        typer.echo(f"  {kind:>3}: {path}")


def _live_not_available() -> int:
    """Emit the clean 'Lasair auto-ingest blocked' message and return a nonzero exit code."""
    typer.echo(
        "ERROR: --live auto-ingest uses the Lasair ZTF REST API, which is ACCOUNT-GATED.\n"
        "Lasair-ZTF accounts do not transfer to the Rubin era and registration has moved to\n"
        "the Lasair-LSST instance, so most users cannot obtain a working LASAIR_TOKEN.\n"
        "\n"
        "Use the LIVE, ACCOUNT-FREE path instead:\n"
        "    seti-broker run --transients-csv your_alerts.csv\n"
        "which crossmatches your list against anonymous Gaia DR3 TAP (no token) with the\n"
        "parallax zero-point correction. See examples/transients_example.csv and DATA-SOURCES.md.",
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
