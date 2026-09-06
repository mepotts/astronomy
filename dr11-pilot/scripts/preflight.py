"""Offline native CCD-set comparison; no image pixels or network access."""
import argparse
import hashlib
import io
import json
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HASHES = {
    "dr10": "2516b36b132719bd9c403278f7573192c74e3436b4e58c25ade1d0dd31bbd78a",
    "dr11": "97ba8e9aa70975a2828b6e87a8143f398bff7bc4beaaea5b3bc16cd51a2932be",
}
SPEC_HASH = "3662311fbb27112bf4dd7eee2a4a4397c8a6d08ff1c07c8cb97852ed911b7936"


def compare(old, new):
    """Keys are camera, exposure number, CCD name, filter; never dedup silently."""
    for rows in (old, new):
        if not rows or len(set(rows)) != len(rows):
            raise ValueError("empty or duplicated CCD keys: STOP_PROVENANCE")
        if any(len(k) != 4 or not k[0] or not k[2] or k[3] not in "griz"
               or len(k[3]) != 1 or k[1] <= 0 for k in rows):
            raise ValueError("invalid CCD key: STOP_PROVENANCE")
    old, new = set(old), set(new)
    added, removed = new - old, old - new
    bands = {}
    for band in "griz":
        bands[band] = {
            "dr10_ccds": sum(k[3] == band for k in old),
            "dr11_ccds": sum(k[3] == band for k in new),
            "added_ccds": sum(k[3] == band for k in added),
            "removed_ccds": sum(k[3] == band for k in removed),
            "dr10_exposures": len({(k[0], k[1]) for k in old if k[3] == band}),
            "dr11_exposures": len({(k[0], k[1]) for k in new if k[3] == band}),
        }
    return {
        "status": "READY_IMAGE_SPEC" if bands["r"]["added_ccds"] else "STOP_NO_NEW_R_INPUTS",
        "bands": bands, "added_keys": sorted(added), "removed_keys": sorted(removed),
        "common_ccds": len(old & new), "science_pixels_downloaded": False,
        "validated_depth_or_recovery": False,
    }


def replay(bundle):
    from astropy.io import fits
    if hashlib.sha256((ROOT / "SPEC-2026-09-06.md").read_bytes()).hexdigest() != SPEC_HASH:
        raise ValueError("frozen specification changed")
    keys, sources = {}, {}
    with zipfile.ZipFile(bundle) as archive:
        for release, digest in HASHES.items():
            name = f"{release}-1910p165-ccds.fits"
            info = archive.getinfo(name)
            if info.file_size > 4 * 1024**2:
                raise ValueError("response exceeds frozen cap")
            raw = archive.read(name)
            if hashlib.sha256(raw).hexdigest() != digest:
                raise ValueError(f"source hash mismatch: {release}")
            with fits.open(io.BytesIO(raw)) as hdus:
                hdus.verify("exception")
                table = hdus[1].data
                if any(table["ccd_cuts"] != 0):
                    raise ValueError("unexpected rejected CCD in used-input table")
                keys[release] = [(str(r["camera"]).strip(), int(r["expnum"]),
                                  str(r["ccdname"]).strip(), str(r["filter"]).strip())
                                 for r in table]
                sources[release] = {
                    "url": f"https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/{release}/south/coadd/191/1910p165/legacysurvey-1910p165-ccds.fits",
                    "bytes": len(raw), "sha256": digest,
                    "rows": len(table), "ccd_cuts": dict(Counter(map(str, table["ccd_cuts"]))),
                }
    return {"spec_sha256": SPEC_HASH, "sources": sources, **compare(keys["dr10"], keys["dr11"])}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=ROOT / "evidence/ccds-20260906.zip")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = json.dumps(replay(args.bundle), indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(result)
    print(result)
