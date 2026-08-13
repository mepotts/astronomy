"""The ``exosat-rv orders`` command body, kept out of ``cli.py`` only for length."""

from __future__ import annotations

import json

import typer

from .analysis.orders import (
    PATHOLOGICAL_ORDERS,
    SCREEN_RESULTS,
    combination_ceiling_ms,
    combine,
    order_stats,
    read_rvo,
)
from .config import DATA, PUBLISHED

ACCEPTED = "drop order 8, equal"


def run(tag: str, out: str) -> None:
    import numpy as np

    rvo, par = DATA / "viper" / f"{tag}.rvo.dat", DATA / "viper" / f"{tag}.par.dat"
    if not rvo.exists():
        typer.echo(f"no viper output at {rvo} -- see docs/viper-runbook.md")
        raise typer.Exit(1)

    stats = order_stats(rvo, par)
    typer.echo(f"Per-order behaviour, viper run '{tag}'")
    typer.echo("")
    typer.echo(
        f"{'ord':>4s}{'lam/nm':>9s}{'rms m/s':>9s}{'formal':>8s}"
        f"{'ratio':>7s}{'fit rms':>9s}{'tell S/N':>9s}"
    )
    for s in stats:
        flag = "  <- dropped" if s.order in PATHOLOGICAL_ORDERS else ""
        typer.echo(
            f"{s.order:4d}{s.wavelength_nm:9.1f}{s.rms_ms:9.0f}"
            f"{s.median_formal_err_ms:8.0f}{s.error_ratio:7.1f}"
            f"{s.median_fit_rms:9.2f}{s.telluric_snr:9.2f}{flag}"
        )

    bjd, rv, er, ords = read_rvo(rvo)
    typer.echo("")
    typer.echo("Every screen, scored on the TARGET and on the POSITIVE CONTROL:")
    typer.echo(
        f"  {'screen':40s}{'CD-35 rms':>11s}{'GJ229 dchi2':>13s}{'K m/s':>8s}  verdict"
    )
    for label, (rms, dchi2, amp) in SCREEN_RESULTS.items():
        if label == ACCEPTED:
            verdict = "ACCEPTED"
        elif dchi2 < 40:
            verdict = "FAILS CONTROL"
        else:
            verdict = "rejected (worse on target)"
        typer.echo(f"  {label:40s}{rms:11.0f}{dchi2:13.1f}{amp:8.0f}  {verdict}")

    combined = combine(rv, er, ords)
    ceiling = combination_ceiling_ms()
    typer.echo("")
    typer.echo(f"  accepted screen -> {np.nanstd(combined):.0f} m/s over {len(combined)} epochs")
    typer.echo(f"  ceiling of all screens that PASS the control: {ceiling:.0f} m/s")
    typer.echo(
        f"  target {PUBLISHED.rv_err_nodding_ms:.2f} m/s "
        f"-> still {ceiling / PUBLISHED.rv_err_nodding_ms:.0f}x short"
    )
    typer.echo("")
    typer.echo("  M9 verdict: the shortfall is PER-ORDER, and combination already works")
    typer.echo("  (median per-order rms 2133 m/s; sqrt(10) floor 674 m/s; viper gives 823).")
    typer.echo("  No weighting scheme closes it. Attack the per-order forward model.")

    DATA.mkdir(exist_ok=True)
    path = DATA / out
    payload = {
        "tag": tag,
        "orders": [
            {
                "order": s.order,
                "wavelength_nm": s.wavelength_nm,
                "rms_ms": s.rms_ms,
                "median_formal_err_ms": s.median_formal_err_ms,
                "error_ratio": s.error_ratio,
                "median_fit_rms": s.median_fit_rms,
                "telluric_snr": s.telluric_snr,
                "dropped": s.order in PATHOLOGICAL_ORDERS,
            }
            for s in stats
        ],
        "screens": {
            k: {"target_rms_ms": v[0], "control_dchi2": v[1], "control_k_ms": v[2]}
            for k, v in SCREEN_RESULTS.items()
        },
        "accepted_screen": ACCEPTED,
        "combined_rms_ms": float(np.nanstd(combined)),
        "ceiling_ms": ceiling,
        "target_ms": PUBLISHED.rv_err_nodding_ms,
        "bjd": bjd.tolist(),
        "rv_ms": [None if np.isnan(x) else float(x) for x in combined],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    typer.echo("")
    typer.echo(f"wrote {path}")
