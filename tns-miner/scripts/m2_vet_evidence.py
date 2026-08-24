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
from tnscommon import DATA, OUT, session, write_text  # noqa: E402

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

FINK_OBJ = "https://api.ztf.fink-portal.org/api/v1/objects"
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


# --------------------------------------------------------------------------- #
# the pre-registered draw
# --------------------------------------------------------------------------- #
def draw_sample() -> pd.DataFrame:
    c = pd.read_csv(OUT / "m1_candidates_recent.csv")
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
def fetch_alerts_batch(s: requests.Session, oids: list[str], chunk: int = 60) -> dict:
    """Fink /objects accepts a comma-separated objectId list -- ~12x faster."""
    out: dict[str, pd.DataFrame] = {}
    for i in range(0, len(oids), chunk):
        part = oids[i:i + chunk]
        for attempt in range(3):
            try:
                r = s.post(FINK_OBJ, json={"objectId": ",".join(part),
                                           "output-format": "json",
                                           "withupperlim": "False"}, timeout=300)
                if r.status_code == 200:
                    d = pd.DataFrame(r.json())
                    if len(d):
                        for oid, g in d.groupby("i:objectId"):
                            out[str(oid)] = g.reset_index(drop=True)
                    break
            except requests.RequestException:
                pass
            time.sleep(3 * (attempt + 1))
        print(f"  fink batch {min(i+chunk, len(oids))}/{len(oids)}", flush=True)
    for o in oids:
        out.setdefault(o, pd.DataFrame())
    return out


def fetch_cutouts(s: requests.Session, oid: str, candid: str) -> dict:
    p = CUTCACHE / f"{oid}_{candid}.npz"
    if p.exists():
        z = np.load(p)
        return {k: z[k] for k in z.files}
    out = {}
    for kind in ("Science", "Template", "Difference"):
        arr = None
        for attempt in range(3):
            try:
                body = {"objectId": oid, "kind": kind, "output-format": "array"}
                if candid:
                    body["candid"] = str(candid)
                r = s.post(FINK_CUT, json=body, timeout=180)
                if r.status_code == 200:
                    j = r.json()
                    k = next(iter(j))
                    arr = np.array(j[k], dtype=float)
                    break
            except (requests.RequestException, StopIteration, ValueError):
                pass
            time.sleep(2 * (attempt + 1))
        out[kind] = arr if arr is not None else np.zeros((1, 1))
    np.savez_compressed(p, **out)
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
def xmatch(s: requests.Session, pos: pd.DataFrame, tag: str) -> dict:
    """pos: columns id, ra, dec.  Returns {catname: DataFrame}."""
    cache = DATA / f"xmatch_{tag}.json"
    if cache.exists():
        raw = json.loads(cache.read_text(encoding="utf-8"))
        return {k: pd.DataFrame(v) for k, v in raw.items()}
    body = pos[["id", "ra", "dec"]].to_csv(index=False)
    res = {}
    for name, cat, rad, _cols in XCATS:
        df = pd.DataFrame()
        for attempt in range(3):
            try:
                r = s.post(XMATCH,
                           data={"request": "xmatch", "distMaxArcsec": rad,
                                 "RESPONSEFORMAT": "csv", "cat2": cat,
                                 "colRA1": "ra", "colDec1": "dec"},
                           files={"cat1": ("cat1.csv", body, "text/csv")},
                           timeout=300)
                if r.status_code == 200:
                    df = pd.read_csv(io.StringIO(r.text))
                    break
            except (requests.RequestException, pd.errors.ParserError):
                pass
            time.sleep(3 * (attempt + 1))
        print(f"  xmatch {name}: {len(df)} rows")
        res[name] = df
        time.sleep(1.0)
    cache.write_text(json.dumps({k: v.to_dict("list") for k, v in res.items()}),
                     encoding="utf-8")
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
            ax.set_xticks([]); ax.set_yticks([])
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
    sel = pd.read_csv(list_csv)
    oids = sel["oid"].tolist()
    s = session()

    print(f"[{tag}] {len(oids)} objects")
    hist = fetch_alerts_batch(s, oids)

    pos = pd.DataFrame({"id": range(len(oids)), "ra": sel["ra"].values,
                        "dec": sel["dec"].values})
    oid_of = {i: o for i, o in enumerate(oids)}
    xres = xmatch(s, pos, tag)
    xsum = summarise_xmatch(xres, oid_of)
    xsum.to_csv(OUT / f"m2_xmatch_{tag}.csv", index=False, lineterminator="\n")

    objs, diag = [], []
    for _, row in sel.iterrows():
        oid = row["oid"]
        a = hist.get(oid, pd.DataFrame()).copy()
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
        cut = fetch_cutouts(s, oid, candid) if candid else {}

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

    pd.DataFrame(diag).to_csv(OUT / f"m2_vet_diag_{tag}.csv", index=False,
                              lineterminator="\n")
    per = 4
    for i in range(0, len(objs), per):
        chunk = objs[i:i + per]
        p = VET / f"{tag}_sheet{i//per + 1:02d}.png"
        render_sheet(chunk, p, f"{tag} evidence sheet {i//per + 1} "
                               f"(objects {i+1}-{i+len(chunk)} of {len(objs)})")
        print("  ->", p)


def main() -> None:
    cmd = sys.argv[1]
    if cmd == "sample":
        draw_sample()
    elif cmd == "build":
        build(Path(sys.argv[2]), sys.argv[3])


if __name__ == "__main__":
    main()
