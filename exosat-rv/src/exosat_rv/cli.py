"""exosat-rv command line."""

from __future__ import annotations

import json
from datetime import UTC

import typer

from .archive.fetch import describe, download
from .archive.tap import build_inventory, query_reduced_products
from .config import DATA, PUBLISHED
from .targets.catalog import build as build_targets
from .targets.catalog import shortlist

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


@app.command()
def probe(
    n: int = typer.Option(1, help="How many products to download and open."),
) -> None:
    """M1 kill-check: fetch reduced products and report whether viper could use them.

    Answers the one question M0 left open -- do ESO's calib_level=2 CRIRES+ products keep
    the per-order wavelength solution, or are they order-merged? If merged, this project
    needs cr2res for all 20 nights and becomes a much larger undertaking.
    """
    from datetime import datetime

    prods = query_reduced_products(PUBLISHED.star_ra_deg, PUBLISHED.star_dec_deg)
    public = [p for p in prods if p.release <= datetime.now(UTC)]
    public.sort(key=lambda p: p.night)
    typer.echo(f"{len(public)} public reduced products; probing {min(n, len(public))}")

    for frame in public[:n]:
        typer.echo(f"\n--- {frame.night} ---")
        try:
            path = download(frame.access_url)
        except Exception as exc:  # noqa: BLE001 - the outcome IS the result here
            typer.echo(f"  download failed: {type(exc).__name__}: {exc}")
            continue
        d = describe(path)
        typer.echo(f"  file      : {path.name} ({path.stat().st_size/1e6:.1f} MB)")
        typer.echo(f"  HDUs      : {d.n_hdus} {d.hdu_kinds}")
        per_seg = d.n_points // d.n_segments if (d.n_points and d.n_segments) else None
        typer.echo(f"  orders    : {d.n_orders}   segments: {d.n_segments}   "
                   f"points: {d.n_points} ({per_seg}/segment)")
        if d.wav_min_nm is not None:
            typer.echo(f"  wavelength: {d.wav_min_nm:.1f} - {d.wav_max_nm:.1f}")
        typer.echo(f"  VERDICT   : {d.verdict()}")


@app.command()
def targets(
    min_frames: int = typer.Option(4, help="Drop pointings with fewer frames than this."),
    out: str = typer.Option("m5-targets.json", help="Report filename under data/."),
) -> None:
    """M5: substellar companions with public CRIRES+ data, searched archive-first.

    Runs backwards on purpose -- the NASA Exoplanet Archive caps at 30 M_Jup and does not
    contain CD-35 2722 B, so a catalogue-first list would omit the reproduction target.
    CD-35 2722 B coming back out is the control.
    """
    ts = build_targets(min_frames)
    sl = shortlist(ts)
    strong = [t for t in sl if t.match_kind == "identifier" and t.is_substellar]
    bord = [t for t in sl if t.match_kind == "identifier" and t.is_substellar is None]

    typer.echo(f"{len(ts)} candidate companion pointings -> {len(sl)} shortlisted\n")
    for label, group in (("STRONG (substellar, identifier-matched)", strong),
                         ("BORDERLINE (star/BD boundary)", bord)):
        typer.echo(f"{label}: {len(group)}")
        for t in group:
            d = f"{t.distance_pc:.1f} pc" if t.distance_pc else "d unknown"
            names = ", ".join([t.eso_object] + t.aliases)
            typer.echo(f"   {t.simbad_id!s:<16}{t.sp_type or '-'!s:<8}"
                       f"{t.n_frames:>5} frames  {d:<12} [{names}]")

    control = any("2722" in str(t.simbad_id or "") for t in sl)
    typer.echo(f"\ncontrol -- CD-35 2722 B rediscovered: {'YES' if control else 'NO (pipeline broken)'}")

    DATA.mkdir(exist_ok=True)
    path = DATA / out
    path.write_text(json.dumps([{
        "eso_object": t.eso_object, "aliases": t.aliases, "simbad_id": t.simbad_id,
        "otype": t.otype, "sp_type": t.sp_type, "plx_mas": t.plx_mas,
        "distance_pc": t.distance_pc, "n_frames": t.n_frames, "n_public": t.n_public,
        "match_kind": t.match_kind, "is_substellar": t.is_substellar,
        "ra_deg": t.ra_deg, "dec_deg": t.dec_deg,
    } for t in ts], indent=2), encoding="utf-8")
    typer.echo(f"wrote {path}")
