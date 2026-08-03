"""Run Find_Orb's console binary ``fo`` and parse what it produces.

``fo`` is driven entirely by files: it reads MPC 80-column astrometry and writes its
results into the directory given by ``-O``. The three outputs that matter here are

``total.json``
    Merged, machine-readable elements for **every** object in the input, including the
    per-element sigmas and the per-observation residual table. This is the primary source.
``covar.json``
    The 6x6 covariance of the fitted state vector plus the state vector and its epoch.
    Written once per run, so it is only meaningful for single-object runs.
``elements.txt``
    Human-readable elements. Parsed only for the provenance line recording which
    perturbers and which JPL ephemeris were actually used -- a detail that silently
    changes the answer and is not in the JSON.

Two ``fo`` behaviours drive the design here:

* it rewrites ``environ.dat`` **inside its configuration directory** on every run, so
  concurrent runs sharing one config directory race. Each worker therefore gets its own
  config directory of symlinks (:func:`prepare_config_dir`).
* its own ``-p`` multi-process mode leaves ``total.json`` unmerged (header only, no
  objects). Parallelism is done here instead, by splitting designations across
  single-process ``fo`` invocations.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .wsl import Shell, default_shell, shq, shq_expand

#: Elements Find_Orb reports, mapped to the attribute names used here.
_ELEMENT_KEYS = {
    "a": "a",
    "e": "e",
    "i": "incl",
    "q": "q",
    "Q": "aphelion",
    "arg_per": "arg_per",
    "asc_node": "asc_node",
    "M": "mean_anom",
    "n": "mean_motion",
    "P": "period_days",
    "Tp": "tp_jd",
    "H": "h_mag",
    "G": "g_slope",
    "U": "u_param",
}

#: The four sigmas the MPC's published criteria test, plus the ones useful for ranking.
_SIGMA_KEYS = {
    "a sigma": "sigma_a",
    "e sigma": "sigma_e",
    "i sigma": "sigma_i",
    "q sigma": "sigma_q",
    "Q sigma": "sigma_Q",
    "M sigma": "sigma_M",
    "n sigma": "sigma_n",
    "arg_per sigma": "sigma_arg_per",
    "asc_node sigma": "sigma_asc_node",
    "Tp sigma": "sigma_tp",
}

_PERTURBER_RE = re.compile(r"^# Perturbers:\s*(\S+)\s*\(([^)]*)\)(?:;\s*(.*))?$", re.MULTILINE)


def _f(value: Any) -> float | None:
    """Coerce to a finite float, or None. Find_Orb emits NaN and huge sentinels freely."""
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


@dataclass(slots=True)
class FitResult:
    """One object's orbit solution, or the reason there isn't one."""

    desig: str
    converged: bool = False
    status: str = "no_solution"
    fo_object_name: str | None = None
    packed: str | None = None

    n_obs: int | None = None
    n_used: int | None = None
    n_resids: int | None = None
    first_jd: float | None = None
    last_jd: float | None = None

    epoch_jd: float | None = None
    central_body: str | None = None
    frame: str | None = None

    a: float | None = None
    e: float | None = None
    incl: float | None = None
    q: float | None = None
    aphelion: float | None = None
    arg_per: float | None = None
    asc_node: float | None = None
    mean_anom: float | None = None
    mean_motion: float | None = None
    period_days: float | None = None
    tp_jd: float | None = None
    h_mag: float | None = None
    g_slope: float | None = None
    u_param: float | None = None

    sigma_a: float | None = None
    sigma_e: float | None = None
    sigma_i: float | None = None
    sigma_q: float | None = None
    sigma_Q: float | None = None
    sigma_M: float | None = None
    sigma_n: float | None = None
    sigma_arg_per: float | None = None
    sigma_asc_node: float | None = None
    sigma_tp: float | None = None

    rms_residual: float | None = None
    weighted_rms: float | None = None
    max_residual: float | None = None
    moid_earth: float | None = None

    perturbers: str | None = None
    perturbers_label: str | None = None
    jpl_ephemeris: str | None = None
    covariance: list[list[float]] | None = None
    state_vector: list[float] | None = None
    residuals: list[dict[str, Any]] = field(default_factory=list)

    @property
    def arc_days(self) -> float | None:
        if self.first_jd is None or self.last_jd is None:
            return None
        return self.last_jd - self.first_jd

    def as_dict(self, *, with_residuals: bool = False) -> dict[str, Any]:
        out = asdict(self)
        out["arc_days"] = self.arc_days
        if not with_residuals:
            out.pop("residuals", None)
            out.pop("covariance", None)
        return out


# ----------------------------------------------------------------------------------
# Parsers -- pure functions over captured `fo` output, so they can be unit tested
# without WSL or a build. Fixtures live in tests/data/fo/.
# ----------------------------------------------------------------------------------

def parse_total_json(text: str, requested: Iterable[str] | None = None) -> dict[str, FitResult]:
    """Parse ``total.json`` (or ``elem_short.json``) into :class:`FitResult` per object.

    ``requested`` is the set of designations that were submitted. It is used only to key
    the results the way the caller asked for them: Find_Orb renames what it recognises
    (``J009S`` comes back as ``Jupiter IX = Sinope``), and its ``packed`` field holds
    columns 1-12 of the source record, from which a trkSub can be recovered.
    """
    want = set(requested or ())
    doc = json.loads(text)
    objects = doc.get("objects") or {}
    out: dict[str, FitResult] = {}
    for name, obj in objects.items():
        key = _result_key(name, obj, want)
        out[key] = _fit_from_object(key, name, obj)
    return out


def _result_key(name: str, obj: dict[str, Any], want: set[str]) -> str:
    packed = str(obj.get("packed") or "")
    candidates = [
        packed[5:12].strip(),  # columns 6-12: the trkSub proper
        packed.strip(),
        str(obj.get("object") or name).strip(),
        name.strip(),
    ]
    for cand in candidates:
        if cand and cand in want:
            return cand
    return candidates[2] or name


def _fit_from_object(key: str, name: str, obj: dict[str, Any]) -> FitResult:
    res = FitResult(desig=key, fo_object_name=str(obj.get("object") or name))
    res.packed = obj.get("packed")

    obs = obj.get("observations") or {}
    res.n_obs = obs.get("count")
    res.n_used = obs.get("used")
    res.first_jd = _f(obs.get("earliest_used") or obs.get("earliest"))
    res.last_jd = _f(obs.get("latest_used") or obs.get("latest"))
    res.residuals = list(obs.get("residuals") or [])

    el = obj.get("elements")
    if not el:
        res.status = "no_elements"
        return res

    res.epoch_jd = _f(el.get("epoch"))
    res.central_body = el.get("central body")
    res.frame = el.get("frame")
    for src, dst in _ELEMENT_KEYS.items():
        setattr(res, dst, _f(el.get(src)))
    for src, dst in _SIGMA_KEYS.items():
        setattr(res, dst, _f(el.get(src)))
    res.rms_residual = _f(el.get("rms_residual"))
    res.weighted_rms = _f(el.get("weighted_rms_residual"))
    res.n_resids = el.get("n_resids")
    moids = el.get("MOIDs") or {}
    res.moid_earth = _f(moids.get("Earth"))
    res.max_residual = max_residual(res.residuals)

    res.converged, res.status = _convergence(res)
    return res


def _used(r: dict[str, Any]) -> bool:
    """Was this observation included in the least-squares fit?

    The field is ``incl``, **not** ``flags``. Find_Orb's residual records carry both, and
    ``flags`` stays 0 on rejected observations -- on the self-test's 49-day Eros arc, 18 of
    24 observations were rejected with ``flags == 0`` throughout and ``incl`` 0/1 exactly
    tracking the "6 / 24 obs" Find_Orb reported.
    """
    incl = r.get("incl")
    return bool(incl) if incl is not None else True


def max_residual(residuals: Sequence[dict[str, Any]]) -> float | None:
    """Largest total residual, in arcseconds, over observations Find_Orb actually used."""
    best: float | None = None
    for r in residuals:
        if not _used(r):
            continue
        d_ra, d_dec = _f(r.get("dRA")), _f(r.get("dDec"))
        if d_ra is None or d_dec is None:
            continue
        total = math.hypot(d_ra, d_dec)
        best = total if best is None else max(best, total)
    return best


def rms_from_residuals(residuals: Sequence[dict[str, Any]]) -> float | None:
    """Recompute the residual RMS from the per-observation table.

    An independent check on the ``rms_residual`` Find_Orb reports: a parser that picks up
    the wrong field will disagree with this, and the tests pin the agreement.

    The normalisation is **per coordinate** -- ``sqrt(sum(dRA^2 + dDec^2) / 2N)``, not
    ``/ N``. Each observation contributes two residuals, and Find_Orb counts them
    separately (its own ``n_resids`` is twice the observation count). Getting this wrong
    inflates every RMS by sqrt(2), which against a 0.25" gate would reject a large slice
    of perfectly good fits.
    """
    total, n = 0.0, 0
    for r in residuals:
        if not _used(r):
            continue
        d_ra, d_dec = _f(r.get("dRA")), _f(r.get("dDec"))
        if d_ra is None or d_dec is None:
            continue
        total += d_ra * d_ra + d_dec * d_dec
        n += 2
    if not n:
        return None
    return math.sqrt(total / n)


def _convergence(res: FitResult) -> tuple[bool, str]:
    """Decide whether Find_Orb actually converged.

    ``fo`` has no explicit success flag. What it does have is this: a genuine least-squares
    solution carries a covariance matrix, and therefore per-element sigmas. When the
    differential correction fails, Find_Orb still emits whatever preliminary orbit it had
    (from Gauss or Vaisala) but the ``* sigma`` fields are absent. That absence, together
    with a finite RMS and a bound (elliptical) orbit, is the convergence test used here.
    """
    if res.rms_residual is None:
        return False, "no_rms"
    if res.q is None:
        return False, "no_elements"
    sigmas = (res.sigma_a, res.sigma_e, res.sigma_i, res.sigma_q)
    if any(s is None for s in sigmas):
        return False, "no_covariance"
    if res.a is None or res.a <= 0:
        # e >= 1: hyperbolic/parabolic. Real for interstellar objects, but for an ITF
        # trkSub it is nearly always a bad link or a collision, so flag it, do not hide it.
        return False, "unbound"
    if res.n_used is not None and res.n_used < 3:
        return False, "too_few_used"
    return True, "converged"


def parse_covar_json(text: str) -> dict[str, Any]:
    """Parse ``covar.json``: the 6x6 state covariance, the state vector, and its epoch."""
    doc = json.loads(text)
    covar = [[_f(x) for x in row] for row in doc.get("covar", [])]
    return {
        "covariance": covar,
        "state_vector": [_f(x) for x in doc.get("state_vect", [])],
        "epoch_jd": _f(doc.get("epoch")),
    }


def parse_elements_txt(text: str) -> dict[str, Any]:
    """Extract the force-model provenance line from ``elements.txt``.

    ``# Perturbers: 000007fe (Merc-Pluto plus Luna);  JPL DE-440`` -- which perturbers were
    integrated and which ephemeris was used. With the shipped default (``PERTURBERS=0``)
    this reads ``00000000 (unperturbed orbit); not using JPL DE``, which changes a
    week-long main-belt arc at the ~0.1" level: comparable to the MPC's own 0.25" RMS
    gate, so it must be recorded rather than assumed.
    """
    m = _PERTURBER_RE.search(text)
    if not m:
        return {}
    mask, label, eph = m.group(1), m.group(2).strip(), (m.group(3) or "").strip()
    return {
        "perturbers": mask,
        "perturbers_label": label,
        "jpl_ephemeris": eph.rstrip(".") or None,
    }


# ----------------------------------------------------------------------------------
# Runner
# ----------------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class FoRun:
    """One completed ``fo`` invocation: results plus everything needed to reproduce it."""

    results: dict[str, FitResult]
    returncode: int
    stdout: str
    stderr: str
    command: str
    workdir: Path
    force_model: dict[str, Any]

    @property
    def produced_nothing(self) -> bool:
        """``fo`` was asked for objects and returned none -- not even a failed solution.

        Distinct from "every object failed to converge": this means ``total.json`` was
        absent or empty, i.e. the invocation itself did not do its job. Observed once
        under 12 concurrent workers and not reproducible afterwards, so it is retried
        rather than trusted.
        """
        return not any(r.status != "not_returned_by_fo" for r in self.results.values())


#: Where per-worker config directories live. Deliberately on the **Linux** filesystem and
#: not under ``/mnt/c``: symlinks on DrvFs are second-class, and Find_Orb has fixed-size
#: path buffers (a 94-byte one aborts with ``strlcpy overflow`` on a long Windows path).
WORKER_CONFIG_ROOT = "$HOME/.cache/itf-linker-fo"

#: Files ``fo`` *writes*, which accumulate in whatever directory it treats as its own and
#: must never be inherited by a worker.
#:
#: This is not tidiness. ``fo`` drops results into its configuration directory in some
#: code paths, so a config directory that has ever been used directly ends up holding
#: ``elements.json``, ``total.json`` and friends. Symlinking a directory's whole contents
#: into each worker then points twelve concurrent processes at **one shared
#: ``elements.json``** -- and ``fo`` merges each object by re-reading that file, so the
#: reader trips ``fo.cpp:457 Assertion 'found_start' failed`` and aborts with SIGABRT.
#: The symptom is "0 of 979 designations converged" while the identical command run alone
#: works perfectly, which is a genuinely nasty thing to debug.
FO_OUTPUT_FILES = frozenset(
    {
        "combined.json", "covar.json", "covar.txt", "debug.txt", "dummy.txt",
        "elem_short.json", "elements.json", "elements.txt", "eph.json", "ephemeri.txt",
        "errors.txt", "gauss.out", "guide.txt", "monte.txt", "mpc_fmt.txt", "mpc_sr.txt",
        "observe.txt", "residual.txt", "sof.txt", "sofv.txt", "sr_elems.txt", "state.txt",
        "total.json", "vectors.txt", "virtual.txt",
    }
)

#: Prefixes of JPL/IMCCE planetary ephemeris files Find_Orb knows how to read
#: (from ``jpl_eph.txt``). Used only to assert one is present and readable.
_EPHEM_PREFIXES = ("linux_p", "lnx", "jpleph", "unix.", "sub_de", "inpop", "unxp")


def config_dir_listing(shell: Shell) -> list[str]:
    """Filenames in the shared Find_Orb configuration directory."""
    proc = shell.run(f"ls -1 {shq_expand(shell.config_dir)}", timeout=60, check=True)
    return [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]


def prepare_config_dir(shell: Shell, name: str) -> str:
    """Create a per-worker Find_Orb config directory of symlinks into the real one.

    ``fo`` rewrites ``environ.dat`` in its config directory on every run, so parallel
    workers must not share one. The shipped data files -- including the ~100 MB JPL
    ephemeris -- are read-only and symlinked, so a worker costs a few kilobytes.
    Anything in :data:`FO_OUTPUT_FILES` is skipped.

    The directory is rebuilt from scratch every time and the file list is decided **in
    Python**, not by shell globbing. Incremental construction leaves stale entries behind
    -- once a worker directory has a symlink named ``elements.json``, no later run
    removes it, and the ``[ -e ]`` guard cannot even see it because a dangling symlink
    fails that test.
    """
    cfg = f"{WORKER_CONFIG_ROOT}/{name}/"
    names = [f for f in config_dir_listing(shell) if f not in FO_OUTPUT_FILES]
    if not any(f.startswith(_EPHEM_PREFIXES) for f in names):
        raise RuntimeError(
            f"no JPL planetary ephemeris in {shell.config_dir}; fits would silently fall "
            "back to Find_Orb's built-in analytic theory (see DATA-SOURCES.md)"
        )
    script = (
        f"set -e; SRC={shq_expand(shell.config_dir)}; DST={shq_expand(cfg)}; "
        'rm -rf "$DST"; mkdir -p "$DST"; '
        + "; ".join(
            f'ln -s "$SRC"/{shq(f)} "$DST"{shq(f)}'
            for f in names
            if f != "environ.dat"
        )
        # environ.dat is copied, not linked: fo rewrites it on every run, and a shared
        # one is the concurrency hazard this whole function exists to remove.
        + '; cp "$SRC"/environ.dat "$DST"environ.dat'
    )
    shell.run(script, timeout=120, check=True)
    return cfg


def clean_config_dir(shell: Shell) -> list[str]:
    """Remove ``fo``'s own outputs from the shared configuration directory.

    Run before a batch. Not strictly required now that :func:`prepare_config_dir` filters,
    but it keeps the shared directory equal to what the install step produced, which is
    what makes ``config_files`` in the provenance block meaningful.
    """
    present = [f for f in config_dir_listing(shell) if f in FO_OUTPUT_FILES]
    if present:
        shell.run(
            f"cd {shq_expand(shell.config_dir)} && rm -f "
            + " ".join(shq(f) for f in present),
            timeout=60,
            check=True,
        )
    return present


def run_fo(
    obs_lines: Sequence[str],
    workdir: Path,
    *,
    designations: Iterable[str] | None = None,
    shell: Shell | None = None,
    config_dir: str | None = None,
    timeout: float = 1800.0,
    ignore_previous: bool = True,
    extra_args: Sequence[str] = (),
) -> FoRun:
    """Write ``obs_lines`` as MPC 80-column astrometry, run ``fo``, and parse the results.

    ``workdir`` is a *host* path; it holds the input file and receives ``fo``'s outputs, so
    everything a run did stays inspectable afterwards.
    """
    shell = shell or default_shell()
    workdir.mkdir(parents=True, exist_ok=True)
    workdir = workdir.resolve()
    obs_path = workdir / "obs.txt"
    # newline="\n": the MPC format is column-exact and Find_Orb reads it as a Linux file.
    # Python's default newline translation on Windows would append a CR to every record.
    with obs_path.open("w", encoding="ascii", newline="\n") as fh:
        fh.write("\n".join(line.rstrip("\r\n") for line in obs_lines) + "\n")

    wsl_work = shell.path(workdir)
    cfg = config_dir or shell.config_dir.rstrip("/") + "/"
    args = [
        shq_expand(shell.fo_path),
        shq("obs.txt"),
        "-O",
        shq(wsl_work),
        "-x",
        shq_expand(cfg),
        "-q",
    ]
    if ignore_previous:
        args.append("-i")
    args.extend(shq(a) for a in extra_args)
    script = f"cd {shq(wsl_work)} && " + " ".join(args)

    proc = shell.run(script, timeout=timeout)

    total = workdir / "total.json"
    results: dict[str, FitResult] = {}
    if total.exists():
        try:
            results = parse_total_json(total.read_text(encoding="utf-8", errors="replace"),
                                       requested=designations)
        except json.JSONDecodeError:
            results = {}

    force_model: dict[str, Any] = {}
    elements_txt = workdir / "elements.txt"
    if elements_txt.exists():
        force_model = parse_elements_txt(elements_txt.read_text(encoding="utf-8", errors="replace"))
    covar_path = workdir / "covar.json"
    if covar_path.exists() and len(results) == 1:
        try:
            cov = parse_covar_json(covar_path.read_text(encoding="utf-8", errors="replace"))
            only = next(iter(results.values()))
            only.covariance = cov["covariance"]
            only.state_vector = cov["state_vector"]
        except json.JSONDecodeError:
            pass
    for res in results.values():
        res.perturbers = force_model.get("perturbers")
        res.perturbers_label = force_model.get("perturbers_label")
        res.jpl_ephemeris = force_model.get("jpl_ephemeris")

    # Designations that went in but did not come out get an explicit failure record rather
    # than silently vanishing from the tally.
    for desig in designations or ():
        results.setdefault(desig, FitResult(desig=desig, status="not_returned_by_fo"))

    return FoRun(
        results=results,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        command=script,
        workdir=workdir,
        force_model=force_model,
    )


def load_previous_run(workdir: Path, designations: Sequence[str]) -> dict[str, FitResult] | None:
    """Re-read a chunk directory a previous invocation already completed.

    Returns ``None`` unless the directory holds a parseable ``total.json`` covering
    **every** designation asked for -- a partially written file is worse than no file,
    because it silently turns "not fitted" into "did not converge".

    This exists because fitting is the long pole: a full M3 batch is hours of ``fo``, and
    an interrupted run that had to start over would make the milestone unfinishable on a
    laptop. Chunk membership is deterministic (designations are sorted before chunking),
    so chunk *N* always holds the same objects and the check is exact rather than hopeful.
    """
    total = workdir / "total.json"
    if not total.exists():
        return None
    try:
        results = parse_total_json(total.read_text(encoding="utf-8", errors="replace"),
                                   requested=designations)
    except (json.JSONDecodeError, OSError):
        return None
    if not results or any(d not in results for d in designations):
        return None

    elements_txt = workdir / "elements.txt"
    force_model: dict[str, Any] = {}
    if elements_txt.exists():
        force_model = parse_elements_txt(
            elements_txt.read_text(encoding="utf-8", errors="replace")
        )
    for res in results.values():
        res.perturbers = force_model.get("perturbers")
        res.perturbers_label = force_model.get("perturbers_label")
        res.jpl_ephemeris = force_model.get("jpl_ephemeris")
    return results


def run_fo_batched(
    groups: dict[str, Sequence[str]],
    workroot: Path,
    *,
    shell: Shell | None = None,
    workers: int = 8,
    chunk_size: int = 64,
    timeout: float = 3600.0,
    progress: Any = None,
    diagnostics: list[dict[str, Any]] | None = None,
    resume: bool = False,
) -> dict[str, FitResult]:
    """Fit many designations by splitting them across single-process ``fo`` runs.

    ``groups`` maps designation -> its 80-column observation lines (continuation ``s``/``v``
    lines included, in file order). Find_Orb's own ``-p`` mode is deliberately not used:
    it leaves ``total.json`` with a header and no objects.

    A chunk that produces *no* output at all is **bisected** rather than retried blindly.
    ``fo`` merges each object's ``elements.json`` into ``total.json`` with an assertion
    that the per-object file contains a ``"  {"`` line; an object that yields no elements
    at all (every observation excluded, for instance) trips
    ``fo.cpp:457 Assertion 'found_start' failed`` and **aborts the whole invocation with
    SIGABRT**, losing every other object in the batch. Splitting in half repeatedly
    isolates the offender and salvages the rest, at the cost of ``log2(chunk_size)`` extra
    runs for each poisoned chunk. Without this, one bad designation in forty silently
    turned "916 converged" into "0 converged".
    """
    shell = shell or default_shell()
    workroot.mkdir(parents=True, exist_ok=True)
    workroot = workroot.resolve()
    clean_config_dir(shell)
    keys = list(groups)
    chunks = [keys[i : i + chunk_size] for i in range(0, len(keys), chunk_size)]
    # Appended to, never replaced, so the caller's list is the one that fills up.
    failures = diagnostics if diagnostics is not None else []

    def attempt(chunk: list[str], tag: str) -> dict[str, FitResult]:
        wd = workroot / tag
        if resume:
            previous = load_previous_run(wd, chunk)
            if previous is not None:
                return previous
        lines: list[str] = []
        for desig in chunk:
            lines.extend(groups[desig])
        cfg = prepare_config_dir(shell, tag)
        run = run_fo(
            lines, wd, designations=chunk, shell=shell, config_dir=cfg, timeout=timeout
        )
        if not run.produced_nothing:
            return run.results
        failures.append(
            {
                "chunk": tag,
                "designations": len(chunk),
                "returncode": run.returncode,
                "stdout_tail": run.stdout[-400:],
                "stderr_tail": run.stderr[-400:],
            }
        )
        if len(chunk) == 1:
            # Isolated: this single designation is the one fo cannot handle.
            return {
                chunk[0]: FitResult(
                    desig=chunk[0],
                    status=f"fo_aborted(rc={run.returncode})",
                )
            }
        mid = len(chunk) // 2
        merged = attempt(chunk[:mid], f"{tag}a")
        merged.update(attempt(chunk[mid:], f"{tag}b"))
        return merged

    def one(idx_chunk: tuple[int, list[str]]) -> dict[str, FitResult]:
        idx, chunk = idx_chunk
        results = attempt(chunk, f"chunk{idx:04d}")
        if progress is not None:
            progress(idx, len(chunks), results)
        return results

    out: dict[str, FitResult] = {}
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for part in pool.map(one, enumerate(chunks)):
            out.update(part)
    return out
