"""Bounded known-control DASCH M0 retrieval and reproducible offline audit."""

from __future__ import annotations

import argparse
import base64
import csv
import gzip
import hashlib
import io
import json
import re
import statistics
import tarfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from m0_dasch_pilot import (
    STANDARD_BAD_AFLAGS,
    angular_sep_arcsec,
    decimal_year,
    maybe_float,
    sha256_file,
)

BASE = Path(__file__).resolve().parents[1]
API = "https://api.starglass.cfa.harvard.edu/public/dasch/dr7/"
SPEC = BASE / "M0-EXTENSION-SPEC-2026-09-05.md"
RECOVERY_SPEC = BASE / "M0-IMAGE-RECOVERY-AMENDMENT-2026-09-05.md"
RUN = BASE / "data/m0-extension-20260905"
CONTROLS = {"rcnc": "R Cnc", "v404cyg": "V404 Cyg"}
MAX_BYTES = 16 * 1024 * 1024
# Official daschlab.series classifications; diagnostic only, not an added rejection.
# https://daschlab.readthedocs.io/en/latest/_modules/daschlab/series.html
METEOR_SERIES = frozenset({
    "ad", "ai", "al", "bi", "darnor", "darsou", "fa", "ka", "kb", "ke",
    "kf", "kg", "kge", "kh", "meteor", "pz",
})


def text_sha256(path: Path) -> str:
    """Canonical LF text hashes survive Git's Windows checkout conversion."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def table(raw: bytes) -> list[dict[str, str]]:
    payload = json.loads(raw)
    if not isinstance(payload, list) or not payload or not all(
        isinstance(x, str) for x in payload
    ):
        raise ValueError("expected JSON-encoded CSV table")
    reader = csv.DictReader(io.StringIO("\n".join(payload)))
    rows = list(reader)
    if any(None in row or None in row.values() for row in rows):
        raise ValueError("malformed table row")
    return [
        {re.sub(r"(?<!^)(?=[A-Z])", "_", k).lower(): v for k, v in row.items()}
        for row in rows
    ]


def resolve(raw: bytes) -> dict:
    root = ET.fromstring(raw)
    nodes = root.findall(".//Resolver")
    valid = [x for x in nodes if x.find("jradeg") is not None]
    if len(valid) != 1:
        raise ValueError("resolver must yield exactly one coordinate identity")
    node = valid[0]
    return {
        "name": node.findtext("oname"),
        "object_type": node.findtext("otype"),
        "ra_deg": float(node.findtext("jradeg")),
        "dec_deg": float(node.findtext("jdedeg")),
    }


def select_source(rows: list[dict], pos: dict) -> dict | None:
    matches = [
        row for row in rows if angular_sep_arcsec(
            pos["ra_deg"], pos["dec_deg"], float(row["ra_deg"]), float(row["dec_deg"])
        ) <= 5.0
    ]
    return matches[0] if len(matches) == 1 else None


def clean(rows: list[dict]) -> list[dict]:
    result = []
    for row in rows:
        mag = maybe_float(row.get("magcal_magdep"))
        if mag is None:
            continue
        if row.get("aflags") in (None, ""):
            raise ValueError("detection missing quality flags")
        if int(row["aflags"]) & STANDARD_BAD_AFLAGS:
            continue
        coords = [maybe_float(row.get(k)) for k in (
            "ra_deg", "dec_deg", "ra_cat_corrected", "dec_cat_corrected"
        )]
        if None in coords or angular_sep_arcsec(*coords) > 15.0:
            continue
        result.append(row)
    return result


def summarize(rows: list[dict], expected: int, source: dict | None = None) -> dict:
    detected = sum(maybe_float(x.get("magcal_magdep")) is not None for x in rows)
    if detected != expected:
        raise ValueError("catalog/lightcurve detection accounting mismatch")
    if source is not None:
        for row in rows:
            if maybe_float(row.get("magcal_magdep")) is not None and any(
                row.get(key) != source[key] for key in ("ref_number", "gsc_bin_index")
            ):
                raise ValueError("detected row belongs to a different catalog source")
    good = clean(rows)
    mags = sorted(float(x["magcal_magdep"]) for x in good)
    years = [decimal_year(float(x["date_jd"])) for x in good]
    span = max(years) - min(years) if years else 0.0
    quantile_range = None
    if len(mags) >= 2:
        quantiles = statistics.quantiles(mags, n=10, method="inclusive")
        quantile_range = quantiles[8] - quantiles[0]
    return {
        "rows": len(rows), "detections": detected, "clean_detections": len(good),
        "clean_span_years": span,
        "clean_median_mag": statistics.median(mags) if mags else None,
        "p90_minus_p10_mag": quantile_range,
        "clean_meteor_series_detections": sum(x.get("series") in METEOR_SERIES for x in good),
        "access_gate": len(good) >= 20 and span >= 10,
        "coverage_verdict": "MEASURED_KNOWN_VARIABLE" if len(good) >= 20 and span >= 10
        else "INSUFFICIENT_COVERAGE",
        "note": "No quiet/stable classification can be inferred from insufficient coverage.",
    }


class Archive:
    """Immutable cached responses tied to the pre-outcome specification."""

    def __init__(self, directory: Path = RUN):
        self.directory = directory
        self.path = directory / "provenance.json"
        self.bundled = {}
        bundle = directory / "known-control-responses.tar.gz"
        if bundle.exists():
            with tarfile.open(bundle, "r:gz") as tar:
                for member in tar:
                    if not member.isfile() or member.size > MAX_BYTES or Path(member.name).name != member.name:
                        raise ValueError("invalid bundled response member")
                    if member.name in self.bundled or len(self.bundled) >= 32:
                        raise ValueError("duplicate or excessive bundled members")
                    handle = tar.extractfile(member)
                    assert handle is not None
                    self.bundled[member.name] = handle.read(MAX_BYTES + 1)
        if self.path.exists():
            self.manifest = json.loads(self.path.read_text())
            self.verify()
        else:
            self.manifest = {
                "schema_version": 1, "analysis_id": "dasch-m0-extension-20260905",
                "text_hash_policy": "CRLF normalized to LF; raw response digests remain byte-exact",
                "spec_sha256": text_sha256(SPEC),
                "original_provenance_sha256": text_sha256(BASE / "data/provenance.json"),
                "artifacts": {},
            }

    def verify(self):
        if self.manifest.get("schema_version") != 1 or self.manifest.get("analysis_id") != "dasch-m0-extension-20260905":
            raise ValueError("wrong extension provenance identity")
        if self.manifest["spec_sha256"] != text_sha256(SPEC):
            raise ValueError("specification changed since retrieval")
        if self.manifest["original_provenance_sha256"] != text_sha256(BASE / "data/provenance.json"):
            raise ValueError("original provenance changed")
        original = json.loads((BASE / "data/provenance.json").read_text())
        for artifact in original["artifacts"]:
            path = (BASE / artifact["path"]).resolve()
            if not path.is_relative_to(BASE.resolve()):
                raise ValueError("original artifact escapes pilot directory")
            if path.stat().st_size != artifact["bytes"] or sha256_file(path) != artifact["sha256"]:
                raise ValueError("original positive-control artifact mutated")
        if "recovery_spec_sha256" in self.manifest and self.manifest["recovery_spec_sha256"] != text_sha256(RECOVERY_SPEC):
            raise ValueError("exploratory recovery specification changed")
        for role, record in self.manifest["artifacts"].items():
            path = (self.directory / record["file"]).resolve()
            if not path.is_relative_to(self.directory.resolve()):
                raise ValueError("artifact escapes archive directory")
            raw = self.content(record)
            if len(raw) != record["bytes"] or hashlib.sha256(raw).hexdigest() != record["sha256"]:
                raise ValueError(f"cached artifact mutated: {role}")

    def content(self, record: dict) -> bytes:
        path = self.directory / record["file"]
        if path.exists():
            return path.read_bytes()
        if record["file"] in self.bundled:
            return self.bundled[record["file"]]
        raise FileNotFoundError(f"missing raw response or bundle member: {record['file']}")

    def get(self, role: str) -> bytes:
        self.verify()
        return self.content(self.manifest["artifacts"][role])

    def bundle(self):
        self.verify()
        destination = self.directory / "known-control-responses.tar.gz"
        with (destination.open("wb") as raw,
              gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as compressed,
              tarfile.open(fileobj=compressed, mode="w") as tar):
            for record in self.manifest["artifacts"].values():
                content = self.content(record)
                info = tarfile.TarInfo(record["file"])
                info.size = len(content)
                tar.addfile(info, io.BytesIO(content))
        print(f"Known-control bundle: {destination.stat().st_size:,} bytes; {sha256_file(destination)}")

    def fetch(self, role: str, url: str, body: dict | None = None) -> bytes:
        if role in self.manifest["artifacts"]:
            record = self.manifest["artifacts"][role]
            if record["url"] != url or record["request"] != body:
                raise ValueError(f"request changed for cached role: {role}")
            return self.get(role)
        data = None if body is None else json.dumps(body, sort_keys=True).encode()
        req = urllib.request.Request(url, data=data, headers={
            "Content-Type": "application/json", "User-Agent": "astronomy-dasch-m0-known-controls/1.0"
        })
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read(MAX_BYTES + 1)
            status = response.status
        if len(raw) > MAX_BYTES:
            raise ValueError("response exceeds frozen 16 MiB per-request bound")
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / f"{role}.raw"
        if path.exists():
            raise ValueError(f"unmanifested artifact exists: {path.name}")
        path.write_bytes(raw)
        self.manifest["artifacts"][role] = {
            "file": path.name, "url": url, "request": body, "status": status,
            "retrieved_utc": datetime.now(timezone.utc).isoformat(),
            "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
        }
        self.path.write_text(json.dumps(self.manifest, indent=2, sort_keys=True) + "\n")
        print(f"Retrieved {role}: {len(raw):,} bytes", flush=True)
        return raw


def prepare(archive: Archive):
    for key, name in CONTROLS.items():
        url = "https://cds.unistra.fr/cgi-bin/nph-sesame/-oxp/SNV?" + urllib.parse.quote(name)
        pos = resolve(archive.fetch(f"{key}-resolver", url))
        query = {"refcat": "apass", "ra_deg": pos["ra_deg"], "dec_deg": pos["dec_deg"], "radius_arcsec": 30}
        rows = table(archive.fetch(f"{key}-querycat", API + "querycat", query))
        archive.fetch(f"{key}-field", API + "querycat", {**query, "radius_arcsec": 300})
        source = select_source(rows, pos)
        print(f"{name}: {len(rows)} catalog rows; unique <=5 arcsec match: {source is not None}", flush=True)
        if source is not None:
            archive.fetch(f"{key}-lightcurve", API + "lightcurve", {
                "refcat": "apass", "ref_number": int(source["ref_number"]),
                "gsc_bin_index": int(source["gsc_bin_index"]),
            })
        if key == "v404cyg":
            archive.fetch(f"{key}-exposures", API + "queryexps", {
                "ra_deg": pos["ra_deg"], "dec_deg": pos["dec_deg"]
            })
    target = json.loads((BASE / "data/provenance.json").read_text())["target"]
    archive.fetch("tcrb-exposures", API + "queryexps", {
        "ra_deg": target["ra_deg"], "dec_deg": target["dec_deg"]
    })


def exposure_key(row: dict) -> tuple:
    return row["series"], int(row["platenum"]), int(row["solnum"]), int(row["mosnum"])


def exposure_jd(row: dict) -> float | None:
    value = row.get("expdate", "")
    if not value:
        return None
    try:
        instant = datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return instant.timestamp() / 86400.0 + 2440587.5


def image_selections(archive: Archive) -> dict:
    selected = {}
    exps = table(archive.get("tcrb-exposures"))
    by_key = {exposure_key(row): row for row in exps if int(row["solnum"]) >= 0}
    good = clean(table((BASE / "data/raw/tcrb-lightcurve.json").read_bytes()))
    for label, year in (("pre", 1937.0), ("high", 1942.0), ("post", 1947.0)):
        eligible = [x for x in good if abs(decimal_year(float(x["date_jd"])) - year) <= 1]
        point = min(eligible, key=lambda x: (
            abs(decimal_year(float(x["date_jd"])) - year), x["series"],
            int(x["plate_number"]), int(x["solution_number"])
        )) if eligible else None
        row = None
        if point is not None:
            row = by_key.get((point["series"], int(point["plate_number"]),
                              int(point["solution_number"]), int(point["mosaic_number"])))
        selected[f"tcrb-{label}"] = row
    exps = table(archive.get("v404cyg-exposures"))
    good = [x for x in exps if int(x["solnum"]) >= 0 and x["wcssource"] == "imwcs"
            and exposure_jd(x) is not None]
    event = [x for x in good if abs(exposure_jd(x) - 2429200) <= 30]
    pre = [x for x in good if 2429100 - 365 <= exposure_jd(x) < 2429100]
    post = [x for x in good if 2429400 < exposure_jd(x) <= 2429400 + 365]
    for label, rows, metric in (
        ("event", event, lambda x: abs(exposure_jd(x) - 2429200)),
        ("pre", pre, lambda x: -exposure_jd(x)),
        ("post", post, exposure_jd),
    ):
        selected[f"v404cyg-{label}"] = min(rows, key=lambda x: (metric(x), exposure_key(x))) if rows else None
    return selected


def recovery_selections(archive: Archive) -> dict:
    rows = table(archive.get("v404cyg-lightcurve"))
    events = [x for x in clean(rows) if 2429190 <= float(x["date_jd"]) <= 2429250]
    point_key = lambda x: (float(x["date_jd"]), x["series"], int(x["plate_number"]), int(x["solution_number"]))
    event = min(events, key=point_key) if events else None
    output = dict.fromkeys(("v404matched-pre", "v404matched-event", "v404matched-post"))
    if event is None:
        return output
    exps = {exposure_key(x): x for x in table(archive.get("v404cyg-exposures")) if int(x["solnum"]) >= 0}
    eligible = [x for x in rows if x["series"] == event["series"]
                and maybe_float(x["magcal_magdep"]) is None
                and maybe_float(x["limiting_mag_local"]) is not None
                and float(x["limiting_mag_local"]) >= float(event["magcal_magdep"]) + .5]
    pre = [x for x in eligible if 2429100 - 365 <= float(x["date_jd"]) < 2429100]
    post = [x for x in eligible if 2429400 < float(x["date_jd"]) <= 2429400 + 365]
    for role, point in (("event", event),
                        ("pre", max(pre, key=point_key) if pre else None),
                        ("post", min(post, key=point_key) if post else None)):
        if point is None:
            continue
        key = point["series"], int(point["plate_number"]), int(point["solution_number"]), int(point["mosaic_number"])
        if key in exps:
            output[f"v404matched-{role}"] = {
                **exps[key], "target_local_limiting_mag": point["limiting_mag_local"],
                "target_detection_mag": point["magcal_magdep"],
            }
    return output


def fetch_images(archive: Archive, recovery: bool = False):
    if recovery:
        archive.manifest["recovery_spec_sha256"] = text_sha256(RECOVERY_SPEC)
        archive.path.write_text(json.dumps(archive.manifest, indent=2, sort_keys=True) + "\n")
    selected = recovery_selections(archive) if recovery else image_selections(archive)
    selection_file = "recovery-selection.json" if recovery else "image-selection.json"
    (RUN / selection_file).write_text(json.dumps(selected, indent=2, sort_keys=True) + "\n")
    for role, row in selected.items():
        if row is None:
            print(f"{role}: BLOCKED_NO_VALID_EXPOSURE")
            continue
        pos = (json.loads((BASE / "data/provenance.json").read_text())["target"]
               if role.startswith("tcrb") else resolve(archive.get("v404cyg-resolver")))
        print(f"{role}: {row['series']}{int(row['platenum']):05d} {row['expdate']}", flush=True)
        archive.fetch(f"{role}-cutout", API + "cutout", {
            "plate_id": f"{row['series']}{int(row['platenum']):05d}",
            "solution_number": int(row["solnum"]),
            "center_ra_deg": pos["ra_deg"], "center_dec_deg": pos["dec_deg"],
        })


def decode_cutout(raw: bytes) -> bytes:
    compressed = base64.b64decode(json.loads(raw), validate=True)
    with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as handle:
        binary = handle.read(8 * 1024 * 1024 + 1)
    if len(binary) > 8 * 1024 * 1024:
        raise ValueError("decoded FITS exceeds 8 MiB size bound")
    if not binary.startswith(b"SIMPLE  ="):
        raise ValueError("cutout payload is not a primary FITS image")
    return binary


def render_images(archive: Archive):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from astropy.io import fits
    from astropy.wcs import WCS

    selected = image_selections(archive)
    selected.update(recovery_selections(archive))
    results = {}
    output = BASE / "figures"
    output.mkdir(exist_ok=True)
    for target, labels in (("tcrb", ("pre", "high", "post")), ("v404cyg", ("pre", "event", "post")),
                           ("v404matched", ("pre", "event", "post"))):
        fig, axes = plt.subplots(2, 3, figsize=(13, 9))
        for column, label in enumerate(labels):
            role = f"{target}-{label}"
            row = selected[role]
            if row is None:
                for axis in axes[:, column]:
                    axis.text(.5, .5, "NO VALID EXPOSURE", ha="center")
                results[role] = {"status": "BLOCKED_NO_VALID_EXPOSURE"}
                continue
            raw = archive.get(f"{role}-cutout")
            binary = decode_cutout(raw)
            with fits.open(io.BytesIO(binary)) as hdus:
                data = hdus[0].data.astype(float)
                header = hdus[0].header.copy()
            if data.ndim != 2:
                raise ValueError("cutout must be 2-dimensional")
            record = archive.manifest["artifacts"][f"{role}-cutout"]
            pos = record["request"]
            x, y = WCS(header).world_to_pixel_values(pos["center_ra_deg"], pos["center_dec_deg"])
            center = data[round(float(y)), round(float(x))]
            finite = data[np.isfinite(data)]
            lo, hi = np.percentile(finite, [5, 99.8])
            for index, axis in enumerate(axes[:, column]):
                axis.imshow(data, origin="lower", cmap="gray_r", vmin=lo, vmax=hi)
                axis.plot([x - 22, x - 9], [y, y], color="red", linewidth=.8)
                axis.plot([x + 9, x + 22], [y, y], color="red", linewidth=.8)
                axis.plot([x, x], [y - 22, y - 9], color="red", linewidth=.8)
                if index:
                    axis.set_xlim(x - 60, x + 60)
                    axis.set_ylim(y - 60, y + 60)
                axis.set_title(f"{label}: {row['series']}{int(row['platenum']):05d}\n{row['expdate'][:10]}")
                axis.set_xlabel("resampled pixel (1.44 arcsec)")
            results[role] = {
                "status": "VALID_FITS_PENDING_VISUAL_REVIEW", "shape": list(data.shape),
                "finite_fraction": float(len(finite) / data.size),
                "center_xy_zero_based": [float(x), float(y)], "center_finite": bool(np.isfinite(center)),
                "plate_id": pos["plate_id"], "date": row["expdate"],
                "exposure_minutes": row["exptime"], "field_limiting_mag_apass": row["lim_mag_apass"],
                "target_local_limiting_mag": row.get("target_local_limiting_mag"),
                "target_detection_mag": row.get("target_detection_mag"),
                "decoded_fits_sha256": hashlib.sha256(binary).hexdigest(),
            }
        fig.suptitle(f"DASCH DR7 known control: {target}\nTop: full cutout; bottom: fixed central crop. Independent 5–99.8% density stretches; not calibrated flux.")
        fig.tight_layout()
        fig.savefig(output / f"m0-{target}-epochs-20260905.png", dpi=130)
        plt.close(fig)
    archive.verify()
    (RUN / "image-results.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    print(json.dumps(results, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["fetch", "images", "recovery", "render", "analyze", "bundle"])
    args = parser.parse_args()
    archive = Archive()
    if args.mode == "bundle":
        archive.bundle()
        return
    if args.mode == "fetch":
        prepare(archive)
        return
    if args.mode == "images":
        fetch_images(archive)
        return
    if args.mode == "recovery":
        fetch_images(archive, recovery=True)
        return
    if args.mode == "render":
        render_images(archive)
        return
    result = {"discovery_scan": "NOT_RUN", "controls": {}, "spec_sha256": text_sha256(SPEC)}
    for key, name in CONTROLS.items():
        pos = resolve(archive.get(f"{key}-resolver"))
        rows = table(archive.get(f"{key}-querycat"))
        field = table(archive.get(f"{key}-field"))
        source = select_source(rows, pos)
        info = {"name": name, "position": pos, "catalog_rows_30_arcsec": len(rows),
                "catalog_rows_300_arcsec_box": len(field),
                "identity_status": "UNIQUE" if source else "AMBIGUOUS_OR_MISSING"}
        if source:
            info["catalog"] = source
            info["lightcurve"] = summarize(table(archive.get(f"{key}-lightcurve")), int(source["num_matches"]), source)
        else:
            info["access_gate"] = False
            info["coverage_verdict"] = "INSUFFICIENT_COVERAGE"
        result["controls"][key] = info
    archive.verify()
    (RUN / "lightcurve-results.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
