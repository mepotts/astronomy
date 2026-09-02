"""M2 step 4: the final candidate list.

NOTHING HERE REPORTS ANYTHING.  This writes a CSV and a set of evidence sheets.
No TNS write path is imported, called or referenced anywhere in this repository;
the allowlist guard in tnscommon.py is untouched.

Per candidate: position, galactic latitude, magnitude and band at the passing
epoch, per-band amplitude above quiescence, the outburst history broken into
episodes, six archival cross-matches, every catalogue flag, the negative-fraction
diagnostic, the reason it passed, a plain-language one-liner, and the
pre-registered rank score of M2-01 B4.

usage: python m2_candidates.py <tag>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m1_filter as M1  # noqa: E402
from cache_contract import (  # noqa: E402
    atomic_write,
    canonical_digest,
    load_cache_contract,
    sha256_file,
    sidecar_path,
    validated_tag,
    write_cache,
)
from m1_fetch_fink import (  # noqa: E402
    HISTORY_MAX_AGE_SECONDS,
    cache_provenance,
    history_as_of,
    require_single_jd_ceiling,
)
from m2_pool import fetch_batch  # noqa: E402
from m2_vet_evidence import XCATS, summarise_xmatch, xmatch  # noqa: E402
from tns_candidate_match import apply_tns_contract, verified_provenance  # noqa: E402
from tnscommon import DATA, OUT, session  # noqa: E402

POOL = DATA / "pool"
EPISODE_GAP_DAYS = 30.0     # a gap longer than this separates outburst episodes
CANDIDATE_COLUMNS = [
    "rank_score", "oid", "STATUS", "arm", "ra", "dec", "gal_b", "channel",
    "history_jd_floor", "history_jd_ceiling",
    "reason", "mag_at_pass", "band_at_pass", "amp", "ptp_band",
    "n_outburst_episodes", "brightest_ever_mag", "hist_span_days",
    "neg_frac", "n_neg", "n_conf", "n_clean", "n_alerts", "ndethist",
    "drb", "sgscore1", "distpsnr1", "distnr", "magnr",
    "gaia_DR3Name", "gaia_Gmag", "gaia_Plx", "gaia_BP-RP", "JK",
    "gaiavar_Class", "vsx_Name", "vsx_Type", "vsx_sep",
    "atlasvs_Class", "atlasvs_sep", "ps1_sep",
    "flag_vsx", "flag_gcvs", "flag_known_cv", "flag_simbad", "simbad",
    "tns_frozen_nearest", "tns_frozen_sep_arcsec",
    "tns_current_nearest", "tns_current_sep_arcsec", "tns_current_match",
    "tns_snapshot_id", "tns_snapshot_jd", "tns_current_snapshot_id",
    "probably", "outburst_history", "fink_link", "first_pass_jd",
]


def _empty_candidates(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a schema-stable zero-row M2 candidate result."""
    return frame.iloc[0:0].reindex(columns=CANDIDATE_COLUMNS)


def _load_filtered(tag: str) -> pd.DataFrame:
    tag = validated_tag(tag)
    path = POOL / f"m2_filtered_{tag}.csv"
    manifest = OUT / f"m2_pool_{tag}.json"
    try:
        saved = json.loads(manifest.read_text(encoding="utf-8"))
        proved = saved["filtered_output_provenance"]
        contract = proved["contract"]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise RuntimeError(
            f"{manifest} does not prove a completed filtered pool; rerun m2_pool.py"
        ) from exc
    if saved.get("tag") != tag or contract.get("tag") != tag:
        raise RuntimeError(f"filtered pool tag mismatch for {tag}")
    if contract.get("mjd_window") != saved.get("mjd_window"):
        raise RuntimeError(f"filtered pool window mismatch for {tag}")
    for field in ("history_jd_floor", "history_jd_ceiling"):
        if float(contract.get(field, float("nan"))) != float(
            saved.get(field, float("nan"))
        ):
            raise RuntimeError(f"filtered pool {field} mismatch for {tag}")
    actual = load_cache_contract(
        path,
        kind="m2_filtered_pool",
        expected_contract=contract,
    )
    if actual != proved:
        raise RuntimeError(f"filtered pool proof does not match manifest for {tag}")
    try:
        frame = pd.read_csv(path)
    except (OSError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise RuntimeError(f"cannot parse proved filtered pool {path}") from exc
    if len(frame) != int(proved.get("row_count", -1)):
        raise RuntimeError(f"filtered pool row-count mismatch for {tag}")
    if len(frame):
        ceiling = require_single_jd_ceiling(
            frame["history_jd_ceiling"].tolist(), str(path)
        )
        if ceiling != float(saved["history_jd_ceiling"]):
            raise RuntimeError(f"filtered rows do not share manifest ceiling for {tag}")
    return frame


def _existing_tns_reference(tag: str) -> dict | None:
    tag = validated_tag(tag)
    manifest = OUT / f"m2_candidates_{tag}.tns-input.json"
    if not manifest.exists():
        return None
    try:
        saved = json.loads(manifest.read_text(encoding="utf-8"))
        reference = saved["frozen_dedupe"]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise RuntimeError(f"invalid frozen TNS input manifest {manifest}") from exc
    if not isinstance(reference, dict):
        raise RuntimeError(f"invalid frozen TNS reference in {manifest}")
    return reference


def _pin_tns_reference(tag: str, jd_ceiling: float) -> dict:
    tag = validated_tag(tag)
    existing = _existing_tns_reference(tag)
    if existing is not None:
        saved = json.loads(
            (OUT / f"m2_candidates_{tag}.tns-input.json").read_text(encoding="utf-8")
        )
        if float(saved.get("history_jd_ceiling", float("nan"))) != float(jd_ceiling):
            raise RuntimeError(f"TNS input manifest ceiling mismatch for tag {tag}")
        verified_provenance(existing, jd_ceiling)
        return existing
    frozen, _current = verified_provenance(None, jd_ceiling)
    manifest = {
        "schema_version": 1,
        "tag": tag,
        "history_jd_ceiling": jd_ceiling,
        "frozen_dedupe": frozen,
    }
    atomic_write(
        OUT / f"m2_candidates_{tag}.tns-input.json",
        (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return frozen


def _source_jd_ceiling(tag: str, frame: pd.DataFrame) -> float:
    tag = validated_tag(tag)
    if "history_jd_ceiling" in frame.columns and len(frame):
        return require_single_jd_ceiling(
            frame["history_jd_ceiling"].tolist(), f"m2_filtered_{tag}.csv"
        )
    manifest = OUT / f"m2_pool_{tag}.json"
    if not manifest.exists():
        raise RuntimeError(
            f"no history ceiling for {tag}; rerun m2_pool.py before candidates"
        )
    saved = json.loads(manifest.read_text(encoding="utf-8"))
    try:
        return require_single_jd_ceiling(
            [saved["history_jd_ceiling"]], str(manifest)
        )
    except KeyError as exc:
        raise RuntimeError(
            f"{manifest} predates history ceilings; rerun m2_pool.py"
        ) from exc


def episodes(a: pd.DataFrame) -> tuple[str, int, float]:
    """Split the clean detection history into outburst episodes.

    This is the thing M1 could not report: whether a source has erupted before,
    how often, and how bright it got each time.  Descriptive only -- no threshold.
    """
    if not len(a):
        return "", 0, float("nan")
    d = a.copy()
    d["_mjd"] = pd.to_numeric(d["i:jd"], errors="coerce") - 2400000.5
    d["_mag"] = pd.to_numeric(d["i:magpsf"], errors="coerce")
    d = d.dropna(subset=["_mjd", "_mag"]).sort_values("_mjd")
    if not len(d):
        return "", 0, float("nan")
    grp = (d["_mjd"].diff().fillna(0) > EPISODE_GAP_DAYS).cumsum()
    out, peaks = [], []
    for _g, e in d.groupby(grp):
        out.append(f"MJD {e['_mjd'].min():.1f}-{e['_mjd'].max():.1f} "
                   f"peak {e['_mag'].min():.2f} ({len(e)} det)")
        peaks.append(float(e["_mag"].min()))
    return " | ".join(out[-8:]), len(out), (min(peaks) if peaks else float("nan"))


def one_liner(r: pd.Series) -> str:
    ch, b, amp = r["channel"], r.get("gal_b"), r.get("amp")
    mag, ptp = r.get("mag_at_pass"), r.get("ptp_band")
    plane = pd.notna(b) and abs(b) < M1.GAL_PLANE_ABS_B
    where = (f"in the galactic plane (|b| = {abs(b):.1f} deg)" if plane
             else f"at |b| = {abs(b):.1f} deg" if pd.notna(b) else "at an unknown latitude")
    bits = []
    if str(r.get("flag_known_cv") or "") not in ("", "nan"):
        bits.append("ALREADY CATALOGUED AS A CV -- the outburst is real but the "
                    "object is not new; do NOT file an AT report")
    if pd.isna(r.get("gaia_DR3Name")) or not str(r.get("gaia_DR3Name") or ""):
        bits.append("no Gaia DR3 counterpart within 3 arcsec, so the quiescent "
                    "source is fainter than G~21 -- consistent with a CV or nova "
                    "progenitor")
    else:
        bits.append(f"a Gaia DR3 star sits at this position (G={r.get('gaia_Gmag')})")
    if pd.notna(r.get("atlasvs_sep")):
        bits.append(f"ATLAS variable-star counterpart {r['atlasvs_sep']}\" away "
                    f"(class {r.get('atlasvs_Class')})")
    jk = r.get("JK")
    if pd.notna(jk) and jk > 1.0 and pd.notna(r.get("gaia_BP-RP")) \
            and float(r["gaia_BP-RP"]) > 2.0:
        bits.append("VERY RED (J-K > 1, BP-RP > 2) -- the classic Mira false "
                    "positive; colour-check before doing anything")

    if ch == "A1_cv_outburst":
        head = (f"a point source has brightened by {amp:.1f} mag above its "
                f"quiescent level {where}, now at mag {mag:.1f}")
        guess = ("dwarf-nova outburst or classical nova" if plane
                 else "dwarf-nova outburst or a flare star")
    elif ch == "A2_nova_like":
        head = (f"a new point source with nothing in Pan-STARRS within 3 arcsec "
                f"{where}, mag {mag:.1f}, first detected "
                f"{r.get('hist_span_days')} d ago")
        guess = ("classical-nova shaped" if plane else
                 "a nova, a faint CV, or a supernova in an uncatalogued host")
    elif str(ch).startswith("B_"):
        head = f"inside the {str(ch)[2:]} field at mag {mag:.1f}"
        guess = "M31/M81 novae peak near this brightness"
    elif ch == "D_galactic_plane":
        head = f"{where}, mag {mag:.1f}"
        guess = "the survey pipelines report almost nothing from here at any magnitude"
    else:
        head = f"faint residue at mag {mag:.1f} {where}"
        guess = "no catalogue counterpart"
    if pd.notna(ptp):
        head += f", varying {ptp:.2f} mag peak-to-peak within one band"
    return f"{head}; {guess}. " + ". ".join(bits) + "."


def rank_score(c: pd.DataFrame) -> pd.Series:
    """M2-01 B4, declared before the list existed.  A presentation order, not a
    threshold -- nothing is removed by the score."""
    amp = pd.to_numeric(c["amp"], errors="coerce").fillna(0).clip(0, 5)
    ptp = pd.to_numeric(c["ptp_band"], errors="coerce").fillna(0).clip(0, 2)
    b = pd.to_numeric(c["gal_b"], errors="coerce").abs()
    ndet = pd.to_numeric(c["ndethist"], errors="coerce").fillna(0)
    ch = c["channel"].astype(str)
    uncat = (c["atlasvs_sep"].isna() & c["vsx_sep"].isna()
             & c["gaiavar_Class"].isna())
    knowncv = c["flag_known_cv"].astype(str).replace("nan", "") != ""
    return (2.0 * amp / 5
            + 1.5 * (b < M1.GAL_PLANE_ABS_B).astype(float)
            + 1.0 * (ch.str.startswith("A2") | ch.str.startswith("B_")).astype(float)
            + 1.0 * ptp / 2
            + 0.5 * uncat.astype(float)
            - 2.0 * knowncv.astype(float)
            - 1.0 * (ndet > 100).astype(float)).round(3)


def build(tag: str, *, tns_reference: dict | None = None) -> pd.DataFrame:
    tag = validated_tag(tag)
    res = _load_filtered(tag).drop_duplicates(subset=["oid"])
    if "history_jd_ceiling" not in res.columns and len(res):
        raise RuntimeError(
            f"m2_filtered_{tag}.csv predates history ceilings; rerun m2_pool.py first"
        )
    jd_ceiling = _source_jd_ceiling(tag, res)
    pinned_reference = _pin_tns_reference(tag, jd_ceiling)
    if tns_reference is not None and tns_reference != pinned_reference:
        raise RuntimeError(f"caller supplied a different frozen TNS snapshot for {tag}")
    tns_reference = pinned_reference
    c = res[res["passed"] == True].copy()  # noqa: E712
    print(f"{tag}: {len(res)} pool objects, {len(c)} pass the M2 filter "
          f"({int(res['m1_passed'].sum())} would pass the M1 baseline)")
    if not len(c):
        return _empty_candidates(c)

    # --- Layer 6: frozen historical membership, current status annotation -----
    c, tns_contract = apply_tns_contract(
        c,
        frozen_reference=tns_reference,
        jd_ceiling=jd_ceiling,
        match_arcsec=M1.TNS_MATCH_ARCSEC,
    )
    print(
        f"  {tns_contract['n_removed_frozen_discovery_date_bounded']} frozen TNS "
        f"dedupe matches within {M1.TNS_MATCH_ARCSEC}\" -- removed; current-only matches "
        "remain flagged"
    )
    c = c.reset_index(drop=True)
    if not len(c):
        return _empty_candidates(c)

    # --- archival cross-match, the panel M2-02 proved the filter needs ---------
    s = session()
    pos = pd.DataFrame({"id": range(len(c)), "oid": c["oid"].values,
                        "ra": c["ra"].values, "dec": c["dec"].values})
    xres = xmatch(s, pos, f"cand_{tag}")
    xs = summarise_xmatch(xres, {i: o for i, o in enumerate(c["oid"])})
    c = c.merge(xs, on="oid", how="left")
    for name, _cat, _rad, cols in XCATS:
        for col in [f"{name}_sep"] + [f"{name}_{x}" for x in cols]:
            if col not in c.columns:
                c[col] = np.nan
    c["JK"] = (pd.to_numeric(c["2mass_Jmag"], errors="coerce")
               - pd.to_numeric(c["2mass_Kmag"], errors="coerce")).round(2)

    # --- flags out of the JSON blob ------------------------------------------
    fl = c["flags"].fillna("{}").map(json.loads)
    for k in ("flag_vsx", "flag_gcvs", "flag_known_cv", "flag_simbad",
              "flag_simbad_target"):
        c[k] = [d.get(k, "") for d in fl]

    # --- outburst history -----------------------------------------------------
    hist = fetch_batch(
        s,
        c["oid"].tolist(),
        max_age_seconds=HISTORY_MAX_AGE_SECONDS,
        required_coverage_jd=jd_ceiling,
    )
    ep, nep, pk = [], [], []
    for oid in c["oid"]:
        records = hist.get(oid, pd.DataFrame()).to_dict("records")
        a = pd.DataFrame(history_as_of(records, jd_ceiling))
        e, n, p = episodes(a)
        ep.append(e[:700])
        nep.append(n)
        pk.append(None if pd.isna(p) else round(p, 2))
    c["outburst_history"] = ep
    c["n_outburst_episodes"] = nep
    c["brightest_ever_mag"] = pk

    c["fink_link"] = "https://fink-portal.org/" + c["oid"]
    c["STATUS"] = "MATTHEW-GATED -- NOT REPORTED TO TNS"
    c["rank_score"] = rank_score(c)
    c["probably"] = c.apply(one_liner, axis=1)

    c = c.reindex(columns=CANDIDATE_COLUMNS)
    return c.sort_values("rank_score", ascending=False).reset_index(drop=True)


def main() -> None:
    tag = validated_tag(sys.argv[1])
    tns_reference = _existing_tns_reference(tag)
    c = build(tag, tns_reference=tns_reference)
    tns_reference = _existing_tns_reference(tag)
    jd_ceiling = _source_jd_ceiling(tag, c)
    historical_tns, current_tns = verified_provenance(
        tns_reference, jd_ceiling
    )
    out = OUT / f"m2_candidates_{tag}.csv"
    pool_summary_path = OUT / f"m2_pool_{tag}.json"
    history_provenance = cache_provenance(c["oid"].tolist())
    xmatch_meta_path = sidecar_path(DATA / f"xmatch_cand_{tag}.json")
    xmatch_provenance = (
        json.loads(xmatch_meta_path.read_text(encoding="utf-8"))
        if xmatch_meta_path.exists()
        else None
    )
    output_contract = {
        "contract_schema_version": 1,
        "tag": tag,
        "history_jd_ceiling": jd_ceiling,
        "source_pool_summary_sha256": sha256_file(pool_summary_path),
        "history_cache_provenance_sha256": canonical_digest(history_provenance),
        "xmatch_provenance_sha256": canonical_digest(xmatch_provenance),
        "frozen_tns_provenance_sha256": canonical_digest(historical_tns),
        "current_tns_provenance_sha256": canonical_digest(current_tns),
    }
    output_provenance = write_cache(
        out,
        c.to_csv(index=False, lineterminator="\n").encode("utf-8"),
        kind="m2_candidate_output",
        contract=output_contract,
        row_count=len(c),
    )
    summary = {
        "tag": tag, "n_candidates": int(len(c)),
        "history_jd_ceiling": jd_ceiling,
        "history_as_of_mjd": jd_ceiling - 2400000.5,
        "history_cache_policy": {
            "refresh": False,
            "max_age_seconds": HISTORY_MAX_AGE_SECONDS,
            "required_coverage_jd": jd_ceiling,
        },
        "history_cache_provenance": history_provenance,
        "xmatch_cache_provenance": xmatch_provenance,
        "candidate_output_provenance": output_provenance,
        "tns_snapshot_provenance": {
            "frozen_dedupe": historical_tns,
            "operational_current": current_tns,
            "membership_rule": (
                "conservative dedupe using Discovery Date (UT) <= "
                "history_jd_ceiling in an immutable candidate-pinned snapshot; "
                "not exact historical registry membership; latest is annotation-only"
            ),
        },
        "by_arm": c["arm"].value_counts().to_dict() if len(c) else {},
        "channels": c["channel"].value_counts().to_dict() if len(c) else {},
        "in_galactic_plane": (int((c["gal_b"].abs() < M1.GAL_PLANE_ABS_B).sum())
                              if len(c) else 0),
        "no_gaia_counterpart": (int(c["gaia_DR3Name"].isna().sum()) if len(c) else 0),
        "with_archival_variable_match": (
            int(((c["atlasvs_sep"].notna()) | (c["vsx_sep"].notna())
                 | (c["gaiavar_Class"].notna())).sum()) if len(c) else 0),
        "flagged_known_cv": (int((c["flag_known_cv"].astype(str) != "").sum())
                             if len(c) else 0),
        "note": "MATTHEW-GATED. Nothing in this list has been reported to TNS.",
    }
    atomic_write(
        OUT / f"m2_candidates_{tag}.json",
        (json.dumps(summary, indent=2) + "\n").encode("utf-8"),
    )
    print(json.dumps(summary, indent=2))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
