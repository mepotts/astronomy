"""W2 first slice: eRASS1 (DR1) vs eRASS:3-stacked (DR2) rate ratios.

Route (b) of M1: DR2 carries NO per-eRASS epoch columns (verified against the
eRASS3_Main_v1.3 data model,
https://erosita.mpe.mpg.de/dr2/AllSkySurveyData_dr2/Catalogues_dr2/RamosM_DR2/eRASS3_Main_v1.3.html),
so the only public variability axis is DR1 (eRASS1) vs DR2 (eRASS:3 stacked).
The join uses the consortium's own cross-walk column UID_DR1 (>0 strong, <0 weak,
0 none; NO flux criterion was applied in that match — arXiv:2607.27772 Sect. 5),
so we are not inventing a positional match, and strong matches are not biased
against variables.

Physics of the construction (document in M1 doc):
  The DR2 stack CONTAINS the eRASS1 data. For eRASS1 rate r1 with vignetted
  exposure t1 and stacked rate r3 with exposure t3, a source that switched off
  after eRASS1 has r3 ~= r1*t1/t3 (per-source "fader floor"), so raw stacked
  ratios compress faders to >= ~1/3. We therefore also reconstruct the implied
  post-eRASS1 rate:
      r23 = (r3*t3 - r1*t1) / (t3 - t1)
  which estimates the true eRASS2+3 mean rate, and rank on the epoch ratio
  r23/r1 (and its inverse), with 1-sigma-conservative amplitudes.
  Caveat: DR2 was processed with pipeline version 030 vs DR1's 010 ("changes
  relative to DR1 are generally small" — arXiv:2607.27772 Sect. 3), so the
  subtraction is approximate; the bright-pair median ratio measures the net
  scale offset and is applied as a global correction factor m.

Cleaning cuts (documented in M1 doc; sources: arXiv:2607.27772 Sect. 5.3):
  - point-like in BOTH catalogs (EXT_LIKE == 0) — extent changes fake variability
  - drop any of FLAG_SP_SNR/BPS/LGA/GC_CONS, FLAG_NO_RADEC_ERR, FLAG_NO_CTS_ERR,
    FLAG_OPT in either catalog; keep FLAG_SP_SCL (paper 5.3: unproblematic)
  - separation sanity: sep <= 10 arcsec AND sep <= 3.44*sqrt(POS_ERR_1^2+POS_ERR_3^2)
    (3.44 = 2D 99% radius for Rayleigh; POS_ERR is the 1-sigma radial error)
  - rates > 0 and finite errors on both sides

Outputs:
  data/w2_pairs.parquet          full cleaned join (gitignored)
  out/w2_stats.json              distribution statistics
  out/w2_ranked_variables.csv    ranked strong variables (committed)
  out/w2_vanished.csv            bright DR1 sources with no DR2 counterpart
  out/w2_new_bright.csv          bright DR2 sources with no DR1 counterpart
  out/w2_ratio_distribution.png  log10 ratio histogram
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.io import fits

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "out"

DR2_FITS = DATA / "eRASS3_Main_v1.3.fits"
DR1_FITS = DATA / "eRASS1_Main.v1.2.fits"

FLAGS = [
    "FLAG_SP_SNR", "FLAG_SP_BPS", "FLAG_SP_LGA", "FLAG_SP_GC_CONS",
    "FLAG_NO_RADEC_ERR", "FLAG_NO_CTS_ERR", "FLAG_OPT",
]

DR2_COLS = [
    "IAUNAME", "DETUID", "UID", "UID_DR1", "RA", "DEC", "POS_ERR",
    "DET_LIKE_0", "EXT_LIKE", "ID_CLUSTER",
    "ML_RATE_1", "ML_RATE_ERR_1", "ML_RATE_LOWERR_1", "ML_RATE_UPERR_1",
    "ML_CTS_1", "ML_FLUX_1", "ML_FLUX_ERR_1", "ML_EXP_1", "ML_BKG_1",
    "APE_CTS_1", "APE_BKG_1", "APE_EXP_1", "APE_POIS_1", "FLAG_SP_SCL",
] + FLAGS

DR1_COLS = [
    "IAUNAME", "UID", "RA", "DEC", "POS_ERR", "DET_LIKE_0", "EXT_LIKE",
    "ID_CLUSTER", "MJD_MIN", "MJD_MAX",
    "ML_RATE_1", "ML_RATE_ERR_1", "ML_RATE_LOWERR_1", "ML_RATE_UPERR_1",
    "ML_CTS_1", "ML_FLUX_1", "ML_FLUX_ERR_1", "ML_EXP_1", "ML_BKG_1",
    "APE_CTS_1", "APE_BKG_1", "APE_EXP_1", "APE_POIS_1",
] + FLAGS


def load_fits_cols(path: Path, cols: list[str]) -> pd.DataFrame:
    with fits.open(path, memmap=True) as h:
        d = h[1].data
        out = {}
        for c in cols:
            v = d[c]
            if v.dtype.kind in ("S", "U"):
                out[c] = np.char.strip(v.astype("U32"))
            elif v.dtype.kind == "b":
                out[c] = v.astype(bool)
            else:
                out[c] = v.byteswap().view(v.dtype.newbyteorder("="))
        return pd.DataFrame(out)


def angsep_arcsec(ra1, dec1, ra2, dec2):
    """Small-angle-safe angular separation (haversine), degrees in, arcsec out."""
    ra1, dec1, ra2, dec2 = (np.radians(np.asarray(x, dtype="f8")) for x in (ra1, dec1, ra2, dec2))
    sd = np.sin((dec2 - dec1) / 2) ** 2
    sr = np.sin((ra2 - ra1) / 2) ** 2
    h = sd + np.cos(dec1) * np.cos(dec2) * sr
    return np.degrees(2 * np.arcsin(np.sqrt(np.clip(h, 0, 1)))) * 3600.0


def clean_mask(df: pd.DataFrame) -> pd.Series:
    m = df["EXT_LIKE"] == 0
    for f in FLAGS:
        m &= ~df[f].astype(bool)
    return m


def main() -> None:
    OUT.mkdir(exist_ok=True)
    print("loading DR2 ...")
    dr2 = load_fits_cols(DR2_FITS, DR2_COLS)
    print(f"  {len(dr2):,} rows")
    print("loading DR1 ...")
    dr1 = load_fits_cols(DR1_FITS, DR1_COLS)
    print(f"  {len(dr1):,} rows")

    stats: dict = {"n_dr2_total": int(len(dr2)), "n_dr1_total": int(len(dr1))}

    # --- join on the consortium cross-walk -----------------------------------
    dr2["match_type"] = np.where(dr2["UID_DR1"] > 0, "strong",
                          np.where(dr2["UID_DR1"] < 0, "weak", "none"))
    stats["n_dr2_with_dr1_match"] = int((dr2["UID_DR1"] != 0).sum())
    stats["n_dr2_strong"] = int((dr2["UID_DR1"] > 0).sum())
    stats["n_dr2_weak"] = int((dr2["UID_DR1"] < 0).sum())

    j = dr2[dr2["UID_DR1"] != 0].copy()
    j["UID_DR1_ABS"] = j["UID_DR1"].abs()
    j = j.merge(dr1.add_suffix("_D1"), left_on="UID_DR1_ABS", right_on="UID_D1",
                how="inner", validate="many_to_one")
    stats["n_joined"] = int(len(j))

    # --- cleaning -------------------------------------------------------------
    n0 = len(j)
    m_point = (j["EXT_LIKE"] == 0) & (j["EXT_LIKE_D1"] == 0)
    m_flags = np.ones(len(j), dtype=bool)
    for f in FLAGS:
        m_flags &= ~j[f].astype(bool) & ~j[f + "_D1"].astype(bool)
    j["sep_arcsec"] = angsep_arcsec(j["RA"], j["DEC"], j["RA_D1"], j["DEC_D1"])
    poserr = np.sqrt(j["POS_ERR"] ** 2 + j["POS_ERR_D1"] ** 2)
    m_sep = (j["sep_arcsec"] <= 10.0) & (j["sep_arcsec"] <= 3.44 * poserr)
    m_rate = (
        (j["ML_RATE_1"] > 0) & (j["ML_RATE_1_D1"] > 0)
        & np.isfinite(j["ML_RATE_ERR_1"]) & np.isfinite(j["ML_RATE_ERR_1_D1"])
        & (j["ML_RATE_ERR_1"] > 0) & (j["ML_RATE_ERR_1_D1"] > 0)
        & (j["ML_EXP_1"] > 0) & (j["ML_EXP_1_D1"] > 0)
        & (j["ML_EXP_1"] > j["ML_EXP_1_D1"])  # stack must be deeper than eRASS1
    )
    stats["cut_losses"] = {
        "not_point_both": int((~m_point).sum()),
        "flagged_either": int((~m_flags).sum()),
        "sep_fail": int((~m_sep).sum()),
        "rate_invalid": int((~m_rate).sum()),
    }
    j = j[m_point & m_flags & m_sep & m_rate].copy()
    stats["n_clean_pairs"] = int(len(j))
    print(f"clean pairs: {len(j):,} / {n0:,}")

    # --- ratios ---------------------------------------------------------------
    r1, e1 = j["ML_RATE_1_D1"].to_numpy("f8"), j["ML_RATE_ERR_1_D1"].to_numpy("f8")
    r3, e3 = j["ML_RATE_1"].to_numpy("f8"), j["ML_RATE_ERR_1"].to_numpy("f8")
    r1lo = np.maximum(r1 - j["ML_RATE_LOWERR_1_D1"].to_numpy("f8"), 1e-12)
    r1up = r1 + j["ML_RATE_UPERR_1_D1"].to_numpy("f8")
    r3lo = np.maximum(r3 - j["ML_RATE_LOWERR_1"].to_numpy("f8"), 1e-12)
    r3up = r3 + j["ML_RATE_UPERR_1"].to_numpy("f8")
    t1, t3 = j["ML_EXP_1_D1"].to_numpy("f8"), j["ML_EXP_1"].to_numpy("f8")

    j["R_raw"] = r3 / r1
    # bright tier defines the global scale offset m (010 vs 030 + ECF etc.)
    sig1, sig3 = r1 / e1, r3 / e3
    bright = (sig1 >= 20) & (sig3 >= 20)
    m_scale = float(np.median(j.loc[bright, "R_raw"])) if bright.sum() >= 100 else 1.0
    stats["n_bright_tier"] = int(bright.sum())
    stats["bright_tier_median_R"] = m_scale
    stats["bright_tier_R_quantiles"] = {
        q: float(np.quantile(j.loc[bright, "R_raw"], float(q)))
        for q in ["0.05", "0.25", "0.5", "0.75", "0.95"]
    }
    # flux-vs-rate consistency (ECF change diagnostic)
    with np.errstate(divide="ignore", invalid="ignore"):
        rf = j["ML_FLUX_1"].to_numpy("f8") / j["ML_FLUX_1_D1"].to_numpy("f8")
    ok = np.isfinite(rf) & bright
    stats["bright_tier_median_fluxratio_over_rateratio"] = (
        float(np.median(rf[ok] / j.loc[ok, "R_raw"])) if ok.sum() else None
    )

    j["R"] = j["R_raw"] / m_scale  # scale-corrected stacked ratio
    # per-source fader floor: R expected if source off after eRASS1
    j["fader_floor"] = (t1 / t3) / m_scale

    # implied post-eRASS1 rate (in DR1 rate units; r3 corrected back by m)
    r3c = r3 / m_scale
    e3c = e3 / m_scale
    dt = t3 - t1
    j["rate23"] = (r3c * t3 - r1 * t1) / dt
    j["rate23_err"] = np.sqrt((e3c * t3) ** 2 + (e1 * t1) ** 2) / dt
    with np.errstate(divide="ignore", invalid="ignore"):
        j["epoch_ratio"] = j["rate23"] / r1          # >1 riser, <1 fader
    # conservative (1-sigma worst-direction) stacked amplitudes
    with np.errstate(divide="ignore", invalid="ignore"):
        R_min = (r3lo / m_scale) / r1up              # risers survive this
        R_max = (r3up / m_scale) / r1lo              # faders survive 1/this
    j["amp_cons"] = np.maximum(R_min, 1.0 / np.maximum(R_max, 1e-12))
    # variability significance in rate space (scale-corrected)
    j["z_var"] = np.abs(r3c - r1) / np.sqrt(e3c ** 2 + e1 ** 2)

    # epoch-space conservative amplitudes.
    # Faders: lower bound on the fade factor = r1 (1-sigma low) over the 2-sigma
    #         UPPER limit on the post-eRASS1 rate.
    #         If rate23 + 2 sigma < 0 the stack contains significantly FEWER
    #         counts than eRASS1 alone supplied -> the containment assumption is
    #         violated (030 flare-filtering removed eRASS1 events, pileup, or a
    #         bad eRASS1 fit). Amplitude is then undefined: NaN + flag.
    # Risers: lower bound on the rise factor = rate23 (1-sigma low) over r1
    #         (1-sigma high).
    r23_ul2 = j["rate23"].to_numpy("f8") + 2 * j["rate23_err"].to_numpy("f8")
    j["containment_violated"] = r23_ul2 <= 0
    with np.errstate(divide="ignore", invalid="ignore"):
        fade_amp = np.where(r23_ul2 > 0, r1lo / r23_ul2, np.nan)
    r23_lo = j["rate23"] - j["rate23_err"]
    rise_amp = np.maximum(r23_lo.to_numpy("f8"), 1e-12) / r1up
    j["epoch_amp_cons"] = np.where(j["epoch_ratio"] < 1, fade_amp, rise_amp)
    j["direction"] = np.where(j["R"] < 1, "fade", "rise")
    # sub-floor stacked ratios (R below the pure switch-off prediction) share the
    # same pathology in weaker form: mark them.
    j["subfloor"] = j["R"] < 0.9 * j["fader_floor"]

    # --- distribution statistics ---------------------------------------------
    for lbl, msk in [
        ("all_clean", np.ones(len(j), dtype=bool)),
        ("z5", (j["z_var"] >= 5).to_numpy()),
        ("z5_sig8", ((j["z_var"] >= 5) & (np.maximum(sig1, sig3) >= 8)).to_numpy()),
    ]:
        sub = j.loc[msk, "R"]
        stats[f"{lbl}_n"] = int(msk.sum())
        if msk.sum():
            stats[f"{lbl}_R_quantiles"] = {q: float(np.quantile(sub, float(q)))
                                           for q in ["0.01", "0.05", "0.5", "0.95", "0.99"]}
            stats[f"{lbl}_frac_amp_gt"] = {
                str(k): float((np.maximum(sub, 1 / sub) > k).mean()) for k in [2, 3, 5, 10]
            }
    # counts of strong stacked variables at conservative amplitude
    for k in [2, 3, 5, 10]:
        stats[f"n_cons_amp_gt{k}_z5"] = int(((j["amp_cons"] > k) & (j["z_var"] >= 5)).sum())
    for k in [5, 10, 20, 50]:
        stats[f"n_epoch_amp_gt{k}_z5"] = int(
            ((j["epoch_amp_cons"] > k) & (j["z_var"] >= 5) & j["epoch_amp_cons"].notna()).sum())
    stats["n_containment_violated_z5"] = int((j["containment_violated"] & (j["z_var"] >= 5)).sum())

    # --- ranked table ---------------------------------------------------------
    rank = j[(j["z_var"] >= 5)].copy()
    rank["rank_amp"] = np.fmax(rank["amp_cons"], rank["epoch_amp_cons"].fillna(0))
    rank = rank.sort_values("rank_amp", ascending=False)
    keep = [
        "IAUNAME", "DETUID", "RA", "DEC", "POS_ERR", "sep_arcsec", "match_type",
        "direction", "DET_LIKE_0", "DET_LIKE_0_D1",
        "ML_RATE_1", "ML_RATE_ERR_1", "ML_RATE_1_D1", "ML_RATE_ERR_1_D1",
        "ML_FLUX_1", "ML_FLUX_1_D1", "ML_EXP_1", "ML_EXP_1_D1",
        "R_raw", "R", "fader_floor", "rate23", "rate23_err", "epoch_ratio",
        "amp_cons", "epoch_amp_cons", "z_var", "rank_amp",
        "containment_violated", "subfloor", "IAUNAME_D1",
        "MJD_MIN_D1", "MJD_MAX_D1", "FLAG_SP_SCL",
    ]
    rank[keep].head(200).to_csv(OUT / "w2_ranked_variables.csv", index=False)

    # --- vanished: bright clean DR1 sources with no DR2 counterpart ----------
    matched_uids = set(np.abs(dr2.loc[dr2["UID_DR1"] != 0, "UID_DR1"]).tolist())
    v = dr1[clean_mask(dr1) & (dr1["DET_LIKE_0"] >= 30)].copy()
    v = v[~v["UID"].isin(matched_uids)]
    stats["n_dr1_clean_detlike30"] = int((clean_mask(dr1) & (dr1["DET_LIKE_0"] >= 30)).sum())
    stats["n_vanished_detlike30"] = int(len(v))
    v.sort_values("DET_LIKE_0", ascending=False)[
        ["IAUNAME", "UID", "RA", "DEC", "POS_ERR", "DET_LIKE_0",
         "ML_RATE_1", "ML_RATE_ERR_1", "ML_FLUX_1", "ML_EXP_1", "MJD_MIN", "MJD_MAX"]
    ].head(100).to_csv(OUT / "w2_vanished.csv", index=False)

    # --- new-bright: clean DR2 sources with no DR1 counterpart ---------------
    nb = dr2[clean_mask(dr2) & (dr2["UID_DR1"] == 0) & (dr2["DET_LIKE_0"] >= 30)].copy()
    stats["n_new_detlike30"] = int(len(nb))
    # empirical eRASS1 detectability: 5th percentile of DR1 clean rate in exposure bins
    d1c = dr1[clean_mask(dr1)]
    bins = np.geomspace(max(d1c["ML_EXP_1"].min(), 30), d1c["ML_EXP_1"].max() * 1.01, 25)
    idx = np.digitize(d1c["ML_EXP_1"], bins)
    r_lim = {i: float(np.quantile(d1c["ML_RATE_1"][idx == i], 0.05))
             for i in np.unique(idx) if (idx == i).sum() >= 50}
    nb_t1 = nb["ML_EXP_1"] / 3.0  # rough eRASS1 exposure ~ stack/3 (approximation, flagged)
    nb_idx = np.digitize(nb_t1, bins)
    nb["approx_erass1_rate_lim"] = [r_lim.get(i, np.nan) for i in nb_idx]
    with np.errstate(divide="ignore", invalid="ignore"):
        nb["implied_min_rise"] = nb["ML_RATE_1"] / nb["approx_erass1_rate_lim"]
    nb = nb.sort_values("ML_RATE_1", ascending=False)
    nb[["IAUNAME", "DETUID", "RA", "DEC", "POS_ERR", "DET_LIKE_0",
        "ML_RATE_1", "ML_RATE_ERR_1", "ML_FLUX_1", "ML_EXP_1",
        "approx_erass1_rate_lim", "implied_min_rise"]].head(100).to_csv(
        OUT / "w2_new_bright.csv", index=False)
    stats["n_new_bright_rate_gt_p2"] = int((nb["ML_RATE_1"] > 0.2).sum())

    # --- plot -----------------------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    SURFACE, INK, INK2 = "#fcfcfb", "#0b0b0b", "#52514e"
    BLUE, ORANGE = "#2a78d6", "#eb6834"
    fig, ax = plt.subplots(figsize=(8.5, 4.6), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    logR = np.log10(j["R"])
    bins2 = np.linspace(-1.6, 1.6, 129)
    ax.hist(logR, bins=bins2, color=BLUE, alpha=0.85, label="all clean pairs")
    z5m = (j["z_var"] >= 5).to_numpy()
    ax.hist(logR[z5m], bins=bins2, color=ORANGE, alpha=0.9,
            label=r"variability $z \geq 5$")
    ax.set_yscale("log")
    for x, lab in [(-1.0, "10x fade"), (1.0, "10x rise")]:
        ax.axvline(x, color=INK2, lw=1, ls="--")
        ax.text(x, ax.get_ylim()[1] * 0.5, f" {lab}", color=INK2, fontsize=8,
                rotation=90, va="top")
    ax.axvline(np.log10(1 / 3 / m_scale), color=INK2, lw=0.8, ls=":")
    ax.text(np.log10(1 / 3 / m_scale), ax.get_ylim()[1] * 0.5, " stacking fader floor (~1/3)",
            color=INK2, fontsize=7, rotation=90, va="top")
    ax.set_xlabel("log10  eRASS:3-stacked rate / eRASS1 rate  (scale-corrected, 0.2-2.3 keV)",
                  color=INK)
    ax.set_ylabel("pairs per bin", color=INK)
    ax.tick_params(colors=INK2, labelsize=8)
    for s in ax.spines.values():
        s.set_color("#d8d7d3")
    ax.grid(axis="y", color="#e8e7e3", lw=0.6)
    ax.set_axisbelow(True)
    leg = ax.legend(frameon=False, fontsize=9, labelcolor=INK)
    fig.suptitle("DR1 vs DR2: stacked rate-ratio distribution (clean point-source pairs)",
                 color=INK, fontsize=11, y=0.97)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(OUT / "w2_ratio_distribution.png", facecolor=SURFACE)

    # --- persist --------------------------------------------------------------
    j.to_parquet(DATA / "w2_pairs.parquet", index=False)
    with open(OUT / "w2_stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
