"""M2 step 1: assemble the vetting evidence for a pre-registered sample.

Protocol is frozen in M2-01-preregistration.md, Part A.  This script only
ASSEMBLES evidence -- it makes no classification.  The classification is a human
(agent) act recorded in out/m2_vetting.csv.

Evidence per object (M2-01 A2):
  E1  ZTF cutout triplet science/template/difference, one zscale stretch
  E2  per-band light curve, magpsf vs MJD, with the per-band magnr level
  E3  alert diagnostics at the trigger epoch
  E4  archival cross-match via CDS X-Match: Gaia DR3, Gaia DR3 vclassre, VSX,
      ATLAS variable stars, 2MASS, PS1

Everything tokenless.  No TNS path is touched at all.

usage:
    python m2_vet_evidence.py sample          # execute the pre-registered draw
    python m2_vet_evidence.py build <listfile> <tag>
"""

from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cache_contract import (  # noqa: E402
    canonical_digest,
    load_cache_contract,
    load_proved_output,
    sha256_file,
    sidecar_path,
    validated_tag,
    write_cache,
)
from m1_fetch_fink import (  # noqa: E402
    HISTORY_MAX_AGE_SECONDS,
    cache_provenance,
    fetch_histories_batch,
    history_as_of,
    require_single_jd_ceiling,
)
from tnscommon import DATA, OUT, session, write_text  # noqa: E402

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

FINK_CUT = "https://api.ztf.fink-portal.org/api/v1/cutouts"
XMATCH = "http://cdsxmatch.u-strasbg.fr/xmatch/api/v1/sync"

VET = OUT / "vet"
VET.mkdir(parents=True, exist_ok=True)
CUTCACHE = DATA / "cutouts"
CUTCACHE.mkdir(parents=True, exist_ok=True)

BANDS = {1: ("g", "tab:green"), 2: ("r", "tab:red"), 3: ("i", "tab:orange")}

# --- E4 catalogue panel, exactly as pre-registered ---------------------------
XCATS = [
    ("gaia",     "vizier:I/355/gaiadr3",         3.0,
     ["DR3Name", "Plx", "e_Plx", "pmRA", "pmDE", "Gmag", "BP-RP"]),
    ("gaiavar",  "vizier:I/358/vclassre",        3.0, ["Class", "ClassSc"]),
    ("vsx",      "vizier:B/vsx/vsx",             5.0, ["Name", "Type", "max", "min", "Period"]),
    ("atlasvs",  "vizier:J/AJ/156/241/table4",   5.0, ["ATOID", "Class", "fp-lngfitper"]),
    ("2mass",    "vizier:II/246/out",            3.0, ["2MASS", "Jmag", "Hmag", "Kmag"]),
    ("ps1",      "vizier:II/349/ps1",            3.0, ["objID", "gmag", "rmag", "imag"]),
]


def authenticate_candidate_list(path: Path) -> dict | None:
    """Require output+summary proof when a final M1/M2 candidate CSV is read."""
    kinds = {
        "m1_candidates_": "m1_candidate_output",
        "m2_candidates_": "m2_candidate_output",
    }
    for prefix, kind in kinds.items():
        if path.name.startswith(prefix) and path.suffix.lower() == ".csv":
            return load_proved_output(
                path,
                path.with_suffix(".json"),
                kind=kind,
            )
    return None


# --------------------------------------------------------------------------- #
# the pre-registered draw
# --------------------------------------------------------------------------- #
def draw_sample() -> pd.DataFrame:
    candidate_path = OUT / "m1_candidates_recent.csv"
    proof = authenticate_candidate_list(candidate_path)
    c = pd.read_csv(candidate_path)
    if proof is not None and len(c) != int(proof["row_count"]):
        raise RuntimeError(f"candidate output row-count mismatch: {candidate_path}")
    if "history_jd_ceiling" not in c.columns:
        raise RuntimeError(
            "m1_candidates_recent.csv predates history ceilings; rebuild M1 first"
        )
    require_single_jd_ceiling(
        c["history_jd_ceiling"].tolist(), "m1_candidates_recent.csv"
    )
    ab = c[c["tier"].isin(["A", "B"])].copy()
    tc = c[c["tier"] == "C"].copy()
    rng = np.random.default_rng(20260824)          # M2-01 A1, frozen
    oids = sorted(tc["oid"].tolist())
    pick = rng.choice(oids, size=32, replace=False)
    sel = pd.concat([ab, tc[tc["oid"].isin(pick)]], ignore_index=True)
    sel["stratum"] = sel["tier"]
    sel.to_csv(OUT / "m2_vet_sample.csv", index=False, lineterminator="\n")
    print(f"pre-registered draw: {len(ab)} tier A/B (census) + {len(pick)} tier C "
          f"= {len(sel)} objects")
    print("tier C draw:", ", ".join(sorted(pick)))
    return sel


# --------------------------------------------------------------------------- #
# E1 / E2 / E3 -- Fink
# --------------------------------------------------------------------------- #
def fetch_alerts_batch(
    s: requests.Session,
    oids: list[str],
    chunk: int = 60,
    *,
    refresh: bool = True,
    required_coverage_jd: float | None = None,
) -> dict:
    """Load live-fresh histories; abort rather than render outage-shaped evidence."""
    histories = fetch_histories_batch(
        s,
        oids,
        chunk=chunk,
        refresh=refresh,
        max_age_seconds=HISTORY_MAX_AGE_SECONDS,
        required_coverage_jd=required_coverage_jd,
    )
    return {oid: pd.DataFrame(records) for oid, records in histories.items()}


def _valid_cutout(array: np.ndarray) -> bool:
    return (
        isinstance(array, np.ndarray)
        and array.ndim == 2
        and min(array.shape) > 1
        and bool(np.isfinite(array).any())
    )


def _cutout_contract(oid: str, candid: str) -> dict:
    return {
        "source_url": FINK_CUT,
        "object_id": str(oid),
        "candid": str(candid),
        "kinds": ["Science", "Template", "Difference"],
        "output_format": "array",
    }


def fetch_cutouts(s: requests.Session, oid: str, candid: str) -> dict:
    p = CUTCACHE / f"{oid}_{candid}.npz"
    cached = load_cache_contract(
        p,
        kind="fink_cutout_triplet",
        expected_contract=_cutout_contract(oid, candid),
    )
    if cached is not None:
        try:
            with np.load(p, allow_pickle=False) as archive:
                out = {key: archive[key] for key in archive.files}
        except (OSError, ValueError) as exc:
            raise RuntimeError(f"invalid cutout archive {p}: {exc}") from exc
        if set(out) != {"Science", "Template", "Difference"} or not all(
            _valid_cutout(array) for array in out.values()
        ):
            raise RuntimeError(f"cutout cache fails structural validation: {p}")
        return out
    out = {}
    for kind in ("Science", "Template", "Difference"):
        arr: np.ndarray | None = None
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                body = {"objectId": oid, "kind": kind, "output-format": "array"}
                if candid:
                    body["candid"] = str(candid)
                r = s.post(FINK_CUT, json=body, timeout=180)
                if r.status_code != 200:
                    raise RuntimeError(f"HTTP {r.status_code}")
                j = r.json()
                if not isinstance(j, dict) or len(j) != 1:
                    raise RuntimeError("unexpected cutout JSON schema")
                arr = np.asarray(next(iter(j.values())), dtype=float)
                if not _valid_cutout(arr):
                    raise RuntimeError(
                        f"invalid {kind} cutout shape/content {getattr(arr, 'shape', None)}"
                    )
                break
            except (requests.RequestException, ValueError, TypeError, RuntimeError) as exc:
                last_error = exc
                arr = None
                if attempt + 1 < 3:
                    time.sleep(2 * (attempt + 1))
        if arr is None:
            raise RuntimeError(
                f"failed to fetch valid {kind} cutout for {oid}/{candid}; "
                "evidence build aborted and no null image was cached"
            ) from last_error
        out[kind] = arr
    buffer = io.BytesIO()
    np.savez_compressed(buffer, **out)
    write_cache(
        p,
        buffer.getvalue(),
        kind="fink_cutout_triplet",
        contract=_cutout_contract(oid, candid),
    )
    return out


def zscale(a: np.ndarray, contrast: float = 0.25) -> tuple[float, float]:
    """Approximate IRAF zscale: robust linear fit to the sorted pixel values."""
    v = a[np.isfinite(a)].ravel()
    if v.size < 10:
        return 0.0, 1.0
    v = np.sort(v)
    n = v.size
    mid = n // 2
    x = np.arange(n) - mid
    # iterative clip
    keep = np.ones(n, bool)
    for _ in range(5):
        sl, ic = np.polyfit(x[keep], v[keep], 1)
        res = v - (sl * x + ic)
        sd = res[keep].std()
        if sd == 0:
            break
        keep = np.abs(res) < 2.5 * sd
        if keep.sum() < n * 0.2:
            break
    med = np.median(v)
    z1 = med + (sl / max(contrast, 1e-3)) * (-mid)
    z2 = med + (sl / max(contrast, 1e-3)) * (n - 1 - mid)
    if not np.isfinite(z1) or not np.isfinite(z2) or z2 <= z1:
        z1, z2 = np.percentile(v, [1, 99])
    return float(z1), float(z2)


# --------------------------------------------------------------------------- #
# E4 -- CDS X-Match
# --------------------------------------------------------------------------- #
def _xmatch_contract(pos: pd.DataFrame) -> dict:
    required = {"id", "oid", "ra", "dec"}
    if not required.issubset(pos.columns):
        raise RuntimeError(f"xmatch input lacks columns {sorted(required - set(pos.columns))}")
    records = []
    seen_ids: set[int] = set()
    seen_oids: set[str] = set()
    for row in pos[list(required)].itertuples(index=False):
        values = row._asdict()
        ident = int(values["id"])
        oid = str(values["oid"])
        ra, dec = float(values["ra"]), float(values["dec"])
        if ident in seen_ids or oid in seen_oids or not np.isfinite([ra, dec]).all():
            raise RuntimeError("xmatch input IDs/OIDs must be unique with finite positions")
        seen_ids.add(ident)
        seen_oids.add(oid)
        records.append({"id": ident, "oid": oid, "ra": ra, "dec": dec})
    catalogues = [
        {"name": name, "catalogue": cat, "radius_arcsec": rad, "columns": cols}
        for name, cat, rad, cols in XCATS
    ]
    return {
        "source_url": XMATCH,
        "ordered_oid_position_sha256": canonical_digest(records),
        "n_positions": len(records),
        "catalogue_contract_sha256": canonical_digest(catalogues),
    }


def xmatch(s: requests.Session, pos: pd.DataFrame, tag: str) -> dict:
    """pos: columns id, oid, ra, dec. Returns {catname: DataFrame}."""
    tag = validated_tag(tag)
    cache = DATA / f"xmatch_{tag}.json"
    contract = _xmatch_contract(pos)
    cached = load_cache_contract(
        cache,
        kind="cds_xmatch_panel",
        expected_contract=contract,
    )
    if cached is not None:
        try:
            raw = json.loads(cache.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"invalid xmatch cache {cache}: {exc}") from exc
        if not isinstance(raw, dict) or set(raw) != {item[0] for item in XCATS}:
            raise RuntimeError(f"xmatch cache catalogue set mismatch: {cache}")
        return {key: pd.DataFrame(value) for key, value in raw.items()}
    body = pos[["id", "ra", "dec"]].to_csv(index=False)
    res = {}
    valid_ids = set(pd.to_numeric(pos["id"], errors="raise").astype(int))
    for name, cat, rad, cols in XCATS:
        df: pd.DataFrame | None = None
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                r = s.post(XMATCH,
                           data={"request": "xmatch", "distMaxArcsec": rad,
                                 "RESPONSEFORMAT": "csv", "cat2": cat,
                                 "colRA1": "ra", "colDec1": "dec"},
                           files={"cat1": ("cat1.csv", body, "text/csv")},
                           timeout=300)
                if r.status_code != 200:
                    raise RuntimeError(f"HTTP {r.status_code}")
                parsed = pd.read_csv(io.StringIO(r.text))
                expected_columns = {"id", "angDist", *cols}
                if not expected_columns.issubset(parsed.columns):
                    raise RuntimeError(
                        f"xmatch {name} response lacks columns "
                        f"{sorted(expected_columns - set(parsed.columns))}"
                    )
                if len(parsed):
                    ids = set(pd.to_numeric(parsed["id"], errors="raise").astype(int))
                    distances = pd.to_numeric(parsed["angDist"], errors="raise")
                    if (
                        not ids.issubset(valid_ids)
                        or not np.isfinite(distances).all()
                        or (distances < 0).any()
                        or (distances > float(rad) + 1e-9).any()
                    ):
                        raise RuntimeError(
                            f"xmatch {name} response has unknown IDs or distances "
                            f"outside [0, {rad}] arcsec"
                        )
                df = parsed
                break
            except (
                requests.RequestException,
                pd.errors.ParserError,
                pd.errors.EmptyDataError,
                ValueError,
                RuntimeError,
            ) as exc:
                last_error = exc
                df = None
                if attempt + 1 < 3:
                    time.sleep(3 * (attempt + 1))
        if df is None:
            raise RuntimeError(
                f"CDS X-Match failed for {name}; panel incomplete, no cache written"
            ) from last_error
        print(f"  xmatch {name}: {len(df)} rows")
        res[name] = df
        time.sleep(1.0)
    serialisable = {
        key: value.astype(object).where(pd.notna(value), None).to_dict("list")
        for key, value in res.items()
    }
    payload = json.dumps(
        serialisable,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    write_cache(
        cache,
        payload,
        kind="cds_xmatch_panel",
        contract=contract,
        row_count=sum(len(frame) for frame in res.values()),
    )
    return res


def summarise_xmatch(res: dict, oid_of: dict) -> pd.DataFrame:
    """One row per object, the E4 columns flattened, nearest match kept."""
    rows: dict[str, dict] = {o: {"oid": o} for o in oid_of.values()}
    for name, _cat, _rad, cols in XCATS:
        d = res.get(name, pd.DataFrame())
        if not len(d) or "id" not in d.columns:
            continue
        d = d.sort_values("angDist")
        for _id, g in d.groupby("id"):
            o = oid_of.get(int(_id))
            if o is None:
                continue
            top = g.iloc[0]
            rows[o][f"{name}_n"] = len(g)
            rows[o][f"{name}_sep"] = round(float(top["angDist"]), 2)
            for c in cols:
                if c in g.columns:
                    rows[o][f"{name}_{c}"] = top[c]
    return pd.DataFrame(list(rows.values()))


# --------------------------------------------------------------------------- #
# rendering
# --------------------------------------------------------------------------- #
def render_sheet(objs: list[dict], path: Path, title: str) -> None:
    n = len(objs)
    fig, axes = plt.subplots(n, 4, figsize=(15.5, 3.15 * n),
                             gridspec_kw={"width_ratios": [1, 1, 1, 2.6]})
    if n == 1:
        axes = np.array([axes])
    for i, ob in enumerate(objs):
        for j, kind in enumerate(("Science", "Template", "Difference")):
            ax = axes[i, j]
            a = ob["cut"].get(kind)
            if a is None or a.size <= 1:
                ax.text(.5, .5, "no cutout", ha="center", va="center", fontsize=9)
            else:
                if kind == "Difference":
                    # A difference stamp is noise centred on ~0 with the transient
                    # as a positive excursion.  zscale on it hides faint real
                    # sources AND hides dipoles.  Stretch symmetrically about the
                    # median in units of the robust noise instead, on a diverging
                    # map, so positive lobes are red, negative lobes are blue, and
                    # a bipolar subtraction residual is unmistakable.
                    v = a[np.isfinite(a)]
                    med = float(np.median(v))
                    sig = 1.4826 * float(np.median(np.abs(v - med))) or 1.0
                    ax.imshow(a, origin="lower", cmap="RdBu_r",
                              vmin=med - 6 * sig, vmax=med + 6 * sig,
                              interpolation="nearest")
                    ax.set_facecolor("w")
                    axes[i, j].set_xlabel(f"±6σ, σ={sig:.1f}", fontsize=6)
                else:
                    z1, z2 = zscale(a)
                    ax.imshow(a, origin="lower", cmap="gray", vmin=z1, vmax=z2,
                              interpolation="nearest")
                ax.plot(a.shape[1] / 2 - .5, a.shape[0] / 2 - .5, "+",
                        color="lime", ms=13, mew=1.3)
            ax.set_xticks([])
            ax.set_yticks([])
            if kind != "Difference":
                ax.set_xlabel("")
            ax.set_title(kind, fontsize=8, pad=2)
            if j == 0:
                ax.set_ylabel(f"{ob['oid']}\n[{ob['label']}]", fontsize=7.5)
        ax = axes[i, 3]
        lc = ob["lc"]
        if len(lc):
            for fid, (bn, col) in BANDS.items():
                g = lc[lc["_fid"] == fid]
                if not len(g):
                    continue
                ax.plot(g["_mjd"], g["_mag"], "o", ms=3, color=col, label=f"{bn}")
                mn = pd.to_numeric(g.get("i:magnr"), errors="coerce").median()
                if pd.notna(mn) and 0 < mn < 30:
                    ax.axhline(mn, color=col, ls=":", lw=1, alpha=.75)
            ax.axvline(ob["trigger_mjd"], color="k", ls="--", lw=.8, alpha=.6)
            ax.invert_yaxis()
            ax.legend(fontsize=6, loc="best", ncol=3, frameon=False)
        ax.set_xlabel("MJD", fontsize=7)
        ax.set_ylabel("mag", fontsize=7)
        ax.tick_params(labelsize=6.5)
        ax.set_title(ob["caption"], fontsize=7, loc="left")
    fig.suptitle(title, fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.985])
    fig.savefig(path, dpi=105)
    plt.close(fig)


def build(list_csv: Path, tag: str) -> None:
    tag = validated_tag(tag)
    proof = authenticate_candidate_list(list_csv)
    sel = pd.read_csv(list_csv)
    if proof is not None and len(sel) != int(proof["row_count"]):
        raise RuntimeError(f"candidate output row-count mismatch: {list_csv}")
    if "history_jd_ceiling" not in sel.columns:
        raise RuntimeError(
            f"{list_csv} predates history ceilings; rebuild its pool/candidate list"
        )
    jd_ceiling = require_single_jd_ceiling(
        sel["history_jd_ceiling"].tolist(), str(list_csv)
    )
    oids = sel["oid"].tolist()
    s = session()

    print(f"[{tag}] {len(oids)} objects")
    hist = fetch_alerts_batch(
        s,
        oids,
        refresh=True,
        required_coverage_jd=jd_ceiling,
    )

    pos = pd.DataFrame({"id": range(len(oids)), "oid": oids,
                        "ra": sel["ra"].values, "dec": sel["dec"].values})
    oid_of = {i: o for i, o in enumerate(oids)}
    xres = xmatch(s, pos, tag)
    xsum = summarise_xmatch(xres, oid_of)
    xsum.to_csv(OUT / f"m2_xmatch_{tag}.csv", index=False, lineterminator="\n")

    objs, diag = [], []
    for _, row in sel.iterrows():
        oid = row["oid"]
        records = hist.get(oid, pd.DataFrame()).to_dict("records")
        a = pd.DataFrame(history_as_of(records, jd_ceiling))
        trig_mjd = float(row["first_pass_jd"]) - 2400000.5 if pd.notna(
            row.get("first_pass_jd")) else np.nan
        candid = ""
        if len(a):
            a["_mjd"] = pd.to_numeric(a["i:jd"], errors="coerce") - 2400000.5
            a["_mag"] = pd.to_numeric(a["i:magpsf"], errors="coerce")
            a["_fid"] = pd.to_numeric(a.get("i:fid"), errors="coerce")
            a = a.dropna(subset=["_mjd"]).sort_values("_mjd")
            k = (a["_mjd"] - (trig_mjd if np.isfinite(trig_mjd)
                              else a["_mjd"].max())).abs().idxmin()
            candid = str(a.loc[k, "i:candid"]) if "i:candid" in a.columns else ""
            trg = a.loc[k]
        else:
            trg = pd.Series(dtype=object)
        if not candid:
            raise RuntimeError(
                f"no validated alert candid for {oid} at/before the history ceiling; "
                "cannot assemble required cutout evidence"
            )
        cut = fetch_cutouts(s, oid, candid)

        xr = xsum[xsum["oid"] == oid]
        xr = xr.iloc[0].to_dict() if len(xr) else {}
        cap = (f"{row['channel']} | b={row['gal_b']:.1f} | mag={row['mag_at_pass']:.1f}"
               f" | M1amp={row['outburst_amp']} | ndethist="
               f"{int(pd.to_numeric(trg.get('i:ndethist'), errors='coerce') or 0)}"
               f" | n_alerts={len(a)}")
        xbits = []
        for nm in ("vsx", "atlasvs", "gaiavar"):
            if pd.notna(xr.get(f"{nm}_sep", np.nan)):
                t = xr.get(f"{nm}_Type") or xr.get(f"{nm}_Class") or "?"
                xbits.append(f"{nm}:{t}@{xr[f'{nm}_sep']}\"")
        plx = xr.get("gaia_Plx")
        if pd.notna(plx):
            xbits.append(f"Plx={float(plx):.2f}")
        bprp = xr.get("gaia_BP-RP")
        if pd.notna(bprp):
            xbits.append(f"BP-RP={float(bprp):.2f}")
        jk = (pd.to_numeric(xr.get("2mass_Jmag"), errors="coerce")
              - pd.to_numeric(xr.get("2mass_Kmag"), errors="coerce"))
        if pd.notna(jk):
            xbits.append(f"J-K={float(jk):.2f}")
        if not xbits:
            xbits = ["no archival match"]
        cap += "\n" + " | ".join(xbits)

        objs.append({"oid": oid, "cut": cut, "lc": a, "trigger_mjd": trig_mjd,
                     "caption": cap, "label": row.get("stratum", row.get("tier", "?"))})
        diag.append({
            "oid": oid, "stratum": row.get("stratum", row.get("tier")),
            "candid": candid,
            "history_jd_ceiling": jd_ceiling,
            "ra": row["ra"], "dec": row["dec"], "gal_b": row["gal_b"],
            "channel": row["channel"], "mag_at_pass": row["mag_at_pass"],
            "m1_outburst_amp": row.get("outburst_amp"),
            "m1_ptp_60d": row.get("ptp_mag_60d"),
            "n_alerts_total": len(a),
            "drb": trg.get("i:drb"), "nbad": trg.get("i:nbad"),
            "fwhm": trg.get("i:fwhm"), "elong": trg.get("i:elong"),
            "distnr": trg.get("i:distnr"), "magnr": trg.get("i:magnr"),
            "sgscore1": trg.get("i:sgscore1"), "distpsnr1": trg.get("i:distpsnr1"),
            "ndethist": trg.get("i:ndethist"), "jdstarthist": trg.get("i:jdstarthist"),
            "hist_span_d": (float(pd.to_numeric(trg.get("i:jd"), errors="coerce")
                                  - pd.to_numeric(trg.get("i:jdstarthist"),
                                                  errors="coerce"))
                            if "i:jdstarthist" in trg else np.nan),
            **{k: v for k, v in xr.items() if k != "oid"},
        })

    pd.DataFrame(diag).to_csv(
        OUT / f"m2_vet_diag_{tag}.csv", index=False, lineterminator="\n"
    )
    manifest = {
        "tag": tag,
        "source_list": str(list_csv),
        "source_list_sha256": sha256_file(list_csv),
        "history_jd_ceiling": jd_ceiling,
        "history_as_of_mjd": jd_ceiling - 2400000.5,
        "history_cache_policy": {
            "refresh": True,
            "max_age_seconds": HISTORY_MAX_AGE_SECONDS,
            "required_coverage_jd": jd_ceiling,
        },
        "history_cache_provenance": cache_provenance(oids),
        "xmatch_cache_provenance": json.loads(
            sidecar_path(DATA / f"xmatch_{tag}.json").read_text(encoding="utf-8")
        ),
        "cutout_cache_provenance": {
            oid: json.loads(
                sidecar_path(CUTCACHE / f"{oid}_{candid}.npz").read_text(
                    encoding="utf-8"
                )
            )
            for oid, candid in [
                (item["oid"], str(item.get("candid", ""))) for item in diag
            ]
            if candid and sidecar_path(CUTCACHE / f"{oid}_{candid}.npz").exists()
        },
    }
    write_text(
        OUT / f"m2_vet_diag_{tag}.json", json.dumps(manifest, indent=2)
    )
    per = 4
    for i in range(0, len(objs), per):
        chunk = objs[i:i + per]
        p = VET / f"{tag}_sheet{i//per + 1:02d}.png"
        render_sheet(
            chunk,
            p,
            f"{tag} evidence sheet {i//per + 1} "
            f"(objects {i+1}-{i+len(chunk)} of {len(objs)}; "
            f"history through MJD {jd_ceiling - 2400000.5:.5f})",
        )
        print("  ->", p)


def main() -> None:
    cmd = sys.argv[1]
    if cmd == "sample":
        draw_sample()
    elif cmd == "build":
        build(Path(sys.argv[2]), validated_tag(sys.argv[3]))


if __name__ == "__main__":
    main()
