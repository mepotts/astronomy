#!/usr/bin/env python
"""M6: the PRODUCTION epoch-vetting harness -- the verdict factory.

M3 proved the loop works (3 orbit sources kept, 9 quiet ones demoted) with
a 40-line prototype that reads one local file and holds everything in
memory.  On 2026-12-02 the same loop has to run over a 983-row queue
against a DataLink service that is the day's bottleneck, survive being
killed, and report how fast it actually went.  This is that harness.

=======================================================================
PRE-REGISTERED VERDICT RULES (written before the M6 runs; they extend
M3's prototype rule, they do not replace it)
=======================================================================
Input per source: the epoch astrometry served for it, and the single-star
(5/6-parameter) fit of it by ESA's `gaiasupdate`.

  f2  = the fit's goodness-of-fit statistic (gaiasupdate
        solution_statistic.f2).  A source whose photocentre really moves on
        an orbit cannot be fit by a single-star model, so f2 blows up; a
        source with no epoch-level wobble sits at |f2| ~ 1.

  n_used = CCD transits that survived the AGIS-like filtering and entered
        the fit (results['n_measurements']).

  RULE 1  n_used < MIN_TRANSITS (=50)      -> INCONCLUSIVE (scope
          orbit_reality).  Too few epochs to say anything; NOT a demotion.
  RULE 2  |f2| >  F2_GATE (=5)             -> CONFIRMED  (scope
          orbit_reality): epoch-level wobble present, the orbit survives
          and goes to the orbital refit.
  RULE 3  |f2| <= F2_GATE                  -> SPURIOUS   (scope
          orbit_reality): no epoch-level support for the claimed
          photocentre orbit.
  RULE 4  DataLink served nothing          -> NO_DATA.
  RULE 5  the fit raised                   -> ERROR, with the exception
          text in `notes`.  Never silently dropped, never retried into a
          verdict.

CONFIDENCE (pre-registered, r = |f2| / F2_GATE):
  HIGH    r >= 2 (KEEP side) or r <= 0.5 (DEMOTE side) -- clear of the gate
          by a factor 2 in either direction
  MEDIUM  0.5 < r < 2 -- within a factor 2 of the gate
  LOW     INCONCLUSIVE / NO_DATA / ERROR, or n_used < 100

VERDICT SCOPE.  Every harness verdict is scope `orbit_reality`: it answers
"does this photocentre orbit have epoch-level support?", NOT "is there a
dark massive companion?" (EB26's `compact_companion` scope).  A harness
SPURIOUS and an EB26 SPURIOUS mean nearly the same thing; a harness
CONFIRMED is WEAKER than an EB26 CONFIRMED.  The schema keeps the two
apart on purpose -- see scripts/verdict_schema.py.

=======================================================================
OPERATIONAL DESIGN (the part M3's prototype did not have)
=======================================================================
BATCHED.  DataLink epoch astrometry is not a TAP table (M1 finding #1), so
  it is fetched through `Gaia.load_data(ids=[...], retrieval_type=
  'EPOCH_ASTROMETRY', data_structure='RAW')`, which returns ONE file for
  the whole batch with one row per (source, transit).  gaiasupdate's own
  `from_gacs_datalink()` sends ids=[source_id] -- one HTTP round trip per
  source -- which is why this harness does not use it.
RESUMABLE.  Every fetched source is written to its own parquet under
  data/epoch_cache/<release_tag>/ (atomically: .tmp then os.replace) and
  every verdict is appended to the ledger CSV as it is produced.  On
  restart, cached sources are not re-fetched and ledgered sources are not
  re-fit.  A session kill costs at most the batch in flight.
POLITE + RATE-LIMIT AWARE.  >= GAP_S between requests, 6 retries with
  exponential backoff, and HTTP 429 / 503 with a Retry-After header is
  honoured to the second (the archive is entitled to say "slow down"; the
  house rule since M5 is that a multi-request pull cannot survive a
  no-retry policy).
INSTRUMENTED.  Per-batch: n_ids, n_served, seconds, rows, cache-hits.
  Per-source: fetch share, fit seconds, transits.  Written to
  out/m6_harness_timings.csv + out/m6_harness_throughput.txt, so
  sources-per-hour is MEASURED, not assumed.

Sources of epoch astrometry (--source):
  prerelease  the 2026-06-26 12-source RAW VOTable -- the only real epoch
              astrometry that exists today; the end-to-end validation path
  datalink    the Gaia archive (December); needs `--release "Gaia DR4"`
  cache       fits whatever is already in data/epoch_cache/, no network

Run:
  .venv/Scripts/python.exe scripts/epoch_vet_harness.py --source prerelease
  .venv/Scripts/python.exe scripts/epoch_vet_harness.py --source datalink \
      --queue out/epoch_vet_day1_queue.v2.csv --limit 50 --batch 20
"""

import argparse
import os
import sys
import time
import traceback
import warnings

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verdict_schema as vs  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_ROOT = os.path.join(BASE, "data", "epoch_cache")
OUT_DIR = os.path.join(BASE, "out")
PRERELEASE_XML = os.path.join(
    BASE, "data", "epoch-astrometry",
    "GAIA_DR4_PRERELEASE_EPOCH_ASTROMETRY_RAW.xml")

HARNESS_VERSION = "epoch_vet_harness 1.0 (M6, 2026-08-21)"
CONFIG_VERSION = 5

# ---- the pre-registered constants (docstring above) ----------------------
F2_GATE = 5.0
MIN_TRANSITS = 50
LOW_CONFIDENCE_TRANSITS = 100
CONF_FACTOR = 2.0

# ---- politeness ----------------------------------------------------------
GAP_S = 0.5
RETRIES = 6
BACKOFF_S = 5.0
DEFAULT_BATCH = 20

# columns gaiasupdate's archive->CU9 adapter requires; a served source
# missing any of them is an ERROR, not a silent drop
REQUIRED_EPOCH_COLS = [
    "source_id", "obs_time_bary_corr", "centroid_pos_al",
    "centroid_pos_error_al", "scan_pos_angle", "parallax_factor_al",
    "colour_factor_al", "obs_time_tcb", "used_by_agis_al",
    "agis_source_excess_noise", "ccd_proc_flags", "ipd_error_al",
    "nu_eff_used_in_astrometry"]


def release_tag(release):
    return "".join(ch if ch.isalnum() else "_" for ch in release).strip("_")


# ======================================================================
# fetch layer
# ======================================================================
class EpochSource:
    """Common interface: .fetch(ids) -> {source_id: DataFrame}, plus the
    provenance strings that go on every verdict record."""

    name = "abstract"
    release = "unknown"
    data_structure = "RAW"

    def fetch(self, ids):
        raise NotImplementedError


class PrereleaseSource(EpochSource):
    """The 2026-06-26 pre-release file.  No network; the whole point is
    that the production code path is exercised on real epoch astrometry."""

    name = "prerelease_file"

    def __init__(self, path=PRERELEASE_XML):
        from astropy.table import Table
        self.path = path
        self.release = "Gaia DR4 pre-release 2026-06-26"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self._df = Table.read(path, format="votable").to_pandas()
        self._df["source_id"] = self._df["source_id"].astype("int64")

    def all_ids(self):
        return sorted(self._df["source_id"].unique().tolist())

    def fetch(self, ids):
        out = {}
        for sid in ids:
            sub = self._df[self._df["source_id"] == sid]
            if len(sub):
                out[int(sid)] = sub.reset_index(drop=True)
        return out


class DataLinkSource(EpochSource):
    """Gaia archive DataLink, batched, polite, retrying, Retry-After aware.

    RAW data_structure = one file per request holding every requested
    source (arrays preserved) -- so one HTTP round trip serves `batch`
    sources instead of one.  That is the single biggest lever on the
    day-one wall clock and it is why this class exists rather than a call
    to gaiasupdate's own one-id-per-call helper.
    """

    name = "gaia_datalink"

    def __init__(self, release="Gaia DR4", retrieval_type="EPOCH_ASTROMETRY",
                 fmt="votable", server=None):
        from astroquery.gaia import Gaia, GaiaClass
        self.release = release
        self.retrieval_type = retrieval_type
        self.fmt = fmt
        self._Gaia = Gaia if server is None else GaiaClass(
            gaia_tap_server=server, gaia_data_server=server)
        self.last_response_seconds = None

    def _load(self, ids):
        return self._Gaia.load_data(
            ids=[int(i) for i in ids], data_release=self.release,
            retrieval_type=self.retrieval_type, data_structure="RAW",
            format=self.fmt, verbose=False)

    def _call_with_retries(self, ids):
        """The polite, retrying, fail-fast HTTP half of fetch().

        Extracted from fetch() in M7 (behaviour unchanged) so that a
        subclass can reuse the retry/backoff/Retry-After/deterministic-error
        policy while parsing a DIFFERENT DataLink product -- the day-one-scale
        dry run has to be transported by the same code that December will
        use, or it rehearses nothing.
        """
        last = None
        for attempt in range(RETRIES):
            try:
                t0 = time.time()
                res = self._load(ids)
                self.last_response_seconds = time.time() - t0
                break
            except Exception as exc:            # noqa: BLE001
                last = exc
                if _is_deterministic(exc):
                    # MEASURED 2026-08-21: asking ESAC for
                    # retrieval_type='EPOCH_ASTROMETRY' returns
                    #   HTTP 500: Unknown retrieval type: 'EPOCH_ASTROMETRY'
                    # for BOTH 'Gaia DR4' and 'Gaia DR4_INT4' -- the service
                    # does not serve it yet.  astroquery 0.4.11 lists the
                    # type client-side, so nothing catches this earlier.
                    # It is a 500, i.e. exactly what the retry policy is
                    # built for -- and retrying it six times with backoff
                    # burns five minutes on a deterministic answer.  Fail
                    # fast and say what to do.
                    raise RuntimeError(
                        f"DataLink rejected the request DETERMINISTICALLY "
                        f"({exc}). This is a wrong retrieval_type/release "
                        f"pair, not a flaky archive -- probe the live "
                        f"values (Phase 3.0 in DR4-DAY-RUNBOOK.md) instead "
                        f"of retrying.") from exc
                wait = _retry_after_seconds(exc)
                if wait is None:
                    wait = BACKOFF_S * (2 ** attempt)
                print(f"    DataLink attempt {attempt+1}/{RETRIES} failed "
                      f"({type(exc).__name__}: {exc}); sleeping {wait:.0f}s",
                      flush=True)
                if attempt == RETRIES - 1:
                    raise
                time.sleep(wait)
        else:                                    # pragma: no cover
            raise last
        return res

    def _frames_from(self, res):
        """Parse a DataLink RAW result into epoch-astrometry frames."""
        from gaiasupdate.epoch_astrometry import GaiaEpochAstrometryArchive
        frames = []
        for _key, val in (res or {}).items():
            for item in (val if isinstance(val, list) else [val]):
                try:
                    df = item.to_table().to_pandas()
                except AttributeError:
                    df = item.to_pandas()
                frames.append(GaiaEpochAstrometryArchive.astropy_table_to_df(df))
        return frames

    @staticmethod
    def _temp_dirs():
        """astroquery's own scratch directories, in the CWD.

        M9 FINDING (the small one, and it is 50 directories by the end of a
        December run).  `Gaia.load_data` writes the downloaded payload into
        a fresh `temp_<YYYYMMDD_HHMMSS.ffffff>/` directory **in the current
        working directory** -- one per call -- and never removes it.  M6
        landmine #8 noticed astroquery writing into the CWD for
        `dump_to_file`; this is the same habit on the normal path.  At DR4's
        50.9 KiB/source and batch 20 that is ~1 MB per batch, so a 50-batch
        run leaves ~50 MB of DUPLICATED payload and 50 untracked
        directories in the repo root, on top of the harness's own cache.
        """
        try:
            return {d for d in os.listdir(".")
                    if d.startswith("temp_") and os.path.isdir(d)}
        except OSError:
            return set()

    def fetch(self, ids):
        before = self._temp_dirs()
        res = self._call_with_retries(ids)
        frames = self._frames_from(res)
        # remove only what THIS call created, and only if it matches
        # astroquery's own name shape.  Never a blanket temp_* sweep.
        import shutil
        for d in self._temp_dirs() - before:
            try:
                shutil.rmtree(d, ignore_errors=True)
            except OSError:
                pass
        if not frames:
            return {}
        allrows = pd.concat(frames, ignore_index=True)
        idcol = "source_id" if "source_id" in allrows.columns else "SOURCE_ID"
        allrows = allrows.rename(columns={idcol: "source_id"})
        allrows["source_id"] = allrows["source_id"].astype("int64")
        return {int(s): g.reset_index(drop=True)
                for s, g in allrows.groupby("source_id")}


DETERMINISTIC_MARKERS = ("unknown retrieval type", "unknown release",
                         "invalid retrieval type", "not a valid release")


def _is_deterministic(exc):
    """True for archive errors that a retry cannot fix.

    The Gaia data server answers a bad retrieval_type/release pair with an
    HTTP 500 whose BODY says what is wrong -- so status code alone cannot
    tell a deterministic rejection from a transient failure, and the retry
    policy would happily burn six backoffs on it.  Read the body.
    """
    msg = str(exc).lower()
    return any(m in msg for m in DETERMINISTIC_MARKERS)


def _retry_after_seconds(exc):
    """Honour an HTTP 429/503 Retry-After header if the exception carries
    one (astroquery wraps requests' HTTPError in several ways)."""
    for attr in ("response", "resp", "_response"):
        r = getattr(exc, attr, None)
        hdrs = getattr(r, "headers", None)
        if hdrs:
            ra = hdrs.get("Retry-After") or hdrs.get("retry-after")
            if ra:
                try:
                    return max(1.0, float(ra))
                except ValueError:
                    return None
    return None


# ======================================================================
# cache + ledger
# ======================================================================
def cache_dir(release):
    d = os.path.join(CACHE_ROOT, release_tag(release))
    os.makedirs(d, exist_ok=True)
    return d


def cache_path(release, sid):
    return os.path.join(cache_dir(release), f"{int(sid)}.parquet")


REPLACE_RETRIES = 6
REPLACE_BACKOFF_S = 0.2


def cache_write(release, sid, df):
    """Write one source's epoch table atomically.

    M9 DEFECT, found only by a long run at December scale.  `os.replace` is
    atomic on Windows but it is NOT immune to sharing violations: another
    process holding either path open -- an antivirus or the search indexer
    scanning the file microseconds after it is written is the usual one --
    makes it raise

        PermissionError: [WinError 5] Access is denied: '...parquet.tmp'
                          -> '...parquet'

    and that killed a 981-source transport run at source 360 with a
    non-zero exit.  The failure is TRANSIENT and per-file: the only correct
    response is to retry.  Nothing about the atomicity guarantee changes --
    the reader still sees either the old file or the new one, never a half
    one -- and if every retry fails the exception is re-raised with the
    cause named, because a cache that cannot be written is a real stop.
    """
    p = cache_path(release, sid)
    tmp = p + ".tmp"
    df.to_parquet(tmp, index=False)
    last = None
    for attempt in range(REPLACE_RETRIES):
        try:
            os.replace(tmp, p)         # atomic: a kill mid-write cannot
            return p                   # leave a half-file that looks cached
        except PermissionError as exc:                           # noqa: PERF203
            last = exc
            time.sleep(REPLACE_BACKOFF_S * (2 ** attempt))
    raise PermissionError(
        "cache_write could not replace %s after %d attempts (%s). On "
        "Windows this is a sharing violation, usually an antivirus or "
        "indexer holding the file; exclude data/epoch_cache/ from "
        "real-time scanning." % (p, REPLACE_RETRIES, last)) from last


def cache_read(release, sid):
    p = cache_path(release, sid)
    return pd.read_parquet(p) if os.path.exists(p) else None


class LedgerLock:
    """One writer per ledger.  M9 DEFECT, paid for in duplicated work.

    The harness's whole resume contract is "the ledger is the resume point:
    a restart skips what is in it".  That is only true of ONE writer.  Two
    processes pointed at the same ledger each read it at start-up, each
    compute a `todo` from a snapshot that is immediately stale, and then
    both fetch and both append -- so the file grows with DUPLICATE rows,
    the "already in the ledger" count under-reports, and the two runs
    silently do the same work twice.  Measured here: 440 rows for 260
    distinct sources, 180 duplicates, and one restart that announced "220
    already in the ledger" against a file holding 360.

    Nothing in the harness prevented it, and on release day somebody WILL
    double-launch -- a terminal left open, a scheduled retry, a background
    job the shell reported as finished while the detached process ran on
    (which is exactly how it happened here).  An exclusive-create lock file
    beside the ledger costs nothing and refuses the second run out loud.
    A stale lock (the holder died) is detected by pid and can be cleared
    with --force-unlock.
    """

    def __init__(self, ledger, force=False):
        self.path = ledger + ".lock"
        self.force = force
        self.fd = None

    def __enter__(self):
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        if self.force and os.path.exists(self.path):
            os.remove(self.path)
        try:
            self.fd = os.open(self.path,
                              os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(self.fd, ("pid=%d\nstarted=%s\n"
                               % (os.getpid(),
                                  time.strftime("%Y-%m-%dT%H:%M:%S"))
                               ).encode())
        except FileExistsError:
            try:
                held = open(self.path).read().strip().replace("\n", " ")
            except Exception:                                    # noqa: BLE001
                held = "unreadable"
            raise RuntimeError(
                "another harness run already holds %s (%s). Two writers on "
                "one ledger duplicate work and corrupt the resume count -- "
                "wait for it, or if it is dead re-run with --force-unlock."
                % (os.path.relpath(self.path, BASE), held)) from None
        return self

    def __exit__(self, *exc):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        try:
            os.remove(self.path)
        except OSError:
            pass
        return False


def _flush_timings(path, rows):
    """Append and CLEAR the pending timing rows.

    M9 DEFECT, the twin of the one above and found by the same crash.  The
    timings CSV used to be written ONCE, after the batch loop -- so a run
    that died at batch 17 of 50 lost every per-batch measurement it had
    made, which is precisely the instrumentation you need to (a) diagnose
    the crash and (b) read the day's delivered KiB/s, which DR4-DAY-RUNBOOK
    sec.3.0 instructs you to take from `out/m6_harness_timings.csv`.  The
    ledger checkpointed every batch and the instrumentation did not.
    Flushed per batch now; the rows list is cleared in place so nothing is
    written twice.
    """
    if not rows:
        return
    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    header = not os.path.exists(path) or os.path.getsize(path) == 0
    df.to_csv(path, mode="a", header=header, index=False,
              lineterminator="\n")
    rows.clear()


def load_ledger(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return vs.empty_frame()
    return vs.coerce(pd.read_csv(path))


def append_ledger(path, records):
    """Append verdict records, writing the header only once.  Appending
    (rather than rewriting) is what makes a session kill cost nothing."""
    df = vs.coerce(pd.DataFrame(records))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    header = not os.path.exists(path) or os.path.getsize(path) == 0
    df.to_csv(path, mode="a", header=header, index=False, lineterminator="\n")
    return df


# ---- transport-rehearsal ledger (M7) -------------------------------------
# A dry run against DR3 EPOCH_PHOTOMETRY transports real products through the
# real code path but CANNOT adjudicate anything: photometry carries no
# astrometric epochs, so there is no f2 and therefore no verdict.  Writing a
# placeholder verdict into the verdict store would be exactly the kind of
# provenance lie the schema exists to prevent, so a transport rehearsal gets
# its own ledger, with its own columns, outside out/verdicts/.  The resume
# contract is identical: append-only, one row per source, restart skips what
# is already in it.
TRANSPORT_LEDGER_COLS = ["source_id", "run_id", "batch", "served", "n_rows",
                         "n_cols", "n_transits", "n_cells", "cache_bytes",
                         "produced_utc", "note"]


def payload_cells(df):
    """Served data volume in table cells, counting array-valued cells by
    their length.

    A DataLink RAW product is not always one row per transit: epoch
    ASTROMETRY arrives exploded (one row per CCD transit), epoch PHOTOMETRY
    arrives as ONE row per source with ~48 array columns.  Row count is
    therefore not a payload measure across products, and the parquet cache
    file size is dominated by per-file format overhead at these sizes.
    Cells are the measure that means the same thing for both.
    """
    total = 0
    for c in df.columns:
        for v in df[c].to_numpy():
            total += int(v.size) if isinstance(v, np.ndarray) else 1
    return total


def load_transport_ledger(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return pd.DataFrame({c: pd.Series(dtype="object")
                             for c in TRANSPORT_LEDGER_COLS})
    return pd.read_csv(path)


def append_transport_ledger(path, rows):
    df = pd.DataFrame(rows)[TRANSPORT_LEDGER_COLS]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    header = not os.path.exists(path) or os.path.getsize(path) == 0
    df.to_csv(path, mode="a", header=header, index=False, lineterminator="\n")
    return df


# ======================================================================
# fit + verdict
# ======================================================================
def fit_single_star(df, sid, model=None):
    """ESA's single-star fit.  Returns the gaiasupdate results dict."""
    from gaiasupdate.epoch_astrometry import GaiaEpochAstrometryArchive
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return GaiaEpochAstrometryArchive.supdate(df.copy(), int(sid),
                                                 model=model)


def verdict_from_fit(f2, n_used):
    """The pre-registered rules, in one place so the runbook can quote it."""
    if n_used is None or n_used < MIN_TRANSITS:
        return ("INCONCLUSIVE", "LOW",
                f"n_used {n_used} < MIN_TRANSITS {MIN_TRANSITS}: too few "
                f"epochs to adjudicate the orbit")
    r = abs(f2) / F2_GATE
    if abs(f2) > F2_GATE:
        conf = "HIGH" if r >= CONF_FACTOR else "MEDIUM"
        basis = (f"|f2| {abs(f2):.2f} = {r:.2f}x the gate {F2_GATE} "
                 f"(>= {CONF_FACTOR}x = HIGH)")
        v = "CONFIRMED"
    else:
        conf = "HIGH" if r <= 1.0 / CONF_FACTOR else "MEDIUM"
        basis = (f"|f2| {abs(f2):.2f} = {r:.2f}x the gate {F2_GATE} "
                 f"(<= {1/CONF_FACTOR:.2f}x = HIGH)")
        v = "SPURIOUS"
    if n_used < LOW_CONFIDENCE_TRANSITS:
        conf, basis = "LOW", basis + f"; but only {n_used} transits used"
    return (v, conf, basis)


def base_record(sid, src, run_id, queue_row=None):
    import gaiasupdate
    rec = {c: None for c in vs.COLUMNS}
    rec.update({
        "source_id": int(sid),
        "release": src.release,
        "nss_solution_type": None,
        # provenance of the ORBIT being adjudicated -- which is the NSS
        # table only when the source came off the queue.  The 12
        # pre-release sources are a demo epoch-astrometry sample, not NSS
        # candidates, and saying "gaiadr4.nss_two_body_orbit" for them
        # would be a provenance lie in a schema whose whole point is
        # provenance.
        "orbit_source": (
            "gaia_dr4_prerelease_epoch_sample_2026-06-26"
            if queue_row is None and src.name == "prerelease_file"
            else ("gaiadr4.nss_two_body_orbit" if "DR4" in src.release
                  else "gaiadr3.nss_two_body_orbit")),
        "queue_bin": None,
        "queue_rank": None,
        "verdict_scope": "orbit_reality",
        "verdict_basis": "epoch_astrometry_f2",
        "schema_version": vs.SCHEMA_VERSION,
        "verdict_source": "epoch_vet_harness",
        "verdict_source_version": HARNESS_VERSION,
        "config_version": CONFIG_VERSION,
        "epoch_data_release": src.release,
        "epoch_data_structure": src.data_structure,
        "gaiasupdate_version": getattr(gaiasupdate, "__version__", "0.1.2"),
        "produced_utc": vs.utcnow(),
        "run_id": run_id,
    })
    for f in vs.CAUTION_FLAGS:
        rec[f] = False
    if queue_row is not None:
        for k, col in (("nss_solution_type", "nss_solution_type"),
                       ("queue_bin", "queue_bin"),
                       ("orbit_period_d", "period"),
                       ("orbit_significance", "significance")):
            if col in queue_row and pd.notna(queue_row[col]):
                rec[k] = queue_row[col]
        if "rank" in queue_row and pd.notna(queue_row["rank"]):
            rec["queue_rank"] = int(queue_row["rank"])
        for f in vs.CAUTION_FLAGS:
            if f in queue_row and pd.notna(queue_row[f]):
                rec[f] = bool(queue_row[f])
    return rec


# ======================================================================
# the loop
# ======================================================================
def run(*a, **kw):
    """The production loop, under a single-writer lock (M9).

    Everything is in _run_unlocked; this wrapper exists only so that no
    caller can accidentally run two writers against one ledger.  See
    LedgerLock for what that cost when it happened.
    """
    force = kw.pop("force_unlock", False)
    ledger = kw.get("ledger")
    if ledger is None:
        src = kw.get("source", a[0] if a else "prerelease")
        ledger = os.path.join(OUT_DIR, "verdicts", "harness_%s.v1.csv" % src)
    with LedgerLock(ledger, force=force):
        return _run_unlocked(*a, **kw)


def _run_unlocked(source="prerelease", queue=None, limit=None,
        batch=DEFAULT_BATCH,
        release=None, ledger=None, timings=None, run_id=None, gap=GAP_S,
        model=None, refit=False, verbose=True, retrieval_type=None,
        epoch_source=None, transport_only=False, progress_every=0):
    """The production loop.

    M7 added three optional arguments, none of which change the December
    path: `retrieval_type` / `epoch_source` (inject an already-built fetch
    layer -- used by the day-one-scale dry run so the SAME batching, cache,
    retry and checkpoint code transports a different DataLink product) and
    `transport_only` (skip adjudication and write the transport ledger; see
    TRANSPORT_LEDGER_COLS for why a dry run must not write verdicts).
    """
    run_id = run_id or f"m6_{source}_{time.strftime('%Y%m%dT%H%M%S')}"
    if epoch_source is not None:
        src = epoch_source
    elif source == "prerelease":
        src = PrereleaseSource()
    elif source == "datalink":
        src = DataLinkSource(release=release or "Gaia DR4",
                             **({"retrieval_type": retrieval_type}
                                if retrieval_type else {}))
    elif source == "cache":
        src = EpochSource()
        src.release = release or "Gaia DR4 pre-release 2026-06-26"
        src.name = "cache_only"
        src.fetch = lambda ids: {}
    else:
        raise ValueError(f"unknown --source {source}")

    ledger = ledger or os.path.join(OUT_DIR, "verdicts",
                                    f"harness_{source}.v1.csv")
    timings = timings or os.path.join(OUT_DIR, "m6_harness_timings.csv")

    # ---- the work list ---------------------------------------------------
    qrows = {}
    if queue:
        q = pd.read_csv(queue)
        ids = q["source_id"].astype("int64").tolist()
        qrows = {int(r["source_id"]): r for _, r in q.iterrows()}
    elif source == "prerelease":
        ids = src.all_ids()
    elif source == "cache":
        d = cache_dir(src.release)
        ids = sorted(int(f[:-8]) for f in os.listdir(d)
                     if f.endswith(".parquet"))
    else:
        raise ValueError("--queue is required for --source datalink")
    if limit:
        ids = ids[:int(limit)]

    done = (load_transport_ledger(ledger) if transport_only
            else load_ledger(ledger))
    already = set(done["source_id"].dropna().astype("int64")) if len(done) \
        else set()
    if refit:
        already = set()
    todo = [i for i in ids if i not in already]
    if verbose:
        print(f"harness run {run_id}: {len(ids)} queued, {len(already)} "
              f"already in the ledger, {len(todo)} to do "
              f"(source={source}, release='{src.release}', batch={batch})")

    rows_t = []
    t_run0 = time.time()
    n_fetch_calls = n_cached = n_fetched = 0
    t_fetch_total = t_fit_total = 0.0
    new_records = []

    for bi in range(0, len(todo), batch):
        chunk = todo[bi:bi + batch]
        need = [s for s in chunk
                if cache_read(src.release, s) is None]
        n_cached += len(chunk) - len(need)
        t0 = time.time()
        served = {}
        if need:
            served = src.fetch(need)
            n_fetch_calls += 1
            for sid, df in served.items():
                cache_write(src.release, sid, df)
            n_fetched += len(served)
        t_fetch = time.time() - t0
        t_fetch_total += t_fetch
        n_rows_served = int(sum(len(d) for d in served.values()))
        rows_t.append({"kind": "batch", "run_id": run_id, "batch": bi // batch,
                       "n_ids": len(chunk), "n_needed_fetch": len(need),
                       "n_served": len(served), "n_rows": n_rows_served,
                       "seconds": round(t_fetch, 3),
                       "seconds_per_source": round(
                           t_fetch / max(len(need), 1), 3)})
        if verbose:
            print(f"  batch {bi//batch}: {len(chunk)} ids "
                  f"({len(chunk)-len(need)} cached), fetched {len(served)} "
                  f"in {t_fetch:.1f}s ({n_rows_served} rows)", flush=True)

        if transport_only:
            # transport rehearsal: no fit is possible and none is faked
            for sid in chunk:
                df = cache_read(src.release, sid)
                p = cache_path(src.release, sid)
                new_records.append({
                    "source_id": int(sid), "run_id": run_id,
                    "batch": bi // batch,
                    "served": df is not None and len(df) > 0,
                    "n_rows": 0 if df is None else int(len(df)),
                    "n_cols": 0 if df is None else int(df.shape[1]),
                    "n_transits": (0 if df is None else
                                   int(pd.to_numeric(df["n_transits"],
                                                     errors="coerce").sum())
                                   if "n_transits" in df.columns
                                   else int(len(df))),
                    "n_cells": 0 if df is None else payload_cells(df),
                    "cache_bytes": (os.path.getsize(p)
                                    if os.path.exists(p) else 0),
                    "produced_utc": vs.utcnow(),
                    "note": ("transport rehearsal: DR3 EPOCH_PHOTOMETRY "
                             "carries no astrometric epochs, no adjudication "
                             "attempted"),
                })
            append_transport_ledger(ledger, new_records)
            _flush_timings(timings, rows_t)
            n_done = bi + len(chunk)
            if progress_every and (bi // batch) % progress_every == 0:
                el = time.time() - t_run0
                print(f"  [checkpoint] {n_done}/{len(todo)} in {el/60:.1f} min "
                      f"-> {3600.0*n_done/max(el,1e-9):.0f} sources/hour; "
                      f"ETA {(el/max(n_done,1))*(len(todo)-n_done)/60:.0f} min",
                      flush=True)
            new_records = []
            if need and bi + batch < len(todo):
                time.sleep(gap)
            continue

        for sid in chunk:
            rec = base_record(sid, src, run_id, qrows.get(int(sid)))
            df = cache_read(src.release, sid)
            if df is None or not len(df):
                rec.update({"verdict": "NO_DATA", "verdict_confidence": "LOW",
                            "verdict_confidence_basis":
                                "DataLink served no epoch astrometry",
                            "notes": "no epoch astrometry served"})
                new_records.append(rec)
                continue
            missing = [c for c in REQUIRED_EPOCH_COLS if c not in df.columns]
            if missing:
                rec.update({"verdict": "ERROR", "verdict_confidence": "LOW",
                            "verdict_confidence_basis":
                                "served table missing required columns",
                            "n_transits_fetched": len(df),
                            "notes": f"missing columns: {missing}"})
                new_records.append(rec)
                continue
            t1 = time.time()
            try:
                res = fit_single_star(df, sid, model=model)
                t_fit = time.time() - t1
                f2 = float(res["solution_statistic"].f2)
                n_used = int(res["n_measurements"])
                params = np.asarray(res["parameters"], float)
                errs = np.asarray(res["parameters_formal_uncertainty"], float)
                v, conf, basis = verdict_from_fit(f2, n_used)
                rec.update({
                    "n_transits_fetched": len(df),
                    "n_transits_used": n_used,
                    "f2_single_star": round(f2, 4),
                    "parallax_mas": round(float(params[2]), 6),
                    "excess_noise_mas": (None if res.get("excess_noise") is None
                                         else float(res["excess_noise"])),
                    "fit_model": str(res["solution_statistic"].model),
                    "fit_seconds": round(t_fit, 4),
                    "verdict": v, "verdict_confidence": conf,
                    "verdict_confidence_basis": basis,
                    "notes": (f"sigma_parallax {errs[2]:.4f} mas; "
                              f"chi2 {res['solution_statistic'].chi2:.1f}; "
                              f"n_outliers {res['n_outliers']}"),
                })
            except Exception as exc:              # noqa: BLE001
                t_fit = time.time() - t1
                rec.update({
                    "n_transits_fetched": len(df), "fit_seconds": round(t_fit, 4),
                    "verdict": "ERROR", "verdict_confidence": "LOW",
                    "verdict_confidence_basis": "single-star fit raised",
                    "notes": f"{type(exc).__name__}: {exc}",
                })
                if verbose:
                    print(f"    {sid}: FIT FAILED {type(exc).__name__}: {exc}")
                    traceback.print_exc(limit=1)
            t_fit_total += t_fit
            rows_t.append({"kind": "source", "run_id": run_id,
                           "batch": bi // batch, "source_id": int(sid),
                           "n_rows": len(df),
                           "n_transits_used": rec["n_transits_used"],
                           "seconds": round(t_fit, 3),
                           "verdict": rec["verdict"]})
            new_records.append(rec)

        # checkpoint after every batch: the ledger is the resume point
        if new_records:
            append_ledger(ledger, new_records)
            new_records = []
        _flush_timings(timings, rows_t)
        if need and bi + batch < len(todo):
            time.sleep(gap)

    if new_records:
        (append_transport_ledger if transport_only else append_ledger)(
            ledger, new_records)

    wall = time.time() - t_run0
    _flush_timings(timings, rows_t)

    stats = {
        "run_id": run_id, "source": source, "release": src.release,
        "n_queued": len(ids), "n_processed": len(todo),
        "n_cache_hits": n_cached, "n_fetched": n_fetched,
        "n_fetch_calls": n_fetch_calls, "batch_size": batch,
        "wall_seconds": round(wall, 2),
        "fetch_seconds": round(t_fetch_total, 2),
        "fit_seconds": round(t_fit_total, 2),
        "fit_seconds_per_source": (round(t_fit_total / len(todo), 4)
                                   if todo else None),
        "fetch_seconds_per_source": (round(t_fetch_total / n_fetched, 4)
                                     if n_fetched else None),
        "sources_per_hour": (round(3600.0 * len(todo) / wall, 1)
                             if todo and wall > 0 else None),
    }
    led = load_transport_ledger(ledger) if transport_only \
        else load_ledger(ledger)
    if verbose:
        print(f"\nrun {run_id} complete: {len(todo)} sources in {wall:.1f}s "
              f"-> {stats['sources_per_hour']} sources/hour")
        print(f"  fetch {t_fetch_total:.1f}s ({n_fetch_calls} calls, "
              f"{n_cached} cache hits) | fit {t_fit_total:.1f}s "
              f"({stats['fit_seconds_per_source']} s/source)")
        tally = (led["served"].value_counts().to_dict() if transport_only
                 else led["verdict"].value_counts().to_dict())
        print(f"  ledger {os.path.relpath(ledger, BASE)}: {len(led)} records "
              f"{tally}")
    return led, stats


# ======================================================================
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--source", default="prerelease",
                    choices=["prerelease", "datalink", "cache"])
    ap.add_argument("--queue", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--batch", type=int, default=DEFAULT_BATCH)
    ap.add_argument("--release", default=None)
    ap.add_argument("--ledger", default=None)
    ap.add_argument("--timings", default=None)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--gap", type=float, default=GAP_S)
    ap.add_argument("--model", default=None)
    ap.add_argument("--refit", action="store_true",
                    help="ignore the ledger and re-fit everything")
    ap.add_argument("--force-unlock", action="store_true",
                    help="clear a STALE ledger lock (only when you have "
                         "checked that no other harness run is alive)")
    ap.add_argument("--expect-keep", default=None,
                    help="comma-separated source_ids that MUST come back "
                         "CONFIRMED and be the only ones (acceptance gate)")
    a = ap.parse_args(argv)

    led, stats = run(source=a.source, queue=a.queue, limit=a.limit,
                     batch=a.batch, release=a.release, ledger=a.ledger,
                     timings=a.timings, run_id=a.run_id, gap=a.gap,
                     model=a.model, refit=a.refit,
                     force_unlock=a.force_unlock)

    if a.expect_keep is not None:
        expect = {int(x) for x in a.expect_keep.split(",") if x.strip()}
        kept = set(led.loc[led["verdict"] == "CONFIRMED",
                           "source_id"].astype("int64"))
        ok = kept == expect
        print(f"\nACCEPTANCE kept == expected: "
              f"{'PASS' if ok else 'FAIL -- symmetric difference ' + str(kept ^ expect)}")
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
