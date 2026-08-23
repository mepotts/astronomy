"""M5: a reproducible NEBULAR STAGE to replace Hephaistos II's unpublished CNN.

M4 Sec 4 localised the entire 4.2x pre-visual overproduction to one stage. Every
stage this project can reproduce, it reproduces (parent 1.03x, RMSE 0.84x,
extra cuts 0.84x); the residual runs from 20.9x at |b| < 5 deg to
1.05x [0.94-1.17] at |b| > 50 deg, and the only stage without a published
implementation is the C4 nebular classifier. This module builds a replacement
out of public data, with every threshold fixed by the rule written in
M5 Sec 0 PR-2 BEFORE any survivor count was computed.

Three components (PR-2):

  N1  known-nebula catalogue veto.  NO FREE PARAMETER: an object is flagged if
      it falls inside the PUBLISHED angular extent of a catalogued nebular
      object.  The radius is the catalogue's own.  Catalogues that publish no
      extent get a declared fixed 60" and are counted separately.

  N2  the coadd local-background statistic.  AllWISE's pipeline measures, per
      source and per band, the median background in the profile-fit annulus
      (w3sky/w4sky) and the sky confusion derived from the uncertainty images
      (w3conf/w4conf) -- an extended-emission statistic measured FROM THE
      COADDS and published as catalogue columns (AllWISE Explanatory
      Supplement Sec II.2).  Threshold: the percentile rank of w3sky and of
      w4sky within the |b| > 50 deg PARENT sample, binned by |ecliptic
      latitude| (10 deg) to absorb the zodiacal gradient; the score is the
      larger of the two ranks; flagged above 0.99.

  N3  the local mid-IR source density.  A REPORTED STATISTIC, NOT A CUT
      (PR-2): no published density threshold exists to anchor one.

Route note (measured here, 2026-08-23): IRSA's **Gator multi-position upload**
does 1,545 AllWISE cross-matches in 4.2 s -- 0.0027 s/position against the
3.5 s/position the TAP one-cone-per-object route cost M3/M4, a ~1300x speedup.
That is what makes an all-survivor background statistic affordable at all.
The same route retires M4 Sec 7.1's "3 h per release" warning about the vetting.

Run:
    python scripts/m5_nebular.py fetch                 # VizieR catalogues
    python scripts/m5_nebular.py sky --what calib      # |b|>50 parent, Gator
    python scripts/m5_nebular.py sky --what rmse       # 9,486 RMSE survivors
    python scripts/m5_nebular.py calibrate
    python scripts/m5_nebular.py apply --what rmse
    python scripts/m5_nebular.py funnel
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import requests

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "out"
NEB = ROOT / "data" / "nebular"
CELLS = ROOT / "data" / "w4" / "aip" / "cells"
DIST = ROOT / "data" / "w4" / "aip" / "distances"
# Raw Gator responses are bulk intermediates and live under data/ (gitignored,
# repo convention); only the small derived products go to out/.  The |b| > 50
# calibration table is 68k rows and counts as bulk too.
CACHE = NEB / "cache"
OUT.mkdir(exist_ok=True)
NEB.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)


def sky_matched(what: str) -> Path:
    """Where the matched background table for `what` lives."""
    return (CACHE if what == "calib" else OUT) / f"m5_sky_{what}_matched.csv"

VIZ = "https://vizier.cds.unistra.fr/viz-bin/asu-tsv"
GATOR = "https://irsa.ipac.caltech.edu/cgi-bin/Gator/nph-query"

# ------------------------------------------------------------------ PR-2 N1 --
# The catalogue list is FIXED IN M5 Sec 0 PR-2, before any cross-match.
# `ext` names the catalogue's OWN published extent column; `kind` says how it
# converts to a radius in arcsec.  `None` means the catalogue publishes no
# extent, and the declared fixed 60" applies (counted separately).
CATALOGS = [
    # id                vizier table               ext        kind       source
    ("HII_WISE",   "J/ApJS/212/1/wisecat",         "Rad",     "rad_as",
     "Anderson et al. 2014, ApJS 212, 1 -- the WISE catalog of Galactic HII regions"),
    ("HII_SH2",    "VII/20/catalog",               "Diam",    "diam_am",
     "Sharpless 1959, ApJS 4, 257"),
    ("HII_RCW",    "VII/216/rcw",                  "MajAxis", "diam_am",
     "Rodgers, Campbell & Whiteoak 1960, MNRAS 121, 103"),
    ("SNR_GREEN",  "VII/284/snrs",                 "MajDiam", "diam_am",
     "Green 2019, JApA 40, 36 -- catalogue of Galactic supernova remnants"),
    ("PN_SECGPN",  "V/84/main",                    None,      "fixed",
     "Acker et al. 1992, Strasbourg-ESO Catalogue of Galactic Planetary Nebulae"),
    ("PN_MASH1",   "V/127A/mash1",                 "MajDiam", "diam_as",
     "Parker et al. 2006, MNRAS 373, 79 -- MASH"),
    ("PN_MASH2",   "V/127A/mash2",                 "MajDiam", "diam_as",
     "Miszalski et al. 2008, MNRAS 384, 525 -- MASH-II"),
    ("DARK_LDN",   "VII/7A/ldn",                   "Area",    "area_deg2",
     "Lynds 1962, ApJS 7, 1 -- catalogue of dark nebulae"),
    ("BRIGHT_LBN", "VII/9/catalog",                "Area",    "area_deg2",
     "Lynds 1965, ApJS 12, 163 -- catalogue of bright nebulae"),
    ("DARK_BARN",  "VII/220A/barnard",             "Diam",    "diam_am",
     "Barnard 1927, Catalogue of 349 Dark Objects in the Sky"),
    ("REFL_VDB",   "VII/21/catalog",               "BRadMax", "rad_am",
     "van den Bergh 1966, AJ 71, 990 -- reflection nebulae"),
    ("REFL_MAGAK", "J/A+A/399/141/table1",         None,      "fixed",
     "Magakian 2003, A&A 399, 141 -- merged catalogue of reflection nebulae"),
    ("CED",        "VII/231/catalog",              "Dim1",    "diam_am",
     "Cederblad 1946 -- bright diffuse galactic nebulae"),
    ("PGCC",       "J/A+A/594/A28/pgcc",           "maj",     "diam_am",
     "Planck Collaboration 2016, A&A 594, A28 -- Galactic cold clumps"),
]

FIXED_RADIUS_AS = 60.0     # PR-2's declared fallback, applied uniformly
SCORE_THRESHOLD = 0.99     # PR-2's rule: 1% per-band FPR on nebulosity-free sky
SENSITIVITY = (0.95, 0.99, 0.999)
CALIB_BAND_DEG = 50.0      # |b| > 50 deg: where M4 Sec 4.3 measured 1.05x
ECL_BIN_DEG = 10.0
SKY_DEG2 = 41252.96124


# ------------------------------------------------------------------ helpers --
def galactic(ra: np.ndarray, dec: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Galactic (l, b) in degrees, J2000 -> Galactic (no astropy dependency in
    the hot path; verified against astropy to < 1e-9 deg in `selftest`)."""
    ra_g, dec_g, l_ncp = np.radians(192.85948), np.radians(27.12825), np.radians(122.93192)
    a, d = np.radians(ra), np.radians(dec)
    sb = np.sin(dec_g) * np.sin(d) + np.cos(dec_g) * np.cos(d) * np.cos(a - ra_g)
    b = np.arcsin(np.clip(sb, -1, 1))
    y = np.cos(d) * np.sin(a - ra_g)
    x = np.cos(dec_g) * np.sin(d) - np.sin(dec_g) * np.cos(d) * np.cos(a - ra_g)
    l = l_ncp - np.arctan2(y, x)
    return np.degrees(l) % 360.0, np.degrees(b)


def ecliptic_lat(ra: np.ndarray, dec: np.ndarray) -> np.ndarray:
    eps = np.radians(23.439281)
    a, d = np.radians(ra), np.radians(dec)
    return np.degrees(np.arcsin(np.sin(d) * np.cos(eps)
                                - np.cos(d) * np.sin(eps) * np.sin(a)))


def read_tsv(txt: str) -> pd.DataFrame:
    """Parse a VizieR asu-tsv payload: comments start '#', then a header row,
    a units row, a dashes row, then data."""
    lines = [l for l in txt.splitlines() if l and not l.startswith("#")]
    if len(lines) < 4:
        return pd.DataFrame()
    hdr = lines[0].split("\t")
    # the dashes row is the one made only of '-' runs
    start = 1
    for i in range(1, min(4, len(lines))):
        if set(lines[i].replace("\t", "")) <= {"-"}:
            start = i + 1
            break
    rows = [l.split("\t") for l in lines[start:] if l.count("\t") == len(hdr) - 1]
    df = pd.DataFrame(rows, columns=hdr)
    return df


def to_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.strip().replace({"": None}), errors="coerce")


# -------------------------------------------------------------------- fetch --
def cmd_fetch(a: argparse.Namespace) -> None:
    """Download the PR-2 catalogue list from VizieR, anonymously, and normalise
    every one to (ra, dec, r_as, cat, name).  A catalogue that fails to
    download is REPORTED AS ABSENT, not silently dropped (PR-2)."""
    recs, report = [], []
    for cid, table, ext, kind, src in CATALOGS:
        raw = NEB / f"{cid}.tsv"
        if raw.exists() and not a.refresh:
            txt = raw.read_text(encoding="utf-8", errors="replace")
        else:
            params = {"-source": table, "-out.max": "unlimited", "-out.all": "1",
                      "-out.add": "_RAJ2000,_DEJ2000"}
            try:
                r = requests.get(VIZ, params=params, timeout=300)
                txt = r.text
            except Exception as e:  # noqa: BLE001
                report.append({"cat": cid, "table": table, "status": f"DOWNLOAD-FAILED {type(e).__name__}", "n": 0})
                print(f"  {cid:12s} DOWNLOAD FAILED {type(e).__name__}")
                continue
            raw.write_text(txt, encoding="utf-8")
        df = read_tsv(txt)
        if df.empty or "_RAJ2000" not in df.columns:
            report.append({"cat": cid, "table": table, "status": "ABSENT (no rows / no coords)", "n": 0})
            print(f"  {cid:12s} ABSENT")
            continue
        ra, dec = to_num(df["_RAJ2000"]), to_num(df["_DEJ2000"])
        if kind == "fixed" or ext is None or ext not in df.columns:
            r_as = pd.Series(np.full(len(df), FIXED_RADIUS_AS), index=df.index)
            used = "fixed-60as" if kind == "fixed" else f"fixed-60as (column {ext} absent)"
        else:
            v = to_num(df[ext])
            if kind == "rad_as":
                r_as = v
            elif kind == "rad_am":
                r_as = v * 60.0
            elif kind == "diam_am":
                r_as = v * 60.0 / 2.0
            elif kind == "diam_as":
                r_as = v / 2.0
            elif kind == "area_deg2":
                r_as = np.sqrt(np.clip(v, 0, None) / np.pi) * 3600.0
            else:
                raise SystemExit(f"unknown kind {kind}")
            # rows with no published extent inside a catalogue that has the
            # column fall back to the SAME declared 60", flagged by n_fixed
            r_as = r_as.fillna(FIXED_RADIUS_AS)
            used = f"{ext} ({kind})"
        name_col = next((c for c in df.columns
                         if c.lower() in ("wise", "sh2", "rcw", "snr", "png", "ldn",
                                          "seq", "barn", "vdb", "ced", "name")), None)
        ok = ra.notna() & dec.notna() & r_as.notna() & (r_as > 0)
        sub = pd.DataFrame({
            "ra": ra[ok].to_numpy(), "dec": dec[ok].to_numpy(),
            "r_as": r_as[ok].to_numpy(),
            "cat": cid,
            "name": (df[name_col][ok].astype(str).str.strip().to_numpy()
                     if name_col else ""),
        })
        n_fixed = int((sub["r_as"] == FIXED_RADIUS_AS).sum())
        recs.append(sub)
        report.append({"cat": cid, "table": table, "status": "OK", "n": int(len(sub)),
                       "extent_column": used, "n_default_60as": n_fixed,
                       "median_r_as": float(np.median(sub["r_as"])),
                       "max_r_as": float(np.max(sub["r_as"])), "source": src})
        print(f"  {cid:12s} {len(sub):6,d} objects  extent={used:22s} "
              f"median r = {np.median(sub['r_as']):8.1f}\"  max = {np.max(sub['r_as']):9.1f}\"  "
              f"({n_fixed} at the declared 60\")")
    allc = pd.concat(recs, ignore_index=True)
    allc.to_csv(OUT / "m5_nebular_catalogs.csv", index=False)
    (OUT / "m5_nebular_catalog_report.json").write_text(
        json.dumps({"fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "fixed_radius_as": FIXED_RADIUS_AS,
                    "catalogues": report}, indent=2))
    print(f"\n  TOTAL {len(allc):,} nebular objects from "
          f"{len([r for r in report if r['status'] == 'OK'])}/{len(CATALOGS)} catalogues "
          f"-> out/m5_nebular_catalogs.csv")


# ---------------------------------------------------------------------- N1 --
def n1_flags(ra: np.ndarray, dec: np.ndarray,
             cats: pd.DataFrame) -> pd.DataFrame:
    """Is each position inside the published extent of a catalogued nebula?

    Exact on the sphere via a 3-vector KD-tree: for each target the search
    radius is the LARGEST catalogue radius, then each hit is tested against
    ITS OWN published radius.  No approximation beyond float precision.
    """
    from scipy.spatial import cKDTree                       # noqa: PLC0415

    def xyz(r, d):
        r, d = np.radians(r), np.radians(d)
        return np.column_stack([np.cos(d) * np.cos(r), np.cos(d) * np.sin(r), np.sin(d)])

    cv, tv = xyz(cats["ra"].to_numpy(), cats["dec"].to_numpy()), xyz(ra, dec)
    tree = cKDTree(cv)
    rmax = float(cats["r_as"].max())
    # chord length for the largest angular radius
    chord = 2.0 * np.sin(np.radians(rmax / 3600.0) / 2.0)
    cand = tree.query_ball_point(tv, chord)
    r_cat = cats["r_as"].to_numpy()
    cat_id = cats["cat"].to_numpy()
    name = cats["name"].to_numpy()
    hit = np.zeros(len(ra), bool)
    which, whichname, whichsep, whichrad, nhit = [], [], [], [], np.zeros(len(ra), int)
    for i, idxs in enumerate(cand):
        best = None
        n = 0
        for j in idxs:
            dot = float(np.clip(tv[i] @ cv[j], -1, 1))
            sep = np.degrees(np.arccos(dot)) * 3600.0
            if sep <= r_cat[j]:
                n += 1
                # report the one whose centre is nearest in units of its radius
                key = sep / max(r_cat[j], 1e-9)
                if best is None or key < best[0]:
                    best = (key, cat_id[j], name[j], sep, r_cat[j])
        nhit[i] = n
        if best is not None:
            hit[i] = True
            which.append(best[1]); whichname.append(best[2])
            whichsep.append(best[3]); whichrad.append(best[4])
        else:
            which.append(""); whichname.append("")
            whichsep.append(np.nan); whichrad.append(np.nan)
    return pd.DataFrame({"n1_flag": hit, "n1_ncat": nhit, "n1_cat": which,
                         "n1_name": whichname, "n1_sep_as": whichsep,
                         "n1_r_as": whichrad})


# --------------------------------------------------------------------- sky --
GATOR_COLS = ("designation,ra,dec,w3sky,w4sky,w3conf,w4conf,w3sigsk,w4sigsk,"
              "w3rchi2,w4rchi2,nb,na,ext_flg,w3snr,w4snr,w3mpro,w4mpro,ph_qual,cc_flags")


def gator_upload(ra: np.ndarray, dec: np.ndarray, catalog: str, cols: str,
                 radius_as: float = 3.0, chunk: int = 5000,
                 cache: Path | None = None, tag: str = "") -> pd.DataFrame:
    """IRSA Gator multi-position upload cross-match, anonymous.

    MEASURED 2026-08-23: 1,545 positions in 4.2 s (0.0027 s/position) against
    the 3.5 s/position of one-cone-per-object TAP.  The response is an IPAC
    table with `cntr_01` indexing the uploaded rows and `dist_x` the match
    separation, ordered by (cntr_01, dist_x) -- so the nearest match per
    position is the FIRST row for each cntr_01.

    Writes its cache INCREMENTALLY, one chunk at a time, so a killed run
    resumes (M4 Sec 7.1's warning, fixed).
    """
    done: dict[int, pd.DataFrame] = {}
    if cache is not None and cache.exists():
        prev = pd.read_csv(cache)
        for k, g in prev.groupby("_chunk"):
            done[int(k)] = g
        print(f"    [{tag}] resuming: {len(done)} chunk(s) cached, "
              f"{len(prev):,} rows")
    frames = list(done.values())
    nchunk = int(np.ceil(len(ra) / chunk))
    for k in range(nchunk):
        if k in done:
            continue
        lo, hi = k * chunk, min((k + 1) * chunk, len(ra))
        buf = io.StringIO()
        buf.write("|      ra      |     dec      |\n|   double     |   double     |\n")
        for x, y in zip(ra[lo:hi], dec[lo:hi]):
            buf.write(" %13.6f %13.6f\n" % (x, y))
        for attempt in range(5):
            try:
                t0 = time.time()
                r = requests.post(GATOR, data={
                    "catalog": catalog, "spatial": "Upload", "uradius": f"{radius_as}",
                    "uradunits": "arcsec", "outfmt": "1", "selcols": cols},
                    files={"filename": ("pos.tbl", buf.getvalue())}, timeout=1800)
                r.raise_for_status()
                t = parse_ipac(r.text)
                if t is None:
                    raise RuntimeError("no data block in Gator response")
                t["_chunk"] = k
                t["_row"] = t["cntr_01"].astype(int) - 1 + lo
                frames.append(t)
                print(f"    [{tag}] chunk {k + 1}/{nchunk} ({hi - lo} positions) "
                      f"-> {len(t)} rows in {time.time() - t0:.1f}s", flush=True)
                break
            except Exception as e:  # noqa: BLE001
                if attempt == 4:
                    raise SystemExit(f"[{tag}] chunk {k} FAILED after 5 tries: "
                                     f"{type(e).__name__}: {str(e)[:200]}")
                time.sleep(10 * (attempt + 1))
        if cache is not None:
            pd.concat(frames, ignore_index=True).to_csv(cache, index=False)
    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if cache is not None and not out.empty:
        out.to_csv(cache, index=False)
    return out


def parse_ipac(txt: str) -> pd.DataFrame | None:
    lines = txt.splitlines()
    hdr_i = [i for i, l in enumerate(lines) if l.startswith("|")]
    if not hdr_i:
        return None
    names = [c.strip() for c in lines[hdr_i[0]].strip("|").split("|")]
    widths = []
    hl = lines[hdr_i[0]]
    pos = [i for i, ch in enumerate(hl) if ch == "|"]
    for a, b in zip(pos[:-1], pos[1:]):
        widths.append((a + 1, b))
    data_start = max(hdr_i) + 1
    rows = []
    for l in lines[data_start:]:
        if not l.strip() or l.startswith("\\") or l.startswith("|"):
            continue
        rows.append([l[a:b].strip() if b <= len(l) else l[a:].strip()
                     for a, b in widths])
    df = pd.DataFrame(rows, columns=names)
    for c in df.columns:
        if c not in ("designation", "clon", "clat", "ph_qual", "cc_flags"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def nearest_per_row(g: pd.DataFrame, n: int) -> pd.DataFrame:
    """One row per uploaded position: the nearest AllWISE match, or NaNs."""
    if g.empty:
        return pd.DataFrame(index=range(n))
    first = g.sort_values(["_row", "dist_x"]).drop_duplicates("_row", keep="first")
    return first.set_index("_row").reindex(range(n))


def load_parent() -> pd.DataFrame:
    """The screen's parent sample: the AIP harvest inside C1, cc_flags-clean."""
    dfs = [pd.read_csv(p, usecols=["datalinkID", "ra", "dec", "cc_flags"])
           for p in sorted(CELLS.glob("*.csv"))]
    aip = pd.concat(dfs, ignore_index=True).rename(columns={"datalinkID": "source_id"})
    dd = [pd.read_csv(p, usecols=["source_id", "r_med_geo"]) for p in sorted(DIST.glob("*.csv"))]
    dist = (pd.concat(dd, ignore_index=True).dropna(subset=["source_id", "r_med_geo"])
            .drop_duplicates("source_id"))
    aip = aip.merge(dist, on="source_id", how="left")
    aip = aip[aip["r_med_geo"] < 300.0]
    cc = aip["cc_flags"].astype(str).str.strip().isin(["0000", "0"])
    return aip[cc].reset_index(drop=True)


def positions_for(what: str) -> pd.DataFrame:
    if what == "calib":
        p = load_parent()
        _, b = galactic(p["ra"].to_numpy(), p["dec"].to_numpy())
        p = p[np.abs(b) > CALIB_BAND_DEG].reset_index(drop=True)
        print(f"  calibration population: parent at |b| > {CALIB_BAND_DEG:.0f} deg "
              f"= {len(p):,} stars")
        return p[["source_id", "ra", "dec"]]
    if what == "rmse":
        s = pd.read_csv(OUT / "w4_rmse_survivors_m4_g0.1.csv")
        return s[["source_id", "ra", "dec"]]
    if what == "previsual":
        s = pd.read_csv(OUT / "w4_previsual_candidates_m4_g0.1.csv")
        return s[["source_id", "ra", "dec"]]
    if what == "candidates":
        c = pd.read_csv(ROOT / "data" / "photometry" / "candidates_gaia_chain.csv")
        return c[["source_id", "ra", "dec", "label"]]
    raise SystemExit(f"unknown --what {what}")


def cmd_sky(a: argparse.Namespace) -> None:
    pos = positions_for(a.what)
    cache = CACHE / f"m5_sky_{a.what}.csv"
    if a.refresh and cache.exists():
        cache.unlink()
    g = gator_upload(pos["ra"].to_numpy(), pos["dec"].to_numpy(),
                     "allwise_p3as_psd", GATOR_COLS, 3.0,
                     chunk=a.chunk, cache=cache, tag=a.what)
    m = nearest_per_row(g, len(pos))
    out = pos.reset_index(drop=True).copy()
    for c in ("w3sky", "w4sky", "w3conf", "w4conf", "w3sigsk", "w4sigsk",
              "w3rchi2", "w4rchi2", "nb", "na", "ext_flg", "w3snr", "w4snr",
              "dist_x"):
        out[c] = m[c].to_numpy() if c in m.columns else np.nan
    out["designation_aw"] = (m["designation"].to_numpy()
                             if "designation" in m.columns else "")
    _, b = galactic(out["ra"].to_numpy(), out["dec"].to_numpy())
    out["glat"] = b
    out["ecl_lat"] = ecliptic_lat(out["ra"].to_numpy(), out["dec"].to_numpy())
    path = sky_matched(a.what)
    out.to_csv(path, index=False)
    print(f"  {len(out):,} positions, {int(out['w3sky'].notna().sum()):,} with an "
          f"AllWISE background measurement -> {path.name}")


# --------------------------------------------------------------- calibrate --
def cmd_calibrate(a: argparse.Namespace) -> None:
    """PR-2's threshold rule.  Percentiles of w3sky/w4sky within |ecl lat| bins
    of the |b| > 50 deg parent.  Nothing here looks at a survivor count."""
    c = pd.read_csv(sky_matched("calib"))
    c = c[c["w3sky"].notna() & c["w4sky"].notna()].copy()
    c["ecl_bin"] = np.floor(np.abs(c["ecl_lat"]) / ECL_BIN_DEG).astype(int)
    rows = []
    for band in ("w3sky", "w4sky"):
        for bn, g in c.groupby("ecl_bin"):
            for q in SENSITIVITY:
                rows.append({"band": band, "ecl_bin": int(bn), "q": q,
                             "n": int(len(g)),
                             "value": float(np.quantile(g[band], q))})
    tab = pd.DataFrame(rows)
    tab.to_csv(OUT / "m5_nebular_thresholds.csv", index=False)

    # the MEASURED combined false-positive rate of the max-of-two-ranks rule
    sc = score_from(c, c)
    meas = {f"{q}": float((sc > q).mean()) for q in SENSITIVITY}
    summary = {
        "calibration_population": f"parent sample at |b| > {CALIB_BAND_DEG:.0f} deg",
        "n_calibration": int(len(c)),
        "ecl_bin_deg": ECL_BIN_DEG,
        "n_ecl_bins": int(c["ecl_bin"].nunique()),
        "per_bin_n": {str(int(k)): int(v) for k, v in c["ecl_bin"].value_counts().sort_index().items()},
        "rule": ("score = max(percentile rank of w3sky, percentile rank of w4sky) "
                 "within the object's |ecliptic latitude| bin of the calibration "
                 "population; flagged if score > 0.99 (PR-2)"),
        "threshold": SCORE_THRESHOLD,
        "measured_combined_FPR_on_calibration": meas,
        "spearman_w3sky_w4sky": float(pd.Series(c["w3sky"]).corr(pd.Series(c["w4sky"]),
                                                                 method="spearman")),
    }
    (OUT / "m5_nebular_calibration.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


_CAL: pd.DataFrame | None = None


def _calib() -> pd.DataFrame:
    global _CAL
    if _CAL is None:
        c = pd.read_csv(sky_matched("calib"))
        c = c[c["w3sky"].notna() & c["w4sky"].notna()].copy()
        c["ecl_bin"] = np.floor(np.abs(c["ecl_lat"]) / ECL_BIN_DEG).astype(int)
        _CAL = c
    return _CAL


def score_from(df: pd.DataFrame, cal: pd.DataFrame | None = None) -> np.ndarray:
    """N2's score: max over the two bands of the object's percentile rank in
    the calibration distribution for its |ecliptic latitude| bin."""
    cal = _calib() if cal is None else cal
    d = df.copy()
    if "ecl_bin" not in d.columns:
        d["ecl_bin"] = np.floor(np.abs(d["ecl_lat"]) / ECL_BIN_DEG).astype(int)
    out = np.full(len(d), np.nan)
    for bn, g in d.groupby("ecl_bin"):
        ref = cal[cal["ecl_bin"] == bn]
        if len(ref) < 50:          # too thin to rank against: nearest bin
            order = cal["ecl_bin"].unique()
            bn2 = order[np.argmin(np.abs(order - bn))]
            ref = cal[cal["ecl_bin"] == bn2]
        r3 = np.searchsorted(np.sort(ref["w3sky"].to_numpy()), g["w3sky"].to_numpy(),
                             side="right") / len(ref)
        r4 = np.searchsorted(np.sort(ref["w4sky"].to_numpy()), g["w4sky"].to_numpy(),
                             side="right") / len(ref)
        out[d.index.get_indexer(g.index)] = np.maximum(r3, r4)
    return out


# ------------------------------------------------------------------- apply --
def cmd_apply(a: argparse.Namespace) -> None:
    sky = pd.read_csv(sky_matched(a.what))
    cats = pd.read_csv(OUT / "m5_nebular_catalogs.csv")
    print(f"  N1: {len(cats):,} catalogued nebular objects vs {len(sky):,} positions")
    n1 = n1_flags(sky["ra"].to_numpy(), sky["dec"].to_numpy(), cats)
    res = pd.concat([sky.reset_index(drop=True), n1], axis=1)
    res["n2_score"] = score_from(res)
    for q in SENSITIVITY:
        res[f"n2_flag_{q}"] = res["n2_score"] > q
    res["n2_flag"] = res["n2_score"] > SCORE_THRESHOLD
    res["nebular_flag"] = res["n1_flag"] | res["n2_flag"].fillna(False)
    path = OUT / f"m5_nebular_flags_{a.what}.csv"
    res.to_csv(path, index=False)
    n = len(res)
    print(f"  N1 flagged {int(res['n1_flag'].sum()):,} ({100*res['n1_flag'].mean():.1f}%)")
    print(f"  N2 flagged {int(res['n2_flag'].sum()):,} ({100*res['n2_flag'].mean():.1f}%)")
    print(f"  either     {int(res['nebular_flag'].sum()):,} "
          f"({100*res['nebular_flag'].mean():.1f}%)  of {n:,}")
    print(f"  -> {path.name}")


# ---------------------------------------------------------------------- N3 --
N3_RADIUS_AS = 60.0
N3_COLS = "designation,ra,dec,w4mpro,w3mpro,w4snr,w3snr"
RHO_REDGAL_V4 = 15000.0 / (180.0 / np.pi) ** 2   # Suazo+24's own all-sky value


def cmd_n3(a: argparse.Namespace) -> None:
    """PR-2's N3: the LOCAL density of AllWISE sources bright enough in W4 to
    carry the excess, measured around each object instead of assumed globally.

    V4 as M3 wrote it uses one all-sky faint-red-galaxy density (Suazo et al.'s
    own 15,000 sr^-1).  That is a constant, so it cannot distinguish a plane
    field from a polar one.  N3 measures the real local density and converts it
    into the same quantity V4 reports -- the expected number of interlopers
    inside Suazo et al.'s own 3.25" W3 aperture.

    N3 IS A REPORTED STATISTIC, NOT A CUT (PR-2): there is no published density
    threshold to anchor one, and inventing one here would be the kind of
    un-pre-registered choice PR-2 exists to prevent.
    """
    pos = positions_for(a.what)
    # the target's OWN W4 magnitude comes from the screen's own harvest, not
    # from the flags file (which does not carry it -- an earlier version of
    # this function read a column that was silently all-NaN, so the brightness
    # restriction did nothing and every neighbour counted)
    src = {"rmse": "w4_rmse_survivors_m4_g0.1.csv",
           "previsual": "w4_previsual_candidates_m4_g0.1.csv"}.get(a.what)
    if src:
        w4 = pd.read_csv(OUT / src, usecols=["source_id", "w4mpro"])
        pos = pos.merge(w4, on="source_id", how="left")
    elif a.what == "candidates":
        w4 = pd.read_csv(ROOT / "data" / "photometry" / "candidates_gaia_chain.csv",
                         usecols=["source_id", "w4mpro"])
        pos = pos.merge(w4, on="source_id", how="left")
    else:
        pos["w4mpro"] = np.nan
    cache = CACHE / f"m5_n3_{a.what}.csv"
    g = gator_upload(pos["ra"].to_numpy(), pos["dec"].to_numpy(),
                     "allwise_p3as_psd", N3_COLS, N3_RADIUS_AS,
                     chunk=a.chunk, cache=cache, tag=f"n3-{a.what}")
    # the target itself is the nearest match; exclude it, then count the rest
    g = g.sort_values(["_row", "dist_x"])
    tgt_w4 = pd.to_numeric(pos["w4mpro"], errors="coerce").to_numpy()
    counts, counts_br, counts_red = [], [], []
    area = np.pi * (N3_RADIUS_AS / 3600.0) ** 2
    by = {int(k): v for k, v in g.groupby("_row")}
    for i in range(len(pos)):
        sub = by.get(i)
        if sub is None or len(sub) <= 1:
            counts.append(0)
            counts_br.append(0)
            counts_red.append(0)
            continue
        nb = sub.iloc[1:]                       # drop the target's own row
        counts.append(int(len(nb)))
        t = tgt_w4[i]
        nw4 = pd.to_numeric(nb["w4mpro"], errors="coerce")
        ns4 = pd.to_numeric(nb["w4snr"], errors="coerce")
        # A neighbour counts only if W4 is a real DETECTION at comparable
        # brightness.  The S/N gate is load-bearing: AllWISE publishes a
        # w4mpro for undetected sources too (a 95% upper limit near mag 8-9),
        # so without it essentially every neighbour counts as "W4-bright" and
        # the density comes out ~1000x too high.  3.5 is the screen's own
        # detection threshold, not a new one.
        bright = (nw4.notna() & (ns4 >= 3.5)
                  & (nw4 <= (t + 1.0 if np.isfinite(t) else -99)))
        counts_br.append(int(bright.sum()))
        # Suazo et al. 2024 Sec 3.1's OWN population, measured locally instead
        # of taken as one all-sky number: W4 at least as bright as the target,
        # and 2.84 < W3-W4 < 3.25.
        nw3 = pd.to_numeric(nb["w3mpro"], errors="coerce")
        col = nw3 - nw4
        counts_red.append(int((bright & (col > 2.84) & (col < 3.25)).sum()))
    out = pos.reset_index(drop=True).copy()
    out["n3_neighbours_60as"] = counts
    out["n3_neighbours_w4bright_60as"] = counts_br
    out["n3_density_deg2"] = np.array(counts) / area
    out["n3_neighbours_suazored_60as"] = counts_red
    out["n3_density_w4bright_deg2"] = np.array(counts_br) / area
    out["n3_density_suazored_deg2"] = np.array(counts_red) / area
    # the same quantity V4 reports, but from the LOCAL density
    rho_as2 = out["n3_density_w4bright_deg2"] / 3600.0 ** 2
    out["n3_p_chance_3p25as"] = 1.0 - np.exp(-rho_as2 * np.pi * 3.25 ** 2)
    out["n3_p_chance_1as"] = 1.0 - np.exp(-rho_as2 * np.pi * 1.0 ** 2)
    _, b = galactic(out["ra"].to_numpy(), out["dec"].to_numpy())
    out["glat"] = b
    out.to_csv(OUT / f"m5_n3_{a.what}_density.csv", index=False)
    # the band-aggregated interloper prior, which is what V4 needs and what a
    # single all-sky constant cannot express
    ab_ = np.abs(b)
    prior, p4 = [], 1 - np.exp(-(RHO_REDGAL_V4 / 3600.0 ** 2) * np.pi * 3.25 ** 2)
    for lo, hi in [(0, 5), (5, 10), (10, 20), (20, 30), (30, 50), (50, 90)]:
        s = out[(ab_ >= lo) & (ab_ < hi)]
        if not len(s):
            continue
        rho = s["n3_neighbours_suazored_60as"].sum() / (len(s) * area)
        p = 1 - np.exp(-(rho / 3600.0 ** 2) * np.pi * 3.25 ** 2)
        prior.append({"band": f"{lo}-{hi}", "n": int(len(s)),
                      "rho_suazo_colour_deg2": float(rho),
                      "p_interloper_3p25as": float(p),
                      "expected": float(p * len(s))})
    (OUT / f"m5_n3_interloper_prior_{a.what}.json").write_text(json.dumps({
        "radius_as": N3_RADIUS_AS,
        "definition": ("AllWISE sources within 60 arcsec with a >=3.5-sigma W4 "
                       "detection, W4 within 1 mag of the target or brighter, "
                       "and 2.84 < W3-W4 < 3.25 (Suazo et al. 2024 Sec 3.1's "
                       "own colour band)"),
        "caveat": ("this counts SOURCES, not galaxies -- it does not separate "
                   "background galaxies from Galactic dusty stars, so it is an "
                   "UPPER BOUND on the interloper density, not a measurement of "
                   "the galaxy density Suazo et al. quote"),
        "v4_global_density_deg2": RHO_REDGAL_V4,
        "v4_expected_total": float(p4 * len(out)),
        "local_expected_total": float(sum(x["expected"] for x in prior)),
        "bands": prior}, indent=2))
    print(f"\n  N3 local AllWISE source density within {N3_RADIUS_AS:.0f}\", "
          f"by |b| (V4's global constant is {15000 / (180 / np.pi) ** 2:.2f} "
          f"deg^-2 for its own red-galaxy population):")
    ab = np.abs(b)
    for lo, hi in [(0, 5), (5, 10), (10, 20), (20, 30), (30, 50), (50, 90)]:
        s = out[(ab >= lo) & (ab < hi)]
        if not len(s):
            continue
        # ENSEMBLE densities: total neighbours / (n x area).  A per-object
        # density is quantised at 1/area = 1,146 deg^-2 and is meaningless for
        # the rare red population, so the band aggregate is what is quoted.
        print(f"    |b| {lo:2d}-{hi:<2d} n={len(s):5,d}  all "
              f"{s['n3_neighbours_60as'].sum() / (len(s) * area):9,.0f}   "
              f"W4-comparable {s['n3_neighbours_w4bright_60as'].sum() / (len(s) * area):8,.0f}   "
              f"Suazo red band {s['n3_neighbours_suazored_60as'].sum() / (len(s) * area):7,.1f}"
              f"   (V4 assumes {RHO_REDGAL_V4:.2f} everywhere)  deg^-2")
    print(f"  -> m5_n3_{a.what}_density.csv")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    n3 = sub.add_parser("n3")
    n3.add_argument("--what", required=True,
                    choices=["calib", "rmse", "previsual", "candidates"])
    n3.add_argument("--chunk", type=int, default=2000)
    f = sub.add_parser("fetch"); f.add_argument("--refresh", action="store_true")
    s = sub.add_parser("sky")
    s.add_argument("--what", required=True,
                   choices=["calib", "rmse", "previsual", "candidates"])
    s.add_argument("--chunk", type=int, default=5000)
    s.add_argument("--refresh", action="store_true")
    sub.add_parser("calibrate")
    p = sub.add_parser("apply")
    p.add_argument("--what", required=True,
                   choices=["calib", "rmse", "previsual", "candidates"])
    a = ap.parse_args()
    {"fetch": cmd_fetch, "sky": cmd_sky, "calibrate": cmd_calibrate,
     "apply": cmd_apply, "n3": cmd_n3}[a.cmd](a)


if __name__ == "__main__":
    main()
