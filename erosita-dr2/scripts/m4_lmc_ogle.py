"""M4 Part A: LMC-box fade-candidates x OGLE (OCVS / XROM / Be candidates / HMXB VAC).

Input: the 25 LMC-box (RA 60-105, Dec -75..-60) FADE-CANDIDATE rows of
out/m2_vanished_forensics.csv (M2 Sect. 3).

Matching catalogs, all account-free (M3 Sect. 3 feasibility):
  * OGLE-IV OCVS, LMC ident.dat per type (acep, cep, dsct, ecl, hb, rrlyr, t2cep)
    from the OGLE anonymous FTP over HTTPS
    (https://ftp.astrouw.edu.pl/ogle/ogle4/OCVS/lmc/; collection page
    https://ogle.astrouw.edu.pl/main/collections.html). OGLE-IV OCVS has NO LMC
    LPV or Be class.
  * OGLE-III OIII-CVS, LMC ident.dat for the classes OGLE-IV lacks (lpv, dpv, rcb)
    (https://ftp.astrouw.edu.pl/ogle/ogle3/OIII-CVS/lmc/).
  * XROM real-time X-ray-binary monitoring roster + per-object I-band phot.dat
    (https://ogle.astrouw.edu.pl/ogle4/xrom/xrom.html and
    https://ftp.astrouw.edu.pl/ogle/ogle4/xrom/). NOTE the XROM page asks to be
    contacted before the photometry is used in a publication.
  * OGLE-II Be-star candidates in the LMC, Sabogal et al. 2005 (MNRAS 361, 1055),
    via VizieR TAP table "J/MNRAS/361/1055/table1" (types 1-4).
  * eROSITA DR1 VAC eRASS1_HMXB_LMC_v1.0 (Kaltenbrunner et al.,
    https://erosita.mpe.mpg.de/dr1/AllSkySurveyData_dr1/Catalogues_dr1/
    KaltenbrunnerD_DR1/eRASS1_HMXB_LMC_v1.0.fits.tgz) - the consortium's own
    census of 53 known LMC HMXBs seen in eRASS1.

Match radius per fader: 3.44 * sqrt(POS_ERR^2 + 1^2) arcsec (2-D 99% Rayleigh
radius incl. a 1" systematic floor; same convention family as M1/M2). Context
matches recorded to 30".

Chance-alignment control (house pattern): every fader position re-matched from
16 shifted positions (8 azimuths x offsets 240" and 480"), same per-object
radius; the mean control match rate is the expected number of chance alignments.

Light curves: for every real OCVS/XROM match the public I-band series is
downloaded and summarised in windows keyed to the eROSITA calendar
(HJD-2450000 = MJD - 49999.5): pre-eRASS [8100, 8829.5), the object's own
eRASS1 detection window (MJD_MIN..MJD_MAX +/- 5 d), the full eRASS1-3 window
[8829.5, 9381.5] (2019-12-12..2021-06-16), and post-stack (> 9381.5). The
OGLE-IV COVID interruption is measured from the data (largest gap 2019.5-2024).

Counterpart physics (the Be-donor test): an LMC Be/XRB donor is an O9-B3e star
at V ~ 13-16.5 (the 53 eRASS1_HMXB_LMC VAC donors have Gaia G 12.68-17.00,
median 14.85, computed from the VAC), i.e. it MUST appear in Gaia DR3 at
G <~ 17 with a blue
color and ~zero parallax. Per fader we therefore query Gaia DR3 (ESA archive
TAP, https://gea.esac.esa.int/tap-server/tap, anonymous sync; CDS X-Match was
502-down on 2026-08-16) within 10" and test for any such star inside the match
radius (G <= 17.5, BP-RP <= 0.7, parallax consistent with zero at 3 sigma).
CatWISE counterpart evidence is merged from out/m2_archival_xray.csv (M2).

Also, a coverage probe: I-band light curves of a few context OCVS stars near
the faders, to measure whether OGLE-IV was observing at all during the eRASS
window (the COVID interruption) - i.e. whether the Be-fade correlation was
even testable in principle.

Outputs:
  out/m4_lmc_ogle_matches.csv      - one row per fader: all matches + verdict inputs
  out/m4_lmc_ogle_lightcurves.csv  - matched + context light curves: window stats
  out/m4_lmc_ogle_control.csv      - shifted-position control summary per catalog
Bulk cache in data/ogle/ (gitignored). No accounts, nothing submitted.
"""

from __future__ import annotations

import io
import re
import tarfile
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from astropy.coordinates import SkyCoord
import astropy.units as u

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OGLE = DATA / "ogle"
LC = OGLE / "lc"
OUT = ROOT / "out"

FTP = "https://ftp.astrouw.edu.pl/ogle"
OCVS4_TYPES = ["acep", "cep", "dsct", "ecl", "hb", "rrlyr", "t2cep"]
OCVS3_TYPES = ["lpv", "dpv", "rcb"]
XROM_HTML = "https://ogle.astrouw.edu.pl/ogle4/xrom/xrom.html"
TAP_VIZIER = "https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync"

R_CONTEXT = 30.0  # arcsec, context reporting
CONTROL_OFFSETS = [240.0, 480.0]  # arcsec
CONTROL_AZIMUTHS = 8

# eROSITA calendar in HJD-2450000 (= MJD - 49999.5)
ERASS_START = 58829.0 - 49999.5   # 2019-12-12 survey start
STACK_END = 59381.0 - 49999.5     # 2021-06-16 eRASS3 end (arXiv:2607.27772)
PRE_LO = 8100.0                   # ~2 yr pre-eRASS baseline


def fetch(url: str, dest: Path, binary: bool = False) -> bytes:
    """Cached download."""
    if dest.exists() and dest.stat().st_size > 0:
        return dest.read_bytes()
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=120)
            r.raise_for_status()
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(r.content)
            return r.content
        except Exception as e:  # noqa: BLE001
            if attempt == 2:
                raise
            print(f"  retry {url}: {e}")
            time.sleep(3)
    raise RuntimeError("unreachable")


COORD_RE = re.compile(
    r"(\d{1,2}:\d{2}:\d{2}(?:\.\d+)?)\s+([+-]?\d{1,3}:\d{2}:\d{2}(?:\.\d+)?)")
# some ident files (e.g. OGLE-IV lmc/hb) write "4 45 19.56 -67  3 14.3"
COORD_RE_SP = re.compile(
    r"(\d{1,2}\s+\d{1,2}\s+\d{1,2}(?:\.\d+)?)\s+([+-]\d{1,3}\s+\d{1,2}\s+\d{1,2}(?:\.\d+)?)")


def parse_ident(text: str, source: str, vtype: str) -> pd.DataFrame:
    """Parse an OCVS ident.dat: ID = first token, coordinates by regex,
    everything between ID and RA kept as raw subtype/field info."""
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = COORD_RE.search(line) or COORD_RE_SP.search(line)
        if not m:
            continue
        oid = line.split()[0]
        pre = line[: m.start()].split()
        sub = " ".join(pre[1:]) if len(pre) > 1 else ""
        rows.append((oid, sub, re.sub(r"\s+", ":", m.group(1)),
                     re.sub(r"\s+", ":", m.group(2))))
    df = pd.DataFrame(rows, columns=["ogle_id", "subtype", "ra_s", "dec_s"])
    c = SkyCoord(df["ra_s"], df["dec_s"], unit=(u.hourangle, u.deg))
    df["ra"] = c.ra.deg
    df["dec"] = c.dec.deg
    df["vtype"] = vtype
    df["source"] = source
    return df.drop(columns=["ra_s", "dec_s"])


def load_ocvs() -> pd.DataFrame:
    frames = []
    for t in OCVS4_TYPES:
        url = f"{FTP}/ogle4/OCVS/lmc/{t}/ident.dat"
        txt = fetch(url, OGLE / f"ocvs4_lmc_{t}_ident.dat").decode("utf-8", "replace")
        df = parse_ident(txt, "OCVS-IV", t)
        print(f"  OCVS OGLE-IV lmc/{t}: {len(df)} objects")
        frames.append(df)
    for t in OCVS3_TYPES:
        url = f"{FTP}/ogle3/OIII-CVS/lmc/{t}/ident.dat"
        txt = fetch(url, OGLE / f"ocvs3_lmc_{t}_ident.dat").decode("utf-8", "replace")
        df = parse_ident(txt, "OCVS-III", t)
        print(f"  OCVS OGLE-III lmc/{t}: {len(df)} objects")
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def load_xrom() -> pd.DataFrame:
    """Roster (name, RA, Dec) from xrom.html + FTP directory mapping."""
    html = fetch(XROM_HTML, OGLE / "xrom.html").decode("utf-8", "replace")
    plain = re.sub(r"<[^>]+>", "\n", html)
    lines = [ln.strip() for ln in plain.splitlines() if ln.strip()]
    rows = []
    i = 0
    coord = re.compile(r"^\d{1,2}:\d{2}:\d{2}(\.\d+)?$")
    dcoord = re.compile(r"^[+-]?\d{1,3}:\d{2}:\d{2}(\.\d+)?$")
    while i < len(lines) - 4:
        if coord.match(lines[i + 3]) and dcoord.match(lines[i + 4]):
            rows.append((lines[i], lines[i + 1], lines[i + 2],
                         lines[i + 3], lines[i + 4]))
            i += 5
        else:
            i += 1
    df = pd.DataFrame(rows, columns=["name", "field", "starno", "ra_s", "dec_s"])
    c = SkyCoord(df["ra_s"], df["dec_s"], unit=(u.hourangle, u.deg))
    df["ra"] = c.ra.deg
    df["dec"] = c.dec.deg
    # FTP directory names differ from display names -> normalized mapping
    idx = fetch(f"{FTP}/ogle4/xrom/", OGLE / "xrom_index.html").decode("utf-8", "replace")
    dirs = [d[:-1] for d in re.findall(r'href="([^"?/][^"]*/)"', idx)]
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())  # noqa: E731
    dmap = {norm(d): d for d in dirs}
    df["ftp_dir"] = [dmap.get(norm(n), "") for n in df["name"]]
    print(f"  XROM roster: {len(df)} objects ({df['ftp_dir'].ne('').sum()} with FTP dir)")
    return df.drop(columns=["ra_s", "dec_s"])


def load_sabogal() -> pd.DataFrame:
    dest = OGLE / "sabogal_lmc_be.csv"
    if not dest.exists():
        q = 'SELECT "OGLE","Type","Vmag","_RA","_DE" FROM "J/MNRAS/361/1055/table1"'
        r = requests.get(TAP_VIZIER, params={
            "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv",
            "QUERY": q}, timeout=180)
        r.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(r.content)
    df = pd.read_csv(dest)
    df = df.rename(columns={"_RA": "ra", "_DE": "dec", "OGLE": "ogle_id",
                            "Type": "be_type"})
    print(f"  Sabogal 2005 LMC Be candidates: {len(df)}")
    return df


def load_hmxb() -> pd.DataFrame:
    from astropy.io import fits
    t = tarfile.open(DATA / "eRASS1_HMXB_LMC_v1.0.fits.tgz")
    buf = t.extractfile("eRASS1_HMXB_LMC_v1.0.fits").read()
    f = fits.open(io.BytesIO(buf))
    d = f[1].data
    df = pd.DataFrame({
        "xray_name": [s.strip() for s in d["XrayName"]],
        "erass1_name": [s.strip() for s in d["eRASS1_name"]],
        "ra": d["RA_eRASS1"].astype(float),
        "dec": d["DEC_eRASS1"].astype(float),
        "porb": d["Porb"].astype(float),
        "conf": [str(s).strip() for s in d["confclass_Kaltenbrunner"]],
    })
    print(f"  eRASS1_HMXB_LMC VAC: {len(df)} known LMC HMXBs")
    return df


def load_gaia(faders: pd.DataFrame) -> pd.DataFrame:
    """Gaia DR3 sources within 10 arcsec of every fader (one anonymous TAP call)."""
    dest = OGLE / "gaia_cones_25.csv"
    if not dest.exists():
        circles = " OR ".join(
            f"1=CONTAINS(POINT(ra,dec),CIRCLE({r.RA},{r.DEC},0.0027778))"
            for r in faders.itertuples())
        q = ("SELECT source_id, ra, dec, phot_g_mean_mag, bp_rp, parallax, "
             "parallax_error, pmra, pmdec, pm, ruwe "
             "FROM gaiadr3.gaia_source WHERE " + circles)
        r = requests.post("https://gea.esac.esa.int/tap-server/tap/sync",
                          data={"REQUEST": "doQuery", "LANG": "ADQL",
                                "FORMAT": "csv", "QUERY": q}, timeout=300)
        r.raise_for_status()
        dest.write_bytes(r.content)
    df = pd.read_csv(dest)
    print(f"  Gaia DR3 cone union: {len(df)} sources within 10\" of the faders")
    return df


def match_one(cat: pd.DataFrame, cc: SkyCoord, radius_arcsec: np.ndarray,
              faders: pd.DataFrame):
    """All catalog rows within R_CONTEXT of any fader; flag inside r_match."""
    kc = SkyCoord(cat["ra"].to_numpy() * u.deg, cat["dec"].to_numpy() * u.deg)
    ii, kk, sep, _ = kc.search_around_sky(cc, R_CONTEXT * u.arcsec)
    recs = []
    for i, k, s in zip(ii, kk, sep.arcsec):
        recs.append({
            "fader": faders.iloc[i]["IAUNAME"],
            "cat_row": int(k),
            "sep_arcsec": float(s),
            "inside_match_radius": bool(s <= radius_arcsec[i]),
        })
    return pd.DataFrame(recs)


def control_rate(cat: pd.DataFrame, faders: pd.DataFrame,
                 radius_arcsec: np.ndarray) -> tuple[int, int]:
    """Total control matches and number of control positions."""
    kc = SkyCoord(cat["ra"].to_numpy() * u.deg, cat["dec"].to_numpy() * u.deg)
    n_hit = 0
    n_pos = 0
    base = SkyCoord(faders["RA"].to_numpy() * u.deg, faders["DEC"].to_numpy() * u.deg)
    for off in CONTROL_OFFSETS:
        for j in range(CONTROL_AZIMUTHS):
            pa = j * (360.0 / CONTROL_AZIMUTHS) * u.deg
            shifted = base.directional_offset_by(pa, off * u.arcsec)
            idx, sep2, _ = shifted.match_to_catalog_sky(kc)
            n_hit += int(np.sum(sep2.arcsec <= radius_arcsec))
            n_pos += len(faders)
    return n_hit, n_pos


def lc_url(row: pd.Series) -> str:
    if row["source"] == "OCVS-IV":
        return f"{FTP}/ogle4/OCVS/lmc/{row['vtype']}/phot/I/{row['ogle_id']}.dat"
    return f"{FTP}/ogle3/OIII-CVS/lmc/{row['vtype']}/phot/I/{row['ogle_id']}.dat"


def lc_stats(hjd: np.ndarray, mag: np.ndarray, w1_lo: float, w1_hi: float) -> dict:
    def win(lo, hi):
        m = (hjd >= lo) & (hjd < hi)
        if m.sum() == 0:
            return (0, np.nan, np.nan, np.nan)
        return (int(m.sum()), float(np.median(mag[m])),
                float(np.min(mag[m])), float(np.max(mag[m])))
    n_pre, med_pre, min_pre, max_pre = win(PRE_LO, ERASS_START)
    n_e1, med_e1, min_e1, max_e1 = win(w1_lo, w1_hi)
    n_er, med_er, min_er, max_er = win(ERASS_START, STACK_END)
    n_post, med_post, min_post, max_post = win(STACK_END, 1e9)
    # largest sampling gap between 2019.5 and 2024.0 (HJD' ~ 8650..10310)
    m = (hjd >= 8650) & (hjd <= 10310)
    gap = float(np.max(np.diff(np.sort(hjd[m])))) if m.sum() > 1 else np.nan
    return {
        "n_all": int(len(hjd)), "hjd_first": float(np.min(hjd)),
        "hjd_last": float(np.max(hjd)),
        "i_median_all": float(np.median(mag)),
        "i_min_all": float(np.min(mag)), "i_max_all": float(np.max(mag)),
        "n_pre": n_pre, "i_med_pre": med_pre, "i_min_pre": min_pre, "i_max_pre": max_pre,
        "n_erass1win": n_e1, "i_med_erass1win": med_e1,
        "i_min_erass1win": min_e1, "i_max_erass1win": max_e1,
        "n_erass": n_er, "i_med_erass": med_er, "i_min_erass": min_er, "i_max_erass": max_er,
        "n_post": n_post, "i_med_post": med_post, "i_min_post": min_post,
        "i_max_post": max_post,
        "max_gap_2019p5_2024_d": gap,
    }


def main() -> None:
    OGLE.mkdir(parents=True, exist_ok=True)
    LC.mkdir(parents=True, exist_ok=True)

    forensics = pd.read_csv(OUT / "m2_vanished_forensics.csv")
    faders = forensics[(forensics.RA >= 60) & (forensics.RA <= 105)
                       & (forensics.DEC >= -75) & (forensics.DEC <= -60)
                       & (forensics.forensic_class_v2 == "FADE-CANDIDATE")
                       ].reset_index(drop=True)
    print(f"LMC-box fade candidates: {len(faders)}")
    r_match = 3.44 * np.sqrt(faders["POS_ERR"].to_numpy() ** 2 + 1.0)
    cc = SkyCoord(faders["RA"].to_numpy() * u.deg, faders["DEC"].to_numpy() * u.deg)

    print("loading catalogs ...")
    ocvs = load_ocvs()
    xrom = load_xrom()
    sab = load_sabogal()
    hmxb = load_hmxb()

    # ---- matches ---------------------------------------------------------
    res = faders[["IAUNAME", "RA", "DEC", "POS_ERR", "DET_LIKE_0", "ML_RATE_1",
                  "ML_FLUX_1", "MJD_MIN", "MJD_MAX", "ul_presence",
                  "ul_fade_frac"]].copy()
    res["r_match_arcsec"] = np.round(r_match, 2)

    m_ocvs = match_one(ocvs, cc, r_match, faders)
    m_xrom = match_one(xrom, cc, r_match, faders)
    m_sab = match_one(sab, cc, r_match, faders)
    m_hx = match_one(hmxb, cc, r_match, faders)

    # nearest-anything distances: footprint/coverage context per fader
    for tag, cat in [("ocvs", ocvs), ("xrom", xrom), ("be", sab),
                     ("hmxb", hmxb)]:
        kc = SkyCoord(cat["ra"].to_numpy() * u.deg, cat["dec"].to_numpy() * u.deg)
        _, sep, _ = cc.match_to_catalog_sky(kc)
        res[f"{tag}_nearest_any_arcmin"] = np.round(sep.arcmin, 2)

    def summarize(mdf: pd.DataFrame, cat: pd.DataFrame, idcol: str,
                  extra: list[str]) -> pd.DataFrame:
        if mdf.empty:
            return pd.DataFrame(columns=["fader", "n_in", "ids",
                                         "nearest_context"])
        mdf = mdf.merge(cat.reset_index(drop=True), left_on="cat_row",
                        right_index=True)
        rows = []
        for f, g in mdf.groupby("fader"):
            g = g.sort_values("sep_arcsec")
            gin = g[g["inside_match_radius"]]
            rows.append({
                "fader": f,
                "n_in": len(gin),
                "ids": "; ".join(
                    f"{r[idcol]}[{'+'.join(str(r[e]) for e in extra)}]@"
                    f"{r['sep_arcsec']:.1f}\""
                    for _, r in gin.iterrows()),
                "nearest_context": (
                    f"{g.iloc[0][idcol]}@{g.iloc[0]['sep_arcsec']:.1f}\""
                    if len(g) else ""),
            })
        return pd.DataFrame(rows)

    s_ocvs = summarize(m_ocvs, ocvs, "ogle_id", ["vtype", "subtype"])
    s_xrom = summarize(m_xrom, xrom, "name", ["ftp_dir"])
    s_sab = summarize(m_sab, sab, "ogle_id", ["be_type"])
    s_hx = summarize(m_hx, hmxb, "xray_name", ["conf"])

    for tag, s in [("ocvs", s_ocvs), ("xrom", s_xrom), ("be", s_sab),
                   ("hmxb", s_hx)]:
        s = s.rename(columns={
            "n_in": f"{tag}_n_match", "ids": f"{tag}_matches",
            "nearest_context": f"{tag}_nearest30"})
        res = res.merge(s, left_on="IAUNAME", right_on="fader", how="left"
                        ).drop(columns=["fader"])
        res[f"{tag}_n_match"] = res[f"{tag}_n_match"].fillna(0).astype(int)
        res[f"{tag}_matches"] = res[f"{tag}_matches"].fillna("")
        res[f"{tag}_nearest30"] = res[f"{tag}_nearest30"].fillna("")

    # ---- Gaia DR3: the Be-donor test ------------------------------------
    gaia = load_gaia(faders)
    gc = SkyCoord(gaia["ra"].to_numpy() * u.deg, gaia["dec"].to_numpy() * u.deg)
    res["gaia_n10"] = 0
    for col in ("gaia_nearest_sep", "gaia_nearest_G", "gaia_nearest_bp_rp",
                "gaia_nearest_plx", "gaia_nearest_plx_err", "gaia_nearest_pm"):
        res[col] = np.nan
    res["be_donor_candidate"] = False
    res["be_donor_detail"] = ""
    ii, kk, sep, _ = gc.search_around_sky(cc, 10.0 * u.arcsec)
    for i in range(len(faders)):
        sel = ii == i
        res.loc[i, "gaia_n10"] = int(sel.sum())
        if not sel.any():
            continue
        ks = kk[sel]
        ss = sep.arcsec[sel]
        j = np.argmin(ss)
        g = gaia.iloc[ks[j]]
        res.loc[i, "gaia_nearest_sep"] = round(float(ss[j]), 2)
        res.loc[i, "gaia_nearest_G"] = g["phot_g_mean_mag"]
        res.loc[i, "gaia_nearest_bp_rp"] = g["bp_rp"]
        res.loc[i, "gaia_nearest_plx"] = g["parallax"]
        res.loc[i, "gaia_nearest_plx_err"] = g["parallax_error"]
        res.loc[i, "gaia_nearest_pm"] = g["pm"]
        # any Be-donor-like star inside the match radius?
        inside = ss <= r_match[i]
        details = []
        for k, s in zip(ks[inside], ss[inside]):
            g = gaia.iloc[k]
            G, col_ = g["phot_g_mean_mag"], g["bp_rp"]
            plx, plxe = g["parallax"], g["parallax_error"]
            blue = pd.notna(col_) and col_ <= 0.7
            bright = pd.notna(G) and G <= 17.5
            distant = pd.isna(plx) or plxe <= 0 or abs(plx) < 3 * plxe
            if bright and blue and distant:
                details.append(f"G={G:.1f} bp_rp={col_:.2f} @{s:.1f}\"")
        if details:
            res.loc[i, "be_donor_candidate"] = True
            res.loc[i, "be_donor_detail"] = "; ".join(details)

    # CatWISE counterpart evidence from the M2 archival sweep
    arx = pd.read_csv(OUT / "m2_archival_xray.csv")[
        ["name", "catwise_sep", "catwise_w1", "catwise_w2", "gclass_class",
         "gclass_score", "2rxs_id", "2rxs_sep"]]
    res = res.merge(arx, left_on="IAUNAME", right_on="name", how="left"
                    ).drop(columns=["name"])
    res["catwise_w1_w2"] = res["catwise_w1"] - res["catwise_w2"]

    # auto-draft reading (finalised by hand in the M4 doc)
    def reading(r) -> str:
        if pd.notna(r["catwise_w1_w2"]) and r["catwise_w1_w2"] >= 0.8:
            return "AGN-colored IR counterpart (W1-W2 >= 0.8)"
        plx, plxe = r["gaia_nearest_plx"], r["gaia_nearest_plx_err"]
        if pd.notna(plx) and plxe > 0 and plx / plxe >= 5:
            return "foreground star (significant parallax)"
        if r["be_donor_candidate"]:
            return "blue LMC-luminous star present - Be donor not excluded"
        return "no Be-donor-like star; faint/ambiguous counterpart"
    res["auto_reading"] = res.apply(reading, axis=1)

    # ---- shifted-position control ---------------------------------------
    ctrl = []
    for tag, cat in [("ocvs_all", ocvs), ("xrom", xrom), ("be_sabogal", sab),
                     ("hmxb_vac", hmxb)]:
        hits, npos = control_rate(cat, faders, r_match)
        real = {"ocvs_all": int((res["ocvs_n_match"] > 0).sum()),
                "xrom": int((res["xrom_n_match"] > 0).sum()),
                "be_sabogal": int((res["be_n_match"] > 0).sum()),
                "hmxb_vac": int((res["hmxb_n_match"] > 0).sum())}[tag]
        exp25 = hits / npos * len(faders)
        ctrl.append({"catalog": tag, "control_positions": npos,
                     "control_hits": hits,
                     "expected_chance_matches_per_25": round(exp25, 3),
                     "real_faders_matched": real})
        print(f"  control {tag}: {hits}/{npos} -> expect {exp25:.3f} chance "
              f"matches in 25; real = {real}")
    # per-OCVS-type control for the types that actually matched
    for t in sorted(ocvs["vtype"].unique()):
        sub = ocvs[ocvs["vtype"] == t]
        hits, npos = control_rate(sub, faders, r_match)
        ctrl.append({"catalog": f"ocvs_{t}", "control_positions": npos,
                     "control_hits": hits,
                     "expected_chance_matches_per_25":
                         round(hits / npos * len(faders), 3),
                     "real_faders_matched": np.nan})
    pd.DataFrame(ctrl).to_csv(OUT / "m4_lmc_ogle_control.csv", index=False)

    # ---- light curves for real matches ----------------------------------
    lcrows = []
    for mdf in (m_ocvs, m_xrom):
        for col in ("inside_match_radius", "cat_row", "sep_arcsec", "fader"):
            if col not in mdf.columns:
                mdf[col] = pd.Series(dtype=object)
    matched_ocvs = m_ocvs[m_ocvs["inside_match_radius"] == True].merge(  # noqa: E712
        ocvs.reset_index(drop=True), left_on="cat_row", right_index=True)
    for _, r in matched_ocvs.iterrows():
        url = lc_url(r)
        dest = LC / f"{r['ogle_id']}_I.dat"
        try:
            txt = fetch(url, dest).decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            print(f"  LC fetch failed {url}: {e}")
            lcrows.append({"fader": r["fader"], "ogle_id": r["ogle_id"],
                           "vtype": r["vtype"], "lc_error": str(e)[:80]})
            continue
        arr = np.loadtxt(io.StringIO(txt), usecols=(0, 1))
        frow = faders[faders["IAUNAME"] == r["fader"]].iloc[0]
        st = lc_stats(arr[:, 0], arr[:, 1],
                      frow["MJD_MIN"] - 49999.5 - 5, frow["MJD_MAX"] - 49999.5 + 5)
        lcrows.append({"fader": r["fader"], "ogle_id": r["ogle_id"],
                       "vtype": r["vtype"], "subtype": r["subtype"],
                       "sep_arcsec": round(r["sep_arcsec"], 2),
                       "lc_error": "", **st})
    matched_xrom = m_xrom[m_xrom["inside_match_radius"] == True].merge(  # noqa: E712
        xrom.reset_index(drop=True), left_on="cat_row", right_index=True)
    for _, r in matched_xrom.iterrows():
        if not r["ftp_dir"]:
            continue
        url = f"{FTP}/ogle4/xrom/{r['ftp_dir']}/phot.dat"
        dest = LC / f"xrom_{r['ftp_dir']}_I.dat"
        try:
            txt = fetch(url, dest).decode("utf-8", "replace")
            arr = np.loadtxt(io.StringIO(txt), usecols=(0, 1))
        except Exception as e:  # noqa: BLE001
            print(f"  XROM LC failed {url}: {e}")
            continue
        hjd = arr[:, 0]
        hjd = np.where(hjd > 2000000, hjd - 2450000, hjd)  # either convention
        frow = faders[faders["IAUNAME"] == r["fader"]].iloc[0]
        st = lc_stats(hjd, arr[:, 1],
                      frow["MJD_MIN"] - 49999.5 - 5, frow["MJD_MAX"] - 49999.5 + 5)
        lcrows.append({"fader": r["fader"], "ogle_id": f"XROM {r['name']}",
                       "vtype": "xrom", "subtype": "",
                       "sep_arcsec": round(r["sep_arcsec"], 2),
                       "lc_error": "", **st})
    # coverage probe: context OCVS stars nearest to faders (was OGLE-IV even
    # observing during the eRASS window?)
    kc = SkyCoord(ocvs["ra"].to_numpy() * u.deg, ocvs["dec"].to_numpy() * u.deg)
    idx, sepn, _ = cc.match_to_catalog_sky(kc)
    order = np.argsort(sepn.arcsec)[:3]
    for i in order:
        r = ocvs.iloc[idx[i]]
        if r["source"] != "OCVS-IV":
            continue
        url = lc_url(r)
        dest = LC / f"context_{r['ogle_id']}_I.dat"
        try:
            txt = fetch(url, dest).decode("utf-8", "replace")
            arr = np.loadtxt(io.StringIO(txt), usecols=(0, 1))
        except Exception as e:  # noqa: BLE001
            print(f"  context LC failed {url}: {e}")
            continue
        frow = faders.iloc[i]
        st = lc_stats(arr[:, 0], arr[:, 1],
                      frow["MJD_MIN"] - 49999.5 - 5, frow["MJD_MAX"] - 49999.5 + 5)
        lcrows.append({"fader": f"(context for {frow['IAUNAME']})",
                       "ogle_id": r["ogle_id"], "vtype": r["vtype"],
                       "subtype": r["subtype"],
                       "sep_arcsec": round(float(sepn.arcsec[i]), 1),
                       "lc_error": "", **st})
    # the OGLE-IV COVID interruption, measured from a live XROM series
    # (XROM phot.dat is real-time, unlike the frozen OCVS collection files):
    # nearest XROM object to any fader
    xc = SkyCoord(xrom["ra"].to_numpy() * u.deg, xrom["dec"].to_numpy() * u.deg)
    xi, xsep, _ = cc.match_to_catalog_sky(xc)
    ib = int(np.argmin(xsep.arcmin))
    xr = xrom.iloc[xi[ib]]
    url = f"{FTP}/ogle4/xrom/{xr['ftp_dir']}/phot.dat"
    try:
        txt = fetch(url, LC / f"context_xrom_{xr['ftp_dir']}_I.dat"
                    ).decode("utf-8", "replace")
        arr = np.loadtxt(io.StringIO(txt), usecols=(0, 1))
        hjd = arr[:, 0]
        hjd = np.where(hjd > 2000000, hjd - 2450000, hjd)
        frow = faders.iloc[ib]
        st = lc_stats(hjd, arr[:, 1],
                      frow["MJD_MIN"] - 49999.5 - 5, frow["MJD_MAX"] - 49999.5 + 5)
        s = np.sort(hjd[(hjd >= 8650)])
        if len(s) > 1:
            gi = int(np.argmax(np.diff(s)))
            print(f"  XROM {xr['name']}: largest gap {s[gi]:.1f} -> {s[gi+1]:.1f} "
                  f"({s[gi+1]-s[gi]:.0f} d)")
        lcrows.append({"fader": f"(context XROM, {xsep.arcmin[ib]:.0f}' from "
                                f"{frow['IAUNAME']})",
                       "ogle_id": f"XROM {xr['name']}", "vtype": "xrom",
                       "subtype": "", "sep_arcsec": round(xsep.arcsec[ib], 0),
                       "lc_error": "", **st})
    except Exception as e:  # noqa: BLE001
        print(f"  XROM context failed: {e}")
    pd.DataFrame(lcrows).to_csv(OUT / "m4_lmc_ogle_lightcurves.csv", index=False)

    res.to_csv(OUT / "m4_lmc_ogle_matches.csv", index=False)
    nm = (res[["ocvs_n_match", "xrom_n_match", "be_n_match", "hmxb_n_match"]]
          .sum(axis=1) > 0).sum()
    print(f"\nfaders with >=1 match in any catalog: {nm}/{len(faders)}")
    print("wrote out/m4_lmc_ogle_matches.csv, _lightcurves.csv, _control.csv")


if __name__ == "__main__":
    main()
