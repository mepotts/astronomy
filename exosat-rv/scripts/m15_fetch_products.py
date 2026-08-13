"""M15: fetch the eta Tel B calib_level=2 products and report their actual settings.

Downloads every ObsCore product from data/m15-eta-tel-inventory.json into
data/spectra_etatel/ (safe names, skip-if-present), then reads each header's
WLEN ID / CWLEN / MJD-OBS. The product header is authoritative for the setting
(DATA-SOURCES.md: filter_path lies at least once in 18) — and the setting split
decides how many nights can share one template and order set.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from exosat_rv.archive.fetch import download, _safe_name  # noqa: E402

INV = ROOT / "data" / "m15-eta-tel-inventory.json"
DEST = ROOT / "data" / "spectra_etatel"


def main() -> None:
    inv = json.loads(INV.read_text(encoding="utf-8"))
    prods = inv["products"]
    DEST.mkdir(parents=True, exist_ok=True)
    print(f"{len(prods)} products -> {DEST}", flush=True)

    got = []
    for p in prods:
        url = p["access_url"]
        dp = p.get("dp_id") or url.rsplit("/", 1)[-1]
        dest = DEST / _safe_name(f"{dp}.fits" if not dp.endswith(".fits") else dp)
        if dest.exists() and dest.stat().st_size > 0:
            print(f"  have {dest.name}", flush=True)
            got.append(dest)
            continue
        try:
            path = download(url, dest)
            print(f"  got  {path.name}  ({path.stat().st_size // 1024} kB)", flush=True)
            got.append(path)
        except Exception as e:  # noqa: BLE001 - report and continue; retry on rerun
            print(f"  FAIL {dp}: {e}", flush=True)

    print("\nsettings (header is authoritative):", flush=True)
    from astropy.io import fits
    rows = []
    for f in sorted(got):
        try:
            h = fits.getheader(f)
            wlen = h.get("HIERARCH ESO INS WLEN ID") or h.get("ESO INS WLEN ID") or "?"
            rows.append((str(h.get("DATE-OBS", "?"))[:10], str(wlen),
                         float(h.get("MJD-OBS", 0)), f.name))
        except Exception as e:  # noqa: BLE001
            print(f"  unreadable {f.name}: {e}", flush=True)
    rows.sort()
    from collections import Counter
    for date, wlen, mjd, name in rows:
        print(f"  {date}  {wlen:8s}  {name}", flush=True)
    print("\nsetting counts:", dict(Counter(w for _, w, _, _ in rows)), flush=True)
    (ROOT / "data" / "m15-product-settings.json").write_text(
        json.dumps([{"date": d, "wlen": w, "mjd": m, "file": n}
                    for d, w, m, n in rows], indent=2), encoding="utf-8")
    print("M15FETCH_DONE", flush=True)


if __name__ == "__main__":
    main()
