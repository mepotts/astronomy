"""Select a published stream from an independently frozen incremental footprint."""
import hashlib
import io
import json
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from astropy.io import fits
from bs4 import BeautifulSoup
from preflight import compare

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/stream-overlap-20260907"


def main():
    OUT.mkdir(exist_ok=True)
    spec = hashlib.sha256((ROOT / "STREAM-OVERLAP-SPEC-2026-09-07.md").read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    path = OUT / "provenance.json"
    manifest = json.loads(path.read_bytes()) if path.exists() else {"spec_sha256": spec, "artifacts": {}}
    if manifest["spec_sha256"] != spec:
        raise ValueError("spec changed")

    def fetch(role, url):
        if role in manifest["artifacts"]:
            record = manifest["artifacts"][role]
            bundle = ROOT / "data/raw/stream-overlap-responses-20260907.zip" if role == "paper.html" else OUT / "responses.zip"
            with zipfile.ZipFile(bundle) as z:
                raw = z.read(role)
            if record["url"] != url or hashlib.sha256(raw).hexdigest() != record["sha256"]:
                raise ValueError("source changed")
            return raw
        (OUT / "provenance.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        started = datetime.now(timezone.utc).isoformat()
        with urllib.request.urlopen(url, timeout=30) as response:
            raw = response.read(4*1024**2+1)
            if response.status != 200 or len(raw) > 4*1024**2:
                raise ValueError("bad or oversized response")
        bundle = ROOT / "data/raw/stream-overlap-responses-20260907.zip" if role == "paper.html" else OUT / "responses.zip"
        with zipfile.ZipFile(bundle, "a", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr(role, raw)
        manifest["artifacts"][role] = {"url": url, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "retrieved_utc": started}
        (OUT / "provenance.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return raw

    raw = fetch("paper.html", "https://arxiv.org/html/2407.20483v1")
    soup = BeautifulSoup(raw, "html.parser")
    tables = soup.select("figure.ltx_table")
    target = next(t for t in tables if t.get_text(" ", strip=True).startswith("Table 1:"))
    hosts = []
    for row in target.select("tbody tr"):
        cells = [c.get_text(" ", strip=True).replace("\u2212", "-") for c in row.select("th,td")]
        if len(cells) != 12:
            continue
        # Table1 leaves host coordinates blank on additional streams of the
        # same numbered host. Never forward-fill unrelated or partial blanks.
        if not cells[1] and not cells[2] and hosts:
            if cells[0].rsplit("-", 1)[0] != hosts[-1]["host"].rsplit("-", 1)[0]:
                raise ValueError("blank coordinates on an unrelated host")
            hosts.append({"host": cells[0], "ra": hosts[-1]["ra"], "dec": hosts[-1]["dec"], "inherited_host_coordinates": True})
            continue
        try:
            hosts.append({"host": cells[0], "ra": float(cells[1]), "dec": float(cells[2])})
        except ValueError:
            continue
    if len(hosts) != 63:
        raise ValueError(f"table row contract: {len(hosts)}, expected 63")
    footprint = np.load(ROOT / "evidence/footprint-20260907.npz", allow_pickle=False)
    values = footprint["values"]
    overlaps = []
    for host in hosts:
        dra = ((values[:, 0]-host["ra"]+180)%360-180)*np.cos(np.deg2rad(host["dec"]))
        selected = (np.abs(dra) <= .10) & (np.abs(values[:, 1]-host["dec"]) <= .10)
        for index in np.flatnonzero(selected):
            overlaps.append({**host, "brick": str(footprint["brick"][index]), "old_r": int(values[index, 2]), "new_r": int(values[index, 3])})
    overlaps.sort(key=lambda r: (r["brick"], r["host"]))
    result = {"published_rows": len(hosts), "overlaps": overlaps, "selected": overlaps[0] if overlaps else None}
    if overlaps:
        brick = overlaps[0]["brick"]
        keys = {}
        for release in ("dr10", "dr11"):
            raw = fetch(release+"-ccds.fits", f"https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/{release}/south/coadd/{brick[:3]}/{brick}/legacysurvey-{brick}-ccds.fits")
            with fits.open(io.BytesIO(raw)) as hdus:
                rows = hdus[1].data
                if any(rows["ccd_cuts"] != 0):
                    raise ValueError("rejected CCD in input list")
                keys[release] = [(str(r["camera"]).strip(), int(r["expnum"]), str(r["ccdname"]).strip(), str(r["filter"]).strip()) for r in rows]
        result["native_comparison"] = compare(keys["dr10"], keys["dr11"])
    with (OUT / "results.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
