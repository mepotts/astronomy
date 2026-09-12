"""Bounded public manifest inspection only. Never execute downloaded commands."""

import hashlib
import importlib.util
import json
import re
import shlex
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
URL = "https://archive.stsci.edu/missions/tess/download_scripts/sector/tesscurl_sector_106_lc.sh"
NAME = re.compile(r"tess\d{13}-s0106-(\d{16})-\d{4}-[xsab]_lc\.fits")


def inspect_manifest(content):
    names, tics = [], []
    for line in content.decode("utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        words = shlex.split(line)
        if not words or words[0] != "curl" or words.count("-o") != 1:
            raise ValueError("unexpected manifest command; nothing is executed")
        name = words[words.index("-o") + 1]
        matched = NAME.fullmatch(name)
        urls = [word for word in words if word.startswith("https://")]
        if not matched or len(urls) != 1:
            raise ValueError("unexpected sector/product/URL")
        url = urlsplit(urls[0])
        if (url.netloc != "mast.stsci.edu" or url.path.rstrip("/") != "/api/v0.1/Download/file"
                or parse_qs(url.query) != {"uri": ["mast:TESS/product/" + name]}):
            raise ValueError("unexpected archive endpoint or product URI")
        names.append(name)
        tics.append(matched.group(1))
    if not names:
        raise ValueError("empty manifest is not coverage")
    return {"commands_parsed_not_executed": len(names), "unique_lc_products": len(set(names)),
            "unique_tic_ids": len(set(tics)), "duplicate_product_entries": len(names)-len(set(names)),
            "light_curves_downloaded": 0, "unknown_fluxes_inspected": 0,
            "per_product_public_rights_headers_and_quality_verified": False}


def worker():
    import requests
    destination = ROOT / "data/sector106-manifest"
    destination.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    body = bytearray()
    with requests.get(URL, stream=True, timeout=(10, 30)) as response:
        response.raise_for_status()
        for chunk in response.iter_content(65536):
            if len(body) + len(chunk) > 10_000_000 or time.monotonic()-start > 40:
                raise ValueError("metadata byte/time limit")
            body.extend(chunk)
        last_modified = response.headers.get("Last-Modified")
    with (destination / "manifest.txt").open("xb") as stream:
        stream.write(body)
    report = {"url": URL, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
              "http_last_modified": last_modified, **inspect_manifest(body)}
    with (ROOT / "out/sector106-manifest.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps(report))


if __name__ == "__main__":
    if sys.argv[1:] == ["--worker"]:
        worker()
    elif sys.argv[1:]:
        raise SystemExit("Only the fixed manifest is in scope")
    else:
        path = ROOT.parent / "dyson-revet/scripts/check_e_release.py"
        spec = importlib.util.spec_from_file_location("manifest_timeout", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        code, output = module.bounded_run([sys.executable, "-B", str(Path(__file__).resolve()), "--worker"], 45)
        print(output)
        raise SystemExit(code)
