"""The ``exosat-rv gravity`` command body."""

from __future__ import annotations

import json

import typer

from .archive.gravity import KILL_CHECK, inventory
from .config import DATA


def run(out: str) -> None:
    targets = inventory()

    typer.echo("VLTI/GRAVITY holdings on Kral et al. 2026's exomoon shortlist")
    typer.echo("")
    typer.echo(
        f"{'target':18s}{'reduced':>9s}{'nights':>8s}{'baseline':>26s}"
        f"{'span/d':>8s}{'raw sci':>9s}{'public':>8s}  usable?"
    )
    for t in targets:
        base = f"{t.nights[0]} -> {t.nights[-1]}" if t.nights else "-"
        typer.echo(
            f"{t.name:18s}{t.n_products:9d}{len(t.nights):8d}{base:>26s}"
            f"{t.baseline_days:8d}{t.n_raw_science:9d}{t.n_raw_public:8d}"
            f"  {'YES' if t.usable else 'no'}"
        )

    typer.echo("")
    typer.echo("  For comparison, the RV route's best datasets:")
    typer.echo("    CD-35 2722 B  18 reduced nights over  466 d  (the published detection)")
    typer.echo("    eta Tel B     16 reduced nights over  800 d  (M5's best analogue)")

    best = next((t for t in targets if t.usable), None)
    if best:
        typer.echo("")
        typer.echo(
            f"  Best astrometric dataset: {best.name} -- {len(best.nights)} nights over "
            f"{best.baseline_days} d, all public."
        )
    typer.echo("")
    typer.echo("  KILL-CHECK STILL OPEN:")
    for line in KILL_CHECK.splitlines():
        typer.echo(f"    {line}")

    DATA.mkdir(exist_ok=True)
    path = DATA / out
    path.write_text(
        json.dumps(
            {
                "targets": [
                    {
                        "name": t.name,
                        "ra_deg": t.ra_deg,
                        "dec_deg": t.dec_deg,
                        "n_reduced_products": t.n_products,
                        "n_nights": len(t.nights),
                        "nights": t.nights,
                        "baseline_days": t.baseline_days,
                        "n_raw_science": t.n_raw_science,
                        "n_raw_public": t.n_raw_public,
                        "programmes": t.programmes,
                        "usable": t.usable,
                    }
                    for t in targets
                ],
                "kill_check_open": True,
                "kill_check": KILL_CHECK,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    typer.echo("")
    typer.echo(f"wrote {path}")
