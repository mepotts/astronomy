"""M2: per-candidate verdicts for the 140 M1 candidates.

Verdict classes (M2 brief):
  IDENTIFIED            known object / already-reported transient (says as what)
  PLAUSIBLE-CLASS       best class + evidence + what would confirm it
  GENUINELY-UNEXPLAINED survived all checks (the checks are listed)
  ARTIFACT              a catalog systematic explains it (which one)

Inputs (all produced this milestone unless noted):
  out/m1_candidates.csv         the 140 candidates (M1)
  out/m2_vanished_forensics.csv full 261 vanished + Sect.-3.2.5 geometry + UL server
  out/m2_archival_xray.csv      2RXS/XMMSL3/CSC2.1/2SXPS/5XMM/CatWISE/Gaia-var/
                                ART-XC/MKM matches for all touched sources
  out/m2_counterparts.csv       NWAY eRASSc3 counterpart rows (DR2-detected cands)
  out/m2_asassn_summary.csv     ASAS-SN Sky Patrol v2 light-curve summaries

A manual dossier table carries the per-object investigations (TNS cone searches,
literature web searches, LS10 cutout inspection, ASAS-SN details) done 2026-08-14;
everything else is scored by uniform rules. Output: out/m2_verdicts.csv =
all m1_candidates columns + verdict columns.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"

SRC_TAGS = ("services 2026-08-14: CDS X-Match (2RXS J/A+A/588/A103, XMMSL3 IX/71, "
            "CSC2.1 IX/70, 2SXPS IX/58, CatWISE II/365, GaiaDR3 var I/358, "
            "ART-XC J/A+A/687/A183, MKM J/MNRAS/544/885); HEASARC xmmssc(5XMM); "
            "NWAY eRASSc3 27Jul2026; DR2 UL server erodat; SIMBAD; TNS; ASAS-SN SkyPatrol v2")

# --- manual dossier verdicts (per-object investigation, 2026-08-14) ----------
# name -> (verdict, detail, evidence)
DOSSIER: dict[str, tuple[str, str, str]] = {
    "3eRASS J094452.8-711152": (
        "GENUINELY-UNEXPLAINED",
        "x57 hard-detected riser with no counterpart in any band",
        "survived ALL checks: NWAY p_any=0.0000 (GDR3) / 4e-6 (CW2020), LS10 no coverage; "
        "SIMBAD 30\" empty; no 2RXS/XMMSL3/CSC2.1/2SXPS/5XMM entry; not in ART-XC "
        "(4-12 keV, updated 18-Jul-2025); TNS 60\" empty; no literature under "
        "eRASSU/eRASSt/SRGe/1eRASS J094452 names (web search). Present in Hard cat "
        "(DET_LIKE_3=197, eRASS3_Hard_v1.2) -> hard/absorbed spectrum. eRASS1 DET_LIKE 25 "
        "-> stack 9401, epoch rise x57 (cons.), z=43. ASAS-SN source at position is the "
        "10.2\" Gaia star (blend), not the X-ray source. Candidates: obscured XRB/VFXT, "
        "magnetar outburst, extreme absorbed CV; b=-13.6 deg"),
    "3eRASS J155100.8-453347": (
        "PLAUSIBLE-CLASS",
        "M-dwarf superflare candidate (counterpart ambiguous)",
        "new-bright 1.38 ct/s stacked (implied rise >=x49); hard-detected (DET_LIKE_3=70); "
        "Gaia DR3 M dwarf G=17.75 plx=10.99+-0.13 (91 pc) at 1.95\"; CatWISE 1.9\" "
        "W1-W2=0.10 (stellar); NWAY ambiguous: p_any 0.07 (GDR3) vs 0.71 (CW2020); "
        "if the M dwarf: <Lx>~1e30 erg/s over 556 d = extreme, flare-dominated; "
        "Gaia G range 17.67-17.84 (no flare caught); no prior X-ray, TNS+SIMBAD 30\" empty, "
        "no literature. CONFIRM: optical spectrum (activity/youth), X-ray re-observation"),
    "3eRASS J060622.5-624814": (
        "PLAUSIBLE-CLASS",
        "TDE-like extragalactic fader (host unconfirmed)",
        "epoch fade >=x18 (2-sigma cons.); position blank in optical/IR except LS10 "
        "galaxy-class source g=23.5 at ~7\" (NWAY p_any 0.002, class_gal_exgal=1); "
        "SIMBAD galaxy WISE J060621.36-624826.5 at 14.4\" too far; no CatWISE, no prior "
        "X-ray, TNS 60\" empty; LS10 cutout: faint field, no bright host; POS_ERR 2.9\". "
        "CONFIRM: deep imaging/spectroscopy of the LS10 source + sub-arcsec X-ray position"),
    "3eRASS J071521.8-191603": (
        "IDENTIFIED",
        "SRGt J071522.1-191609 - eROSITA-discovered transient (2020)",
        "already reported: discovery ATel #13657, optical counterpart ATel #13669, "
        "VLA radio ATel #13716; our slice catches the decline (epoch fade >=x32)"),
    "3eRASS J123822.2-253210": (
        "IDENTIFIED",
        "SRGt J123822.3-253206 - bright short-duration X-ray flare (eRASS1)",
        "already reported: ATel #13416; = SRGA J123821.5-253208 (ART-XC, NewXray, "
        "UNIDENT type); discussed as fast X-ray transient with radio counterpart "
        "(arXiv:2407.07257); our fade x11 = flare decay in the stack"),
    "3eRASS J142139.6-295321": (
        "IDENTIFIED",
        "eRASSt J142140-295321 - published TDE candidate (IMBH)",
        "already reported: X-ray-selected TDE candidate with ATCA radio study "
        "(arXiv:2504.08426); quasi-simultaneous optical transient, possibly off-nuclear"),
    "3eRASS J090506.7-533020": (
        "IDENTIFIED",
        "MAXI J0903-531 - Be/X-ray binary transient",
        "ART-XC SRGA J090507.5-533024 counterpart name MAXI J0903-531 (HMXB), "
        "sep 6.9\"; SIMBAD 2MASS J09050682-5330195 XB*; rise x55 = outburst"),
    "3eRASS J115415.8-501801": (
        "IDENTIFIED",
        "EP240309a / SRGA J115415.6-501801 - intermediate polar",
        "ART-XC match 2.5\" (CV?, NewXray); classified intermediate polar as "
        "EP J115415.8-501810 (arXiv:2405.01996)"),
    "3eRASS J144357.1-390839": (
        "IDENTIFIED",
        "PKS 1440-389 - blazar (z=0.1385)",
        "ART-XC SRGA J144356.4-390830 counterpart PKS 1440-389, BLAZAR z=0.1385"),
    "1eRASS J011706.7-732648": (
        "ARTIFACT",
        "SMC X-1 field: split/moved detection of a piled-up HMXB",
        "ART-XC SRGA J011704.8-732638 = SMC X-1 at 13\"; DR2 source 13.9\" away at "
        "54 ct/s (UID_DR1 crosswalk miss at 4x pos-err); UL presence 95.5 - flux very "
        "much still there"),
    "1eRASS J131400.5-190157": (
        "IDENTIFIED",
        "MKM eRASS1 Galactic transient - nearby-star flare (d=58 pc)",
        "already reported: Maan+ catalog (J/MNRAS/544/885/ero-g-t) d=58 pc "
        "L=2.1e29 erg/s; CatWISE W1=8.6 bright star 2.9\"; ASAS-SN star steady "
        "V~13.4; DR2 stack blank (presence 1.01) - flare over"),
    "1eRASS J034852.6-552534": (
        "IDENTIFIED",
        "WTP 15abymdq - known MIR nuclear transient (z=0.037), X-ray active in eRASS1",
        "SIMBAD ev at 1.0\"; WTP MIR-transient sample (MIT WTP; z=0.0374); our eRASS1 "
        "detection (DET_LIKE 209) + stack presence 5.2 with neighbor 21.6\" - X-ray "
        "state change at a known nuclear transient; ASAS-SN 2019-21 quiet"),
    "1eRASS J050338.2-304513": (
        "PLAUSIBLE-CLASS",
        "AGN into deep X-ray low state (changing-state candidate)",
        "CatWISE 0.46\" W1-W2=0.94 (AGN colors); Gaia DR3 classifier AGN 0.93; MORX "
        "association; prior X-ray: 2RXS J050337.2-304501 (16.6\", 43.5 cts, 1990-91) + "
        "2SXPS 3.8\" 0.019 ct/s -> historically persistent; eRASS1 F=3.9e-13 "
        "(DET_LIKE 242) then stack-blank (UL presence 1.02) -> collapsed below eRASS1 "
        "level; TNS empty. CONFIRM: optical spectrum now vs archival; X-ray re-obs"),
    "1eRASS J051910.4-253443": (
        "PLAUSIBLE-CLASS",
        "flaring AGN (blazar?) - optical flares + X-ray now low",
        "XMMSL3 4.2\" F(0.2-2)=1.3e-12 (prior slew detection); CatWISE 1.6\" "
        "W1-W2=0.82 (AGN); Gaia classifier AGN 0.63; AllWISE-AGN seed in ASAS-SN; "
        "ASAS-SN optical brightenings to -1.4 mag within the eRASS window; stack "
        "blank (presence 1.03); TNS empty. CONFIRM: radio catalog check + spectrum"),
    "1eRASS J024930.1-274958": (
        "PLAUSIBLE-CLASS",
        "nuclear transient candidate in a GLADE galaxy",
        "GLADE/HyperLEDA galaxy 6.0\" (ASAS-SN blend shows excursions to -1 mag); "
        "no prior X-ray; stack blank (presence 1.07); TNS 60\" empty; DR1 POS_ERR "
        "makes 6\" association plausible but unproven. CONFIRM: host spectrum, "
        "better X-ray position"),
    "1eRASS J121547.0-173140": (
        "PLAUSIBLE-CLASS",
        "real fader, counterpart ambiguous (prior Swift detection)",
        "2SXPS detection 7.5\" (0.039 ct/s) -> was X-ray active before; ASAS-SN "
        "Mira-like variable 6.6\" (V 8.9-11.3); Gaia classifier AGN 0.24 nearby; "
        "stack blank (presence 1.15); association unresolved at eRASS1 POS_ERR"),
    "1eRASS J064759.4-441943": (
        "PLAUSIBLE-CLASS",
        "active-star coronal variability",
        "bright IR star W1=9.46 at 2.4\" (TIC/stellar_main; ASAS-SN steady 13.9); "
        "prior X-ray: 5XMM J064759.5-441941 3.0\" F(0.2-12)=2.7e-13 + 2SXPS 2.1\" "
        "0.014 ct/s -> persistent corona; eRASS1 caught high state, stack diluted"),
    "1eRASS J055329.9-663938": (
        "PLAUSIBLE-CLASS",
        "LMC-direction transient (Be/XRB outburst candidate or background AGN)",
        "LMC field; CatWISE 2.7\" W1=15.8 W1-W2=0.45; no prior X-ray; eRASS1 "
        "DET_LIKE 166 then stack blank (presence 1.03) - real switch-off; "
        "unpublished. CONFIRM: OGLE light curve of the IR source, X-ray re-obs"),
    "1eRASS J054656.6-653401": (
        "PLAUSIBLE-CLASS",
        "faint LMC-direction fader",
        "eRASS1 DET_LIKE 240 at 0.034 ct/s; stack blank (presence 1.08); nearest "
        "bright DR2 neighbor 51.6\" - too far to absorb the counts (PSF HEW ~30\"); "
        "optical-faint (Gaia G=20.1 at 1.2\")"),
    "1eRASS J050558.2-680146": (
        "ARTIFACT",
        "indeterminate: inside bright-source halo (LMC)",
        "13.0 ct/s DR2 source 16.6\" away dominates; UL server insensitive at "
        "position (presence 0.0, Flag_pos set); cannot separate fade from erbox "
        "dropout - paper Sect. 3.2.5 regime either way"),
    "1eRASS J053323.7-645745": (
        "ARTIFACT",
        "absorbed into extended emission (LMC diffuse)",
        "DR2 extended source (EXT_LIKE=136) 28.6\" away; UL presence 2.19 - flux "
        "still present at position; paper Sect. 3.2.5/5.3 regime"),
    "1eRASS J063020.5-674651": (
        "ARTIFACT",
        "absorbed into extended emission (LMC diffuse)",
        "DR2 extended source (EXT_LIKE=106) 32.1\" away; UL presence 2.52 - flux "
        "still present"),
    "1eRASS J051621.3-631123": (
        "ARTIFACT",
        "absorbed into extended emission",
        "DR2 extended source (EXT_LIKE=1486) 60.6\" away; UL presence 4.55 - flux "
        "still present"),
    "1eRASS J052524.1-655818": (
        "ARTIFACT",
        "erbox confusion dropout next to bright extended complex",
        "DR2 EXT_LIKE=42107 complex 45\" away + bright neighbor 94.8\"; UL presence "
        "7.86 - flux still present (paper Sect. 3.2.5)"),
    "1eRASS J013328.1-643410": (
        "ARTIFACT",
        "split/moved: DR2 source 7.2\" away not linked by UID_DR1",
        "3eRASS J013329.0-643406 at 7.2\" (1.06 ct/s); crosswalk miss; UL presence "
        "4.13 - flux still present"),
    "1eRASS J071212.4-363045": (
        "ARTIFACT",
        "erbox confusion dropout (bright neighbor 21.8\")",
        "similarly bright DR2 neighbor at 21.8\"; UL presence 4.17 - flux still "
        "present (paper Sect. 3.2.5)"),
    "1eRASS J053410.9-045032": (
        "ARTIFACT",
        "erbox confusion dropout; source itself = 2E 0531.7-0452 (sigma Ori field star)",
        "SIMBAD X at 7.9\" = Einstein source; ART-XC STAR? 10.6\"; bright DR2 "
        "neighbor 21.8\"; UL presence 3.28 - flux still present"),
    "1eRASS J114724.4-495303": (
        "ARTIFACT",
        "erbox confusion dropout (bright neighbor 32.8\")",
        "DR2 neighbor 9.2 ct/s at 32.8\" (also ART-XC UNIDENT 23\"); UL presence "
        "3.85 - flux still present; DET_LIKE 1061 dropout = exactly the paper "
        "Sect. 3.2.5 bright-source failure mode"),
    "1eRASS J064100.4+095401": (
        "ARTIFACT",
        "erbox confusion dropout (bright neighbor 29.9\")",
        "DR2 neighbor 3.9 ct/s at 29.9\"; UL presence 5.85 - flux still present"),
    "3eRASS J234403.0-352639": (
        "IDENTIFIED",
        "eRASSt J234402.9-352640 - published nuclear ignition (TDE or AGN turn-on)",
        "already reported: 'luminous X-ray ignition' paper (arXiv:2302.06989) + "
        "radio-flare/outflow study (MNRAS 528, 7123, 2024); our new-bright x97 "
        "recovers the ignition"),
    "3eRASS J045649.7-203747": (
        "IDENTIFIED",
        "eRASSt J045650.3-203750 - published repeating partial TDE candidate",
        "already reported: extreme repeating nuclear transient (arXiv:2208.12452, "
        "A&A 2023); our new-bright x58 recovers it"),
    "3eRASS J040311.3-023207": (
        "PLAUSIBLE-CLASS",
        "variable AGN (x16 riser)",
        "Gaia DR3 classifier AGN 0.41; Gaia G range 18.77-19.75 (~1 mag optical "
        "variability); CatWISE 0.80\" W1-W2=0.41; no prior X-ray; no TNS. "
        "CONFIRM: spectrum/redshift"),
    "3eRASS J090533.5-145955": (
        "PLAUSIBLE-CLASS",
        "variable AGN (x9 riser)",
        "prior 2SXPS detection 4.7\" (0.028 ct/s); CatWISE 1.1\" W1-W2=0.62; Gaia "
        "classifier AGN 0.47, G range 17.68-18.51"),
    "3eRASS J082731.8-694520": (
        "PLAUSIBLE-CLASS",
        "Galactic star flare / CV candidate (x14 riser)",
        "CatWISE 0.73\" W1=14.11 W1-W2=0.01 (stellar); ASAS-SN stellar source "
        "0.57\" median 17.5 with mild brightenings; Gaia G=17.17 no plx - distant "
        "star or compact binary. CONFIRM: spectrum"),
    "3eRASS J122150.2-533805": (
        "PLAUSIBLE-CLASS",
        "obscured Galactic transient / YSO flare (plane, b=0.3 deg)",
        "CatWISE 0.98\" W1=14.06 W1-W2=0.60 (reddened/YSO-like); Gaia G=19.9 no "
        "plx; no prior X-ray; x7 rise"),
    "3eRASS J062106.5-711307": (
        "PLAUSIBLE-CLASS",
        "CV candidate (x12 riser)",
        "Gaia G=20.47 plx 0.61+-0.15 (4-sigma, ~1.6 kpc); CatWISE 2.4\" faint "
        "(W1=17.7); no prior X-ray. CONFIRM: spectrum"),
}

AGN_W12 = 0.8  # CatWISE W1-W2 AGN-ish threshold (Stern-like; coarse)


def gen_rule(row: pd.Series) -> tuple[str, str, str]:
    """Uniform rules for candidates without a manual dossier."""
    ot_raw, id_raw = row.get("simbad_otype"), row.get("simbad_main_id")
    otype = "" if pd.isna(ot_raw) else str(ot_raw).strip()
    sid = "" if pd.isna(id_raw) else str(id_raw).strip()
    cand_set = row["cand_set"]
    # --- vanished: forensic v2 drives it -------------------------------------
    if str(cand_set).startswith("vanished"):
        v2 = str(row.get("forensic_class_v2") or "")
        pres = row.get("ul_presence")
        if v2.startswith("ARTIFACT") or v2 in ("CONFUSED-IDENTITY", "INDETERMINATE-HALO"):
            det = {"ARTIFACT-CONFUSION": "erbox confusion dropout (paper Sect. 3.2.5)",
                   "ARTIFACT-EXTENDED": "absorbed into extended source",
                   "ARTIFACT-SPLIT/MOVED": "DR2 source within 15\" (crosswalk miss)",
                   "ARTIFACT-UNCLEAR-PERSIST": "flux persists at position, mechanism unclear",
                   "CONFUSED-IDENTITY": "bright source within ~PSF: identity confused",
                   "INDETERMINATE-HALO": "inside bright-source halo, UL insensitive"}.get(v2, v2)
            ev = (f"UL presence {pres:.2f}; bright-neighbor sep "
                  f"{row.get('nn2_bright_sep_arcsec')}\"" if pd.notna(pres) else v2)
            return "ARTIFACT", det, ev
        # FADE-CANDIDATE
        if otype and otype not in ("X", "ev", "?"):
            return ("IDENTIFIED",
                    f"{sid} ({otype}) - single-epoch flare, faded",
                    f"SIMBAD {otype} at {row.get('simbad_sep_arcsec'):.1f}\"; position now "
                    f"blank in stack (UL presence {pres:.2f})")
        w12 = row.get("catwise_w1w2")
        gcl = str(row.get("gclass_class") or "")
        if gcl == "AGN" or (pd.notna(w12) and w12 >= AGN_W12):
            return ("PLAUSIBLE-CLASS", "AGN fader (high-amplitude X-ray variability)",
                    f"CatWISE W1-W2={w12}; Gaia classifier {gcl} "
                    f"{row.get('gclass_score')}; stack blank (presence {pres:.2f})")
        if pd.notna(row.get("gaia_plx")) and pd.notna(row.get("gaia_plx_err")) \
                and row.get("gaia_plx_err") and row["gaia_plx"] / row["gaia_plx_err"] >= 3:
            return ("PLAUSIBLE-CLASS", "stellar flare fader (parallax star)",
                    f"Gaia plx {row['gaia_plx']:.2f}+-{row['gaia_plx_err']:.2f}; "
                    f"stack blank (presence {pres:.2f})")
        return ("PLAUSIBLE-CLASS", "unclassified real fader (blank counterpart)",
                f"position blank in stack (UL presence {pres:.2f}); no archival X-ray; "
                f"counterpart faint/absent - XRB/CV/AGN flare all open")
    # --- pair / new_bright ----------------------------------------------------
    if otype and otype not in ("X", "ev", "?"):
        extra = ""
        if pd.notna(row.get("artxc_cname")) and str(row.get("artxc_cname")).strip():
            extra = f"; ART-XC counterpart {row['artxc_cname']} ({row.get('artxc_type')})"
        elif pd.notna(row.get("mkm_sep")):
            extra = "; in MKM eRASS1 Galactic-transient catalog"
        return ("IDENTIFIED", f"{sid} ({otype})",
                f"SIMBAD {otype} at {row.get('simbad_sep_arcsec'):.1f}\"{extra}")
    # X-ray-only SIMBAD or nothing: data-driven class
    w12 = row.get("catwise_w1w2")
    gcl = str(row.get("gclass_class") or "")
    prior = []
    for tag in ("2rxs", "xmmsl3", "csc21", "2sxps", "xmmssc"):
        if pd.notna(row.get(f"{tag}_sep")):
            prior.append(tag)
    prior_s = ",".join(prior) if prior else "none"
    if gcl == "AGN" or (pd.notna(w12) and w12 >= AGN_W12):
        gtxt = (f"; Gaia classifier {gcl} {row.get('gclass_score'):.2f}"
                if gcl and gcl != "nan" else "")
        return ("PLAUSIBLE-CLASS", "AGN (variable)",
                f"CatWISE W1-W2={w12:.2f}{gtxt}; prior X-ray: {prior_s}")
    plx, plxe = row.get("gaia_plx"), row.get("gaia_plx_err")
    if pd.notna(plx) and pd.notna(plxe) and plxe and plx / plxe >= 3:
        red = " (red-dwarf flare locus)" if "red-dwarf" in str(row.get("first_guess_class")) else ""
        return ("PLAUSIBLE-CLASS", f"Galactic flare star / CV{red}",
                f"Gaia plx {plx:.2f}+-{plxe:.2f}; prior X-ray: {prior_s}")
    if otype:  # SIMBAD X or ev without dossier
        return ("PLAUSIBLE-CLASS", f"known X-ray source ({sid}), class unset",
                f"SIMBAD {otype}; prior X-ray: {prior_s}")
    if pd.notna(w12):
        return ("PLAUSIBLE-CLASS", "star-like counterpart, class open",
                f"CatWISE W1-W2={w12} at {row.get('catwise_sep'):.1f}\"; "
                f"prior X-ray: {prior_s}")
    return ("GENUINELY-UNEXPLAINED", "no counterpart, no archival X-ray, no identification",
            f"checks: SIMBAD, Gaia, CatWISE, 2RXS, XMMSL3, CSC2.1, 2SXPS, 5XMM, "
            f"ART-XC all empty")


def main() -> None:
    c = pd.read_csv(OUT / "m1_candidates.csv")
    van = pd.read_csv(OUT / "m2_vanished_forensics.csv")
    arx = pd.read_csv(OUT / "m2_archival_xray.csv")
    cp = pd.read_csv(OUT / "m2_counterparts.csv")

    # join helpers by name
    van_j = van[["IAUNAME", "forensic_class_v2", "ul_presence", "ul_fade_frac",
                 "nn2_bright_sep_arcsec", "in_dr2_any_sep"]].rename(
        columns={"IAUNAME": "name"})
    arx = arx.drop_duplicates("name")
    arx_j = arx[["name"] + [col for col in arx.columns if any(
        col.startswith(t) for t in ("2rxs_", "xmmsl3_", "csc21_", "2sxps_", "xmmssc_",
                                    "catwise_", "gvar_", "gclass_", "artxc_", "mkm_"))]]
    cp_j = cp[["IAUNAME", "GDR3_NWAY_p_any", "CW2020_NWAY_p_any", "LS10_NWAY_p_any",
               "hard_name", "hard_detlike3"]].rename(columns={"IAUNAME": "name"})

    # every touched candidate gets a verdict row: the 140 M1 candidates PLUS the
    # 241 vanished-full sources (full forensics+UL+archival ran on all 261; the
    # 20 already inside the 140 keep their M1 rows). SIMBAD/Gaia columns exist
    # only for the 140 (M1 queried those); extras are scored on forensics +
    # archival evidence, 4 of them with manual dossiers.
    extra = van[~van["IAUNAME"].isin(c["name"])].copy()
    extra_rows = pd.DataFrame({
        "cand_set": "vanished_full",
        "name": extra["IAUNAME"],
        "RA": extra["RA"], "DEC": extra["DEC"], "POS_ERR": extra["POS_ERR"],
        "DET_LIKE_0_D1": extra["DET_LIKE_0"],
        "ML_RATE_1_D1": extra["ML_RATE_1"], "ML_FLUX_1_D1": extra["ML_FLUX_1"],
    })
    c = pd.concat([c, extra_rows], ignore_index=True, sort=False)

    m = c.merge(van_j, on="name", how="left").merge(arx_j, on="name", how="left") \
         .merge(cp_j, on="name", how="left")
    m["catwise_w1w2"] = m["catwise_w1"] - m["catwise_w2"]

    verdicts, details, evidences, dossier = [], [], [], []
    for _, row in m.iterrows():
        if row["name"] in DOSSIER:
            v, d, e = DOSSIER[row["name"]]
            dossier.append(True)
        else:
            v, d, e = gen_rule(row)
            dossier.append(False)
        verdicts.append(v)
        details.append(d)
        evidences.append(e)

    out = c.copy()
    out["verdict"] = verdicts
    out["verdict_detail"] = details
    out["verdict_evidence"] = evidences
    out["dossier"] = dossier
    out["forensic_class_v2"] = m["forensic_class_v2"]
    out["ul_presence"] = m["ul_presence"]
    out["nway_p_any_gdr3"] = m["GDR3_NWAY_p_any"]
    out["nway_p_any_cw2020"] = m["CW2020_NWAY_p_any"]
    out["hard_detlike3"] = m["hard_detlike3"]
    out["verdict_sources"] = SRC_TAGS
    out.to_csv(OUT / "m2_verdicts.csv", index=False)

    print("verdict counts (all 140):")
    print(out["verdict"].value_counts().to_string())
    print("\nby candidate set:")
    print(out.groupby(["cand_set", "verdict"]).size().to_string())
    print("\nnon-IDENTIFIED verdicts:")
    sel = out[out["verdict"] != "IDENTIFIED"]
    for _, r in sel.iterrows():
        print(f"  {r['cand_set']:10s} {r['name']}  {r['verdict']}: {r['verdict_detail']}")
    size = (OUT / "m2_verdicts.csv").stat().st_size
    print(f"\nwrote out/m2_verdicts.csv ({size:,} bytes)")


if __name__ == "__main__":
    main()
