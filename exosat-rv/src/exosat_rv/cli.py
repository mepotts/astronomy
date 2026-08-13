"""exosat-rv command line."""

from __future__ import annotations

import json
from datetime import UTC

import typer
from astropy.time import Time

from .analysis import aliases as al
from .analysis import orbits as orb
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


@app.command()
def alias(
    trials: int = typer.Option(400, help="Injection-recovery trials per scenario."),
    out: str = typer.Option("m4-aliases.json", help="Report filename under data/."),
) -> None:
    """M4: is the second signal's period determined by the data, or by the sampling?

    Uses only the observing cadence and synthetic signals -- no RVs required, which is why
    it can run before M2.
    """
    import numpy as np
    from astropy.timeseries import LombScargle

    from .archive.tap import query_raw_frames

    frames = [f for f in query_raw_frames(PUBLISHED.star_ra_deg, PUBLISHED.star_dec_deg)
              if f.setting.upper().startswith("H") and f.night <= "2025-01-21"]
    nights = sorted({f.night for f in frames})
    t = np.array([Time(n).mjd for n in nights], dtype=float)
    span = t.max() - t.min()
    typer.echo(f"{len(nights)} H-band epochs, {nights[0]} -> {nights[-1]} ({span:.0f} d)")

    sep = al.season_separation_d(t)
    seasons = al.season_split(t)
    typer.echo(f"seasons: {[len(x) for x in seasons]}   mean-to-mean separation "
               f"{sep:.1f} d ({sep / al.YEAR_D:.3f} yr)")

    typer.echo(f"\nalias comb from the {PUBLISHED.sat1_period_d} d signal, 1-yr sampling:")
    for m in al.match_alias_comb(list(PUBLISHED.alias_periods_d),
                                 PUBLISHED.sat1_period_d, 1 / al.YEAR_D):
        typer.echo(f"   {m.period_d:6.1f} d   order m={m.order:+3d}   tooth off by "
                   f"{m.period_error_d:6.3f} d   implied sampling {m.implied_sampling_period_d:7.1f} d")

    fmin, fmax = 1 / 400, 1 / 8
    freqs = np.linspace(fmin, fmax, int(20 * span * (fmax - fmin)))
    rng = np.random.default_rng(20260810)
    noise = float(np.hypot(PUBLISHED.rv_err_nodding_ms, PUBLISHED.two_sat_jitter_ms))
    fap1 = float(LombScargle(t, rng.normal(0, noise, t.size), np.full(t.size, noise))
                 .false_alarm_level(0.01, minimum_frequency=fmin, maximum_frequency=fmax))

    cands = (14.0, 70.0, PUBLISHED.sat2_period_d, 115.0)
    typer.echo(f"\ninjection-recovery ({trials} trials, noise {noise:.1f} m/s, "
               f"1% FAP power {fap1:.3f}):")
    report = {}
    for label, sp in [("none", None), ("87.46", PUBLISHED.sat2_period_d),
                      ("115", 115.0), ("70", 70.0), ("14", 14.0)]:
        res = [al.recover_secondary(
            t, rng, primary_period=PUBLISHED.sat1_period_d,
            primary_k=PUBLISHED.sat1_amplitude_ms, secondary_period=sp,
            secondary_k=PUBLISHED.sat2_amplitude_ms, noise_ms=noise,
            freqs=freqs, candidates_d=cands) for _ in range(trials)]
        counts = {c: sum(1 for w, _, _ in res if w == c) / len(res) for c in cands}
        sig = sum(1 for _, _, mx in res if mx > fap1) / len(res)
        report[label] = {"recovered": counts, "significant_frac": sig}
        typer.echo(f"   injected {label:>6} d -> " +
                   "  ".join(f"{c:g}d {100 * v:4.1f}%" for c, v in counts.items() if v) +
                   f"   |  >1% FAP {100 * sig:5.1f}%")

    DATA.mkdir(exist_ok=True)
    path = DATA / out
    path.write_text(json.dumps({
        "nights": nights, "mjd": t.tolist(), "baseline_d": span,
        "season_sizes": [len(x) for x in seasons], "season_separation_d": sep,
        "noise_ms": noise, "fap1_power": fap1, "trials": trials,
        "injection_recovery": report,
    }, indent=2), encoding="utf-8")
    typer.echo(f"\nwrote {path}")


@app.command()
def orbits(
    starts: int = typer.Option(400, help="Optimiser restarts per model."),
    version: str = typer.Option("nature", help="RV table: 'nature' (23 epochs) or 'v1' (superseded)."),
) -> None:
    """M6/M13: reproduce the paper's model comparison from its OWN published RVs.

    Independent of M2's extraction, which fell short of the precision needed. Extraction and
    inference are separate claims; this tests the second. Default is the Nature table; the
    superseded arXiv v1 table (which M6 fitted) stays available via --version v1.
    """
    nature = version == "nature"
    p1_one = PUBLISHED.pub_one_sat_period_d if nature else PUBLISHED.sat1_period_d
    p1_two = PUBLISHED.pub_sat1_period_d if nature else PUBLISHED.sat1_period_d
    p2_pub = PUBLISHED.pub_sat2_period_d if nature else PUBLISHED.sat2_period_d
    dlz_pub = PUBLISHED.pub_delta_logz_two_vs_one if nature else PUBLISHED.delta_logz_two_vs_one
    alias = tuple(sorted({14.0, 70.0, round(p2_pub, 3), 115.0}))

    data = orb.load_published(version=version)
    typer.echo(f"{len(data.rv)} published RVs ({version}), baseline {data.baseline_d:.1f} d, "
               f"mean error {data.erv.mean():.2f} m/s "
               f"(paper states {PUBLISHED.pub_rv_err_nodding_ms if nature else PUBLISHED.rv_err_nodding_ms} m/s)")

    one = orb.fit_fixed_periods(data, (p1_one,), eccentric=True, n_starts=starts)
    typer.echo(f"\n{'model (periods fixed)':<34}{'-lnL':>9}{'BIC':>9}{'dlogZ proxy':>13}")
    typer.echo(f"{'1 satellite, eccentric':<34}{one.neg_log_like:>9.2f}{one.bic:>9.2f}"
               f"{'--':>13}   e={one.ecc:.2f} K={one.amplitudes[0]:.0f} jit={one.jitter_ms:.1f}")

    fits = {}
    for p2 in alias:
        f = orb.fit_fixed_periods(data, (p1_two, p2), n_starts=starts)
        fits[p2] = f
        typer.echo(f"{f'2 satellites, +{p2:g} d':<34}{f.neg_log_like:>9.2f}{f.bic:>9.2f}"
                   f"{orb.delta_logz_proxy(f, one):>13.2f}   K2={f.amplitudes[1]:.0f} "
                   f"jit={f.jitter_ms:.1f}")

    best = min(fits.values(), key=lambda f: f.bic)
    typer.echo(f"\nbest second period: {best.periods[1]:g} d  (paper: {p2_pub})")
    typer.echo(f"  vs 115 d : dlogZ proxy {orb.delta_logz_proxy(best, fits[115.0]):.2f}"
               + ("" if nature else f"  (paper quotes {PUBLISHED.delta_logz_88_vs_115})"))
    typer.echo(f"  vs 1-sat : dlogZ proxy {orb.delta_logz_proxy(best, one):.2f}  "
               f"(paper quotes {dlz_pub})")


@app.command()
def survey(
    threshold: str = typer.Option("hoy", help="Detection threshold: 'hoy' (calibrated) or 'lazzoni'."),
    out: str = typer.Option("m7-survey.json", help="Report filename under data/."),
) -> None:
    """M7: which directly imaged companions can the Hoy et al. method work on?"""
    from .analysis.survey import run_survey

    rows, meta = run_survey(threshold=threshold)
    typer.echo(f"Hoy-method feasibility, {len(rows)} directly imaged companions "
               f"({meta['threshold_label']})\n")
    typer.echo(f"{'companion':24s}{'M/MJup':>8s}{'K':>7s}{'sigma_RV':>10s}"
               f"{'min m_sat':>11s}{'a_stable':>10s}  verdict")
    typer.echo("-" * 92)
    for r in rows:
        typer.echo(f"{r['name']:24s}{r['m_host_mjup']:8.1f}{r['k_mag']:7.2f}"
                   f"{r['threshold_ms']:9.1f}{r['min_sat_mearth']:11.2f}"
                   f"{r['stability_au']:10.3f}  {r['verdict']}")
    typer.echo(f"\n  planet-like reachable: {meta['n_pass']}   sub-Jovian: {meta['n_marginal']}   "
               f"binary-like or out of reach: {meta['n_fail']}")
    typer.echo(f"  {meta['note']}")

    DATA.mkdir(exist_ok=True)
    path = DATA / out
    path.write_text(json.dumps({"targets": rows, "meta": meta}, indent=2), encoding="utf-8")
    typer.echo(f"\nwrote {path}")


@app.command()
def closein(
    max_age_myr: float = typer.Option(200.0, help="Age cut, Myr."),
    t_obs_hr: float = typer.Option(8.0, help="Length of one observing block, hours."),
    q_planet: float = typer.Option(1e5, help="Planetary tidal quality factor."),
    out: str = typer.Option("m8-closein.json", help="Report filename under data/."),
) -> None:
    """M8: can the method reach satellites of young close-in giants ('hot Jupiters')?"""
    from .analysis.closein import run_closein

    rows, meta = run_closein(max_age_myr=max_age_myr, t_obs_hr=t_obs_hr, q_planet=q_planet)
    typer.echo(f"Young close-in giants, age < {max_age_myr:.0f} Myr, Q_p = {q_planet:.0e}\n")
    typer.echo(f"{'planet':20s}{'age':>6s}{'a/au':>7s}{'Mp':>6s}{'spin':>6s}"
               f"{'window/dex':>11s}{'dv/kms':>8s}{'m_min/ME':>9s}  verdict")
    typer.echo("-" * 96)
    for r in rows:
        typer.echo(f"{r['name']:20s}{r['age_myr']:6.0f}{r['sma_au']:7.3f}{r['m_planet_mjup']:6.2f}"
                   f"{'sync' if r['synchronised'] else 'fast':>6s}{r['window_dex']:11.2f}"
                   f"{r['swing_kms']:8.1f}{r['min_sat_mearth']:9.1f}  {r['verdict']}")
    typer.echo(f"\n  survivable: {meta['n_survivable']}   observable: {meta['n_observable']}   "
               f"BOTH: {meta['n_both']}")
    for line in meta["conclusion"]:
        typer.echo(f"  {line}")

    DATA.mkdir(exist_ok=True)
    path = DATA / out
    path.write_text(json.dumps({"targets": rows, "meta": meta}, indent=2), encoding="utf-8")
    typer.echo(f"\nwrote {path}")


@app.command()
def orders(
    tag: str = typer.Option("full1", help="viper run tag under data/viper/."),
    out: str = typer.Option("m9-orders.json", help="Report filename under data/."),
) -> None:
    """M9: per-order screening -- and the measured ceiling on what it can buy."""
    from ._orders_cmd import run

    run(tag, out)


@app.command()
def gravity(
    out: str = typer.Option("m10-gravity.json", help="Report filename under data/."),
) -> None:
    """M10: public VLTI/GRAVITY data on the astrometric exomoon shortlist."""
    from ._gravity_cmd import run

    run(out)


if __name__ == "__main__":
    app()
