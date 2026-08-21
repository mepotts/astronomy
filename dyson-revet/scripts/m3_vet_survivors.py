"""M3: the coded vetting stages, run on every pre-visual finalist the screen
produces, ending in one verdict per object from the PR-3 set.

This is what replaces Hephaistos II's two irreproducible stages (C4, a CNN
whose weights are unpublished; C7, visual inspection), which between them
carry almost all of the late-stage selectivity (368 -> 7). Every gate here is
code, every threshold was fixed in M3 §0 PR-3 before the survivor list
existed, and every verdict carries the centroid floor.

The gates, cheapest first (the ordering is itself pre-registered: the three
catalogue axes are single TAP queries, the centroid stage needs 6 image
cutouts per object, so the catalogue axes run on everything and the centroid
stage runs on whatever is still standing):

  V1  AllWISE detail       -- w3nm/w4nm single-exposure detection counts,
                              w?flg (95% upper-limit flag), ph_qual, S/N,
                              nb/na blend detail, rchi2.        [M2 axis 4]
  V2  WISE All-Sky Release -- the SAME PHOTONS, earlier pipeline. A survivor
                              whose excess band is 'U' there has a
                              release-dependent candidacy.      [M2 axis 3]
  V3  sensitivity          -- is the "detection" above WISE's own 5-sigma
                              standard at this position? Candidate I's
                              failure mode: an excess below the survey's own
                              floor. Uses the object's OWN catalogued S/N
                              (self-calibrating, no external depth table),
                              with the on-ecliptic 5-sigma fluxes as a
                              sourced auxiliary.
  V4  chance alignment     -- with Suazo et al. 2024's own faint red-galaxy
                              density (15000 sr^-1 = 4.57 deg^-2), NOT Ren
                              et al. 2024's 3616x-slipped 9e-6 arcsec^-2.
  V5  centroid offsets     -- AllWISE (+unWISE) first moments vs the
                              PM-propagated Gaia position, WITH the
                              JWST-calibrated 1-2" floor stated per object.

Run:
    python scripts/m3_vet_survivors.py --tag g0.1_full [--max-centroid 40]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyvo

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "out"
OUT.mkdir(exist_ok=True)

IRSA_TAP = "https://irsa.ipac.caltech.edu/TAP"

# WISE Vega zero points (Jarrett et al. 2011 / All-Sky Explanatory Supplement)
ZP_JY = {"W1": 309.540, "W2": 171.787, "W3": 31.674, "W4": 8.363}

# WISE 5-sigma point-source sensitivities ON THE ECLIPTIC (the shallowest
# regime; the depth improves toward the ecliptic poles where coverage is
# deepest). All-Sky Explanatory Supplement Sec 1.1, as used in I-dossier Sec (a).
SENS_ECL_MJY = {"W3": 0.86, "W4": 5.4}

# Suazo et al. 2024 Sec 3.1's OWN faint red-galaxy density: galaxies with W4
# flux >= the candidates' and 2.84 < W3-W4 < 3.25, ~15000 sr^-1. This is the
# population JWST actually found at D and E; the corrected arithmetic of the
# Ren+24 note (M2 Sec 3) is what points at it.
DEG2_PER_SR = (180.0 / np.pi) ** 2          # 3282.806
RHO_REDGAL_DEG2 = 15000.0 / DEG2_PER_SR     # 4.569 deg^-2

# The standing project law from the D calibration (M2 Sec 1): a JWST-confirmed
# real contaminant at 1.0" moved the AllWISE centroid by only 0.5-1.4".
CENTROID_FLOOR_ARCSEC = (1.0, 2.0)


def mag_to_mjy(m: float, band: str) -> float:
    return 1e3 * ZP_JY[band] * 10.0 ** (-0.4 * m)


def ecliptic_latitude(ra: np.ndarray, dec: np.ndarray) -> np.ndarray:
    """Ecliptic latitude in degrees (J2000 obliquity)."""
    eps = np.radians(23.439281)
    a, d = np.radians(ra), np.radians(dec)
    return np.degrees(np.arcsin(np.sin(d) * np.cos(eps)
                                - np.cos(d) * np.sin(eps) * np.sin(a)))


def box_or(ra: np.ndarray, dec: np.ndarray, radius_as: float) -> str:
    """OR'd ra/dec boxes.

    MEASURED 2026-08-21: IRSA's TAP accepts exactly ONE CONTAINS() per query --
    two OR'd cones return "Invalid or unsupported ADQL query string", so the
    obvious batching does not work and one query per position costs ~16 s.
    Plain ra/dec BETWEEN predicates OR together fine (5 positions in 12 s), so
    the batch is expressed as boxes and the exact radial cut is applied
    locally in nearest_match(). At 3" the box/cone difference is irrelevant
    because the match is to the nearest row anyway.
    """
    out = []
    for x, y in zip(ra, dec):
        dd = radius_as / 3600.0
        dr = dd / max(np.cos(np.radians(y)), 1e-6)
        out.append(f"(ra BETWEEN {x - dr:.7f} AND {x + dr:.7f} AND "
                   f"dec BETWEEN {y - dd:.7f} AND {y + dd:.7f})")
    return " OR ".join(out)


def tap_chunks(svc, table: str, cols: str, ra, dec, radius_as: float,
               chunk: int = 40, tag: str = "") -> pd.DataFrame:
    """Positional cross-match in OR'd cone chunks (IRSA TAP has no upload for
    anonymous users; 25 cones per query keeps the ADQL inside the parser)."""
    frames = []
    for i in range(0, len(ra), chunk):
        rs, ds = ra[i:i + chunk], dec[i:i + chunk]
        q = f"SELECT {cols} FROM {table} WHERE {box_or(rs, ds, radius_as)}"
        for attempt in range(4):
            try:
                t = svc.search(q).to_table().to_pandas()
                frames.append(t)
                break
            except Exception as e:  # noqa: BLE001
                if attempt == 3:
                    print(f"    [{tag}] chunk {i // chunk} FAILED after 4 "
                          f"tries: {type(e).__name__}: {str(e)[:120]}")
                else:
                    time.sleep(5 * (attempt + 1))
        print(f"    [{tag}] {min(i + chunk, len(ra))}/{len(ra)} positions, "
              f"{sum(len(f) for f in frames)} rows", flush=True)
    return (pd.concat(frames, ignore_index=True) if frames
            else pd.DataFrame(columns=cols.split(",")))


def nearest_match(surv: pd.DataFrame, cat: pd.DataFrame, suffix: str,
                  radius_as: float = 3.0) -> pd.DataFrame:
    """Attach the nearest catalogue row within radius_as to each survivor."""
    if cat.empty:
        return surv
    out = []
    cra, cdec = cat["ra"].to_numpy(), cat["dec"].to_numpy()
    for _, s in surv.iterrows():
        d = 3600.0 * np.hypot((cra - s["ra"]) * np.cos(np.radians(s["dec"])),
                              cdec - s["dec"])
        j = int(np.argmin(d)) if len(d) else -1
        rec = {}
        if j >= 0 and d[j] <= radius_as:
            # namespace EVERY column: surv already carries ra/dec/w3mpro/...
            # and duplicate labels would make r.get("w3nm_aw") return a Series
            rec = {f"{k}{suffix}": v for k, v in cat.iloc[j].items()}
            rec[f"sep{suffix}"] = float(d[j])
        out.append(rec)
    add = pd.DataFrame(out, index=surv.index)
    return pd.concat([surv, add], axis=1)


# --------------------------------------------------------------- verdicts ---
def verdict(r: pd.Series) -> tuple[str, str]:
    """PR-3's fixed decision set. Returns (verdict, one-line reason).

    Order matters and was fixed in advance: SUB-THRESHOLD first (an excess the
    survey cannot support is not evidence of anything, contaminated or not),
    then CONTAMINATION-CONSISTENT, then STILL-CLEAN, else INDETERMINATE.
    """
    why = []

    # --- V3 sensitivity: is the excess above WISE's own 5-sigma standard? ---
    s3, s4 = r.get("w3snr_aw"), r.get("w4snr_aw")
    s3 = r["snr3"] if s3 is None or not np.isfinite(s3) else s3
    s4 = r["snr4"] if s4 is None or not np.isfinite(s4) else s4
    if np.isfinite(s3) and np.isfinite(s4) and s3 < 5.0 and s4 < 5.0:
        return ("SUB-THRESHOLD",
                f"both excess bands below WISE's own 5σ standard "
                f"(W3 S/N {s3:.1f}, W4 S/N {s4:.1f}) — the excess is at the "
                f"instrument floor, candidate I's failure mode")

    # --- V1/V2 contamination-consistent axes ---
    nm3, nm4 = r.get("w3nm_aw"), r.get("w4nm_aw")
    if pd.notna(nm4) and nm4 == 0:
        why.append("w4nm = 0: never detected in a single exposure, only in "
                   "the coadd")
    if pd.notna(nm3) and nm3 == 0:
        why.append("w3nm = 0: never detected in a single exposure")
    f3, f4 = r.get("w3flg_aw"), r.get("w4flg_aw")
    if pd.notna(f4) and int(f4) == 32:
        why.append("w4flg = 32: the independent aperture photometry gives a "
                   "95% upper limit, not a detection")
    if pd.notna(f3) and int(f3) == 32:
        why.append("w3flg = 32: aperture photometry is a 95% upper limit")
    pq_as = str(r.get("ph_qual_as", "") or "")
    pq_aw = str(r.get("ph_qual_aw", "") or "")
    if len(pq_as) == 4 and len(pq_aw) == 4:
        for i, b in enumerate("W1 W2 W3 W4".split()):
            if b in ("W3", "W4") and pq_as[i] == "U" and pq_aw[i] != "U":
                why.append(f"release-inconsistent: {b} is a non-detection "
                           f"('U') in the WISE All-Sky reduction of the same "
                           f"photons but '{pq_aw[i]}' in AllWISE")
    # V5 IS DELIBERATELY NOT APPLIED -- see M3 Sec 3.2. The peak-search
    # centroid locks onto any BRIGHTER mid-IR source inside the 10" search
    # disk (or its PSF wing just outside it), which is common at scale and
    # was proved on two objects: a 9.51" "offset" is a W3 neighbour at 10.24"
    # that is 2.4x brighter, and an 11.89" "offset" is a source at 16.36"
    # that is 14x brighter. Applying the gate would convict hundreds of
    # objects of contamination on the strength of an unrelated neighbour.
    # A measurement that fails its own validity check does not get to decide
    # a verdict; the offsets are kept in the table as data, flagged.
    off = float("nan")
    if why:
        return "CONTAMINATION-CONSISTENT", "; ".join(why)

    # --- STILL-CLEAN requires positive evidence on every axis ---
    have_nm = pd.notna(nm3) and pd.notna(nm4)
    have_rel = len(pq_as) == 4 and len(pq_aw) == 4
    have_cent = pd.notna(off)
    if have_nm and have_rel and have_cent and nm3 > 0 and nm4 > 0:
        return ("STILL-CLEAN",
                f"detected in {int(nm3)}/{int(nm4)} single exposures (W3/W4), "
                f"release-consistent (All-Sky {pq_as} vs AllWISE {pq_aw}), "
                f"S/N {s3:.1f}/{s4:.1f} above the 5σ standard, no centroid "
                f"offset outside the 1–2″ floor (max {off:.2f}″), "
                f"P(chance red galaxy within 1″) = {r.get('p_chance_1as', float('nan')):.2e}")
    missing = [n for n, ok in [
        ("single-exposure counts", have_nm),
        ("All-Sky release row", have_rel),
        ("a VALID centroid measurement (the peak-search axis fails its own "
         "validity check at scale -- M3 Sec 3.2)", have_cent)] if not ok]
    return ("INDETERMINATE",
            "passes every gate that could be applied, but "
            + ", ".join(missing) + " unavailable — nothing in the archive "
            "moves this object either way")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--max-centroid", dest="max_centroid", type=int, default=60,
                    help="cap on objects sent to the image-cutout stage")
    ap.add_argument("--skip-centroid", action="store_true")
    ap.add_argument("--refresh", action="store_true",
                    help="re-query the V1/V2 catalogue axes instead of using "
                         "the cache")
    a = ap.parse_args()

    src = OUT / f"w4_previsual_candidates_{a.tag}.csv"
    if not src.exists():
        raise SystemExit(f"missing {src}")
    surv = pd.read_csv(src)
    print(f"vetting {len(surv)} pre-visual finalists from {src.name}")
    if surv.empty:
        raise SystemExit("nothing to vet")

    surv["ecl_lat"] = ecliptic_latitude(surv["ra"].to_numpy(),
                                        surv["dec"].to_numpy())
    for b in ("w3mpro", "w4mpro"):
        surv[b.replace("mpro", "_mjy")] = [
            mag_to_mjy(m, b[:2].upper()) for m in surv[b]]
    surv["w3_over_5sig_ecl"] = surv["w3_mjy"] / SENS_ECL_MJY["W3"]
    surv["w4_over_5sig_ecl"] = surv["w4_mjy"] / SENS_ECL_MJY["W4"]

    cache = OUT / f"m3_vet_cache_{a.tag}.csv"
    if cache.exists() and not a.refresh:
        # V1/V2 cost ~100 min of IRSA queries at 845 positions; cache them so
        # the centroid stage can be re-run without repeating that.
        surv = pd.read_csv(cache)
        print(f"  loaded cached V1/V2 catalogue axes from {cache.name} "
              f"({len(surv)} rows) -- pass --refresh to re-query")
        svc = None
    else:
        svc = pyvo.dal.TAPService(IRSA_TAP)
        ra, dec = surv["ra"].to_numpy(), surv["dec"].to_numpy()

        print("\n== V1: AllWISE detail (single-exposure counts, flags) ==")
        aw = tap_chunks(svc, "allwise_p3as_psd",
                        "designation,ra,dec,w3mpro,w3sigmpro,w4mpro,w4sigmpro,"
                        "w3snr,w4snr,w3nm,w4nm,w3m,w4m,w3flg,w4flg,nb,na,"
                        "w3rchi2,w4rchi2,ph_qual,cc_flags,ext_flg,var_flg",
                        ra, dec, 3.0, tag="allwise")
        surv = nearest_match(surv, aw, "_aw", 3.0)

        print("\n== V2: WISE All-Sky Release (same photons, earlier pipeline) ==")
        ask = tap_chunks(svc, "allsky_4band_p3as_psd",
                         "designation,ra,dec,w3mpro,w3sigmpro,w4mpro,w4sigmpro,"
                         "w3snr,w4snr,ph_qual,cc_flags,w3flg,w4flg",
                         ra, dec, 3.0, tag="allsky")
        surv = nearest_match(surv, ask, "_as", 3.0)
        surv.to_csv(cache, index=False)
        print(f"  cached V1/V2 to {cache.name}")

    print("\n== V4: chance alignment, Suazo's own faint red-galaxy density ==")
    rho_as2 = RHO_REDGAL_DEG2 / 3600.0 ** 2          # per arcsec^2
    surv["p_chance_1as"] = 1.0 - np.exp(-rho_as2 * np.pi * 1.0 ** 2)
    surv["p_chance_3p25as"] = 1.0 - np.exp(-rho_as2 * np.pi * 3.25 ** 2)
    print(f"  rho = {RHO_REDGAL_DEG2:.3f} deg^-2 (Suazo+24 15000 sr^-1); "
          f"P(>=1 within 1\") = {surv['p_chance_1as'].iloc[0]:.3e}; "
          f"expected among {len(surv)} survivors = "
          f"{len(surv) * surv['p_chance_1as'].iloc[0]:.3f}")

    # ---------------------------------------------------------- V5 centroid
    surv["cent_max_offset"] = np.nan
    surv["cent_max_sigma"] = np.nan
    surv["cent_note"] = ""
    # PR-3's pre-registered ordering: the catalogue axes are cheap and run on
    # everything; the centroid stage costs ~6 image cutouts per object, so it
    # runs only on objects the catalogue axes could not already resolve. An
    # object already CONTAMINATION-CONSISTENT or SUB-THRESHOLD does not need a
    # centroid measurement to reach its verdict.
    surv["_prov"] = [verdict(r)[0] for _, r in surv.iterrows()]
    need = surv.index[surv["_prov"].isin(["STILL-CLEAN", "INDETERMINATE"])]
    print("\n  provisional verdicts from V1-V4 alone: "
          + ", ".join(f"{k} {v}" for k, v in
                      surv["_prov"].value_counts().items()))
    print(f"  -> {len(need)} object(s) need the centroid stage")

    if not a.skip_centroid:
        print("\n== V5: centroid offsets (AllWISE atlas cutouts) ==")
        from w2_centroids import (fetch_cutout, ibe_tiles_for,  # noqa: PLC0415
                                  measure_centroid, propagate)
        todo = surv.loc[need].head(a.max_centroid)
        for i, (idx, s) in enumerate(todo.iterrows()):
            lab = f"S{int(s['source_id']) % 10 ** 10}"
            try:
                tiles = ibe_tiles_for(s["ra"], s["dec"])
                best_off, best_sig, notes = -1.0, np.nan, []
                # AllWISE atlas mean epoch ~2010.4. The screen's rows carry no
                # PM columns, so propagation uses 0 PM -- at most ~1" for a
                # high-PM star over 5.6 yr, and stated as a limitation.
                tgt = dict(ra=s["ra"], dec=s["dec"], pmra=0.0, pmdec=0.0)
                ra_e, dec_e = propagate(tgt, 2010.4)
                for band in (3, 4):
                    m = None
                    # try tiles best-centred first; a clipped cutout yields no
                    # measurement rather than a spurious 10" offset
                    for tile in tiles[:3]:
                        cp = fetch_cutout(f"{lab}_{tile}", tile, band,
                                          s["ra"], s["dec"])
                        cand = measure_centroid(cp, ra_e, dec_e, band)
                        if not cand.get("edge_clipped"):
                            m = cand
                            break
                    if m is None:
                        notes.append(f"W{band} EDGE-CLIPPED (no usable tile)")
                        continue
                    notes.append(f"W{band} {m['offset_arcsec']:.2f}±"
                                 f"{m['sigma_pos_arcsec']:.2f}\"")
                    if m["offset_arcsec"] > best_off:
                        best_off = m["offset_arcsec"]
                        best_sig = m["sigma_pos_arcsec"]
                if best_off < 0:
                    best_off, best_sig = np.nan, np.nan
                surv.loc[idx, "cent_max_offset"] = best_off
                surv.loc[idx, "cent_max_sigma"] = best_sig
                surv.loc[idx, "cent_note"] = "; ".join(notes)
                print(f"  [{i + 1}/{len(todo)}] {lab}: {'; '.join(notes)}",
                      flush=True)
            except Exception as e:  # noqa: BLE001
                surv.loc[idx, "cent_note"] = f"FAILED {type(e).__name__}"
                print(f"  [{i + 1}/{len(todo)}] {lab}: FAILED "
                      f"{type(e).__name__}: {str(e)[:90]}", flush=True)

    # ------------------------------------------------------------- verdicts
    vs, ws = [], []
    for _, r in surv.iterrows():
        v, w = verdict(r)
        vs.append(v)
        ws.append(w)
    surv["verdict"] = vs
    surv["verdict_reason"] = ws
    surv["centroid_floor_arcsec"] = f"{CENTROID_FLOOR_ARCSEC[0]:.0f}–" \
                                    f"{CENTROID_FLOOR_ARCSEC[1]:.0f}"

    path = OUT / f"m3_survivor_table_{a.tag}.csv"
    surv.to_csv(path, index=False)
    print(f"\nwrote {path}")
    counts = surv["verdict"].value_counts()
    print("\n== VERDICTS ==")
    for k, v in counts.items():
        print(f"  {k:28s} {v}")
    clean = surv[surv["verdict"] == "STILL-CLEAN"]
    if len(clean):
        print(f"\n*** {len(clean)} STILL-CLEAN survivor(s) -- MATTHEW-GATED. "
              f"Report nothing externally. ***")
        for _, c in clean.iterrows():
            print(f"    source_id {int(c['source_id'])} at "
                  f"{c['ra']:.5f} {c['dec']:+.5f}")
    (OUT / f"m3_verdict_counts_{a.tag}.json").write_text(
        json.dumps({k: int(v) for k, v in counts.items()}, indent=2))


if __name__ == "__main__":
    main()
