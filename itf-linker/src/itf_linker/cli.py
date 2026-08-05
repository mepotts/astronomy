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

    itf-linker link             # HelioLinC over a slice: propose links nobody has made
    itf-linker link-validate    # hide the trkSub linkage and measure recall/precision
    itf-linker link-populations # re-link real NEOs/Centaurs/TNOs from Horizons astrometry
    itf-linker link-fit         # fit saved links without repeating the search
    itf-linker m3               # link + gate + fit + rank, as one JSON report

``m3``, ``link``, ``link-validate`` and ``link-populations`` all take ``--bands``:
``belt`` is M3's single 1.4-5.6 AU grid and ``wide`` is M4's four-band 0.55-50 AU set,
which reaches NEOs, Centaurs and TNOs. ``--mjd-max 60000`` runs the older 80% of the file.

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


# --- M3: linking ------------------------------------------------------------------
#
# Nothing below submits anything either. The only network use is the (cached) observatory
# table; the linking itself is pure local computation over the snapshot.


def _obscodes_full() -> Any:
    from .ingest.fetch import fetch_obscodes_full

    try:
        return fetch_obscodes_full()
    except Exception as exc:
        raise typer.BadParameter(
            f"observatory parallax constants unavailable ({exc}); M3 cannot place observers"
        ) from exc


def _link_inputs() -> tuple[pl.DataFrame, dict[str, float], dict[str, tuple[float, float, float]]]:
    from .fit.candidates import bad_data_filter
    from .index.tracklets import add_night

    obs = _load_observations()
    filtered, stats = bad_data_filter(obs.lazy())
    try:
        lon = fetch_obscodes()
    except Exception as exc:
        typer.echo(f"[warn] observatory longitudes unavailable ({exc}); using UTC nights", err=True)
        lon = {}
    typer.echo(f"[bad-data filter] {stats}", err=True)
    return add_night(filtered, lon).collect(), lon, _obscodes_full()


def _grid(r_min: float, r_max: float, r_step: float, n_rdot: int) -> Any:
    from .link.heliolinc import HypothesisGrid

    return HypothesisGrid.build(r_min=r_min, r_max=r_max, r_step=r_step, n_rdot=n_rdot)


#: Bands searched when ``--bands wide`` is given, best-yield-first for fitting. NEO and
#: outer distances are fitted before the main belt because the belt is the population every
#: all-sky survey re-detects constantly, and M3 already searched it.
WIDE_FIT_ORDER = ("neo", "inner", "outer", "belt")


def _bands(kind: str, r_step: float, n_rdot: int, radius: float) -> Any:
    """``belt`` is M3's single band unchanged; ``wide`` is M4's 0.55-50 AU set."""
    from .link.pipeline import belt_band, wide_bands

    if kind == "belt":
        return [belt_band(r_step=r_step, n_rdot=n_rdot)]
    if kind == "wide":
        return wide_bands(r_step=r_step, n_rdot=n_rdot, radius_au=radius)
    if kind == "wide-no-inner":
        return wide_bands(
            r_step=r_step, n_rdot=n_rdot, radius_au=radius, include_inner=False
        )
    raise typer.BadParameter(f"unknown band set {kind!r}; use belt, wide or wide-no-inner")


@app.command("link")
def link_cmd(
    out: Path | None = typer.Option(None, help="Write the JSON link report here."),
    mjd_min: float = typer.Option(60000.0, help="Start of the slice (M0's recommended sandbox)."),
    mjd_max: float | None = typer.Option(None, help="End of the slice."),
    window_days: float = typer.Option(14.0, help="Length of each linking window."),
    step_days: float = typer.Option(3.5, help="Spacing between window starts."),
    radius: float = typer.Option(0.0025, help="Six-dimensional clustering radius, AU."),
    r_min: float = typer.Option(1.4, help="Smallest heliocentric distance hypothesis, AU."),
    r_max: float = typer.Option(5.6, help="Largest heliocentric distance hypothesis, AU."),
    r_step: float = typer.Option(0.10, help="Spacing of the distance grid, AU."),
    n_rdot: int = typer.Option(9, help="Radial-velocity samples per distance."),
    link_workers: int = typer.Option(1, help="Processes sweeping windows in parallel."),
    show: int = typer.Option(10, help="Print this many ranked links."),
    bands: str | None = typer.Option(
        None, help="Sweep a band set ('belt' / 'wide') instead of one r_min..r_max grid."
    ),
) -> None:
    """Propose links between tracklets nobody has connected, over a slice of the ITF.

    Cross-observatory links rank first: individual surveys already link their own data, so
    a link joining two observatory codes is the part nobody else is positioned to do.
    **A proposed link is not an object** -- it has not been fitted or vetted here.
    """
    from .link.arrows import build_arrows
    from .link.pipeline import link_bands, link_slice

    observations, _, full = _link_inputs()

    def progress(i: int, n: int, stats: dict[str, Any]) -> None:
        if i % 10 == 0 or stats["candidates"]:
            typer.echo(
                f"[window {i}/{n}] arrows={stats['arrows']} candidates={stats['candidates']}",
                err=True,
            )

    if bands:
        arrows = build_arrows(observations, full, mjd_min=mjd_min, mjd_max=mjd_max)
        links, report = link_bands(
            arrows, _bands(bands, r_step, n_rdot, radius), radius_au=radius,
            link_workers=link_workers, progress=progress,
        )
        report["arrow_build"] = arrows.stats
        report["slice"] = {"mjd_min": mjd_min, "mjd_max": mjd_max}
    else:
        links, report = link_slice(
            observations, full, mjd_min=mjd_min, mjd_max=mjd_max,
            grid=_grid(r_min, r_max, r_step, n_rdot),
            window_days=window_days, window_step_days=step_days, radius_au=radius,
            link_workers=link_workers, progress=progress,
        )
    payload = dict(report)
    payload["links"] = [c.as_dict() for c in links]
    if out:
        out.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        typer.echo(f"wrote {out}")
    _echo({k: v for k, v in report.items() if k != "busiest_windows"})
    for cand in links[:show]:
        typer.echo(
            f"  {'+'.join(cand.obscodes):16s} nights={cand.n_nights} "
            f"arc={cand.arc_days:6.2f} d  trkSubs={','.join(cand.desigs)}"
        )


def _score_embedded(
    links_path: Path,
    obscodes_full: dict[str, tuple[float, float, float]],
    observations: pl.DataFrame,
    window_days: float,
    mjd_min: float,
    mjd_max: float | None = None,
) -> dict[str, Any]:
    """Score a production link set against the ground truth *inside* the full population.

    The isolated run measures the algorithm; this measures the algorithm plus the
    confusion. Both the raw proposals and the subset that passes the MPC's pre-fit gate are
    scored, because a truth group with a 2-day arc is rejected by the gate and its
    non-recovery is not the linker's failure.
    """
    from .link.arrows import build_arrows
    from .link.heliolinc import LinkCandidate
    from .link.validate import collision_screen, ground_truth_groups, score_links

    arrows = build_arrows(observations, obscodes_full, mjd_min=mjd_min, mjd_max=mjd_max)
    truth = ground_truth_groups(arrows.table, min_nights=3, max_arc_days=window_days)
    suspects = collision_screen(arrows.table, set(truth))
    clean = {k: v for k, v in truth.items() if k not in suspects}

    frame = pl.read_parquet(links_path)

    def as_candidates(sub: pl.DataFrame) -> list[LinkCandidate]:
        return [
            LinkCandidate(
                arrow_ids=tuple(int(i) for i in r["arrow_ids"]),
                n_nights=int(r["n_nights"]), n_obscodes=int(r["n_obscodes"]),
                obscodes=tuple(r["obscodes"]), desigs=tuple(r["source_desigs"]),
                n_obs=int(r["n_obs"]), arc_days=float(r["arc_days"]),
                mjd_first=float(r["first_mjd"]), mjd_last=float(r["last_mjd"]),
                first_trk_n_obs=int(r["first_trk_n_obs"]),
                last_trk_n_obs=int(r["last_trk_n_obs"]),
                min_trk_n_obs=int(r["min_trk_n_obs"]),
                r_au=float(r["r_au"]), rdot=0.0,
                pos_spread_au=float(r["pos_spread_au"]),
                vel_spread_au_per_day=float(r["vel_spread_au_per_day"]),
            )
            for r in sub.to_dicts()
        ]

    return {
        "arrows": len(arrows),
        "reachable_groups": len(truth),
        "collision_screened_groups": len(clean),
        "all_proposals": score_links(as_candidates(frame), clean),
        "after_the_prefit_gate": score_links(
            as_candidates(frame.filter(pl.col("link_pass"))), clean
        ),
    }


@app.command("link-populations")
def link_populations(
    out: Path | None = typer.Option(None, help="Write the JSON report here."),
    bands: str = typer.Option("wide", help="Band set to test: 'belt' or 'wide'."),
    radius: float = typer.Option(0.0025, help="Six-dimensional clustering radius, AU."),
    r_step: float = typer.Option(0.10, help="Spacing of the main-belt distance grid, AU."),
    n_rdot: int = typer.Option(9, help="Radial-velocity samples per distance."),
    link_workers: int = typer.Option(1, help="Processes sweeping windows in parallel."),
    distances: bool = typer.Option(True, help="Also ask Horizons for each object's r."),
) -> None:
    """Re-link *real* NEOs, Centaurs and TNOs from JPL Horizons astrometry alone.

    This is the measurement behind M4's claim that widening the distance grid reaches
    populations M3 could not: run it with ``--bands belt`` and the NEO and TNO targets are
    not recovered; run it with ``--bands wide`` and they are. Read-only network use.
    """
    from .link.populations import run_population_check

    full = _obscodes_full()
    report = run_population_check(
        _bands(bands, r_step, n_rdot, radius), full,
        radius_au=radius, link_workers=link_workers, with_distances=distances,
    )
    report["band_set"] = bands
    if out:
        out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        typer.echo(f"wrote {out}")
    for desig, row in report["by_target"].items():
        verdict = (
            "exact" if row["recovered_exactly"]
            else "partial" if row["recovered_partially"]
            else "MIXED" if row["mixed_with_other_targets"]
            else "missed"
        )
        typer.echo(
            f"  {desig:8s} {row['label']:20s} {row['population']:14s} "
            f"r={row.get('r_helio_au') or float('nan'):7.2f} AU  "
            f"nights={row['nights']} arc={row['arc_days']:6.2f}  {verdict:8s} "
            f"expect={row.get('expected_band')} found={row['found_in_band']} "
            f"r_hyp={row['hypothesis_r_au']} near={row['hypothesis_near_branch']}"
        )
    _echo(
        {
            k: v for k, v in report.items()
            if k not in ("by_target", "linking", "arrow_build")
        }
    )


@app.command("link-validate")
def link_validate(
    out: Path | None = typer.Option(None, help="Write the JSON report here."),
    window_days: float = typer.Option(14.0, help="Length of each linking window."),
    step_days: float = typer.Option(3.5, help="Spacing between window starts."),
    radius: float = typer.Option(0.0025, help="Six-dimensional clustering radius, AU."),
    r_step: float = typer.Option(0.10, help="Spacing of the distance grid, AU."),
    n_rdot: int = typer.Option(9, help="Radial-velocity samples per distance."),
    link_workers: int = typer.Option(1, help="Processes sweeping windows in parallel."),
    embedded_links: Path | None = typer.Option(
        None,
        help="Also score a saved production link set (data/link-candidates.parquet) "
        "against the ground truth inside the full population.",
    ),
    embedded_mjd_min: float = typer.Option(60000.0, help="Slice those links were built on."),
    embedded_mjd_max: float | None = typer.Option(None, help="End of that slice."),
    bands: str | None = typer.Option(
        None,
        help="Score a band set ('belt' / 'wide') instead of M3's single 1.4-5.6 AU grid. "
        "'wide' is the run that answers whether widening costs main-belt recall.",
    ),
    embedded_max_arc_days: float | None = typer.Option(
        None, help="Arc a truth group must fit inside; defaults to the widest band window."
    ),
) -> None:
    """Hide the trkSub linkage on the ITF's own 3+-night designations and re-derive it.

    This is the ground truth M0 called for after establishing that re-deriving a published
    identification MPEC cannot work -- the ITF contains zero designated objects, so those
    MPECs' observations were never in the file.

    The default run is **isolated**: only the ground-truth designations' own tracklets are
    present, which measures the algorithm. ``--embedded-links`` additionally scores a saved
    production link set, where the same groupings are buried among half a million other
    tracklets -- that is the number that matters operationally, and it is lower.
    """
    from .link.arrows import build_arrows
    from .link.pipeline import link_arrows, link_bands
    from .link.validate import collision_screen, ground_truth_groups, score_links

    observations, _, full = _link_inputs()
    trk = build_tracklets(observations.lazy()).collect()
    per = trk.group_by("desig").agg(pl.col("night").n_unique().alias("nights"))
    multi = set(per.filter(pl.col("nights") >= 3)["desig"].to_list())
    typer.echo(f"[ground truth] {len(multi)} designations span 3+ nights", err=True)

    band_set = _bands(bands, r_step, n_rdot, radius) if bands else None
    # A truth group is reachable if its arc fits inside *some* band's window, so the
    # reachability cut has to use the longest window actually swept -- scoring a 20-day
    # group against a 14-day figure would understate the widened grid.
    arc_cut = (
        embedded_max_arc_days
        if embedded_max_arc_days is not None
        else (max(b.window_days for b in band_set) if band_set else window_days)
    )

    arrows = build_arrows(observations.filter(pl.col("desig").is_in(multi)), full)
    truth_all = ground_truth_groups(arrows.table, min_nights=3)
    truth_win = ground_truth_groups(arrows.table, min_nights=3, max_arc_days=arc_cut)
    suspects = collision_screen(arrows.table, set(truth_all))
    clean = {k: v for k, v in truth_win.items() if k not in suspects}

    if band_set is not None:
        links, link_report = link_bands(
            arrows, band_set, radius_au=radius, link_workers=link_workers
        )
    else:
        links, link_report = link_arrows(
            arrows, grid=_grid(1.4, 5.6, r_step, n_rdot),
            window_days=window_days, window_step_days=step_days, radius_au=radius,
            link_workers=link_workers,
        )
    report = {
        "arc_cut_days": arc_cut,
        "population": {
            "designations_with_3plus_nights": len(multi),
            "surviving_arrow_construction": len(truth_all),
            "arc_within_one_window": len(truth_win),
            "flagged_as_trksub_collisions_by_m1": len(suspects),
            "clean_and_reachable": len(clean),
            "arrow_build": arrows.stats,
        },
        "linking": {k: v for k, v in link_report.items() if k != "busiest_windows"},
        "against_all_reachable_groups": score_links(links, truth_win),
        "against_collision_screened_groups": score_links(links, clean),
    }
    if embedded_links is not None:
        report["embedded"] = _score_embedded(
            embedded_links, full, observations, arc_cut, embedded_mjd_min, embedded_mjd_max
        )
    if out:
        out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        typer.echo(f"wrote {out}")
    _echo(report)


@app.command("link-fit")
def link_fit(
    links: Path = typer.Option(
        Path("data/link-candidates.parquet"), help="Gated links saved by `m3`."
    ),
    out: Path | None = typer.Option(None, help="Write the JSON report here."),
    workdir: Path = typer.Option(Path("data/link-fits"), help="Where fo runs."),
    astrometry: Path = typer.Option(
        config.VET_ASTROMETRY_LINKS, help="Write the links' 80-column lines here."
    ),
    mjd_min: float = typer.Option(60000.0, help="Slice the arrows were built from."),
    mjd_max: float | None = typer.Option(None, help="Slice the arrows were built from."),
    workers: int = typer.Option(8, help="Concurrent fo processes."),
    limit: int | None = typer.Option(None, help="Fit only the first N gated links."),
    resume: bool = typer.Option(
        False, help="Reuse chunk directories a previous run already completed."
    ),
    completed_only: bool = typer.Option(
        False,
        help="With --resume: report the chunks already finished and run nothing. Turns an "
        "unfinishable fit into an honest sample rather than a total loss.",
    ),
) -> None:
    """Fit links saved by a previous `m3` run, without repeating the linking.

    Linking takes tens of minutes and fitting takes hours, so re-running the fit -- with a
    different worker count, or after an interruption -- must not have to redo the search.
    """
    from .link.arrows import build_arrows
    from .link.run import fit_links, prioritise_bands

    shell = default_shell()
    if not shell.available():
        raise typer.BadParameter(f"Find_Orb not reachable at {shell.fo_path}")
    if not links.exists():
        raise typer.BadParameter(f"{links} not found -- run `itf-linker m3` first.")

    observations, lon, full = _link_inputs()
    arrows = build_arrows(observations, full, mjd_min=mjd_min, mjd_max=mjd_max)
    gated = prioritise_bands(
        pl.read_parquet(links).filter(pl.col("link_pass")), WIDE_FIT_ORDER
    ).sort(
        ["band_priority", "cross_observatory", "cross_designation",
         "n_nights", "pos_spread_au"],
        descending=[False, True, True, True, False],
    )
    typer.echo(f"[link-fit] {gated.height} gated links, {len(arrows)} arrows", err=True)

    def fit_progress(i: int, n: int, _results: Any) -> None:
        typer.echo(f"[fit chunk {i + 1}/{n}]", err=True)

    report = fit_links(
        gated, arrows.table, lon, workdir, shell=shell, workers=workers,
        limit=limit, resume=resume or completed_only, completed_only=completed_only,
        astrometry_out=astrometry, progress=fit_progress,
    )
    payload = {"provenance": load_provenance(), "find_orb": shell.version(), "fits": report}
    if out:
        out.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        typer.echo(f"wrote {out}")
    _echo({k: v for k, v in report.items() if k not in ("ranked", "outcomes", "conflicted")})


@app.command()
def m3(
    out: Path | None = typer.Option(None, help="Write the JSON report here."),
    workdir: Path = typer.Option(Path("data/link-fits"), help="Where fo runs."),
    astrometry: Path = typer.Option(
        config.VET_ASTROMETRY_LINKS, help="Write the links' 80-column lines here."
    ),
    mjd_min: float = typer.Option(60000.0, help="Start of the slice."),
    mjd_max: float | None = typer.Option(None, help="End of the slice."),
    window_days: float = typer.Option(14.0, help="Length of each linking window."),
    step_days: float = typer.Option(3.5, help="Spacing between window starts."),
    radius: float = typer.Option(0.0025, help="Six-dimensional clustering radius, AU."),
    r_step: float = typer.Option(0.10, help="Spacing of the distance grid, AU."),
    n_rdot: int = typer.Option(9, help="Radial-velocity samples per distance."),
    workers: int = typer.Option(8, help="Concurrent fo processes."),
    link_workers: int = typer.Option(1, help="Processes sweeping windows in parallel."),
    fit_limit: int | None = typer.Option(None, help="Fit only the first N gated links."),
    fit_resume: bool = typer.Option(
        False, help="Reuse fo chunk directories a previous run already completed."
    ),
    links_out: Path = typer.Option(
        Path("data/link-candidates.parquet"), help="Save the gated links before fitting."
    ),
    bands: str = typer.Option(
        "belt",
        help="Distance bands: 'belt' is M3's 1.4-5.6 AU grid; 'wide' adds NEO (0.55-1.45) "
        "and Centaur/TNO (5.6-50) bands, each with the window its own curvature allows.",
    ),
) -> None:
    """Link, gate, fit, gate again and rank -- the whole M3 chain as one JSON report.

    Produces **linked candidates surviving gates**, ranked cross-observatory first. Not
    discoveries: catalogue vetting is a separate step (``itf-linker vet``), and even a
    vetted survivor is only a candidate that has not been ruled out.
    """
    from .link.run import run_m3

    observations, lon, full = _link_inputs()
    shell = default_shell()

    def link_progress(i: int, n: int, stats: dict[str, Any]) -> None:
        if i % 10 == 0 or stats["candidates"]:
            typer.echo(
                f"[window {i}/{n}] arrows={stats['arrows']} candidates={stats['candidates']}",
                err=True,
            )

    def fit_progress(i: int, n: int, _results: Any) -> None:
        typer.echo(f"[fit chunk {i + 1}/{n}]", err=True)

    def band_progress(label: str, stats: dict[str, Any]) -> None:
        typer.echo(
            f"[band {label}] windows={stats.get('windows_run')} "
            f"candidates={stats.get('candidates_this_band')} "
            f"elapsed={stats.get('elapsed_s')}s",
            err=True,
        )

    band_set = _bands(bands, r_step, n_rdot, radius)
    common: dict[str, Any] = {
        "workroot": workdir, "mjd_min": mjd_min, "mjd_max": mjd_max,
        "shell": shell, "workers": workers, "fit_limit": fit_limit,
        "fit_resume": fit_resume, "astrometry_out": astrometry, "links_out": links_out,
        "radius_au": radius, "link_workers": link_workers,
        "link_progress": link_progress, "fit_progress": fit_progress,
    }
    if bands == "belt" and window_days == 14.0 and step_days == 3.5:
        # M3's exact call path, so `--bands belt` reproduces M3 rather than merely
        # resembling it.
        report, _links = run_m3(
            observations, lon, full, grid=_grid(1.4, 5.6, r_step, n_rdot),
            window_days=window_days, window_step_days=step_days, **common,
        )
    else:
        report, _links = run_m3(
            observations, lon, full, bands=band_set,
            band_progress=band_progress, fit_order=WIDE_FIT_ORDER, **common,
        )
    report["provenance"] = load_provenance()
    if out:
        out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        typer.echo(f"wrote {out}")
    fits = report.get("fits", {})
    _echo(
        {
            "linking": {k: v for k, v in report["linking"].items() if k != "busiest_windows"},
            "link_gate": report["link_gate"],
            "fits": {k: v for k, v in fits.items() if k not in ("ranked", "outcomes", "conflicted")},
        }
    )


if __name__ == "__main__":  # pragma: no cover
    app()
