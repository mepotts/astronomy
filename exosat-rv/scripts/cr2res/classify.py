"""Tag every downloaded frame with the SOF category cr2res expects.

Raw frames are typed by DPR TYPE/CATG; ESO master products carry PRO CATG directly.
"""
import glob, os, sys
from astropy.io import fits

d = sys.argv[1]
rows = []
for f in sorted(glob.glob(os.path.join(d, "*.fits"))):
    try:
        h = fits.getheader(f)
    except Exception as e:
        print(f"# unreadable {os.path.basename(f)}: {e}", file=sys.stderr); continue
    pro = h.get("HIERARCH ESO PRO CATG") or h.get("ESO PRO CATG")
    dpr = h.get("HIERARCH ESO DPR TYPE") or h.get("ESO DPR TYPE") or ""
    cat = h.get("HIERARCH ESO DPR CATG") or h.get("ESO DPR CATG") or ""
    tech = h.get("HIERARCH ESO DPR TECH") or h.get("ESO DPR TECH") or ""
    wlen = h.get("HIERARCH ESO INS WLEN ID") or h.get("ESO INS WLEN ID") or ""
    dit = h.get("HIERARCH ESO DET SEQ1 DIT") or h.get("ESO DET SEQ1 DIT") or ""
    if pro:
        tag = pro
    elif dpr.startswith("DARK"):
        tag = "DARK"
    elif dpr.startswith("FLAT"):
        tag = "FLAT"
    elif "UNE" in dpr:
        tag = "WAVE_UNE"
    elif "FPET" in dpr:
        tag = "WAVE_FPET"
    elif cat == "SCIENCE" or "OBJECT" in dpr:
        # staring-mode science (HD 1160, AF Lep, 51 Eri campaigns) has no NODDING
        # in DPR TECH and must go to cr2res_obs_staring, not obs_nodding
        tag = "OBS_NODDING_OTHER" if "NODDING" in tech else "OBS_STARING_OTHER"
    else:
        tag = "UNKNOWN:" + dpr
    rows.append((f, tag, str(wlen), str(dit)))
for f, tag, wlen, dit in rows:
    print(f"{f}\t{tag}\t{wlen}\t{dit}")
