"""Command-line entry point.

    itf-linker fetch          # download the ITF snapshot + record provenance
    itf-linker parse          # 80-column text -> typed Parquet
    itf-linker counts         # observation / observatory / top-code census
    itf-linker tracklets      # reconstruct tracklets, write Parquet, print stats
    itf-linker killcheck      # replay the three July-2026 identification MPECs
    itf-linker partition      # HEALPix x night combinatorics
    itf-linker m0             # everything above, as one JSON report

    itf-linker snapshot       # archive this ITF pull for later diffing
    itf-linker snapshots      # list the archive
    itf-linker snapshot-diff  # what disappeared / appeared between two snapshots

    itf-linker fit-selftest   # verify the Find_Orb build against JPL Horizons
    itf-linker candidates     # the 3+-night designations, gated and collision-screened
    itf-linker fit            # fit the candidates and apply the MPC's post-fit gate
    itf-linker m1             # candidates + fit, as one JSON report

    itf-linker vet-extract    # pull a report's designations' 80-col lines out of the ITF
    itf-linker vet-control    # the vetting layer's own positive controls
    itf-linker vet            # cross-match candidates against MPChecker/SkyBoT/SBIDENT
    itf-linker m2             # controls + vetting, as one JSON report

    itf-linker version

Every command is read-only with respect to the outside world: the only network calls are
HTTP GETs against public MPC, IMCCE and JPL URLs, and nothing is ever submitted anywhere.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import polars as pl
import typer

from . import __version__, config
from . import snapshot as snap
from .fit.pipeline import fit_candidates, select_candidates
from .fit.wsl import default_shell
from .index.partition import add_healpix, candidate_combinatorics, partition_stats
from .index.tracklets import add_night, build_tracklets, tracklet_stats
from .ingest.fetch import fetch_itf, fetch_mpec, fetch_obscodes, load_provenance
from .ingest.parse import parse_itf, scan
from .verify.killcheck import check_mpec_against_itf, sensitivity_control
from .verify.mpec import parse_mpec

app = typer.Typer(
    add_completion=False,
    help="Mine the MPC Isolated Tracklet File for linkable minor-planet tracklets.",
)


def _echo(obj: Any) -> None:
    typer.echo(json.dumps(obj, indent=2, default=str))


def _load_observations() -> pl.DataFrame:
    if not config.ITF_PARQUET.exists():
        raise typer.BadParameter(
            f"{config.ITF_PARQUET} not found -- run `itf-linker fetch` then `itf-linker parse`."
        )
    return scan().collect()


def _load_tracklets(obs: pl.DataFrame | None = None) -> tuple[pl.DataFrame, pl.DataFrame]:
    obs = obs if obs is not None else _load_observations()
    try:
        lon = fetch_obscodes()
    except Exception as exc:  # network optional once cached; degrade loudly, not silently
        typer.echo(f"[warn] observatory longitudes unavailable ({exc}); using UTC nights", err=True)
        lon = {}
    with_night = add_night(obs.lazy(), lon)
    trk = build_tracklets(with_night).collect()
    return with_night.collect(), trk


@app.command()
def version() -> None:
    """Print the package version."""
    typer.echo(__version__)


@app.command()
def fetch(force: bool = typer.Option(False, help="Re-download even if cached.")) -> None:
    """Download the ITF snapshot and record its provenance."""
    config.ensure_dirs()
    _echo(fetch_itf(force=force))


@app.command()
def parse(
    batch_size: int = typer.Option(1_000_000, help="Lines per Parquet row group."),
) -> None:
    """Parse the ITF 80-column text into typed Parquet."""
    config.ensure_dirs()
    _echo(parse_itf(batch_size=batch_size))


@app.command()
def counts(top: int = typer.Option(10, help="How many observatory codes to list.")) -> None:
    """Census of the parsed snapshot: observations, observatory codes, top contributors."""
    df = _load_observations()
    top_codes = (
        df.group_by("obscode").agg(pl.len().alias("n")).sort("n", descending=True).head(top)
    )
    _echo(
        {
            "provenance": load_provenance(),
            "observations": df.height,
            "distinct_obscodes": int(df["obscode"].n_unique()),
            "observations_in_2026": df.filter(pl.col("year") == 2026).height,
            "top_obscodes": top_codes.to_dicts(),
            "year_min": int(df["year"].min()),
            "year_max": int(df["year"].max()),
        }
    )


@app.command()
def tracklets(write: bool = typer.Option(True, help="Write the tracklet Parquet.")) -> None:
    """Reconstruct tracklets (desig x observatory x local night) and report the distribution."""
    obs, trk = _load_tracklets()
    if write:
        config.PARQUET_DIR.mkdir(parents=True, exist_ok=True)
        trk.write_parquet(config.TRACKLET_PARQUET)
    _echo(tracklet_stats(trk, obs))


@app.command()
def killcheck(
    packed: list[str] | None = typer.Option(None, help="MPEC ids; defaults to the M0 three."),
    refresh: bool = typer.Option(False, help="Re-download the MPEC HTML."),
) -> None:
    """Replay published identification MPECs against the ITF snapshot."""
    config.ensure_dirs()
    ids = list(packed) if packed else list(config.KILL_CHECK_MPECS)
    obs, trk = _load_tracklets()
    out = {"sensitivity_control": sensitivity_control(obs), "mpecs": []}
    for pid in ids:
        path = fetch_mpec(pid, force=refresh)
        out["mpecs"].append(check_mpec_against_itf(parse_mpec(path, pid), obs, trk))
    _echo(out)


@app.command()
def partition(
    nsides: str = typer.Option("16,32,64,128", help="Comma-separated HEALPix nsides."),
    windows: str = typer.Option("3,7,15,30", help="Comma-separated temporal windows (days)."),
) -> None:
    """Measure HEALPix x night partition occupancy and candidate-pair combinatorics."""
    _, trk = _load_tracklets()
    ns = tuple(int(x) for x in nsides.split(","))
    ws = tuple(float(x) for x in windows.split(","))
    for n in ns:
        trk = add_healpix(trk, n)
    _echo(
        {
            "occupancy": [partition_stats(trk, n) for n in ns],
            "combinatorics": candidate_combinatorics(trk, nsides=ns, windows_days=ws),
        }
    )


@app.command()
def m0(out: Path | None = typer.Option(None, help="Write the JSON report here.")) -> None:
    """Run the whole M0 kill-check and emit one JSON report."""
    config.ensure_dirs()
    obs, trk = _load_tracklets()
    ns = (16, 32, 64, 128)
    for n in ns:
        trk = add_healpix(trk, n)
    top_codes = (
        obs.group_by("obscode").agg(pl.len().alias("n")).sort("n", descending=True).head(10)
    )
    report = {
        "provenance": load_provenance(),
        "counts": {
            "observations": obs.height,
            "distinct_obscodes": int(obs["obscode"].n_unique()),
            "observations_in_2026": obs.filter(pl.col("year") == 2026).height,
            "top_obscodes": top_codes.to_dicts(),
        },
        "tracklets": tracklet_stats(trk, obs),
        "killcheck": {
            "sensitivity_control": sensitivity_control(obs),
            "mpecs": [
                check_mpec_against_itf(parse_mpec(fetch_mpec(p), p), obs, trk)
                for p in config.KILL_CHECK_MPECS
            ],
        },
        "partitioning": {
            "occupancy": [partition_stats(trk, n) for n in ns],
            "combinatorics": candidate_combinatorics(trk, nsides=ns),
        },
    }
    if out:
        out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        typer.echo(f"wrote {out}")
    else:
        _echo(report)


# ----------------------------------------------------------------------------------
# M1: snapshot archive
# ----------------------------------------------------------------------------------

@app.command()
def snapshot(
    refetch: bool = typer.Option(False, help="Pull a fresh ITF before archiving."),
    raw_keep: int = typer.Option(snap.RAW_KEEP, help="Snapshots keeping their raw .gz."),
    full_keep: int = typer.Option(snap.FULL_KEEP, help="Snapshots keeping their full key set."),
    overwrite: bool = typer.Option(False, help="Rebuild if this snapshot id already exists."),
) -> None:
    """Archive the current ITF pull so future disappearances can be measured.

    Keeps a permanent, kilobyte-scale delta against the previous snapshot plus a rolling
    window of full key sets -- not 135 MB/day of near-identical text. Snapshots are named
    after the file's own Last-Modified, since the ITF is regenerated continuously.
    """
    config.ensure_dirs()
    if refetch:
        fetch_itf(force=True)
        parse_itf()
    obs, trk = _load_tracklets()
    _echo(
        snap.build_snapshot(
            obs,
            trk,
            load_provenance(),
            raw_source=config.ITF_GZ,
            raw_keep=raw_keep,
            full_keep=full_keep,
            overwrite=overwrite,
        )
    )


@app.command()
def snapshots() -> None:
    """List the archived snapshots, oldest first."""
    rows = []
    for s in snap.list_snapshots():
        m = s.manifest
        rows.append(
            {
                "snapshot_id": s.snapshot_id,
                "last_modified": (m.get("provenance") or {}).get("last_modified"),
                "observations": m.get("observations"),
                "designations": m.get("designations"),
                "delta": m.get("delta"),
                "has_full_key_set": s.has_full,
                "has_raw": s.has_raw,
                "megabytes_on_disk": round(
                    sum(f.stat().st_size for f in s.path.iterdir() if f.is_file()) / 1e6, 2
                ),
            }
        )
    _echo({"root": str(snap.snapshot_root()), "count": len(rows), "snapshots": rows})


@app.command("snapshot-diff")
def snapshot_diff(
    earlier: str = typer.Argument(..., help="Earlier snapshot id (or 'first')."),
    later: str = typer.Argument(..., help="Later snapshot id (or 'last')."),
    sample: int = typer.Option(20, help="How many changed designations to list."),
) -> None:
    """Report which observations disappeared from (and appeared in) the ITF between two pulls."""
    snaps = {s.snapshot_id: s for s in snap.list_snapshots()}
    ordered = sorted(snaps)
    if not ordered:
        raise typer.BadParameter("no snapshots archived yet -- run `itf-linker snapshot`")
    resolve = {"first": ordered[0], "last": ordered[-1]}
    a, b = resolve.get(earlier, earlier), resolve.get(later, later)
    for sid in (a, b):
        if sid not in snaps:
            raise typer.BadParameter(f"unknown snapshot {sid!r}; have {ordered}")
    _echo(snap.diff(snaps[a], snaps[b], sample=sample))


# ----------------------------------------------------------------------------------
# M1: fitting
# ----------------------------------------------------------------------------------

@app.command("fit-selftest")
def fit_selftest(
    workdir: Path = typer.Option(Path("data/selftest"), help="Where to run the fits."),
    out: Path | None = typer.Option(None, help="Write the JSON report here."),
    wide: bool = typer.Option(True, help="Also run the 49-day-arc cadence."),
) -> None:
    """Verify the Find_Orb build end-to-end against JPL Horizons. Read-only network use."""
    from .fit.verify import run_selftest

    report = run_selftest(workdir, include_wide=wide)
    if out:
        out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        typer.echo(f"wrote {out}")
    typer.echo(
        f"{report['n_passed']}/{report['n_cases']} cases passed"
        + ("" if report["all_passed"] else f"  failures: {report['failures']}")
    )


def _candidates() -> Any:
    obs = _load_observations()
    try:
        lon = fetch_obscodes()
    except Exception as exc:  # network optional once cached; degrade loudly
        typer.echo(f"[warn] observatory longitudes unavailable ({exc}); using UTC nights", err=True)
        lon = {}
    return select_candidates(obs, lon)


@app.command()
def candidates(
    out: Path | None = typer.Option(None, help="Write the candidate table (Parquet) here."),
    show: int = typer.Option(0, help="Print this many candidate rows."),
) -> None:
    """Select the 3+-night designations that survive the pre-fit gate and collision screen."""
    cand = _candidates()
    if out:
        cand.table.write_parquet(out)
    payload = dict(cand.report)
    if show:
        payload["sample"] = cand.table.head(show).to_dicts()
    _echo(payload)


@app.command("fit")
def fit_cmd(
    workdir: Path = typer.Option(Path("data/fits"), help="Where fo runs and writes output."),
    out: Path | None = typer.Option(None, help="Write the JSON report here."),
    workers: int = typer.Option(8, help="Concurrent fo processes."),
    chunk_size: int = typer.Option(48, help="Designations per fo invocation."),
    limit: int | None = typer.Option(None, help="Fit only the first N candidates."),
) -> None:
    """Fit the candidate designations with Find_Orb and apply the MPC's post-fit gate.

    Produces designations with acceptable orbit fits. NOT discoveries -- catalogue
    cross-matching is M2.
    """
    shell = default_shell()
    if not shell.available():
        raise typer.BadParameter(
            f"Find_Orb not reachable at {shell.fo_path} -- see DATA-SOURCES.md 'Find_Orb build'"
        )
    cand = _candidates()
    report = fit_candidates(
        cand, workdir, workers=workers, chunk_size=chunk_size, limit=limit, shell=shell
    )
    report["candidate_selection"] = cand.report
    report["find_orb"] = shell.version()
    if out:
        out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        typer.echo(f"wrote {out}")
    else:
        _echo({k: v for k, v in report.items() if k != "outcomes"})


@app.command()
def m1(
    out: Path | None = typer.Option(None, help="Write the JSON report here."),
    workdir: Path = typer.Option(Path("data/fits"), help="Where fo runs and writes output."),
    workers: int = typer.Option(8, help="Concurrent fo processes."),
) -> None:
    """Run the whole M1 chain -- snapshot, candidates, fits, gates -- as one JSON report."""
    config.ensure_dirs()
    shell = default_shell()
    obs, trk = _load_tracklets()
    manifest = snap.build_snapshot(obs, trk, load_provenance(), raw_source=config.ITF_GZ)
    cand = _candidates()
    report: dict[str, Any] = {
        "provenance": load_provenance(),
        "snapshot": manifest,
        "find_orb": shell.version(),
        "candidate_selection": cand.report,
    }
    if shell.available():
        report["fits"] = fit_candidates(cand, workdir, workers=workers, shell=shell)
    else:
        report["fits"] = {"skipped": f"Find_Orb not reachable at {shell.fo_path}"}
    if out:
        out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        typer.echo(f"wrote {out}")
    else:
        _echo(report)


# --- M2: vetting ------------------------------------------------------------------
#
# Nothing below submits anything. Every call is a rate-limited, disk-cached, read-only GET.


@app.command("vet-extract")
def vet_extract(
    report: Path = typer.Option(Path("m1-report.json"), help="An M1-shaped report."),
    section: str = typer.Option("ranked", help="Which section's designations to extract."),
    out: Path = typer.Option(config.VET_ASTROMETRY, help="Write the 80-column lines here."),
    also: list[str] = typer.Option([], help="Extra designations to include (e.g. controls)."),
) -> None:
    """Pull each designation's ORIGINAL 80-column lines back out of the ITF snapshot.

    The parsed Parquet cannot be turned back into faithful 80-column text, so this is a
    streaming pass over ``itf.txt.gz`` -- a few seconds, and exact by construction.
    """
    from .fit.extract import extract_lines

    blob = json.loads(report.read_text(encoding="utf-8"))
    desigs = [row["desig"] for row in blob["fits"][section]] + list(also)
    groups, stats = extract_lines(desigs)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps({"stats": stats, "lines": {k: v for k, v in groups.items() if v}}, indent=1),
        encoding="utf-8",
    )
    _echo({"wrote": str(out), **stats})


def _session(
    cache: Path,
    min_interval: float,
    offline: bool,
    *,
    max_retries: int = 2,
    backoff: float = 3.0,
) -> Any:
    from .vet import CachedSession

    return CachedSession(
        cache,
        min_interval_s=min_interval,
        offline=offline,
        max_retries=max_retries,
        backoff_base_s=backoff,
    )


def _require_vet_inputs(report: Path, astrometry: Path) -> None:
    """Fail with something actionable rather than a stack trace three frames down."""
    if not report.exists():
        raise typer.BadParameter(f"{report} not found -- run `itf-linker m1 --out {report}`.")
    if not astrometry.exists():
        raise typer.BadParameter(
            f"{astrometry} not found -- run `itf-linker vet-extract` to pull the "
            "80-column astrometry out of the ITF snapshot."
        )


@app.command("vet-control")
def vet_control(
    astrometry: Path = typer.Option(config.VET_ASTROMETRY, help="vet-extract output."),
    cache: Path = typer.Option(config.VET_CACHE_DIR, help="Response cache directory."),
    out: Path | None = typer.Option(None, help="Write the JSON report here."),
    min_interval: float = typer.Option(1.0, help="Minimum seconds between requests."),
    offline: bool = typer.Option(False, help="Use only cached responses; never hit a service."),
    skip_numbered: bool = typer.Option(False, help="Skip the Horizons numbered-object control."),
) -> None:
    """Run the vetting layer's positive controls -- objects whose answer is known in advance."""
    from .vet.controls import run_controls

    report = run_controls(
        _session(cache, min_interval, offline),
        astrometry_path=astrometry,
        include_numbered=not skip_numbered,
    )
    if out:
        out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        typer.echo(f"wrote {out}")
    _echo(report["summary"])


@app.command("vet")
def vet_cmd(
    report: Path = typer.Option(Path("m1-report.json"), help="An M1-shaped report."),
    astrometry: Path = typer.Option(config.VET_ASTROMETRY, help="vet-extract output."),
    section: str = typer.Option("ranked", help="Which section of the report to vet."),
    cache: Path = typer.Option(config.VET_CACHE_DIR, help="Response cache directory."),
    out: Path | None = typer.Option(None, help="Write the JSON report here."),
    limit: int | None = typer.Option(None, help="Vet only the first N candidates."),
    min_interval: float = typer.Option(1.0, help="Minimum seconds between requests."),
    max_epochs: int = typer.Option(3, help="Nights sampled per candidate."),
    no_sbident: bool = typer.Option(False, help="Skip JPL SBIDENT entirely."),
    offline: bool = typer.Option(False, help="Use only cached responses; never hit a service."),
    max_retries: int = typer.Option(2, help="Attempts beyond the first, per request."),
    backoff: float = typer.Option(3.0, help="Base seconds for exponential backoff."),
) -> None:
    """Cross-match fitted candidates against MPChecker, SkyBoT and JPL SBIDENT.

    Produces an identification verdict per candidate. A verdict of ``unmatched`` means
    exactly that -- it is NOT a claim that the object is new.
    """
    from .vet import from_m1_report, vet_candidates

    _require_vet_inputs(report, astrometry)
    candidates = from_m1_report(report, astrometry, section=section, limit=limit)
    if not candidates:
        raise typer.BadParameter(
            f"no candidates with astrometry -- run `itf-linker vet-extract --section {section}`"
        )

    def progress(i: int, n: int, verdict: Any) -> None:
        typer.echo(
            f"[{i}/{n}] {verdict.desig}: {verdict.category}"
            + (f" -> {verdict.identified_as}" if verdict.identified_as else ""),
            err=True,
        )

    result = vet_candidates(
        _session(cache, min_interval, offline, max_retries=max_retries, backoff=backoff),
        candidates,
        max_epochs=max_epochs,
        use_sbident=not no_sbident,
        progress=progress,
    )
    if out:
        out.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        typer.echo(f"wrote {out}")
    _echo({k: v for k, v in result.items() if k not in ("verdicts", "resolved_objects")})


@app.command()
def m2(
    report: Path = typer.Option(Path("m1-report.json"), help="An M1-shaped report."),
    astrometry: Path = typer.Option(config.VET_ASTROMETRY, help="vet-extract output."),
    cache: Path = typer.Option(config.VET_CACHE_DIR, help="Response cache directory."),
    out: Path | None = typer.Option(None, help="Write the JSON report here."),
    min_interval: float = typer.Option(1.0, help="Minimum seconds between requests."),
    offline: bool = typer.Option(False, help="Use only cached responses; never hit a service."),
) -> None:
    """Controls first, then the full vetting pass, as one JSON report.

    The controls run **first and are reported first** on purpose: a vetting layer that
    cannot identify an object whose identity is already known has nothing useful to say
    about one whose identity is not.
    """
    from .vet import from_m1_report, vet_candidates
    from .vet.controls import run_controls

    _require_vet_inputs(report, astrometry)
    session = _session(cache, min_interval, offline)
    controls = run_controls(session, astrometry_path=astrometry)
    candidates = from_m1_report(report, astrometry)

    def progress(i: int, n: int, verdict: Any) -> None:
        typer.echo(f"[{i}/{n}] {verdict.desig}: {verdict.category}", err=True)

    result = {
        "provenance": load_provenance(),
        "controls": controls,
        "vetting": vet_candidates(session, candidates, progress=progress),
    }
    if out:
        out.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        typer.echo(f"wrote {out}")
    else:
        _echo(
            {
                "controls": controls["summary"],
                "tally": result["vetting"]["tally"],
                "http": result["vetting"]["http"],
            }
        )


if __name__ == "__main__":  # pragma: no cover
    app()
