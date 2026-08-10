"""exosat-rv command line."""

from __future__ import annotations

import json

import typer

from .archive.tap import build_inventory
from .config import DATA, PUBLISHED

app = typer.Typer(add_completion=False, help=__doc__, no_args_is_help=True)


@app.callback()
def main() -> None:
    """Reproduce the CD-35 2722 B exosatellite detection from public ESO data."""
    # Present so typer keeps sub-command form while only one command exists.


@app.command()
def inventory(
    band: str = typer.Option("H", help="CRIRES+ setting prefix to select, e.g. H or K."),
    out: str = typer.Option("m0-inventory.json", help="Report filename under data/."),
) -> None:
    """M0: what CD-35 2722 B data is public, reduced, and usable right now."""
    inv = build_inventory("CD-35 2722 B", PUBLISHED.star_ra_deg, PUBLISHED.star_dec_deg)
    s = inv.summary(band)

    typer.echo(f"CD-35 2722 B  --  CRIRES+ {band}-band inventory")
    typer.echo(f"  nights in band     : {s['nights_total']}")
    typer.echo(f"  usable now         : {s['usable_now']}  (public AND pipeline-reduced)")
    typer.echo(f"  reduction gap      : {s['reduction_gap']}  (public, no reduced product)")
    typer.echo(f"  still embargoed    : {s['embargoed']}")
    if s["usable_baseline"]:
        typer.echo(f"  usable baseline    : {s['usable_baseline'][0]} -> {s['usable_baseline'][1]}")
    if s["gap_nights"]:
        typer.echo(f"  gap nights         : {', '.join(s['gap_nights'])}")
    if s["embargo_lifts"]:
        typer.echo(f"  embargo lifts      : {', '.join(s['embargo_lifts'])}")

    typer.echo(f"\n  paper claims {PUBLISHED.n_epochs} usable epochs "
               f"({PUBLISHED.baseline[0]} -> {PUBLISHED.baseline[1]})")
    typer.echo(f"  we can reach {s['usable_now']} without running esorex, "
               f"{s['usable_now'] + s['reduction_gap']} with it")

    DATA.mkdir(exist_ok=True)
    path = DATA / out
    payload = {
        "summary": s,
        "nights": [
            {
                "night": n.night,
                "n_raw": n.n_raw,
                "n_reduced": n.n_reduced,
                "settings": sorted(n.settings),
                "prog_ids": sorted(n.prog_ids),
                "public": n.is_public(inv.now),
                "release": n.earliest_release.isoformat() if n.earliest_release else None,
            }
            for n in inv.nights
        ],
        "generated_utc": inv.now.isoformat(),
    }
    path.write_text(json.dumps(payload, indent=2))
    typer.echo(f"\nwrote {path}")


if __name__ == "__main__":
    app()
