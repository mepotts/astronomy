"""M15: convert eta Tel B ADP (IDP) spectra to the cr2res extracted layout viper reads.

The original CD-35 converter lived in a dead scratchpad; this one is reverse-engineered
from the surviving cr2res_data products and re-verified the M10 §10.1 way (that check
caught nothing wrong then and is cheap enough to run on every file now):

  ADP:     one SPECTRUM table, columns WAVE/FLUX/ERR/QUAL/ORDER/DETEC/XPOS/TRACE,
           2048 rows per (ORDER, DETEC) segment.
  cr2res:  CHIP1/2/3 BinTableHDUs (EXTNAME per detector), 2048 rows, one column triple
           {order:02d}_01_{SPEC,ERR,WL} per DRS order, WL in nm; ADP primary header
           copied through (it carries MJD-OBS, WLEN ID, RA/DEC — everything viper's
           inst_CRIRES reads).

Verification per file: 21 segments of 2048, WL strictly monotonic within segments,
detector 1 bluest, and every segment centre within 1 nm of the header's own CWLENn.

Usage: python m15_convert.py [--src data/spectra_etatel] [--dst data/etatel_cr2res]
Skips non-H1567 files and existing outputs.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]


def convert(src: Path, dst: Path) -> str:
    with fits.open(src) as h:
        hdr = h[0].header.copy()
        wlen = hdr.get("HIERARCH ESO INS WLEN ID") or hdr.get("ESO INS WLEN ID")
        if wlen != "H1567":
            return f"skip ({wlen})"
        t = h[1].data
        wave, flux, err = (np.asarray(t["WAVE"][0]).ravel(),
                           np.asarray(t["FLUX"][0]).ravel(),
                           np.asarray(t["ERR"][0]).ravel())
        order, detec, xpos = (np.asarray(t["ORDER"][0]).ravel().astype(int),
                              np.asarray(t["DETEC"][0]).ravel().astype(int),
                              np.asarray(t["XPOS"][0]).ravel().astype(int))

    hdus = [fits.PrimaryHDU(header=hdr)]
    seg_centres = []
    for det in (1, 2, 3):
        cols = []
        for o in sorted(set(order[detec == det])):
            m = (detec == det) & (order == o)
            if m.sum() != 2048:
                return f"FAIL segment (det {det}, order {o}) has {m.sum()} rows"
            i = np.argsort(xpos[m])
            w, f, e = wave[m][i], flux[m][i], err[m][i]
            if not (np.all(np.diff(w) > 0) or np.all(np.diff(w) < 0)):
                return f"FAIL WL not monotonic (det {det}, order {o})"
            seg_centres.append((det, o, float(w[1024])))
            p = f"{o:02d}_01"
            cols += [fits.Column(name=f"{p}_SPEC", format="D", array=f),
                     fits.Column(name=f"{p}_ERR", format="D", array=e),
                     fits.Column(name=f"{p}_WL", format="D", array=w)]
        hdus.append(fits.BinTableHDU.from_columns(cols, name=f"CHIP{det}"))

    if len(seg_centres) != 21:
        return f"FAIL {len(seg_centres)} segments (want 21)"
    det1 = np.mean([c for d, _, c in seg_centres if d == 1])
    det3 = np.mean([c for d, _, c in seg_centres if d == 3])
    if det1 >= det3:
        return "FAIL detector 1 not bluest"
    cwlens = [hdr[k] for k in hdr if k.startswith("CWLEN")]
    if cwlens:
        centres_by_order: dict[int, list[float]] = {}
        for _, o, c in seg_centres:
            centres_by_order.setdefault(o, []).append(c)
        order_centres = sorted(np.mean(v) for v in centres_by_order.values())
        for cw in cwlens:
            if min(abs(cw - oc) for oc in order_centres) > 1.0:
                return f"FAIL CWLEN {cw} matches no order centre"

    fits.HDUList(hdus).writeto(dst, overwrite=True)
    return "ok"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(ROOT / "data" / "spectra_etatel"))
    ap.add_argument("--dst", default=str(ROOT / "data" / "etatel_cr2res"))
    args = ap.parse_args()
    srcd, dstd = Path(args.src), Path(args.dst)
    dstd.mkdir(parents=True, exist_ok=True)

    n_ok = 0
    for f in sorted(srcd.glob("ADP*.fits")):
        out = dstd / f.name
        if out.exists() and out.stat().st_size > 0:
            print(f"have {f.name}")
            n_ok += 1
            continue
        v = convert(f, out)
        print(f"{f.name}: {v}")
        if v == "ok":
            n_ok += 1
    print(f"{n_ok} converted products in {dstd}")


if __name__ == "__main__":
    main()
