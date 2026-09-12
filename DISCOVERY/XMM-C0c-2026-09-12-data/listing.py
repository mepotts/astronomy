"""Single bounded public directory-index acquisition, never linked products."""

import hashlib
import importlib.util
import json
import logging
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve()
PROTOCOL = HERE.parent / "XMM-C0c-2026-09-12.md"
HELPER = HERE.parents[1] / "dyson-revet/scripts/check_e_release.py"
HELPER_HASH = "11ad0bef9fd2efae234e204358c6b6730e723ed3dc24c6fe0c345f2ddcfb53dd"
URL = "https://heasarc.gsfc.nasa.gov/FTP/xmm/data/rev0/0884250101/PPS/"
CAP = 262144
SAFE_HEADERS = ("Content-Type", "Content-Length", "Content-Encoding", "Date", "ETag", "Last-Modified")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write("\n")


def collect():
    import requests

    with requests.Session() as session:
        session.trust_env = False
        session.auth = None
        session.cookies.clear()
        with session.get(URL, timeout=(5, 15), stream=True, allow_redirects=False,
                         headers={"Accept-Encoding": "identity"}) as response:
            save("http.json", {"status": response.status_code, "url": response.url,
                               "headers": {k: response.headers[k] for k in SAFE_HEADERS if k in response.headers}})
            if response.headers.get("Content-Encoding", "identity").lower() not in ("identity", ""):
                raise ValueError("STOP_CONTENT_ENCODING")
            count = 0
            with (HERE / "index.html").open("xb") as handle:
                while True:
                    chunk = response.raw.read(min(8192, CAP - count + 1), decode_content=False)
                    if not chunk:
                        break
                    keep = chunk[:CAP - count]
                    handle.write(keep)
                    count += len(keep)
                    if len(chunk) > len(keep):
                        raise ValueError("STOP_BYTE_CAP")
            if response.status_code != 200:
                raise ValueError(f"STOP_HTTP_{response.status_code}")
            declared = response.headers.get("Content-Length")
            if count == 0 or (declared is not None and int(declared) != count):
                raise ValueError("STOP_RESPONSE_LENGTH")
            if "html" not in response.headers.get("Content-Type", "").lower():
                raise ValueError("STOP_NOT_HTML")


def validate_completion():
    path = HERE / "index.html"
    receipt = json.loads((HERE / "worker-result.json").read_bytes())
    http = json.loads((HERE / "http.json").read_bytes())
    marker = json.loads((HERE / "worker-start.json").read_bytes())
    start = json.loads((HERE / "run-start.json").read_bytes())
    headers = http["headers"]
    if (receipt["status"] != "HTTP_INDEX_RETAINED" or receipt["request_attempts"] != 1
            or receipt["science_products_fetched"] != 0
            or receipt["body"] != {"bytes": path.stat().st_size, "sha256": sha(path)}
            or not 0 < path.stat().st_size <= CAP or http["status"] != 200 or http["url"] != URL
            or not set(headers) <= set(SAFE_HEADERS)
            or headers.get("Content-Encoding", "identity").lower() not in ("identity", "")
            or "html" not in headers.get("Content-Type", "").lower()
            or ("Content-Length" in headers and int(headers["Content-Length"]) != path.stat().st_size)
            or marker != {"url": URL, "request_attempts": 1}
            or start != {"url": URL, "cap": CAP, "worker_seconds": 30,
                         "source_sha256": sha(SOURCE), "helper_sha256": HELPER_HASH,
                         "protocol_sha256": sha(HERE / "protocol.snapshot.md")}
            or sha(HELPER) != HELPER_HASH):
        raise ValueError("STOP_RECEIPT")


def worker():
    start = json.loads((HERE / "run-start.json").read_bytes())
    if (start["source_sha256"] != sha(SOURCE) or start["helper_sha256"] != sha(HELPER)
            or start["protocol_sha256"] != sha(HERE / "protocol.snapshot.md")):
        raise ValueError("STOP_PROVENANCE")
    save("worker-start.json", {"url": URL, "request_attempts": 1})
    result = {"status": "STOP", "request_attempts": 1, "science_products_fetched": 0}
    try:
        collect()
        result["status"] = "HTTP_INDEX_RETAINED"
    except Exception as error:
        logging.getLogger(__name__).exception("Index request failed")
        result["error"] = f"{type(error).__name__}: {error}"
    finally:
        path = HERE / "index.html"
        result["body"] = {"bytes": path.stat().st_size, "sha256": sha(path)} if path.exists() else None
        save("worker-result.json", result)
    return 0 if result["status"] == "HTTP_INDEX_RETAINED" else 1


def run():
    if sha(HELPER) != HELPER_HASH:
        raise ValueError("STOP_HELPER_HASH")
    save("run-start.json", {"url": URL, "cap": CAP, "worker_seconds": 30,
                           "source_sha256": sha(SOURCE), "helper_sha256": sha(HELPER),
                           "protocol_sha256": sha(PROTOCOL)})
    with (HERE / "protocol.snapshot.md").open("xb") as handle:
        handle.write(PROTOCOL.read_bytes())
    result = {"status": "STOP", "science_products_fetched": 0}
    start = time.monotonic()
    try:
        spec = importlib.util.spec_from_file_location("xmm_index_deadline", HELPER)
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        code, output = helper.bounded_run([str(Path(sys.executable).resolve()), "-B", str(SOURCE), "_worker"], 30)
        result.update(worker_returncode=code, worker_output=output)
        if code:
            raise ValueError("STOP_WORKER")
        validate_completion()
        result["status"] = "HTTP_INDEX_RETAINED"
    except Exception as error:
        logging.getLogger(__name__).exception("Index parent validation or cleanup failed")
        result["error"] = f"{type(error).__name__}: {error}"
    finally:
        result["elapsed_seconds"] = time.monotonic() - start
        result["artifacts"] = {p.name: sha(p) for p in HERE.iterdir() if p.is_file()}
        save("outcome.json", result)
    print(json.dumps(result))
    return 0 if result["status"] == "HTTP_INDEX_RETAINED" else 1


if __name__ == "__main__":
    if sys.argv[1:] == ["run"]:
        raise SystemExit(run())
    if sys.argv[1:] == ["_worker"]:
        raise SystemExit(worker())
    raise SystemExit("Only run or internal _worker is accepted")
